"""
tools/tax_calculator.py
FY 2025-26 tax calculation engine — Old Regime vs New Regime.
Every calculation includes full step-by-step audit trail.
Verifiable against IT department published slabs.
"""

from __future__ import annotations
from dataclasses import dataclass
from models.user_profile import TaxInputs


# ── FY 2025-26 Tax Slabs ─────────────────────────────────────────────────────

OLD_REGIME_SLABS = [
    (250_000, 0.00),
    (500_000, 0.05),
    (1_000_000, 0.20),
    (float("inf"), 0.30),
]

NEW_REGIME_SLABS = [          # Post Budget 2025 — effective FY 2025-26
    (300_000, 0.00),
    (700_000, 0.05),
    (1_000_000, 0.10),
    (1_200_000, 0.15),
    (1_500_000, 0.20),
    (float("inf"), 0.30),
]

STANDARD_DEDUCTION_OLD = 50_000
STANDARD_DEDUCTION_NEW = 75_000
REBATE_87A_OLD_LIMIT = 500_000    # rebate up to ₹12,500 if taxable income ≤ ₹5L
REBATE_87A_NEW_LIMIT = 700_000    # rebate up to ₹25,000 if taxable income ≤ ₹7L
CESS_RATE = 0.04


@dataclass
class TaxBreakdown:
    gross_income: float
    taxable_income: float
    deductions: dict[str, float]
    tax_before_cess: float
    cess: float
    total_tax: float
    effective_rate: float
    steps: list[str]


def calculate_hra_exemption(
    hra_received: float,
    annual_rent: float,
    basic_salary: float,
    is_metro: bool,
) -> tuple[float, str]:
    """
    HRA exemption = min of:
    1. Actual HRA received
    2. Rent paid - 10% of basic
    3. 50% of basic (metro) / 40% of basic (non-metro)
    """
    limit_1 = hra_received
    limit_2 = max(0, annual_rent - 0.10 * basic_salary)
    limit_3 = basic_salary * (0.50 if is_metro else 0.40)
    exemption = min(limit_1, limit_2, limit_3)

    step = (
        f"HRA Exemption = min(₹{limit_1:,.0f} actual HRA, "
        f"₹{limit_2:,.0f} rent-10%basic, "
        f"₹{limit_3:,.0f} {'50' if is_metro else '40'}%basic) = ₹{exemption:,.0f}"
    )
    return exemption, step


def apply_slabs(taxable_income: float, slabs: list[tuple]) -> tuple[float, list[str]]:
    """Apply progressive slab taxation. Returns (tax, steps)."""
    tax = 0.0
    steps = []
    prev_limit = 0
    for limit, rate in slabs:
        if taxable_income <= prev_limit:
            break
        taxable_in_slab = min(taxable_income, limit) - prev_limit
        slab_tax = taxable_in_slab * rate
        tax += slab_tax
        if rate > 0:
            steps.append(
                f"  ₹{prev_limit:,.0f}–₹{min(taxable_income, limit):,.0f} "
                f"@ {rate:.0%} = ₹{slab_tax:,.0f}"
            )
        prev_limit = limit
    return tax, steps


