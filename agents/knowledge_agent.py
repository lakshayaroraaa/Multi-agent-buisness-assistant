"""Factory for the RAG-only company knowledge specialist."""

from __future__ import annotations

import os
from typing import Any

from shared.agent_base import create_foundry_agent
from tools.knowledge_tools import search_knowledge_base

KNOWLEDGE_AGENT_NAME = "knowledge-agent"
KNOWLEDGE_SYSTEM_PROMPT = """You are the Knowledge Agent for internal employees. Answer only from chunks returned by search_knowledge_base. Cite the source document name for every answer. If no relevant chunks are returned, say exactly: 'I couldn't find that in our documentation.' Do not answer from general knowledge, infer missing policy details, or use uncited information."""


KNOWLEDGE_TOOLS = (search_knowledge_base,)


def create_knowledge_agent() -> Any:
    """Create and return the Foundry RAG Knowledge Agent."""
    return create_foundry_agent(
        name=KNOWLEDGE_AGENT_NAME,
        system_prompt=KNOWLEDGE_SYSTEM_PROMPT,
        model_deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", ""),
        tool_functions=KNOWLEDGE_TOOLS,
    )
