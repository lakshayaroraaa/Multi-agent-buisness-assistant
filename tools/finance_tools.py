"""Validated mock finance tools for the Finance specialist agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from shared.agent_base import agent_tool
from shared.schemas import (
    ApprovalItem,
    BudgetSummaryInput,
    BudgetSummaryOutput,
    ExpenseReportStatusInput,
    ExpenseReportStatusOutput,
    InvoiceStatusInput,
    InvoiceStatusOutput,
    PendingApprovalsInput,
    PendingApprovalsOutput,
)


def _mock_get_invoice(invoice_id: str) -> dict[str, object] | None:
    """Mock integration seam; replace its body with an accounts-payable API call."""
    invoices = {
        "INV-1001": {"status": "pending", "amount": "18450.00", "vendor": "Northwind Office Supplies", "due_date": date(2026, 10, 15)},
        "INV-1002": {"status": "paid", "amount": "7200.00", "vendor": "Contoso Cloud Services", "due_date": date(2026, 9, 1)},
    }
    return invoices.get(invoice_id)


@agent_tool
def get_invoice_status(invoice_id: str) -> InvoiceStatusOutput:
    """Look up an invoice's status, vendor, amount, and due date in Accounts Payable."""
    request = InvoiceStatusInput(invoice_id=invoice_id)
    record = _mock_get_invoice(request.invoice_id)
    if record is None:
        raise ValueError(f"Unknown invoice_id: {request.invoice_id!r}.")
    return InvoiceStatusOutput(invoice_id=request.invoice_id, currency="USD", source_system="Mock Accounts Payable", **record)


def _mock_get_budget(department: str, quarter: str) -> dict[str, object] | None:
    """Mock integration seam; replace with a budgeting-system API call."""
    budgets = {
        ("engineering", "Q3-2026"): {"allocated": "500000.00", "spent": "318400.00"},
        ("sales", "Q3-2026"): {"allocated": "300000.00", "spent": "191750.00"},
    }
    return budgets.get((department.casefold(), quarter.upper()))


@agent_tool
def get_budget_summary(department: str, quarter: str) -> BudgetSummaryOutput:
    """Return allocated, spent, and remaining budget for a department and quarter."""
    request = BudgetSummaryInput(department=department, quarter=quarter)
    record = _mock_get_budget(request.department, request.quarter)
    if record is None:
        raise ValueError(f"No budget found for department={request.department!r}, quarter={request.quarter!r}.")
    allocated = Decimal(str(record["allocated"]))
    spent = Decimal(str(record["spent"]))
    return BudgetSummaryOutput(
        department=request.department,
        quarter=request.quarter,
        allocated=allocated,
        spent=spent,
        remaining=allocated - spent,
        currency="USD",
        source_system="Mock Budget Management",
    )


def _mock_list_approvals(employee_id: str) -> list[dict[str, object]] | None:
    """Mock integration seam; replace with an approval-workflow API call."""
    approvals = {
        "EMP-2001": [
            {"approval_id": "APR-7001", "item_type": "invoice", "requester": "Maya Chen", "amount": "18450.00", "currency": "USD", "submitted_date": date(2026, 9, 14)},
            {"approval_id": "APR-7002", "item_type": "expense_report", "requester": "Jon Bell", "amount": "642.50", "currency": "USD", "submitted_date": date(2026, 9, 15)},
        ]
    }
    return approvals.get(employee_id)


@agent_tool
def list_pending_approvals(employee_id: str) -> PendingApprovalsOutput:
    """List items awaiting the specified employee's approval; this tool never approves them."""
    request = PendingApprovalsInput(employee_id=employee_id)
    records = _mock_list_approvals(request.employee_id)
    if records is None:
        raise ValueError(f"Unknown employee_id: {request.employee_id!r}.")
    return PendingApprovalsOutput(
        employee_id=request.employee_id,
        items=[ApprovalItem(**record) for record in records],
        source_system="Mock Approval Workflow",
    )


def _mock_get_expense_report(report_id: str) -> dict[str, object] | None:
    """Mock integration seam; replace with an expense-management API call."""
    reports = {
        "EXP-3001": {"status": "reimbursed", "reimbursement_date": date(2026, 9, 12)},
        "EXP-3002": {"status": "pending_approval", "reimbursement_date": None},
    }
    return reports.get(report_id)


@agent_tool
def get_expense_report_status(report_id: str) -> ExpenseReportStatusOutput:
    """Look up an expense report's current status and reimbursement date."""
    request = ExpenseReportStatusInput(report_id=report_id)
    record = _mock_get_expense_report(request.report_id)
    if record is None:
        raise ValueError(f"Unknown report_id: {request.report_id!r}.")
    return ExpenseReportStatusOutput(report_id=request.report_id, source_system="Mock Expense Management", **record)
