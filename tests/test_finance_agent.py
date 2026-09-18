from decimal import Decimal

import pytest
from pydantic import ValidationError

from shared.schemas import BudgetSummaryOutput, ExpenseReportStatusOutput, InvoiceStatusOutput, PendingApprovalsOutput
from tools.finance_tools import get_budget_summary, get_expense_report_status, get_invoice_status, list_pending_approvals


def test_get_invoice_status_returns_invoice_schema() -> None:
    result = get_invoice_status("INV-1001")
    assert isinstance(result, InvoiceStatusOutput)
    assert result.amount == Decimal("18450.00")
    assert result.source_system == "Mock Accounts Payable"


def test_get_budget_summary_returns_budget_schema() -> None:
    result = get_budget_summary("engineering", "Q3-2026")
    assert isinstance(result, BudgetSummaryOutput)
    assert result.remaining == result.allocated - result.spent


def test_list_pending_approvals_returns_pending_approvals_schema() -> None:
    result = list_pending_approvals("EMP-2001")
    assert isinstance(result, PendingApprovalsOutput)
    assert result.items[0].approval_id == "APR-7001"


def test_get_expense_report_status_returns_expense_schema() -> None:
    result = get_expense_report_status("EXP-3001")
    assert isinstance(result, ExpenseReportStatusOutput)
    assert result.reimbursement_date is not None


@pytest.mark.parametrize(
    ("tool", "argument"),
    [(get_invoice_status, "INV-404"), (get_expense_report_status, "EXP-404"), (list_pending_approvals, "EMP-404")],
)
def test_tools_raise_clear_error_for_unknown_identifier(tool, argument: str) -> None:
    with pytest.raises(ValueError, match="Unknown"):
        tool(argument)


def test_budget_input_is_validated() -> None:
    with pytest.raises(ValidationError):
        get_budget_summary("engineering", "2026-Q3")
