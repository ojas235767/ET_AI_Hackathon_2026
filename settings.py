"""config/settings.py"""

LLM_CONFIG = {
    "large_model": "claude-sonnet-4-20250514",
    "small_model": "claude-haiku-4-5",
    "temperature": 0.1,
    "max_tokens": 4096,
}

FINANCIAL_ASSUMPTIONS = {
    "inflation_rate": 0.06,
    "equity_return": 0.12,
    "debt_return": 0.07,
    "ppf_rate": 0.071,
    "retirement_duration_years": 30,
}
