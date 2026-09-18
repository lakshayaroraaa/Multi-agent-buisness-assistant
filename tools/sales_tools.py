"""Validated mock sales tools for the Sales specialist agent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from shared.agent_base import agent_tool
from shared.schemas import (
    CustomerHistoryInput,
    CustomerHistoryOutput,
    DraftQuoteInput,
    DraftQuoteOutput,
    LeadStatusInput,
    LeadStatusOutput,
    PastOrder,
    PipelineSummaryInput,
    PipelineSummaryOutput,
    QuoteLineItem,
)


def _mock_get_lead(lead_id: str) -> dict[str, object] | None:
    """Mock integration seam; replace with a CRM API call."""
    leads = {
        "LEAD-1001": {"stage": "proposal", "owner": "Avery Patel", "last_contacted": date(2026, 9, 14), "next_step": "Review security questionnaire with customer."},
        "LEAD-1002": {"stage": "qualified", "owner": "Jordan Lee", "last_contacted": date(2026, 9, 10), "next_step": "Schedule product discovery call."},
    }
    return leads.get(lead_id)


@agent_tool
def get_lead_status(lead_id: str) -> LeadStatusOutput:
    """Look up the CRM stage, owner, latest contact, and next step for a lead."""
    request = LeadStatusInput(lead_id=lead_id)
    record = _mock_get_lead(request.lead_id)
    if record is None:
        raise ValueError(f"Unknown lead_id: {request.lead_id!r}.")
    return LeadStatusOutput(lead_id=request.lead_id, source_system="Mock CRM", **record)


def _mock_get_pipeline(rep_id: str, quarter: str) -> dict[str, object] | None:
    """Mock integration seam; replace with a CRM reporting API call."""
    pipelines = {
        ("REP-2001", "Q3-2026"): {"deal_count": 12, "total_value": "845000.00", "weighted_value": "412250.00"},
        ("REP-2002", "Q3-2026"): {"deal_count": 8, "total_value": "521000.00", "weighted_value": "278400.00"},
    }
    return pipelines.get((rep_id, quarter.upper()))


@agent_tool
def get_pipeline_summary(rep_id: str, quarter: str) -> PipelineSummaryOutput:
    """Return deal count, total value, and weighted pipeline value for a sales rep."""
    request = PipelineSummaryInput(rep_id=rep_id, quarter=quarter)
    record = _mock_get_pipeline(request.rep_id, request.quarter)
    if record is None:
        raise ValueError(f"No pipeline found for rep_id={request.rep_id!r}, quarter={request.quarter!r}.")
    return PipelineSummaryOutput(rep_id=request.rep_id, quarter=request.quarter, currency="USD", source_system="Mock CRM", **record)


def _mock_get_customer(customer_id: str) -> dict[str, object] | None:
    """Mock integration seam; replace with CRM/customer-master API calls."""
    customers = {
        "CUST-3001": {
            "name": "Fabrikam Retail",
            "orders": [
                {"order_id": "ORD-8101", "order_date": date(2025, 10, 1), "total": "24000.00", "currency": "USD"},
                {"order_id": "ORD-8255", "order_date": date(2026, 4, 15), "total": "36000.00", "currency": "USD"},
            ],
            "renewal": date(2027, 3, 31),
        }
    }
    return customers.get(customer_id)


def _mock_get_product(product_id: str) -> dict[str, object] | None:
    """Mock integration seam; replace with a product-catalog or CPQ API call."""
    products = {
        "PROD-STARTER": {"product_name": "Starter Platform", "unit_price": "1200.00"},
        "PROD-ANALYTICS": {"product_name": "Analytics Add-on", "unit_price": "800.00"},
        "PROD-ENTERPRISE": {"product_name": "Enterprise Platform", "unit_price": "4500.00"},
    }
    return products.get(product_id)


@agent_tool
def draft_quote(customer_id: str, product_ids: list[str], discount_pct: float) -> DraftQuoteOutput:
    """Build an unsent structured quote and flag discounts above 15% for manager approval."""
    request = DraftQuoteInput(customer_id=customer_id, product_ids=product_ids, discount_pct=discount_pct)
    if _mock_get_customer(request.customer_id) is None:
        raise ValueError(f"Unknown customer_id: {request.customer_id!r}.")
    line_items: list[QuoteLineItem] = []
    for product_id in request.product_ids:
        product = _mock_get_product(product_id)
        if product is None:
            raise ValueError(f"Unknown product_id: {product_id!r}.")
        unit_price = Decimal(str(product["unit_price"]))
        line_items.append(QuoteLineItem(product_id=product_id, product_name=str(product["product_name"]), quantity=1, unit_price=unit_price, line_total=unit_price))
    subtotal = sum((line.line_total for line in line_items), Decimal("0"))
    total = (subtotal * (Decimal("1") - Decimal(str(request.discount_pct)) / Decimal("100"))).quantize(Decimal("0.01"))
    needs_approval = request.discount_pct > 15
    return DraftQuoteOutput(
        quote_id=f"DRAFT-{request.customer_id}-001",
        customer_id=request.customer_id,
        status="draft",
        line_items=line_items,
        subtotal=subtotal,
        discount_pct=request.discount_pct,
        total=total,
        currency="USD",
        requires_manager_approval=needs_approval,
        approval_note="Discount exceeds the 15% standard range; request sales manager approval before sending." if needs_approval else None,
        source_system="Mock CPQ",
    )


@agent_tool
def get_customer_history(customer_id: str) -> CustomerHistoryOutput:
    """Return a customer's past orders and contract renewal date from CRM records."""
    request = CustomerHistoryInput(customer_id=customer_id)
    customer = _mock_get_customer(request.customer_id)
    if customer is None:
        raise ValueError(f"Unknown customer_id: {request.customer_id!r}.")
    return CustomerHistoryOutput(
        customer_id=request.customer_id,
        past_orders=[PastOrder(**order) for order in customer["orders"]],
        contract_renewal_date=customer["renewal"],
        source_system="Mock CRM",
    )
