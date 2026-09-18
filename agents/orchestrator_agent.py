"""Orchestrator agent: routes to specialists and actually executes their tools.

Azure AI Foundry's Connected Agents feature lets a parent agent delegate to
child agents by natural language, but as of this writing it has no hook for the
*client* to answer a child agent's function-tool calls during a nested run —
Connected Agents work for child agents that only use built-in/OpenAPI tools,
not for agents whose tools are local Python functions like ours. Since every
specialist agent in this project uses local function tools (see tools/), this
module does NOT use Connected Agents for execution. Instead, the orchestrator
agent's own tools are four small Python functions ("call_finance_agent" etc.)
that, when the orchestrator's LLM decides to call one, run a full nested
thread/run/tool-submission cycle against that specialist directly. This keeps
routing "the LLM's decision" (true multi-agent behaviour) while keeping tool
execution fully under our control.

If you are on a newer azure-ai-agents release where Connected Agents supports
client-side function tool execution, you can simplify this file considerably —
check the current docs at https://learn.microsoft.com/azure/ai-services/agents/
before assuming the workaround below is still necessary.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Protocol
from uuid import uuid4

from agents.finance_agent import FINANCE_SYSTEM_PROMPT, FINANCE_TOOLS, create_finance_agent
from agents.hr_agent import HR_SYSTEM_PROMPT, HR_TOOLS, create_hr_agent
from agents.knowledge_agent import KNOWLEDGE_SYSTEM_PROMPT, KNOWLEDGE_TOOLS, create_knowledge_agent
from agents.sales_agent import SALES_SYSTEM_PROMPT, SALES_TOOLS, create_sales_agent
from shared.agent_base import _project_endpoint_from_connection_string
from shared.conversation_store import ConversationStore
from shared.schemas import ConversationTurn, SpecialistCallRecord

ORCHESTRATOR_AGENT_NAME = "business-assistant-orchestrator"

ORCHESTRATOR_SYSTEM_PROMPT = """You are the orchestration layer for an internal business assistant. You do not answer from your own knowledge: you only call your tools and synthesize their results.

You have one tool per specialist:
- call_finance_agent: invoices, budgets, pending approvals, expense reports.
- call_sales_agent: leads, pipeline, customer history, draft quotes.
- call_hr_agent: the requesting employee's time off, onboarding, benefits, internal postings, and HR policy questions.
- call_knowledge_agent: company documentation and policy lookups not covered above.

Call every specialist whose domain applies to the request, even if that means calling more than one tool, and merge their results into one concise answer. If the request is too ambiguous to route confidently, ask a clarifying question instead of guessing. Never fabricate a fact, status, price, or policy: report only what a specialist tool returned, and say plainly if a specialist could not answer."""

# Each entry: (tool name exposed to the orchestrator LLM, that specialist's own
# system prompt used as the tool's description, its Foundry agent factory, its
# local tool functions).
_SPECIALISTS: tuple[tuple[str, str, Callable[[], Any], Sequence[Callable[..., Any]]], ...] = (
    ("call_finance_agent", FINANCE_SYSTEM_PROMPT, create_finance_agent, FINANCE_TOOLS),
    ("call_sales_agent", SALES_SYSTEM_PROMPT, create_sales_agent, SALES_TOOLS),
    ("call_hr_agent", HR_SYSTEM_PROMPT, create_hr_agent, HR_TOOLS),
    ("call_knowledge_agent", KNOWLEDGE_SYSTEM_PROMPT, create_knowledge_agent, KNOWLEDGE_TOOLS),
)


def _run_agent_thread(
    client: Any,
    agent_id: str,
    user_message: str,
    tool_functions: Sequence[Callable[..., Any]],
    *,
    timeout_seconds: float,
) -> str:
    """Run one thread to completion against a single Foundry agent, answering
    every function-tool call it makes along the way, and return its final
    text reply. Used for both specialist agents and the orchestrator itself.
    """
    from azure.ai.agents.models import ListSortOrder, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput

    tools_by_name = {function.__name__: function for function in tool_functions}
    thread = client.threads.create()
    client.messages.create(thread_id=thread.id, role="user", content=user_message)
    run = client.runs.create(thread_id=thread.id, agent_id=agent_id)

    deadline = time.monotonic() + timeout_seconds
    while run.status in ("queued", "in_progress", "requires_action"):
        if time.monotonic() > deadline:
            raise TimeoutError(f"Agent {agent_id} did not finish within {timeout_seconds}s.")

        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if not isinstance(tool_call, RequiredFunctionToolCall):
                    continue
                function = tools_by_name.get(tool_call.function.name)
                if function is None:
                    payload: Any = {"error": f"Unknown tool {tool_call.function.name!r}."}
                else:
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                        result = function(**arguments)
                        payload = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
                    except Exception as error:  # noqa: BLE001 - surfaced to the model as a tool error, not raised
                        payload = {"error": str(error)}
                tool_outputs.append(ToolOutput(tool_call_id=tool_call.id, output=json.dumps(payload, default=str)))
            run = client.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)
        else:
            time.sleep(0.5)
            run = client.runs.get(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        raise RuntimeError(f"Agent {agent_id} run ended with status {run.status!r}.")

    for message in client.messages.list(thread_id=thread.id, order=ListSortOrder.DESCENDING):
        if message.role == "assistant" and message.text_messages:
            return message.text_messages[-1].text.value
    raise RuntimeError(f"Agent {agent_id} completed without returning a text message.")


def _bind_specialist_tool(
    *, name: str, description: str, client: Any, agent_id: str, tool_functions: Sequence[Callable[..., Any]], timeout_seconds: float
) -> Callable[[str], str]:
    """Build one orchestrator-facing tool function that runs a specialist's full thread/run cycle."""

    def _tool(user_message: str) -> str:
        return _run_agent_thread(client, agent_id, user_message, tool_functions, timeout_seconds=timeout_seconds)

    _tool.__name__ = name
    _tool.__doc__ = f"Delegate to the specialist agent whose domain is: {description}"
    return _tool


