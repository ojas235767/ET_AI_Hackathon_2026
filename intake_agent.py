"""
agents/intake_agent.py
Conversational intake agent — collects missing financial data naturally.
Uses small LLM for efficiency. Tracks which fields are filled.
"""

from __future__ import annotations
from models.user_profile import UserFinancialProfile, TaxInputs

# Fields required per module
MODULE_REQUIRED_FIELDS = {
    "fire_planner": ["age", "annual_income", "monthly_expenses", "retirement_age_target",
                     "monthly_corpus_needed", "mf_investments", "ppf_balance", "epf_balance"],
    "tax_wizard": ["annual_income", "tax_inputs"],
    "mf_xray": ["mf_portfolio"],
    "health_score": ["age", "annual_income", "monthly_expenses", "life_cover", "health_cover",
                     "credit_card_debt", "mf_investments", "epf_balance"],
    "life_event_advisor": ["age", "annual_income", "recent_life_event", "event_amount", "risk_profile"],
    "couples_planner": ["age", "annual_income", "partner"],
}

FIELD_QUESTIONS = {
    "age": "To get started, may I know your current age?",
    "annual_income": "What is your annual gross income (CTC) in rupees?",
    "monthly_expenses": "What are your approximate monthly household expenses?",
    "retirement_age_target": "At what age would you like to retire?",
    "monthly_corpus_needed": "How much monthly income would you need in retirement (in today's rupees)?",
    "mf_investments": "What is the current value of your mutual fund investments? (Enter 0 if none)",
    "ppf_balance": "What is your current PPF balance? (Enter 0 if none)",
    "epf_balance": "What is your current EPF/PF balance? (Enter 0 if none)",
    "life_cover": "What is your current life insurance cover amount? (Term plan sum assured, or 0)",
    "health_cover": "What is your health insurance cover amount? (or 0 if no mediclaim)",
    "risk_profile": "How would you describe your risk appetite? (conservative / moderate / aggressive)",
    "recent_life_event": "What life event are you planning for? (bonus / marriage / new_baby / inheritance / home_purchase)",
    "event_amount": "What is the amount involved? (e.g., bonus amount or inheritance amount in rupees)",
    "tax_inputs": "What is your annual base salary (before HRA and other components)?",
    "mf_portfolio": (
        "Please upload your CAMS or KFintech consolidated statement (PDF), or type 'demo' "
        "to use a sample portfolio for analysis."
    ),
    "partner": "What is your partner's name and annual income?",
    "credit_card_debt": "Do you have any outstanding credit card or personal loan debt? (amount in ₹, or 0)",
}


class IntakeAgent:
    def __init__(self, llm):
        self.llm = llm

    def collect_next_field(self, profile: UserFinancialProfile, module: str) -> dict:
        """Find the next unfilled required field and return the question to ask."""
        required = MODULE_REQUIRED_FIELDS.get(module, [])

        for field in required:
            if not self._is_filled(profile, field):
                return {
                    "field_name": field,
                    "question": FIELD_QUESTIONS.get(field, f"Could you share your {field}?"),
                }

        return {"field_name": None, "question": "Great, I have all the information I need. Let me analyse..."}

    def _is_filled(self, profile: UserFinancialProfile, field: str) -> bool:
        val = getattr(profile, field, None)
        if val is None:
            return False
        if isinstance(val, (int, float)) and val == 0 and field in [
            "mf_investments", "ppf_balance", "epf_balance", "life_cover",
            "health_cover", "credit_card_debt"
        ]:
            return True  # 0 is a valid explicit answer for these fields
        if isinstance(val, (int, float)) and val == 0:
            return False
        if isinstance(val, str) and val == "":
            return False
        if isinstance(val, list) and len(val) == 0 and field == "mf_portfolio":
            return False
        return True

    def parse_user_response(self, field: str, response: str, profile: UserFinancialProfile) -> UserFinancialProfile:
        """Parse user's text response and update the profile."""
        response = response.strip().lower()

        try:
            if field == "age":
                profile.age = int(response.replace(" ", "").replace("years", "").replace("yr", ""))

            elif field == "annual_income":
                profile.annual_income = self._parse_money(response)

            elif field == "monthly_expenses":
                profile.monthly_expenses = self._parse_money(response)

            elif field == "retirement_age_target":
                profile.retirement_age_target = int(response.split()[0])

            elif field == "monthly_corpus_needed":
                profile.monthly_corpus_needed = self._parse_money(response)

            elif field in ["mf_investments", "ppf_balance", "epf_balance",
                           "life_cover", "health_cover", "event_amount",
                           "credit_card_debt"]:
                setattr(profile, field, self._parse_money(response))

            elif field == "risk_profile":
                from models.user_profile import RiskProfile
                mapping = {"conservative": RiskProfile.CONSERVATIVE,
                           "moderate": RiskProfile.MODERATE,
                           "aggressive": RiskProfile.AGGRESSIVE}
                profile.risk_profile = mapping.get(response, RiskProfile.MODERATE)

            elif field == "recent_life_event":
                from models.user_profile import LifeEvent
                mapping = {e.value: e for e in LifeEvent}
                profile.recent_life_event = mapping.get(response.replace(" ", "_"))

            elif field == "tax_inputs":
                if profile.tax_inputs is None:
                    profile.tax_inputs = TaxInputs()
                profile.tax_inputs.base_salary = self._parse_money(response)

            elif field == "mf_portfolio":
                if response == "demo":
                    from agents.mf_xray import MFXRayAgent
                    profile.mf_portfolio = MFXRayAgent(None)._load_demo_portfolio()

        except (ValueError, AttributeError):
            pass  # graceful degradation — will re-ask

        return profile

    def _parse_money(self, text: str) -> float:
        """Parse money strings: '24L', '24 lakhs', '24,00,000', '2.4cr' → float"""
        text = text.replace(",", "").replace("₹", "").replace("rs", "").strip()
        multiplier = 1
        if "cr" in text or "crore" in text:
            multiplier = 10_000_000
            text = text.replace("crore", "").replace("cr", "")
        elif "l" in text or "lakh" in text or "lac" in text:
            multiplier = 100_000
            text = text.replace("lakh", "").replace("lac", "").replace("l", "")
        elif "k" in text:
            multiplier = 1000
            text = text.replace("k", "")
        return float(text.strip()) * multiplier
