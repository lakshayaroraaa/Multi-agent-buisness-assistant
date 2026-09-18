"""Validated contracts for every specialist-agent tool."""

from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolModel(BaseModel):
    """Base model that rejects unexpected fields at every tool boundary."""

    model_config = ConfigDict(extra="forbid")


class InvoiceStatusInput(ToolModel):
    invoice_id: str = Field(min_length=1, description="Internal invoice identifier.")


class InvoiceStatusOutput(ToolModel):
    invoice_id: str
    status: Literal["pending", "approved", "paid", "overdue"]
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    vendor: str
    due_date: date
    source_system: str


class BudgetSummaryInput(ToolModel):
    department: str = Field(min_length=1)
    quarter: str = Field(pattern=r"^Q[1-4]-\d{4}$", description="Quarter such as Q1-2026.")


class BudgetSummaryOutput(ToolModel):
    department: str
    quarter: str
    allocated: Decimal = Field(ge=0)
    spent: Decimal = Field(ge=0)
    remaining: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    source_system: str


class PendingApprovalsInput(ToolModel):
    employee_id: str = Field(min_length=1)


class ApprovalItem(ToolModel):
    approval_id: str
    item_type: Literal["invoice", "expense_report", "purchase_request"]
    requester: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    submitted_date: date


class PendingApprovalsOutput(ToolModel):
    employee_id: str
    items: list[ApprovalItem]
    source_system: str


class ExpenseReportStatusInput(ToolModel):
    report_id: str = Field(min_length=1)


class ExpenseReportStatusOutput(ToolModel):
    report_id: str
    status: Literal["submitted", "pending_approval", "approved", "reimbursed", "rejected"]
    reimbursement_date: date | None
    source_system: str


class LeadStatusInput(ToolModel):
    lead_id: str = Field(min_length=1)


class LeadStatusOutput(ToolModel):
    lead_id: str
    stage: Literal["new", "qualified", "discovery", "proposal", "negotiation", "closed_won", "closed_lost"]
    owner: str
    last_contacted: date
    next_step: str
    source_system: str


class PipelineSummaryInput(ToolModel):
    rep_id: str = Field(min_length=1)
    quarter: str = Field(pattern=r"^Q[1-4]-\d{4}$")


class PipelineSummaryOutput(ToolModel):
    rep_id: str
    quarter: str
    deal_count: int = Field(ge=0)
    total_value: Decimal = Field(ge=0)
    weighted_value: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    source_system: str


class DraftQuoteInput(ToolModel):
    customer_id: str = Field(min_length=1)
    product_ids: list[str] = Field(min_length=1)
    discount_pct: float = Field(ge=0, le=100)


class QuoteLineItem(ToolModel):
    product_id: str
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class DraftQuoteOutput(ToolModel):
    quote_id: str
    customer_id: str
    status: Literal["draft"]
    line_items: list[QuoteLineItem]
    subtotal: Decimal = Field(ge=0)
    discount_pct: float = Field(ge=0, le=100)
    total: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    requires_manager_approval: bool
    approval_note: str | None
    source_system: str


class CustomerHistoryInput(ToolModel):
    customer_id: str = Field(min_length=1)


class PastOrder(ToolModel):
    order_id: str
    order_date: date
    total: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class CustomerHistoryOutput(ToolModel):
    customer_id: str
    past_orders: list[PastOrder]
    contract_renewal_date: date | None
    source_system: str


class TimeOffBalanceInput(ToolModel):
    employee_id: str = Field(min_length=1)


class TimeOffBalanceOutput(ToolModel):
    employee_id: str
    vacation_days: float = Field(ge=0)
    sick_days: float = Field(ge=0)
    accrual_rate: str
    source_system: str


class OnboardingStatusInput(ToolModel):
    employee_id: str = Field(min_length=1)


class OnboardingStatusOutput(ToolModel):
    employee_id: str
    completed_items: list[str]
    pending_items: list[str]
    start_date: date
    source_system: str


class BenefitsSummaryInput(ToolModel):
    employee_id: str = Field(min_length=1)


class BenefitsSummaryOutput(ToolModel):
    employee_id: str
    enrolled_plans: list[str]
    enrollment_deadline: date | None
    source_system: str


class OpenPositionsInput(ToolModel):
    department: str | None = Field(default=None, min_length=1)


class OpenPosition(ToolModel):
    position_id: str
    title: str
    department: str
    location: str
    employment_type: str


class OpenPositionsOutput(ToolModel):
    department: str | None
    positions: list[OpenPosition]
    source_system: str


class KnowledgeSearchInput(ToolModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=10)


class KnowledgeChunk(ToolModel):
    source_document: str
    chunk_text: str
    relevance_score: float = Field(ge=0)


class KnowledgeSearchOutput(ToolModel):
    query: str
    results: list[KnowledgeChunk]
    source_system: str


class SpecialistCallRecord(ToolModel):
    agent_name: str
    reason: str
    duration_ms: int = Field(ge=0)
    raw_response: str | None = None
    error: str | None = None


class ConversationTurn(ToolModel):
    id: str
    session_id: str
    timestamp: datetime
    user_message: str
    agents_called: list[str]
    specialist_calls: list[SpecialistCallRecord]
    final_response: str