def _with_call_logging(tool: Callable[[str], str], call_log: list[SpecialistCallRecord]) -> Callable[[str], str]:
    """Wrap a specialist tool so every invocation is recorded for telemetry/debugging."""

    @wraps(tool)
    def _logged(user_message: str) -> str:
        started = time.perf_counter()
        try:
            result = tool(user_message)
            call_log.append(SpecialistCallRecord(
                agent_name=tool.__name__, reason="Selected by the orchestrator agent's function-calling decision.",
                duration_ms=int((time.perf_counter() - started) * 1000), raw_response=result,
            ))
            return result
        except Exception as error:
            call_log.append(SpecialistCallRecord(
                agent_name=tool.__name__, reason="Selected by the orchestrator agent's function-calling decision.",
                duration_ms=int((time.perf_counter() - started) * 1000), error=str(error),
            ))
            raise

    return _logged


class Runtime(Protocol):
    def respond(self, user_message: str, history: list[ConversationTurn], timeout_seconds: float) -> tuple[str, list[SpecialistCallRecord]]: ...


class FoundryToolLoopRuntime:
    """Production route: creates every agent once, then runs real thread/run
    cycles per message. The orchestrator and specialist agents are cached
    after first use so repeated messages don't re-create them.
    """

    def __init__(self) -> None:
        self._client: Any | None = None
        self._orchestrator_agent_id: str | None = None
        self._tool_functions: list[Callable[[str], str]] | None = None

    def _ensure_agents(self, timeout_seconds: float) -> None:
        if self._client is not None:
            return
        from azure.ai.agents import AgentsClient
        from azure.ai.agents.models import FunctionTool
        from azure.identity import DefaultAzureCredential

        connection_string = os.environ["AZURE_AI_PROJECT_CONNECTION_STRING"]
        client = AgentsClient(
            endpoint=_project_endpoint_from_connection_string(connection_string),
            credential=DefaultAzureCredential(),
        )

        tool_functions = []
        for tool_name, prompt, factory, tool_funcs in _SPECIALISTS:
            specialist_agent = factory()
            tool_functions.append(_bind_specialist_tool(
                name=tool_name, description=prompt, client=client, agent_id=specialist_agent.id,
                tool_functions=tool_funcs, timeout_seconds=timeout_seconds,
            ))

        function_tool = FunctionTool(functions=set(tool_functions))
        orchestrator_agent = client.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name=ORCHESTRATOR_AGENT_NAME,
            instructions=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=function_tool.definitions,
        )

        self._client = client
        self._orchestrator_agent_id = orchestrator_agent.id
        self._tool_functions = tool_functions

    def respond(self, user_message: str, history: list[ConversationTurn], timeout_seconds: float) -> tuple[str, list[SpecialistCallRecord]]:
        try:
            self._ensure_agents(timeout_seconds)
        except Exception as error:
            return (f"I couldn't set up the assistant's agents: {error}", [])

        call_log: list[SpecialistCallRecord] = []
        logged_tools = [_with_call_logging(tool, call_log) for tool in self._tool_functions or []]
        try:
            final_text = _run_agent_thread(
                self._client, self._orchestrator_agent_id, user_message, logged_tools, timeout_seconds=timeout_seconds,
            )
        except Exception as error:
            return (f"I couldn't complete that request: {error}", call_log)
        return (final_text, call_log)


