"""
tests/test_tax_scenario.py
Scenario Pack #2: Tax regime edge case.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_profile import UserFinancialProfile, TaxInputs
from agents.tax_wizard import TaxWizardAgent


def test_tax_edge_case():
    """
    Inputs: ₹18L base, ₹3.6L HRA, ₹1.5L 80C, ₹50K NPS, ₹40K home loan interest
    Expected: Step-by-step calculation for both regimes, optimal regime identified,
              missed deductions flagged, additional instruments suggested.
    """
    profile = UserFinancialProfile(
        name="Priya",
        age=32,
        annual_income=1_800_000,
        tax_inputs=TaxInputs(
            base_salary=1_800_000,
            hra_component=360_000,
            actual_rent_paid=25_000,
            city_type="metro",
            investments_80c=150_000,
            nps_self=50_000,
            home_loan_interest=40_000,
            medical_insurance=20_000,
        ),
    )

    agent = TaxWizardAgent(llm=None)
    result = agent.run(profile)

    assert "Step 1" in result                    # step-by-step present
    assert "OLD REGIME" in result.upper()
    assert "NEW REGIME" in result.upper()
    assert "OPTIMAL REGIME" in result
    assert "Annual Tax Saving" in result
    assert "MISSED DEDUCTIONS" in result or "missed" in result.lower()

    print("✅ Tax Edge Case Test PASSED")
    print(result[:600], "...\n")


if __name__ == "__main__":
    test_tax_edge_case()


# ─────────────────────────────────────────────────────────────────────────────

"""
tests/test_mf_xray_scenario.py
Scenario Pack #3: MF Portfolio X-Ray with overlap and rebalancing.
"""


def test_mf_xray():
    """
    6 mutual funds across 4 AMCs.
    Reliance, HDFC, Infosys appear in 3 large-cap funds.
    Expected: XIRR, overlap matrix, expense drag, tax-aware fund-level rebalancing.
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.user_profile import UserFinancialProfile
    from agents.mf_xray import MFXRayAgent

    profile = UserFinancialProfile(name="Rahul", age=38, annual_income=3_000_000)
    # portfolio will be loaded from demo data

    agent = MFXRayAgent(llm=None)
    result = agent.run(profile)

    assert "XIRR" in result
    assert "OVERLAP" in result.upper()
    assert "REBALANCING" in result.upper()
    assert "REDEEM" in result or "SWITCH" in result  # specific fund-level action
    assert "tax" in result.lower()                    # tax context present
    assert "expense ratio" in result.lower() or "ER" in result

    print("✅ MF X-Ray Test PASSED")
    print(result[:600], "...\n")


if __name__ == "__main__":
    test_mf_xray()
