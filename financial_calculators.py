"""
tools/financial_calculators.py
Core financial math — all calculations are pure Python, fully auditable.
No black boxes. Every function returns both result AND step-by-step working.
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import brentq
from dataclasses import dataclass
from typing import Optional


INFLATION_RATE = 0.06        # 6% default inflation assumption
EQUITY_RETURN = 0.12         # 12% long-run equity CAGR assumption
DEBT_RETURN = 0.07           # 7% debt return assumption
PPF_RATE = 0.071             # Current PPF rate


@dataclass
class FirePlanResult:
    monthly_sip_required: float
    corpus_required: float
    years_to_retirement: int
    current_corpus: float
    corpus_gap: float
    asset_allocation: dict[str, float]
    glidepath: list[dict]          # year-by-year allocation shift
    monthly_plan: list[dict]       # month-by-month SIP breakdown by category
    assumptions: dict
    steps: list[str]               # step-by-step audit trail


def calculate_inflation_adjusted_corpus(
    monthly_need_today: float,
    years_to_retirement: int,
    retirement_duration_years: int = 30,
    inflation: float = INFLATION_RATE,
    withdrawal_return: float = 0.08,
) -> tuple[float, list[str]]:
    """
    Calculate corpus needed at retirement using the SWR / present value method.
    Returns (corpus_required, steps_list)
    """
    steps = []

    # Step 1: Inflate monthly need to retirement date
    monthly_need_at_retirement = monthly_need_today * ((1 + inflation) ** years_to_retirement)
    annual_need_at_retirement = monthly_need_at_retirement * 12
    steps.append(
        f"Step 1 — Inflate monthly need: ₹{monthly_need_today:,.0f} × "
        f"(1 + {inflation:.0%})^{years_to_retirement} = ₹{monthly_need_at_retirement:,.0f}/month "
        f"(₹{annual_need_at_retirement:,.0f}/year at retirement)"
    )

    # Step 2: Calculate corpus using Present Value of Annuity formula
    # PV = PMT × [1 - (1+r)^-n] / r  where r = real return rate
    real_return = (1 + withdrawal_return) / (1 + inflation) - 1
    if real_return <= 0:
        corpus = annual_need_at_retirement * retirement_duration_years
    else:
        corpus = annual_need_at_retirement * (
            (1 - (1 + real_return) ** -retirement_duration_years) / real_return
        )
    steps.append(
        f"Step 2 — Corpus via PV of annuity formula (real return = {real_return:.2%}, "
        f"{retirement_duration_years} years): ₹{corpus:,.0f}"
    )
    return corpus, steps


def calculate_sip_required(
    future_corpus: float,
    current_corpus: float,
    years: int,
    annual_return: float = EQUITY_RETURN,
) -> tuple[float, list[str]]:
    """
    Calculate monthly SIP needed given current corpus and target corpus.
    Formula: SIP = (FV - PV*(1+r)^n) * r / ((1+r)^n - 1)
    where r = monthly rate
    """
    steps = []
    n = years * 12
    r = annual_return / 12

    # Future value of current corpus
    fv_current = current_corpus * ((1 + r) ** n)
    steps.append(
        f"Step 1 — FV of current corpus ₹{current_corpus:,.0f} at {annual_return:.0%}/yr "
        f"for {years} yrs = ₹{fv_current:,.0f}"
    )

    # Remaining gap
    remaining = future_corpus - fv_current
    steps.append(f"Step 2 — Corpus gap = ₹{future_corpus:,.0f} - ₹{fv_current:,.0f} = ₹{remaining:,.0f}")

    if remaining <= 0:
        steps.append("Step 3 — Existing corpus is sufficient. No additional SIP required.")
        return 0.0, steps

    # SIP required
    sip = remaining * r / ((1 + r) ** n - 1)
    steps.append(
        f"Step 3 — Monthly SIP = ₹{remaining:,.0f} × {r:.6f} / ((1+{r:.6f})^{n} - 1) "
        f"= ₹{sip:,.0f}/month"
    )
    return sip, steps


def build_glidepath(years_to_retirement: int, risk_profile: str = "moderate") -> list[dict]:
    """
    Age-based asset allocation glidepath.
    Equity % decreases as retirement approaches.
    """
    glidepath = []
    for year in range(years_to_retirement + 1):
        years_left = years_to_retirement - year

        if risk_profile == "aggressive":
            equity_pct = min(90, 40 + years_left * 2.5)
        elif risk_profile == "conservative":
            equity_pct = min(70, 20 + years_left * 2.0)
        else:  # moderate
            equity_pct = min(80, 30 + years_left * 2.0)

        equity_pct = max(20, equity_pct)
        debt_pct = 100 - equity_pct

        glidepath.append({
            "year": year,
            "years_to_retirement": years_left,
            "equity_pct": round(equity_pct, 1),
            "debt_pct": round(debt_pct, 1),
            "large_cap_pct": round(equity_pct * 0.5, 1),
            "mid_small_cap_pct": round(equity_pct * 0.3, 1),
            "international_pct": round(equity_pct * 0.2, 1),
            "debt_pct_breakdown": {
                "ppf_epf": round(debt_pct * 0.5, 1),
                "debt_mf": round(debt_pct * 0.3, 1),
                "fd": round(debt_pct * 0.2, 1),
            }
        })
    return glidepath


def calculate_xirr(cash_flows: list[tuple[str, float]], guess: float = 0.1) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return) for a portfolio.
    cash_flows: list of (date_str, amount) — positive=investment, negative=redemption/current_value
    Returns annual XIRR as a decimal.
    """
    from datetime import datetime

    dates = [datetime.strptime(d, "%Y-%m-%d") for d, _ in cash_flows]
    amounts = [a for _, a in cash_flows]
    t0 = dates[0]
    days = [(d - t0).days for d in dates]

    def npv(rate):
        return sum(cf / ((1 + rate) ** (d / 365)) for cf, d in zip(amounts, days))

    try:
        xirr = brentq(npv, -0.5, 10.0, xtol=1e-8)
        return xirr
    except ValueError:
        return float("nan")


