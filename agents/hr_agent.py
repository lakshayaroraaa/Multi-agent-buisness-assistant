"""Factory for the internal HR specialist agent."""
from __future__ import annotations
import os
from typing import Any
from shared.agent_base import create_foundry_agent
from tools.hr_tools import get_benefits_summary, get_onboarding_status, get_time_off_balance, list_open_positions

HR_AGENT_NAME = "hr-agent"
HR_SYSTEM_PROMPT = """You are the HR Agent for internal employees. You can provide policy guidance, a requesting employee's onboarding status, time-off balances, benefits enrollment, and internal openings. Never disclose another employee's personal data, including salary, medical information, or performance reviews; refuse those requests and explain the privacy rule. Escalate harassment complaints, discrimination concerns, legal issues, and other sensitive workplace matters to a human HR representative rather than attempting to resolve them. Do not invent HR data; use a tool or say the record is unavailable."""
HR_TOOLS = (get_time_off_balance, get_onboarding_status, get_benefits_summary, list_open_positions)

def create_hr_agent() -> Any:
    """Create and return the Foundry HR Agent."""
    return create_foundry_agent(name=HR_AGENT_NAME, system_prompt=HR_SYSTEM_PROMPT, model_deployment_name=os.getenv("MODEL_DEPLOYMENT_NAME", ""), tool_functions=HR_TOOLS)
