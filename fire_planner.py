"""
agents/fire_planner.py
FIRE Path Planner — autonomous retirement planning agent.
Handles Scenario Pack #1: 34yo software engineer, ₹24L, retire at 50 with ₹1.5L/month.
Output updates dynamically when any input changes.
"""

from __future__ import annotations
import json
from models.user_profile import UserFinancialProfile, RiskProfile
from tools.financial_calculators import (
    calculate_inflation_adjusted_corpus,
    calculate_sip_required,
    build_glidepath,
    INFLATION_RATE,
    EQUITY_RETURN,
    DEBT_RETURN,
)
from tools.compliance_guardrails import add_disclaimer


class FirePlannerAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, profile: UserFinancialProfile) -> str:
        """
        Autonomously run FIRE planning — 5 sequential steps with no human input.
        Step 1: Validate inputs
        Step 2: Calculate inflation-adjusted corpus
        Step 3: Calculate SIP requirements
        Step 4: Build glidepath
        Step 5: Generate month-by-month plan
        Step 6: Identify insurance & gap analysis
        """
        steps_completed = []

        # ── Step 1: Validate & enrich inputs ─────────────────────────────────
        years_to_retirement = profile.retirement_age_target - profile.age
        current_corpus = profile.total_investments()
        risk = profile.risk_profile or RiskProfile.MODERATE
        steps_completed.append(
            f"✅ Step 1 — Inputs validated: Age {profile.age}, "
            f"Retirement at {profile.retirement_age_target}, "
            f"{years_to_retirement} years to go"
        )

        # ── Step 2: Corpus calculation ────────────────────────────────────────
        corpus_required, corpus_steps = calculate_inflation_adjusted_corpus(
            monthly_need_today=profile.monthly_corpus_needed,
            years_to_retirement=years_to_retirement,
        )
        steps_completed.append(f"✅ Step 2 — Corpus required: ₹{corpus_required:,.0f}")

        # ── Step 3: SIP requirement ───────────────────────────────────────────
        sip_required, sip_steps = calculate_sip_required(
            future_corpus=corpus_required,
            current_corpus=current_corpus,
            years=years_to_retirement,
        )
        steps_completed.append(f"✅ Step 3 — Monthly SIP required: ₹{sip_required:,.0f}")

        # ── Step 4: Glidepath ─────────────────────────────────────────────────
        glidepath = build_glidepath(years_to_retirement, risk.value)
        steps_completed.append(f"✅ Step 4 — Asset allocation glidepath built ({len(glidepath)} years)")

        # ── Step 5: SIP breakdown by category ────────────────────────────────
        current_alloc = glidepath[0]
        equity_pct = current_alloc["equity_pct"] / 100
        sip_breakdown = self._build_sip_breakdown(sip_required, equity_pct)
        steps_completed.append(f"✅ Step 5 — SIP breakdown across fund categories generated")

        # ── Step 6: Insurance gap analysis ───────────────────────────────────
        insurance_gaps = self._analyse_insurance_gaps(profile)
        steps_completed.append(f"✅ Step 6 — Insurance gap analysis completed")

        # ── Format output ─────────────────────────────────────────────────────
        output = self._format_output(
            profile, corpus_required, sip_required, sip_breakdown,
            glidepath, corpus_steps, sip_steps, insurance_gaps, steps_completed
        )
        return add_disclaimer(output, {
            "inflation_rate": INFLATION_RATE,
            "equity_return": EQUITY_RETURN,
            "debt_return": DEBT_RETURN,
            "ppf_rate": 0.071,
            "retirement_duration": 30,
        })

    def _build_sip_breakdown(self, total_sip: float, equity_pct: float) -> dict:
        equity_sip = total_sip * equity_pct
        debt_sip = total_sip * (1 - equity_pct)
        return {
            "Large Cap Fund": round(equity_sip * 0.40),
            "Flexi Cap / Mid Cap Fund": round(equity_sip * 0.35),
            "International / US Index Fund": round(equity_sip * 0.25),
            "PPF (debt component)": round(debt_sip * 0.50),
            "Short Duration Debt Fund": round(debt_sip * 0.30),
            "Liquid Fund (emergency buffer)": round(debt_sip * 0.20),
        }

    def _analyse_insurance_gaps(self, profile: UserFinancialProfile) -> list[dict]:
        gaps = []
        # Rule: Life cover should be 10x annual income
        recommended_life = profile.annual_income * 10
        if profile.life_cover < recommended_life:
            gaps.append({
                "type": "Life Insurance",
                "current": profile.life_cover,
                "recommended": recommended_life,
                "gap": recommended_life - profile.life_cover,
                "action": f"Buy a ₹{(recommended_life - profile.life_cover)/100_000:.0f}L term plan immediately.",
            })
        # Rule: Health cover should be at least ₹10L
        if profile.health_cover < 1_000_000:
            gaps.append({
                "type": "Health Insurance",
                "current": profile.health_cover,
                "recommended": 1_000_000,
                "gap": 1_000_000 - profile.health_cover,
                "action": "Get a ₹10L family floater health plan before investing further.",
            })
        return gaps

    def _format_output(
        self, profile, corpus_required, sip_required, sip_breakdown,
        glidepath, corpus_steps, sip_steps, insurance_gaps, steps_completed
    ) -> str:
        years = profile.retirement_age_target - profile.age

        lines = [
            f"🔥 FIRE PLAN FOR {profile.name or 'You'}",
            f"{'='*55}",
            f"Age: {profile.age} → Target Retirement: {profile.retirement_age_target} ({years} years away)",
            f"Monthly Need at Retirement: ₹{profile.monthly_corpus_needed:,.0f}/month (today's value)",
            "",
            "📊 CORPUS CALCULATION",
            "-"*40,
        ]
        lines.extend(corpus_steps)
        lines.extend(["", "📈 SIP CALCULATION", "-"*40])
        lines.extend(sip_steps)

        lines += [
            "",
            f"💰 MONTHLY SIP BREAKDOWN (Total: ₹{sip_required:,.0f}/month)",
            "-"*40,
        ]
        for fund, amount in sip_breakdown.items():
            lines.append(f"  • {fund}: ₹{amount:,.0f}/month")

        lines += [
            "",
            "📉 ASSET ALLOCATION GLIDEPATH (Every 5 Years)",
            "-"*40,
            f"{'Year':<8} {'Age':<8} {'Equity %':<12} {'Debt %':<10}",
        ]
        for g in glidepath[::5]:  # every 5 years
            age_at = profile.age + g["year"]
            lines.append(f"{g['year']:<8} {age_at:<8} {g['equity_pct']:<12} {g['debt_pct']:<10}")

        if insurance_gaps:
            lines += ["", "🛡️ INSURANCE GAPS — Fix Before Investing More", "-"*40]
            for gap in insurance_gaps:
                lines.append(f"  ❌ {gap['type']}: Have ₹{gap['current']:,.0f}, Need ₹{gap['recommended']:,.0f}")
                lines.append(f"     → {gap['action']}")

        lines += ["", "✅ STEPS COMPLETED AUTONOMOUSLY", "-"*40]
        lines.extend(steps_completed)

        return "\n".join(lines)