def calculate_old_regime(inputs: TaxInputs) -> TaxBreakdown:
    steps = []
    deductions = {}

    # Step 1: Gross total income
    gross = inputs.base_salary + inputs.other_income
    steps.append(f"Step 1 — Gross Income: ₹{gross:,.0f}")

    # Step 2: Standard deduction
    std_ded = STANDARD_DEDUCTION_OLD
    deductions["Standard Deduction"] = std_ded
    steps.append(f"Step 2 — Standard Deduction: ₹{std_ded:,.0f}")

    # Step 3: HRA exemption
    if inputs.hra_component > 0 and inputs.actual_rent_paid > 0:
        # Assume basic = 50% of base salary (standard split)
        basic_salary = inputs.base_salary * 0.50
        hra_exemption, hra_step = calculate_hra_exemption(
            hra_received=inputs.hra_component,
            annual_rent=inputs.actual_rent_paid * 12,
            basic_salary=basic_salary,
            is_metro=(inputs.city_type == "metro"),
        )
        deductions["HRA Exemption"] = hra_exemption
        steps.append(f"Step 3 — {hra_step}")
    else:
        steps.append("Step 3 — HRA: Not applicable (no rent paid or no HRA component)")

    # Step 4: 80C (max ₹1.5L)
    ded_80c = min(inputs.investments_80c + inputs.home_loan_principal, 150_000)
    deductions["80C (ELSS/PPF/EPF/Principal)"] = ded_80c
    steps.append(f"Step 4 — 80C deduction: ₹{ded_80c:,.0f} (capped at ₹1,50,000)")

    # Step 5: 80CCD(1B) — NPS self (max ₹50K additional)
    ded_nps = min(inputs.nps_self, 50_000)
    deductions["80CCD(1B) NPS Self"] = ded_nps
    steps.append(f"Step 5 — 80CCD(1B) NPS: ₹{ded_nps:,.0f} (max ₹50,000)")

    # Step 6: 24(b) Home loan interest (max ₹2L for self-occupied)
    ded_hl_interest = min(inputs.home_loan_interest, 200_000)
    deductions["24(b) Home Loan Interest"] = ded_hl_interest
    steps.append(f"Step 6 — 24(b) Home Loan Interest: ₹{ded_hl_interest:,.0f} (max ₹2,00,000)")

    # Step 7: 80D Medical insurance (max ₹25K self + ₹25K parents = ₹50K)
    ded_80d = min(inputs.medical_insurance, 50_000)
    deductions["80D Medical Insurance"] = ded_80d
    steps.append(f"Step 7 — 80D Medical Insurance: ₹{ded_80d:,.0f}")

    # Step 8: Other deductions
    deductions["Other Deductions"] = inputs.other_deductions
    steps.append(f"Step 8 — Other deductions: ₹{inputs.other_deductions:,.0f}")

    # Step 9: Taxable income
    total_deductions = sum(deductions.values())
    taxable_income = max(0, gross - total_deductions)
    steps.append(
        f"Step 9 — Taxable Income: ₹{gross:,.0f} - ₹{total_deductions:,.0f} = ₹{taxable_income:,.0f}"
    )

    # Step 10: Apply slabs
    steps.append("Step 10 — Slab-wise tax (Old Regime):")
    tax, slab_steps = apply_slabs(taxable_income, OLD_REGIME_SLABS)
    steps.extend(slab_steps)

    # Step 11: 87A rebate
    if taxable_income <= REBATE_87A_OLD_LIMIT:
        rebate = min(tax, 12_500)
        tax -= rebate
        steps.append(f"Step 11 — Section 87A Rebate: -₹{rebate:,.0f} (income ≤ ₹5L)")
    else:
        steps.append(f"Step 11 — No 87A rebate (taxable income > ₹{REBATE_87A_OLD_LIMIT:,.0f})")

    # Step 12: Cess
    cess = tax * CESS_RATE
    total_tax = tax + cess
    steps.append(f"Step 12 — 4% Health & Education Cess: ₹{cess:,.0f}")
    steps.append(f"TOTAL TAX (Old Regime): ₹{total_tax:,.0f}")

    return TaxBreakdown(
        gross_income=gross,
        taxable_income=taxable_income,
        deductions=deductions,
        tax_before_cess=tax,
        cess=cess,
        total_tax=total_tax,
        effective_rate=round(total_tax / gross * 100, 2) if gross > 0 else 0,
        steps=steps,
    )


