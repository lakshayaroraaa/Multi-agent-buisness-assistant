from agents.orchestrator_agent import OfflineRoutingRuntime, handle_message
from shared.conversation_store import InMemoryConversationStore


def _fake_invoker(agent_name: str, user_message: str) -> str:
    return f"{agent_name} response"


def _called_agents(message: str) -> list[str]:
    store = InMemoryConversationStore()
    handle_message("test-session", message, store=store, runtime=OfflineRoutingRuntime(_fake_invoker))
    return store.get_recent_history("test-session")[0].agents_called


def test_invoice_routes_to_finance_only() -> None:
    assert _called_agents("What's the status of invoice INV-2201?") == ["finance-agent"]


def test_deal_and_budget_routes_to_sales_and_finance() -> None:
    assert _called_agents("Is the Acme deal still open and what's our Q3 marketing budget?") == ["finance-agent", "sales-agent"]


def test_policy_routes_to_knowledge() -> None:
    assert _called_agents("What's our remote work policy?") == ["knowledge-agent"]


def test_ambiguous_message_asks_for_clarification() -> None:
    store = InMemoryConversationStore()
    response = handle_message("test-session", "give me an update", store=store, runtime=OfflineRoutingRuntime(_fake_invoker))
    assert "clarify" in response.casefold()
    assert store.get_recent_history("test-session")[0].agents_called == []
