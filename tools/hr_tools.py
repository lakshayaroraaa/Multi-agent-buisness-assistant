"""Validated mock HR tools; each private mock is an API replacement seam."""

from __future__ import annotations

import os
from datetime import date

from shared.agent_base import agent_tool
from shared.schemas import (
    BenefitsSummaryInput, BenefitsSummaryOutput, OnboardingStatusInput,
    OnboardingStatusOutput, OpenPosition, OpenPositionsInput, OpenPositionsOutput,
    TimeOffBalanceInput, TimeOffBalanceOutput,
)


def _mock_employee(employee_id: str) -> dict[str, object] | None:
    return {
        "EMP-1001": {"vacation_days": 12.5, "sick_days": 6.0, "accrual_rate": "1.67 vacation days/month", "completed_items": ["Identity verification", "Payroll setup", "Security training"], "pending_items": ["Benefits enrollment", "Equipment confirmation"], "start_date": date(2026, 9, 1), "enrolled_plans": ["Medical PPO", "Dental", "Vision", "401(k)"], "enrollment_deadline": date(2026, 10, 1)}
    }.get(employee_id)


def _require_employee(employee_id: str) -> dict[str, object]:
    requesting_employee_id = os.getenv("HR_REQUESTING_EMPLOYEE_ID", "EMP-1001")
    if employee_id != requesting_employee_id:
        raise PermissionError(
            "HR privacy rule: you may only access your own HR information. "
            "Contact a human HR representative for another employee's data."
        )
    employee = _mock_employee(employee_id)
    if employee is None:
        raise ValueError(f"Unknown employee_id: {employee_id!r}.")
    return employee


@agent_tool
def get_time_off_balance(employee_id: str) -> TimeOffBalanceOutput:
    """Return the requesting employee's vacation and sick leave balances."""
    request = TimeOffBalanceInput(employee_id=employee_id)
    record = _require_employee(request.employee_id)
    return TimeOffBalanceOutput(employee_id=request.employee_id, vacation_days=record["vacation_days"], sick_days=record["sick_days"], accrual_rate=record["accrual_rate"], source_system="Mock HRIS")


@agent_tool
def get_onboarding_status(employee_id: str) -> OnboardingStatusOutput:
    """Return the requesting employee's completed and pending onboarding tasks."""
    request = OnboardingStatusInput(employee_id=employee_id)
    record = _require_employee(request.employee_id)
    return OnboardingStatusOutput(employee_id=request.employee_id, completed_items=record["completed_items"], pending_items=record["pending_items"], start_date=record["start_date"], source_system="Mock HRIS")


@agent_tool
def get_benefits_summary(employee_id: str) -> BenefitsSummaryOutput:
    """Return the requesting employee's enrolled benefit plans and deadline."""
    request = BenefitsSummaryInput(employee_id=employee_id)
    record = _require_employee(request.employee_id)
    return BenefitsSummaryOutput(employee_id=request.employee_id, enrolled_plans=record["enrolled_plans"], enrollment_deadline=record["enrollment_deadline"], source_system="Mock Benefits Portal")


def _mock_positions() -> list[dict[str, str]]:
    return [
        {"position_id": "JOB-101", "title": "People Analytics Specialist", "department": "People Operations", "location": "Remote - US", "employment_type": "Full-time"},
        {"position_id": "JOB-102", "title": "Account Executive", "department": "Sales", "location": "New York, NY", "employment_type": "Full-time"},
    ]


@agent_tool
def list_open_positions(department: str | None = None) -> OpenPositionsOutput:
    """List internal job postings, optionally filtered by department."""
    request = OpenPositionsInput(department=department)
    positions = _mock_positions()
    if request.department:
        positions = [position for position in positions if position["department"].casefold() == request.department.casefold()]
    return OpenPositionsOutput(department=request.department, positions=[OpenPosition(**position) for position in positions], source_system="Mock Internal Careers")
