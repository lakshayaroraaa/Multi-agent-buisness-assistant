"""Shared Azure AI Foundry agent factory helpers."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def agent_tool(function: F) -> F:
    """Mark a typed, documented Python function as a Foundry callable tool.

    ``FunctionTool`` uses the decorated function's name, annotations, and docstring
    to build the function-calling definition. The marker also makes tools easy for
    an orchestrator to inspect without depending on the SDK internals.
    """

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return function(*args, **kwargs)

    setattr(wrapper, "is_agent_tool", True)
    return wrapper  # type: ignore[return-value]


def _project_endpoint_from_connection_string(connection_string: str) -> str:
    """Normalize the project's configured connection string to an Agents endpoint.

    Foundry deployments commonly provide either the full project endpoint or a
    semicolon-separated connection string containing an endpoint and project name.
    Keeping this translation here lets agent factories expose one stable interface.
    """

    connection_string = connection_string.strip()
    if connection_string.startswith(("https://", "http://")) and ";" not in connection_string:
        return connection_string.rstrip("/")

    parts = {
        key.strip().casefold(): value.strip()
        for segment in connection_string.split(";")
        if "=" in segment
        for key, value in [segment.split("=", 1)]
    }
    endpoint = parts.get("endpoint") or parts.get("project_endpoint")
    project_name = parts.get("projectname") or parts.get("project_name")
    if not endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_CONNECTION_STRING must be a Foundry project endpoint "
            "or include endpoint=<url>."
        )

    endpoint = endpoint.rstrip("/")
    if "/api/projects/" in endpoint:
        return endpoint
    if not project_name:
        raise ValueError(
            "AZURE_AI_PROJECT_CONNECTION_STRING has an endpoint without a project. "
            "Include projectname=<name> or use the full /api/projects/<project> endpoint."
        )
    return f"{endpoint}/api/projects/{project_name}"


def create_foundry_agent(
    *,
    name: str,
    system_prompt: str,
    model_deployment_name: str,
    tool_functions: Sequence[Callable[..., Any]],
) -> Any:
    """Create a Foundry agent from a consistent specialist-agent contract.

    The caller owns execution of function calls returned by Foundry. This helper
    only registers the local functions' schemas with the created agent.
    """

    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError(
            "AZURE_AI_PROJECT_CONNECTION_STRING is not set. "
            "Copy .env.example to .env and provide the project connection string."
        )
    if not model_deployment_name:
        raise ValueError("model_deployment_name must be a non-empty deployment name.")
    # Keep tool modules importable for direct unit tests without Azure installed.
    from azure.ai.agents.models import FunctionTool
    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    function_tool = FunctionTool(functions=set(tool_functions)) if tool_functions else None
    agent_client = AgentsClient(
        endpoint=_project_endpoint_from_connection_string(connection_string),
        credential=DefaultAzureCredential(),
    )
    return agent_client.create_agent(
        model=model_deployment_name,
        name=name,
        instructions=system_prompt,
        tools=function_tool.definitions if function_tool else None,
    )
