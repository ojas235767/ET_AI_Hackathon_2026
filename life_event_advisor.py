"""
agents/life_event_advisor.py
Life Event Financial Advisor — triggered by specific life events.
"""
from models.user_profile import UserFinancialProfile, LifeEvent
from tools.compliance_guardrails import add_disclaimer


class LifeEventAdvisorAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, profile: UserFinancialProfile) -> str:
        event = profile.recent_life_event
        amount = profile.event_amount
        income = profile.annual_income or 0
        risk = (profile.risk_profile.value if profile.risk_profile else "moderate")

        if event == LifeEvent.BONUS:
            return self._handle_bonus(amount, income, risk, profile)
        elif event == LifeEvent.MARRIAGE:
            return self._handle_marriage(amount, income, risk, profile)
        elif event == LifeEvent.NEW_BABY:
            return self._handle_new_baby(income, profile)
        elif event == LifeEvent.INHERITANCE:
            return self._handle_inheritance(amount, risk, profile)
        else:
            return add_disclaimer(f"Life event '{event}' noted. Please share more details for personalised advice.")

    def _handle_bonus(self, bonus: float, income: float, risk: str, profile) -> str:
        emergency_gap = max(0, (profile.monthly_expenses or income/12 * 0.7) * 6 - profile.fd_balance)
        tax_gap = max(0, 150_000 - (profile.tax_inputs.investments_80c if profile.tax_inputs else 0))
        remaining = bonus - emergency_gap - tax_gap

        lines = [
            f"🎉 BONUS UTILISATION PLAN — ₹{bonus:,.0f}",
            "=" * 55,
            f"Priority 1 — Emergency Fund top-up: ₹{min(bonus, emergency_gap):,.0f}",
            f"Priority 2 — 80C gap (tax saving): ₹{min(remaining, tax_gap):,.0f}",
            f"Priority 3 — Investment (risk: {risk}): ₹{max(0, remaining - tax_gap):,.0f}",
            "",
            "Suggested split for investment portion:",
            "  60% — Equity mutual funds (lump sum + monthly SIP)",
            "  20% — NPS Tier-1 (80CCD(1B) benefit)",
            "  20% — PPF / liquid fund",
        ]
        return add_disclaimer("\n".join(lines))

    def _handle_marriage(self, cost: float, income: float, risk: str, profile) -> str:
        lines = [
            "💍 MARRIAGE FINANCIAL PLANNING",
            "=" * 55,
            "Joint financial goals to set up on Day 1:",
            "  1. Combined emergency fund = 6 months of joint expenses",
            "  2. Review and update nominee in all investments/insurance",
            "  3. Consider joint HRA optimisation if both are salaried",
            "  4. Get a joint health floater plan (usually cheaper)",
            "  5. Discuss financial goals and open joint SIPs for them",
            "",
            "Tax saving opportunity: If spouse has no income, invest in their name",
            "to avoid clubbing of income.",
        ]
        return add_disclaimer("\n".join(lines))

    def _handle_new_baby(self, income: float, profile) -> str:
        child_education_corpus = 3_000_000  # ₹30L in today's money — college in 18 yrs
        monthly_sip_needed = round(child_education_corpus * 0.001, -2)  # rough
        lines = [
            "👶 NEW BABY FINANCIAL PLAN",
            "=" * 55,
            f"Child Education Corpus Target: ₹30L (today's value)",
            f"  → Start SIP of ₹{monthly_sip_needed:,.0f}/month in a diversified equity fund now",
            f"  → At 12% CAGR over 18 years, ₹{monthly_sip_needed:,.0f}/month → ~₹1.5Cr",
            "",
            "Immediate actions:",
            "  1. Increase life cover to 15x income (dependent added)",
            "  2. Add child as dependent in health insurance",
            "  3. Start Sukanya Samruddhi (if girl child) — 8.2% guaranteed",
            "  4. Open ELSS SIP in child's name (clubbed till 18, then independent)",
        ]
        return add_disclaimer("\n".join(lines))

    def _handle_inheritance(self, amount: float, risk: str, profile) -> str:
        lines = [
            f"🏦 INHERITANCE / WINDFALL PLAN — ₹{amount:,.0f}",
            "=" * 55,
            "Step 1: Park in liquid fund immediately (don't rush decisions)",
            "Step 2: Set aside 6-month emergency fund if not already done",
            f"Step 3: Deploy over 12 months via STP (Systematic Transfer Plan)",
            f"        → Reduces timing risk significantly",
            "",
            f"Suggested allocation ({risk} risk profile):",
        ]
        allocs = {"conservative": [30, 50, 20], "moderate": [50, 35, 15], "aggressive": [70, 20, 10]}
        a = allocs.get(risk, allocs["moderate"])
        lines += [
            f"  {a[0]}% — Equity funds (split large, mid, flexi cap)",
            f"  {a[1]}% — Debt (PPF, bonds, short duration funds)",
            f"  {a[2]}% — Gold / international funds (hedge)",
        ]
        return add_disclaimer("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────

"""
agents/couples_planner.py
Couple's Money Planner — joint financial optimisation.
"""
from models.user_profile import UserFinancialProfile
from tools.tax_calculator import calculate_old_regime, calculate_new_regime
from tools.compliance_guardrails import add_disclaimer as _add_disclaimer


class CouplesPlannerAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, profile: UserFinancialProfile) -> str:
        p1_income = profile.annual_income or 0
        p2_income = profile.partner.annual_income if profile.partner else 0
        combined = p1_income + p2_income

        lines = [
            "💑 COUPLE'S MONEY PLAN",
            "=" * 55,
            f"Combined Annual Income: ₹{combined:,.0f}",
            "",
            "🏠 HRA Optimisation:",
            "  → Higher-earning partner should claim HRA if renting",
            "  → Other partner can invest in PPF/ELSS to use their 80C slab",
            "",
            "💊 Health Insurance:",
            "  → Family floater is usually cheaper than 2 individual policies",
            "  → Ensure cover = at least ₹15-20L for a couple",
            "",
            "🏦 NPS Split:",
            "  → Both partners should contribute ₹50,000 to NPS Tier-1",
            f"  → Combined 80CCD(1B) benefit = ₹1,00,000 tax deduction",
            "",
            "📈 SIP Strategy:",
            "  → Split SIPs across both names to spread risk",
            "  → If incomes are very different, invest more in lower-earner's name",
            "    to avoid clubbing of income on future gains",
            "",
            "📋 Combined Net Worth Tracker:",
            f"  Person 1 Investments: ₹{profile.total_investments():,.0f}",
            f"  Person 2 Investments: ₹{(profile.partner.existing_investments if profile.partner else 0):,.0f}",
            f"  Combined Net Worth:    ₹{profile.net_worth():,.0f}",
        ]
        return _add_disclaimer("\n".join(lines))
