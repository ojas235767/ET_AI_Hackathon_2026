"""
models/user_profile.py
Typed state shared across all agents in the LangGraph StateGraph.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LifeEvent(str, Enum):
    BONUS = "bonus"
    MARRIAGE = "marriage"
    NEW_BABY = "new_baby"
    INHERITANCE = "inheritance"
    HOME_PURCHASE = "home_purchase"
    JOB_CHANGE = "job_change"
    RETIREMENT = "retirement"


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class TaxInputs:
    base_salary: float = 0.0
    hra_component: float = 0.0
    actual_rent_paid: float = 0.0
    city_type: str = "metro"           # metro / non_metro
    investments_80c: float = 0.0       # EPF, ELSS, PPF, LIC, etc.
    nps_employer: float = 0.0
    nps_self: float = 0.0              # 80CCD(1B) — extra ₹50K
    home_loan_interest: float = 0.0   # 24(b)
    home_loan_principal: float = 0.0  # 80C
    medical_insurance: float = 0.0    # 80D
    other_deductions: float = 0.0
    other_income: float = 0.0
    regime_preference: Optional[str] = None  # "old" / "new" / None (auto)


@dataclass
class MutualFund:
    name: str
    amc: str
    category: str                      # Large Cap, Mid Cap, etc.
    units: float
    nav: float
    current_value: float
    invested_amount: float
    xirr: Optional[float] = None
    expense_ratio: float = 0.0
    plan: str = "regular"              # regular / direct
    top_holdings: list[str] = field(default_factory=list)


@dataclass
class PartnerProfile:
    """Used for Couple's Money Planner"""
    name: str
    age: int
    annual_income: float
    monthly_expenses: float
    existing_investments: float = 0.0
    epf_contribution: float = 0.0
    tax_inputs: Optional[TaxInputs] = None


@dataclass
class UserFinancialProfile:
    """
    Central state object passed between all agents.
    All fields are optional — intake agent fills them progressively.
    """
    # --- Identity ---
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None

    # --- Income & Expenses ---
    annual_income: Optional[float] = None         # gross CTC in ₹
    monthly_take_home: Optional[float] = None
    monthly_expenses: Optional[float] = None
    monthly_savings: Optional[float] = None

    # --- Existing Investments ---
    mf_investments: float = 0.0                   # current MF corpus ₹
    ppf_balance: float = 0.0
    epf_balance: float = 0.0
    fd_balance: float = 0.0
    stocks_value: float = 0.0
    nps_balance: float = 0.0
    real_estate_value: float = 0.0
    gold_value: float = 0.0

    # --- Liabilities ---
    home_loan_outstanding: float = 0.0
    personal_loan_outstanding: float = 0.0
    credit_card_debt: float = 0.0

    # --- Goals ---
    retirement_age_target: Optional[int] = None
    monthly_corpus_needed: Optional[float] = None  # in today's ₹
    child_education_goal: float = 0.0
    home_purchase_goal: float = 0.0

    # --- Insurance ---
    life_cover: float = 0.0
    health_cover: float = 0.0

    # --- Tax ---
    tax_inputs: Optional[TaxInputs] = None

    # --- MF Portfolio ---
    mf_portfolio: list[MutualFund] = field(default_factory=list)

    # --- Risk & Preferences ---
    risk_profile: Optional[RiskProfile] = None
    investment_horizon_years: Optional[int] = None

    # --- Life Events ---
    recent_life_event: Optional[LifeEvent] = None
    event_amount: float = 0.0          # bonus amount / inheritance amount

    # --- Couple's Planning ---
    partner: Optional[PartnerProfile] = None

    # --- Agent State ---
    conversation_history: list[dict] = field(default_factory=list)
    active_module: Optional[str] = None
    collected_fields: set[str] = field(default_factory=set)
    pending_questions: list[str] = field(default_factory=list)

    # --- Computed Outputs ---
    health_score: Optional[dict] = None
    fire_plan: Optional[dict] = None
    tax_analysis: Optional[dict] = None
    mf_xray_report: Optional[dict] = None
    life_event_plan: Optional[dict] = None
    couples_plan: Optional[dict] = None

    def net_worth(self) -> float:
        assets = (self.mf_investments + self.ppf_balance + self.epf_balance +
                  self.fd_balance + self.stocks_value + self.nps_balance +
                  self.real_estate_value + self.gold_value)
        liabilities = (self.home_loan_outstanding + self.personal_loan_outstanding +
                       self.credit_card_debt)
        return assets - liabilities

    def total_investments(self) -> float:
        return (self.mf_investments + self.ppf_balance + self.epf_balance +
                self.fd_balance + self.stocks_value + self.nps_balance)

    def is_ready_for_fire_planning(self) -> bool:
        return all([
            self.age is not None,
            self.annual_income is not None,
            self.monthly_expenses is not None,
            self.retirement_age_target is not None,
            self.monthly_corpus_needed is not None,
        ])

    def is_ready_for_tax_analysis(self) -> bool:
        return self.tax_inputs is not None and self.tax_inputs.base_salary > 0
