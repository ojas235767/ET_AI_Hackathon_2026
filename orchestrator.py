"""
agents/orchestrator.py
Central LangGraph StateGraph orchestrator — routes user intent to specialist agents.
Implements 3+ sequential analysis steps without human input per hackathon requirement.
"""

from __future__ import annotations
import os
from typing import Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing_extensions import TypedDict

from models.user_profile import UserFinancialProfile
from config.settings import LLM_CONFIG


# ── State Definition ──────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    profile: UserFinancialProfile
    current_module: str          # which specialist is active
    completed_steps: list[str]   # audit trail of completed steps
    next_action: str             # orchestrator's routing decision
    output_ready: bool


# ── LLM Setup ────────────────────────────────────────────────────────────────

def get_llm(model_size: Literal["large", "small"] = "large") -> ChatAnthropic:
    """Cost-efficient LLM routing: small model for classification, large for reasoning."""
    if model_size == "small":
        return ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1)


ORCHESTRATOR_SYSTEM = """You are the ET AI Money Mentor orchestrator. 
Your job is to:
1. Understand the user's financial need from their message
2. Route to the correct specialist module
3. Collect missing data through natural conversation

Available modules:
- fire_planner: Retirement planning, FIRE calculations
- tax_wizard: Tax regime comparison, deduction optimisation
- mf_xray: Mutual fund portfolio analysis, CAMS statement upload
- health_score: Financial wellness assessment (5-minute onboarding)
- life_event_advisor: Bonus, marriage, baby, inheritance planning
- couples_planner: Joint financial planning for couples

Respond with JSON: {"module": "<module_name>", "message": "<response to user>"}
If the user's need is unclear, ask ONE focused question to clarify.
Always be warm, jargon-free, and encouraging."""


def classify_intent(state: AgentState) -> AgentState:
    """
    Use small (cheap) model to classify intent and route to module.
    This is the cost-efficiency optimization.
    """
    llm = get_llm("small")
    last_message = state["messages"][-1].content

    classification_prompt = f"""Classify this user message into one module:
fire_planner | tax_wizard | mf_xray | health_score | life_event_advisor | couples_planner | general

Message: "{last_message}"

Respond with only the module name."""

    result = llm.invoke([HumanMessage(content=classification_prompt)])
    module = result.content.strip().lower()

    valid_modules = {
        "fire_planner", "tax_wizard", "mf_xray",
        "health_score", "life_event_advisor", "couples_planner",
    }
    if module not in valid_modules:
        module = "health_score"  # default entry point for new users

    state["current_module"] = module
    state["completed_steps"].append(f"Intent classified → {module}")
    return state


def check_profile_completeness(state: AgentState) -> Literal["collect_data", "run_specialist"]:
    """
    Router: if profile has enough data for the selected module, run specialist.
    Otherwise collect more data.
    """
    profile = state["profile"]
    module = state["current_module"]

    if module == "fire_planner" and not profile.is_ready_for_fire_planning():
        return "collect_data"
    if module == "tax_wizard" and not profile.is_ready_for_tax_analysis():
        return "collect_data"
    return "run_specialist"


def collect_data(state: AgentState) -> AgentState:
    """Intake agent: asks for missing data in a conversational way."""
    from agents.intake_agent import IntakeAgent

    agent = IntakeAgent(get_llm("large"))
    result = agent.collect_next_field(state["profile"], state["current_module"])

    state["messages"].append(AIMessage(content=result["question"]))
    state["completed_steps"].append(f"Data collected: {result.get('field_name', 'unknown')}")
    return state


def run_specialist(state: AgentState) -> AgentState:
    """Route to the appropriate specialist agent and run analysis."""
    module = state["current_module"]
    profile = state["profile"]

    if module == "fire_planner":
        from agents.fire_planner import FirePlannerAgent
        agent = FirePlannerAgent(get_llm("large"))
        output = agent.run(profile)

    elif module == "tax_wizard":
        from agents.tax_wizard import TaxWizardAgent
        agent = TaxWizardAgent(get_llm("large"))
        output = agent.run(profile)

    elif module == "mf_xray":
        from agents.mf_xray import MFXRayAgent
        agent = MFXRayAgent(get_llm("large"))
        output = agent.run(profile)

    elif module == "health_score":
        from agents.health_score import HealthScoreAgent
        agent = HealthScoreAgent(get_llm("large"))
        output = agent.run(profile)

    elif module == "life_event_advisor":
        from agents.life_event_advisor import LifeEventAdvisorAgent
        agent = LifeEventAdvisorAgent(get_llm("large"))
        output = agent.run(profile)

    elif module == "couples_planner":
        from agents.couples_planner import CouplesPlannerAgent
        agent = CouplesPlannerAgent(get_llm("large"))
        output = agent.run(profile)

    else:
        output = "I'm not sure which module to use. Let me start with a quick financial health check."

    state["messages"].append(AIMessage(content=output))
    state["completed_steps"].append(f"Specialist {module} completed analysis")
    state["output_ready"] = True
    return state


def should_continue(state: AgentState) -> Literal["classify_intent", "end"]:
    if state.get("output_ready"):
        return "end"
    return "classify_intent"


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("collect_data", collect_data)
    graph.add_node("run_specialist", run_specialist)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        check_profile_completeness,
        {
            "collect_data": "collect_data",
            "run_specialist": "run_specialist",
        },
    )

    graph.add_edge("collect_data", "classify_intent")  # loop until profile complete
    graph.add_edge("run_specialist", END)

    return graph


def create_mentor() -> object:
    """Factory: returns a compiled, memory-enabled orchestrator."""
    graph = build_graph()
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
