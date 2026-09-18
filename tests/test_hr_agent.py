import pytest

from shared.schemas import BenefitsSummaryOutput, OnboardingStatusOutput, OpenPositionsOutput, TimeOffBalanceOutput
from tools.hr_tools import get_benefits_summary, get_onboarding_status, get_time_off_balance, list_open_positions


def test_time_off_balance_matches_schema() -> None:
    assert isinstance(get_time_off_balance("EMP-1001"), TimeOffBalanceOutput)


def test_onboarding_status_matches_schema() -> None:
    assert isinstance(get_onboarding_status("EMP-1001"), OnboardingStatusOutput)


def test_benefits_summary_matches_schema() -> None:
    assert isinstance(get_benefits_summary("EMP-1001"), BenefitsSummaryOutput)


def test_open_positions_matches_schema() -> None:
    assert isinstance(list_open_positions(), OpenPositionsOutput)


def test_other_employee_hr_data_is_refused() -> None:
    with pytest.raises(PermissionError, match="only access your own"):
        get_time_off_balance("EMP-1002")