def calculate_overlap_matrix(funds: list[dict]) -> dict:
    """
    Calculate portfolio overlap between mutual funds.
    funds: list of dicts with 'name', 'top_holdings' (list of stock names), 'allocation_pct'
    Returns overlap matrix and stocks appearing in multiple funds.
    """
    all_stocks: dict[str, list[str]] = {}
    for fund in funds:
        for stock in fund.get("top_holdings", []):
            if stock not in all_stocks:
                all_stocks[stock] = []
            all_stocks[stock].append(fund["name"])

    # Stocks in 2+ funds = overlap
    overlapping = {
        stock: fund_list
        for stock, fund_list in all_stocks.items()
        if len(fund_list) >= 2
    }

    overlap_score = len(overlapping) / max(len(all_stocks), 1) * 100

    return {
        "overlapping_stocks": overlapping,
        "overlap_score_pct": round(overlap_score, 1),
        "total_unique_stocks": len(all_stocks),
        "high_overlap_funds": _find_high_overlap_fund_pairs(funds),
    }


def _find_high_overlap_fund_pairs(funds: list[dict]) -> list[dict]:
    pairs = []
    for i in range(len(funds)):
        for j in range(i + 1, len(funds)):
            set_i = set(funds[i].get("top_holdings", []))
            set_j = set(funds[j].get("top_holdings", []))
            common = set_i & set_j
            if len(common) > 0 and (len(set_i) + len(set_j)) > 0:
                overlap_pct = len(common) / len(set_i | set_j) * 100
                pairs.append({
                    "fund_a": funds[i]["name"],
                    "fund_b": funds[j]["name"],
                    "common_stocks": list(common),
                    "overlap_pct": round(overlap_pct, 1),
                })
    return sorted(pairs, key=lambda x: x["overlap_pct"], reverse=True)


def calculate_expense_ratio_drag(
    corpus: float,
    regular_er: float,
    direct_er: float,
    years: int = 10,
) -> dict:
    """Calculate the cost of staying in regular plan vs direct plan."""
    er_diff = regular_er - direct_er
    # Drag on ₹1 invested over N years
    drag_factor = (1 + er_diff) ** years - 1
    total_drag = corpus * drag_factor

    return {
        "regular_er_pct": regular_er,
        "direct_er_pct": direct_er,
        "annual_drag_pct": round(er_diff, 3),
        "10yr_cost_inr": round(total_drag, 0),
        "explanation": (
            f"By staying in regular plan (ER {regular_er:.2%}) vs direct (ER {direct_er:.2%}), "
            f"you lose approximately ₹{total_drag:,.0f} over {years} years on ₹{corpus:,.0f} corpus."
        )
    }