class OfflineRoutingRuntime:
    """Deterministic, credential-free test harness and CLI preview. Not the production path."""

    def __init__(self, invoker: Callable[[str, str], str]) -> None:
        self._invoker = invoker

    @staticmethod
    def select_agents(user_message: str) -> list[tuple[str, str]]:
        text = user_message.casefold()
        selected: list[tuple[str, str]] = []
        if any(word in text for word in ("invoice", "budget", "expense", "approval")):
            selected.append(("finance-agent", "The request contains a finance record or budget topic."))
        if any(word in text for word in ("deal", "lead", "pipeline", "quote", "customer")):
            selected.append(("sales-agent", "The request contains a sales, deal, or customer topic."))
        if any(word in text for word in ("policy", "procedure", "benefit", "remote work")):
            selected.append(("knowledge-agent", "The request asks for internal policy or documentation."))
        return selected

    def respond(self, user_message: str, history: list[ConversationTurn], timeout_seconds: float) -> tuple[str, list[SpecialistCallRecord]]:
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        selected = self.select_agents(user_message)
        if not selected:
            return ("Could you clarify whether you need Finance, Sales, or company Knowledge information?", [])
        calls: list[SpecialistCallRecord] = []
        with ThreadPoolExecutor(max_workers=len(selected)) as executor:
            pending = [(name, reason, executor.submit(self._invoker, name, user_message)) for name, reason in selected]
            for name, reason, future in pending:
                started = time.perf_counter()
                try:
                    response = future.result(timeout=timeout_seconds)
                    record = SpecialistCallRecord(agent_name=name, reason=reason, duration_ms=int((time.perf_counter() - started) * 1000), raw_response=response)
                except FuturesTimeoutError:
                    record = SpecialistCallRecord(agent_name=name, reason=reason, duration_ms=int(timeout_seconds * 1000), error=f"Timed out after {timeout_seconds}s")
                except Exception as error:
                    record = SpecialistCallRecord(agent_name=name, reason=reason, duration_ms=int((time.perf_counter() - started) * 1000), error=str(error))
                print(json.dumps({"event": "specialist_called", **record.model_dump(mode="json")}))
                calls.append(record)
        pieces = [call.raw_response for call in calls if call.raw_response]
        failures = [f"{call.agent_name}: {call.error}" for call in calls if call.error]
        if failures:
            pieces.append("Some specialist information was unavailable (" + "; ".join(failures) + ").")
        return ("\n\n".join(pieces), calls)


def handle_message(
    session_id: str,
    user_message: str,
    *,
    store: ConversationStore | Any | None = None,
    runtime: Runtime | None = None,
    timeout_seconds: float = 30,
) -> str:
    """Load context, delegate through the orchestrator, persist one turn, return text."""
    if not session_id.strip() or not user_message.strip():
        raise ValueError("session_id and user_message must both be non-empty.")
    store = store or ConversationStore.from_environment()
    runtime = runtime or FoundryToolLoopRuntime()
    history = store.get_recent_history(session_id, turns=5)
    final_response, calls = runtime.respond(user_message, history, timeout_seconds)
    turn = ConversationTurn(
        id=str(uuid4()), session_id=session_id, timestamp=datetime.now(timezone.utc),
        user_message=user_message, agents_called=[call.agent_name for call in calls],
        specialist_calls=calls, final_response=final_response,
    )
    store.save_turn(turn)
    return final_response