def calculate_new_regime(inputs: TaxInputs) -> TaxBreakdown:
    steps = []
    deductions = {}

    # Step 1: Gross total income (new regime allows fewer deductions)
    gross = inputs.base_salary + inputs.other_income
    steps.append(f"Step 1 — Gross Income: ₹{gross:,.0f}")

    # Step 2: Standard deduction (₹75K in new regime from FY25-26)
    std_ded = STANDARD_DEDUCTION_NEW
    deductions["Standard Deduction"] = std_ded
    steps.append(f"Step 2 — Standard Deduction (New Regime): ₹{std_ded:,.0f}")

    # Step 3: NPS employer contribution u/s 80CCD(2) — allowed in new regime
    nps_employer_ded = min(inputs.nps_employer, inputs.base_salary * 0.10)
    if nps_employer_ded > 0:
        deductions["80CCD(2) NPS Employer"] = nps_employer_ded
        steps.append(f"Step 3 — 80CCD(2) NPS Employer: ₹{nps_employer_ded:,.0f} (max 10% of basic)")
    else:
        steps.append("Step 3 — No employer NPS contribution")

    # New regime: No 80C, 80D, HRA, 24(b) etc.
    steps.append(
        "Note — New regime does NOT allow: 80C, 80D, HRA exemption, 24(b) home loan interest, "
        "80CCD(1B) NPS self, LTA."
    )

    # Step 4: Taxable income
    total_deductions = sum(deductions.values())
    taxable_income = max(0, gross - total_deductions)
    steps.append(
        f"Step 4 — Taxable Income: ₹{gross:,.0f} - ₹{total_deductions:,.0f} = ₹{taxable_income:,.0f}"
    )

    # Step 5: Apply slabs
    steps.append("Step 5 — Slab-wise tax (New Regime FY 2025-26):")
    tax, slab_steps = apply_slabs(taxable_income, NEW_REGIME_SLABS)
    steps.extend(slab_steps)

    # Step 6: 87A rebate — up to ₹25,000 if taxable income ≤ ₹7L
    if taxable_income <= REBATE_87A_NEW_LIMIT:
        rebate = min(tax, 25_000)
        tax -= rebate
        steps.append(f"Step 6 — Section 87A Rebate: -₹{rebate:,.0f} (income ≤ ₹7L)")
    else:
        steps.append(f"Step 6 — No 87A rebate (taxable income > ₹{REBATE_87A_NEW_LIMIT:,.0f})")

    # Step 7: Cess
    cess = tax * CESS_RATE
    total_tax = tax + cess
    steps.append(f"Step 7 — 4% Health & Education Cess: ₹{cess:,.0f}")
    steps.append(f"TOTAL TAX (New Regime): ₹{total_tax:,.0f}")

    return TaxBreakdown(
        gross_income=gross,
        taxable_income=taxable_income,
        deductions=deductions,
        tax_before_cess=tax,
        cess=cess,
        total_tax=total_tax,
        effective_rate=round(total_tax / gross * 100, 2) if gross > 0 else 0,
        steps=steps,
    )


def compare_regimes(inputs: TaxInputs) -> dict:
    """
    Compare both regimes and return recommendation with missed deductions.
    """
    old = calculate_old_regime(inputs)
    new = calculate_new_regime(inputs)

    optimal = "old" if old.total_tax < new.total_tax else "new"
    saving = abs(old.total_tax - new.total_tax)

    # Identify missed deductions
    missed = []
    if inputs.investments_80c < 150_000:
        gap = 150_000 - inputs.investments_80c
        missed.append({
            "section": "80C",
            "gap": gap,
            "instruments": [
                {"name": "ELSS Mutual Fund", "liquidity": "3-yr lock-in", "risk": "medium"},
                {"name": "PPF", "liquidity": "15-yr (partial after 7)", "risk": "low"},
                {"name": "NPS Tier-1", "liquidity": "till retirement", "risk": "low-medium"},
            ],
        })
    if inputs.nps_self < 50_000 and optimal == "old":
        missed.append({
            "section": "80CCD(1B)",
            "gap": 50_000 - inputs.nps_self,
            "instruments": [
                {"name": "NPS Tier-1 (self)", "liquidity": "till retirement", "risk": "low-medium"},
            ],
        })
    if inputs.medical_insurance < 25_000:
        missed.append({
            "section": "80D",
            "gap": 25_000 - inputs.medical_insurance,
            "instruments": [
                {"name": "Health Insurance", "liquidity": "annual premium", "risk": "none"},
            ],
        })

    return {
        "old_regime": {
            "taxable_income": old.taxable_income,
            "total_tax": old.total_tax,
            "effective_rate": old.effective_rate,
            "deductions": old.deductions,
            "steps": old.steps,
        },
        "new_regime": {
            "taxable_income": new.taxable_income,
            "total_tax": new.total_tax,
            "effective_rate": new.effective_rate,
            "deductions": new.deductions,
            "steps": new.steps,
        },
        "optimal_regime": optimal,
        "annual_saving": round(saving, 0),
        "missed_deductions": missed,
        "recommendation": (
            f"{'Old' if optimal == 'old' else 'New'} regime saves you ₹{saving:,.0f}/year. "
            f"{'Switch to old regime and maximise 80C/80D/HRA claims.' if optimal == 'old' else 'New regime is simpler and more beneficial for your income profile.'}"
        ),
    }
