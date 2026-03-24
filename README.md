# 🤖 ET AI Money Mentor — Track 9 Submission
**ET AI Hackathon 2026 | Avataar.ai × Economic Times**

> An autonomous, multi-agent financial planning system that turns confused savers into confident investors — living inside ET, powered by AI.

---

## 🎯 Problem We're Solving

95% of Indians have no financial plan. Financial advisors cost ₹25,000+/year and serve only HNIs. ET AI Money Mentor democratises professional-grade financial planning for every ET user — in under 5 minutes, with zero jargon, and zero cost.

---

## 🧠 What We Built (Hybrid Approach — All 6 Sub-Problems)

| Module | What It Does |
|---|---|
| **FIRE Path Planner** | Month-by-month retirement roadmap with dynamic recalculation |
| **Money Health Score** | 5-minute onboarding across 6 financial wellness dimensions |
| **Life Event Advisor** | Bonus, marriage, baby, inheritance — context-aware advice |
| **Tax Wizard** | Old vs New regime comparison with step-by-step verifiable math |
| **Couple's Money Planner** | Joint income optimisation across HRA, NPS, SIPs |
| **MF Portfolio X-Ray** | CAMS/KFintech upload → XIRR, overlap, rebalancing plan |

---

## 🏗️ Architecture Overview

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│       Orchestrator Agent         │  ← Routes intent, manages state
│  (LangGraph StateGraph)          │
└────────┬────────────────────────┘
         │  dispatches to
    ┌────┴──────────────────────────────────┐
    │                                       │
    ▼                                       ▼
Intake Agent                    Specialist Agents
(Profile Builder)               ├── FIRE Planner Agent
    │                           ├── Tax Wizard Agent
    ▼                           ├── MF X-Ray Agent
UserProfile State               ├── Health Score Agent
    │                           ├── Life Event Agent
    └──────────────────────────►└── Couples Planner Agent
                                        │
                                        ▼
                               Compliance Guardrail Layer
                               (SEBI/RBI disclaimer injection)
                                        │
                                        ▼
                               Output Formatter
                               (Structured plan + PDF export)
```

### Agent Communication Pattern
- **Orchestrator** uses LangGraph `StateGraph` with typed `UserFinancialState`
- **Specialist agents** are nodes in the graph, share state via typed dict
- **Tools** are Python functions registered as LangChain tools
- **Memory** persists across turns using `MemorySaver` checkpointer

---

## ⚙️ Tech Stack

| Category | Choice | Reason |
|---|---|---|
| Agent Framework | LangGraph | Best-in-class stateful multi-agent graph |
| LLM | Claude Sonnet 4 (Anthropic) | Strong reasoning for financial math |
| Small LLM routing | Haiku for intent classification | Cost efficiency |
| Financial calculations | Pure Python (numpy, scipy) | Verifiable, auditable math |
| MF Statement parsing | pdfplumber + pandas | CAMS/KFintech PDF extraction |
| Compliance layer | Rule-based + LLM | SEBI/RBI guardrails |
| API | FastAPI | Lightweight REST interface |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key

### Installation

```bash
git clone https://github.com/your-team/et-money-mentor.git
cd et-money-mentor
pip install -r requirements.txt
```

### Environment Setup

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run the Agent

```bash
# Interactive CLI demo
python main.py

# API server
python api.py
```

### Run Scenario Pack Tests

```bash
# Scenario 1: FIRE plan for mid-career professional
python tests/test_fire_scenario.py

# Scenario 2: Tax regime edge case
python tests/test_tax_scenario.py

# Scenario 3: MF portfolio X-Ray
python tests/test_mf_xray_scenario.py
```

---

## 📁 Project Structure

```
et-money-mentor/
├── main.py                    # Entry point — interactive demo
├── api.py                     # FastAPI server
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── orchestrator.py        # LangGraph StateGraph — central router
│   ├── intake_agent.py        # User profiling & data collection
│   ├── fire_planner.py        # Retirement planning agent
│   ├── tax_wizard.py          # Tax regime optimisation agent
│   ├── mf_xray.py             # MF portfolio analysis agent
│   ├── health_score.py        # Financial wellness scoring agent
│   ├── life_event_advisor.py  # Life event triggered advice agent
│   └── couples_planner.py     # Joint financial planning agent
│
├── tools/
│   ├── financial_calculators.py  # XIRR, SWR, inflation math
│   ├── tax_calculator.py          # FY2025-26 slabs, deductions
│   ├── mf_parser.py               # CAMS/KFintech PDF parser
│   └── compliance_guardrails.py   # SEBI/RBI disclaimer engine
│
├── models/
│   └── user_profile.py        # Typed state — UserFinancialProfile
│
├── config/
│   └── settings.py            # LLM routing, thresholds
│
├── data/
│   └── sample_cams.pdf        # Sample CAMS statement for demo
│
└── tests/
    ├── test_fire_scenario.py
    ├── test_tax_scenario.py
    └── test_mf_xray_scenario.py
```

---

## 🔒 Compliance & Guardrails

Every output from ET AI Money Mentor includes:
1. **Mandatory SEBI disclaimer** — distinguishes AI guidance from licensed financial advice
2. **Calculation audit trail** — every number shown with formula and inputs
3. **Assumption transparency** — inflation rate, return assumptions always displayed
4. **Graceful degradation** — if data is incomplete, agent asks for clarification instead of hallucinating

---

## 📊 Agentic Architecture — Scenario Pack Coverage

| Scenario | Steps Completed Autonomously |
|---|---|
| FIRE Plan (34yo, ₹24L) | Input intake → inflation adjustment → SIP calculation → glidepath → gap analysis → PDF export (6 steps) |
| Tax Regime Edge Case | Salary parsing → Old regime calc → New regime calc → Delta analysis → Deduction suggestions → Step-by-step report (6 steps) |
| MF Portfolio X-Ray | CAMS parse → XIRR calc → Overlap matrix → Expense ratio analysis → Tax-aware rebalancing plan (5 steps) |

---

## ⚠️ Disclaimer

ET AI Money Mentor provides AI-generated financial information for educational purposes only. It does not constitute licensed financial advice under SEBI regulations. Please consult a SEBI-registered investment advisor before making investment decisions.
