from decimal import Decimal

import pytest
from pydantic import ValidationError

from shared.schemas import CustomerHistoryOutput, DraftQuoteOutput, LeadStatusOutput, PipelineSummaryOutput
from tools.sales_tools import draft_quote, get_customer_history, get_lead_status, get_pipeline_summary


def test_get_lead_status_returns_lead_schema() -> None:
    result = get_lead_status("LEAD-1001")
    assert isinstance(result, LeadStatusOutput)
    assert result.stage == "proposal"


def test_get_pipeline_summary_returns_pipeline_schema() -> None:
    result = get_pipeline_summary("REP-2001", "Q3-2026")
    assert isinstance(result, PipelineSummaryOutput)
    assert result.weighted_value == Decimal("412250.00")


def test_draft_quote_returns_unsent_quote_schema() -> None:
    result = draft_quote("CUST-3001", ["PROD-STARTER", "PROD-ANALYTICS"], 10)
    assert isinstance(result, DraftQuoteOutput)
    assert result.status == "draft"
    assert result.total == Decimal("1800.00")
    assert not result.requires_manager_approval


def test_draft_quote_flags_discount_above_standard_range() -> None:
    result = draft_quote("CUST-3001", ["PROD-ENTERPRISE"], 16)
    assert result.requires_manager_approval
    assert result.approval_note is not None


def test_get_customer_history_returns_customer_schema() -> None:
    result = get_customer_history("CUST-3001")
    assert isinstance(result, CustomerHistoryOutput)
    assert len(result.past_orders) == 2


@pytest.mark.parametrize(
    ("function", "arguments", "message"),
    [
        (get_lead_status, ("LEAD-404",), "Unknown"),
        (get_pipeline_summary, ("REP-404", "Q3-2026"), "No pipeline"),
        (draft_quote, ("CUST-404", ["PROD-STARTER"], 5), "Unknown"),
        (get_customer_history, ("CUST-404",), "Unknown"),
    ],
)
def test_sales_tools_raise_clear_errors_for_unknown_records(function, arguments, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        function(*arguments)


def test_draft_quote_input_is_validated() -> None:
    with pytest.raises(ValidationError):
        draft_quote("CUST-3001", [], 10)
