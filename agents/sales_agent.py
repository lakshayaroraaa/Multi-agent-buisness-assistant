"""Factory for the Azure AI Foundry Sales specialist agent."""

from __future__ import annotations

import os
from typing import Any

from shared.agent_base import create_foundry_agent
from tools.sales_tools import draft_quote, get_customer_history, get_lead_status, get_pipeline_summary

SALES_SYSTEM_PROMPT = """You are the Sales Agent for internal employees.
You can look up lead status, pipeline summaries, customer history, and draft quotes
using your tools. A quote is always a draft and is never sent by you. Do not commit
to a discount above 15 percent: if a draft quote flags manager approval, clearly
state that sales-manager approval is required before the price can be offered or
sent. Do not invent CRM, pricing, or customer data; call a tool or say the record
is unavailable. Cite the source system returned by a tool for factual sales data."""

SALES_AGENT_NAME = "sales-agent"
SALES_TOOLS = (get_lead_status, get_pipeline_summary, draft_quote, get_customer_history)


def create_sales_agent() -> Any:
    """Create and return the Foundry Sales Agent using environment configuration."""
    return create_foundry_agent(
        name=SALES_AGENT_NAME,
        system_prompt=SALES_SYSTEM_PROMPT,
        model_deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", ""),
        tool_functions=SALES_TOOLS,
    )
