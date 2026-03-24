"""
agents/tax_wizard.py
Tax Wizard Agent — handles Scenario Pack #2 edge case.
Step-by-step verifiable calculation. Never gives final answer without traceable logic.
"""

from __future__ import annotations
from models.user_profile import UserFinancialProfile
from tools.tax_calculator import compare_regimes
from tools.compliance_guardrails import add_disclaimer


class TaxWizardAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, profile: UserFinancialProfile) -> str:
        """
        Autonomously runs 6 sequential analysis steps:
        1. Parse inputs
        2. Calculate Old Regime (step-by-step)
        3. Calculate New Regime (step-by-step)
        4. Compare and identify optimal
        5. Identify missed deductions
        6. Suggest additional tax-saving instruments ranked by liquidity & risk
        """
        if not profile.is_ready_for_tax_analysis():
            return "I need your salary details to run a tax analysis. What is your annual CTC?"

        result = compare_regimes(profile.tax_inputs)

        lines = [
            "🧾 TAX WIZARD — FY 2025-26 ANALYSIS",
            "=" * 55,
            "",
            "📋 OLD REGIME — Step-by-Step Calculation",
            "-" * 40,
        ]
        lines.extend(result["old_regime"]["steps"])

        lines += [
            "",
            "📋 NEW REGIME — Step-by-Step Calculation",
            "-" * 40,
        ]
        lines.extend(result["new_regime"]["steps"])

        lines += [
            "",
            "⚖️  COMPARISON SUMMARY",
            "-" * 40,
            f"  Old Regime Tax: ₹{result['old_regime']['total_tax']:,.0f} "
            f"(Effective Rate: {result['old_regime']['effective_rate']}%)",
            f"  New Regime Tax: ₹{result['new_regime']['total_tax']:,.0f} "
            f"(Effective Rate: {result['new_regime']['effective_rate']}%)",
            "",
            f"  ✅ OPTIMAL REGIME: {result['optimal_regime'].upper()}",
            f"  💰 Annual Tax Saving: ₹{result['annual_saving']:,.0f}",
            f"  → {result['recommendation']}",
        ]

        if result["missed_deductions"]:
            lines += ["", "🚨 MISSED DEDUCTIONS — You're Leaving Money on the Table", "-" * 40]
            for missed in result["missed_deductions"]:
                lines.append(
                    f"\n  Section {missed['section']}: ₹{missed['gap']:,.0f} unutilised"
                )
                lines.append("  Suggested instruments (ranked by liquidity):")
                for i, inst in enumerate(missed["instruments"], 1):
                    lines.append(
                        f"    {i}. {inst['name']} | Liquidity: {inst['liquidity']} | Risk: {inst['risk']}"
                    )

        return add_disclaimer("\n".join(lines))
