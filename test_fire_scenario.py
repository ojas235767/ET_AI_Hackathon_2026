"""
tests/test_fire_scenario.py
Scenario Pack #1: FIRE Plan for 34yo software engineer.
Tests autonomous 6-step pipeline without human input.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_profile import UserFinancialProfile, RiskProfile
from agents.fire_planner import FirePlannerAgent


def test_fire_scenario():
    """
    Scenario: 34yo software engineer
    - Income: ₹24L/year
    - MF investments: ₹18L
    - PPF: ₹6L
    - Target: Retire at 50 with ₹1.5L/month (today's value)
    Expected: Month-by-month plan, insurance gap detection, dynamic glidepath
    """
    profile = UserFinancialProfile(
        name="Test User",
        age=34,
        annual_income=2_400_000,
        monthly_expenses=80_000,
        mf_investments=1_800_000,
        ppf_balance=600_000,
        epf_balance=400_000,
        retirement_age_target=50,
        monthly_corpus_needed=150_000,
        life_cover=0,               # intentionally 0 to test gap detection
        health_cover=500_000,
        risk_profile=RiskProfile.MODERATE,
    )

    agent = FirePlannerAgent(llm=None)
    result = agent.run(profile)

    # Verify output contains required elements
    assert "FIRE PLAN" in result
    assert "Step 1" in result         # audit trail present
    assert "Step 2" in result
    assert "Step 3" in result
    assert "INSURANCE GAPS" in result  # gap detected
    assert "Life Insurance" in result  # specific gap identified
    assert "GLIDEPATH" in result       # glidepath built

    print("✅ FIRE Scenario Test PASSED")
    print(result[:500], "...\n")


def test_fire_scenario_retirement_age_change():
    """Tests dynamic recalculation when retirement age changes (50 → 55)."""
    profile_50 = UserFinancialProfile(
        age=34, annual_income=2_400_000, monthly_expenses=80_000,
        mf_investments=1_800_000, ppf_balance=600_000, epf_balance=400_000,
        retirement_age_target=50, monthly_corpus_needed=150_000,
        risk_profile=RiskProfile.MODERATE,
    )
    profile_55 = UserFinancialProfile(
        age=34, annual_income=2_400_000, monthly_expenses=80_000,
        mf_investments=1_800_000, ppf_balance=600_000, epf_balance=400_000,
        retirement_age_target=55, monthly_corpus_needed=150_000,
        risk_profile=RiskProfile.MODERATE,
    )

    agent = FirePlannerAgent(llm=None)
    result_50 = agent.run(profile_50)
    result_55 = agent.run(profile_55)

    # Retiring at 55 should require lower monthly SIP (more time to compound)
    assert result_50 != result_55, "Dynamic recalculation should produce different results"
    print("✅ Dynamic Recalculation Test PASSED — retiring at 55 produces different plan")


if __name__ == "__main__":
    test_fire_scenario()
    test_fire_scenario_retirement_age_change()
