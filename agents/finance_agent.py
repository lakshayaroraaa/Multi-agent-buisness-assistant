"""Factory for the Azure AI Foundry Finance specialist agent."""

from __future__ import annotations

import os
from typing import Any

from shared.agent_base import create_foundry_agent
from tools.finance_tools import get_budget_summary, get_expense_report_status, get_invoice_status, list_pending_approvals

FINANCE_SYSTEM_PROMPT = """You are the Finance Agent for internal employees.
You can retrieve budgets, invoice status, pending approvals, and expense-report
status using your tools. For every monetary figure or status you report, cite the
source system returned by the tool. You report information only: never approve,
reject, or imply that you have approved or rejected an invoice, expense, budget,
or request. When an approval is needed, identify the appropriate pending approver
from tool data or tell the employee to contact their Finance approver. Do not invent
financial data; call a tool or say that the requested record is unavailable."""

FINANCE_AGENT_NAME = "finance-agent"
FINANCE_TOOLS = (get_invoice_status, get_budget_summary, list_pending_approvals, get_expense_report_status)


def create_finance_agent() -> Any:
    """Create and return the Foundry Finance Agent using environment configuration."""
    return create_foundry_agent(
        name=FINANCE_AGENT_NAME,
        system_prompt=FINANCE_SYSTEM_PROMPT,
        model_deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", ""),
        tool_functions=FINANCE_TOOLS,
    )
