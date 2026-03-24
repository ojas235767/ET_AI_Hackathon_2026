"""
agents/health_score.py
Money Health Score — 5-minute onboarding across 6 financial dimensions.
"""
from models.user_profile import UserFinancialProfile
from tools.compliance_guardrails import add_disclaimer


DIMENSIONS = ["Emergency Preparedness", "Insurance Coverage", "Investment Diversification",
               "Debt Health", "Tax Efficiency", "Retirement Readiness"]


class HealthScoreAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, profile: UserFinancialProfile) -> str:
        scores = self._score_all(profile)
        total = sum(s["score"] for s in scores) / len(scores)

        lines = ["💰 MONEY HEALTH SCORE", "=" * 55, f"Overall Score: {total:.0f}/100", ""]
        for s in scores:
            bar = "█" * int(s["score"] / 10) + "░" * (10 - int(s["score"] / 10))
            lines.append(f"{s['dimension']:<28} [{bar}] {s['score']}/100")
            lines.append(f"  → {s['insight']}")
            lines.append("")

        lines += ["🎯 TOP 3 PRIORITY ACTIONS:", "-" * 40]
        weak = sorted(scores, key=lambda x: x["score"])[:3]
        for i, s in enumerate(weak, 1):
            lines.append(f"{i}. {s['action']}")

        return add_disclaimer("\n".join(lines))

    def _score_all(self, p: UserFinancialProfile) -> list[dict]:
        monthly_income = (p.annual_income or 0) / 12
        monthly_exp = p.monthly_expenses or monthly_income * 0.7

        scores = []

        # 1. Emergency fund (6 months expenses)
        liquid = p.fd_balance
        needed = monthly_exp * 6
        em_score = min(100, int(liquid / needed * 100)) if needed > 0 else 0
        scores.append({
            "dimension": "Emergency Preparedness",
            "score": em_score,
            "insight": f"Have ₹{liquid:,.0f} liquid, need ₹{needed:,.0f} (6 months expenses)",
            "action": f"Build emergency fund to ₹{needed:,.0f} before investing further",
        })

        # 2. Insurance
        rec_life = (p.annual_income or 0) * 10
        ins_score = min(100, int(min(p.life_cover / rec_life, 1) * 50 + min(p.health_cover / 1_000_000, 1) * 50))
        scores.append({
            "dimension": "Insurance Coverage",
            "score": ins_score,
            "insight": f"Life cover: ₹{p.life_cover:,.0f} (need ₹{rec_life:,.0f}), Health: ₹{p.health_cover:,.0f}",
            "action": f"Increase term cover to ₹{rec_life:,.0f} and health cover to ₹10L",
        })

        # 3. Investment diversification
        total_inv = p.total_investments()
        equity = p.mf_investments + p.stocks_value
        debt = p.ppf_balance + p.epf_balance + p.fd_balance
        div_score = 60 if equity > 0 and debt > 0 else 30
        if p.gold_value > 0: div_score += 10
        if p.nps_balance > 0: div_score += 10
        if p.stocks_value > 0: div_score += 10
        scores.append({
            "dimension": "Investment Diversification",
            "score": min(100, div_score),
            "insight": f"Equity: ₹{equity:,.0f} | Debt: ₹{debt:,.0f} | Total: ₹{total_inv:,.0f}",
            "action": "Ensure equity:debt ratio matches your age-based allocation target",
        })

        # 4. Debt health
        debt_load = (p.home_loan_outstanding + p.personal_loan_outstanding + p.credit_card_debt)
        emis = debt_load * 0.02  # rough EMI estimate
        dti = emis / monthly_income if monthly_income > 0 else 1
        debt_score = max(0, min(100, int((1 - dti / 0.5) * 100)))
        scores.append({
            "dimension": "Debt Health",
            "score": debt_score,
            "insight": f"Total liabilities: ₹{debt_load:,.0f} | Est. EMI-to-income: {dti:.0%}",
            "action": "Pay off credit card debt first (highest interest), then personal loans",
        })

        # 5. Tax efficiency
        ti = p.tax_inputs
        tax_score = 40  # base
        if ti:
            if ti.investments_80c >= 150_000: tax_score += 20
            if ti.nps_self >= 50_000: tax_score += 20
            if ti.medical_insurance >= 25_000: tax_score += 20
        scores.append({
            "dimension": "Tax Efficiency",
            "score": min(100, tax_score),
            "insight": "80C/80D/NPS utilisation checked against income",
            "action": "Max out 80C (₹1.5L) + 80CCD(1B) NPS (₹50K) to save ₹52,000-₹78,000/year in taxes",
        })

        # 6. Retirement readiness
        age = p.age or 30
        target_corpus_today = (p.monthly_corpus_needed or 50_000) * 12 * 25
        actual = p.total_investments()
        ret_score = min(100, int(actual / target_corpus_today * 100))
        scores.append({
            "dimension": "Retirement Readiness",
            "score": ret_score,
            "insight": f"Current corpus: ₹{actual:,.0f} | Rough target (25x rule): ₹{target_corpus_today:,.0f}",
            "action": "Start FIRE planner for a precise month-by-month retirement roadmap",
        })

        return scores
