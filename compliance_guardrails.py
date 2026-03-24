"""
tools/compliance_guardrails.py
SEBI/RBI compliance layer — automatically appended to every agent output.
Ensures ET AI Money Mentor never crosses into unlicensed advisory territory.
"""

from __future__ import annotations

SEBI_DISCLAIMER = """
⚠️ IMPORTANT DISCLAIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ET AI Money Mentor provides AI-generated financial information for 
educational and informational purposes only. 

This does NOT constitute:
• Licensed investment advice under SEBI (Investment Advisers) Regulations, 2013
• A recommendation to buy or sell any specific security or mutual fund
• Insurance advice under IRDAI regulations
• Tax advisory from a qualified Chartered Accountant

All calculations are based on inputs provided and standard assumptions.
Actual results may vary. Please consult:
• A SEBI-Registered Investment Adviser (RIA) for investment decisions
• A qualified CA for tax filing
• An IRDAI-licensed agent for insurance

Returns shown are based on historical averages and are not guaranteed.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

ASSUMPTION_BLOCK_TEMPLATE = """
📊 ASSUMPTIONS USED IN THIS ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Inflation Rate: {inflation_rate:.0%} per annum
• Equity Return (long-term): {equity_return:.0%} per annum
• Debt Return: {debt_return:.0%} per annum
• PPF Rate: {ppf_rate:.1%} per annum
• Retirement Duration: {retirement_duration} years post-retirement
• Tax Slabs: FY 2025-26 (Union Budget 2025)

Changing any assumption will alter the plan. Review annually.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def add_disclaimer(output: str, assumptions: dict | None = None) -> str:
    """Append SEBI disclaimer and assumptions to any agent output."""
    result = output
    if assumptions:
        result += "\n" + ASSUMPTION_BLOCK_TEMPLATE.format(**assumptions)
    result += "\n" + SEBI_DISCLAIMER
    return result


def validate_output(output: str) -> tuple[bool, list[str]]:
    """
    Scan output for phrases that could constitute unlicensed advice.
    Returns (is_safe, flagged_phrases).
    """
    # Phrases that are too advisory without caveats
    risky_phrases = [
        "you must invest",
        "guaranteed returns",
        "definitely buy",
        "best mutual fund",
        "will definitely",
        "100% safe",
        "no risk",
        "I recommend you buy",
        "I advise you to",
    ]
    flagged = [p for p in risky_phrases if p.lower() in output.lower()]
    return len(flagged) == 0, flagged


def sanitize_output(output: str) -> str:
    """Replace risky advisory language with appropriately hedged versions."""
    replacements = {
        "you must invest": "you may consider investing",
        "guaranteed returns": "historical average returns (not guaranteed)",
        "definitely buy": "consider buying based on your risk profile",
        "best mutual fund": "a suitable mutual fund (based on your profile)",
        "I recommend you buy": "based on your inputs, this may be worth considering",
        "I advise you to": "based on your inputs, you might consider",
    }
    for risky, safe in replacements.items():
        output = output.replace(risky, safe)
    return output


def check_stcg_ltcg_context(holding_period_days: int, fund_type: str) -> dict:
    """
    Return capital gains tax context for rebalancing decisions.
    Helps agents flag tax-efficient rebalancing windows.
    """
    if fund_type.lower() in ["equity", "elss", "large cap", "mid cap", "small cap", "hybrid"]:
        if holding_period_days < 365:
            return {
                "gains_type": "STCG",
                "tax_rate": "15%",
                "recommendation": (
                    "Consider waiting until 1-year holding period to avoid 15% STCG tax."
                ),
                "days_to_ltcg": 365 - holding_period_days,
            }
        else:
            return {
                "gains_type": "LTCG",
                "tax_rate": "10% above ₹1L gains",
                "recommendation": "LTCG applicable. Gains up to ₹1L/year are tax-free.",
                "days_to_ltcg": 0,
            }
    else:  # Debt funds
        return {
            "gains_type": "Taxable at slab rate",
            "tax_rate": "As per income tax slab",
            "recommendation": (
                "Debt fund gains (post April 2023) taxed at income slab rate regardless of holding."
            ),
            "days_to_ltcg": None,
        }
