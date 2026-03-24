"""
main.py
ET AI Money Mentor — Entry point for interactive CLI demo.
Demonstrates full agentic pipeline covering all 3 scenario packs.
"""

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

console = Console()


def run_scenario_pack_demo():
    """
    Runs all 3 Scenario Pack scenarios autonomously to demonstrate:
    - 5+ sequential steps without human input
    - Multi-agent coordination
    - Verifiable step-by-step outputs
    """
    from models.user_profile import UserFinancialProfile, RiskProfile
    from models.user_profile import TaxInputs

    console.print(Panel.fit(
        "[bold green]ET AI Money Mentor[/bold green]\n"
        "Track 9 — AI Money Mentor | ET AI Hackathon 2026",
        title="🤖 Demo"
    ))

    # ── Scenario Pack #1: FIRE Plan ───────────────────────────────────────────
    console.print("\n[bold cyan]═══ SCENARIO PACK #1: FIRE Planning ═══[/bold cyan]")
    console.print("34yo software engineer, ₹24L/year, ₹18L MF, ₹6L PPF, retire at 50 with ₹1.5L/month\n")

    profile1 = UserFinancialProfile(
        name="Arjun",
        age=34,
        annual_income=2_400_000,
        monthly_expenses=80_000,
        mf_investments=1_800_000,
        ppf_balance=600_000,
        epf_balance=400_000,
        retirement_age_target=50,
        monthly_corpus_needed=150_000,
        life_cover=0,
        health_cover=500_000,
        risk_profile=RiskProfile.MODERATE,
    )

    from agents.fire_planner import FirePlannerAgent
    agent1 = FirePlannerAgent(None)
    result1 = agent1.run(profile1)
    console.print(result1)

    # ── Scenario Pack #2: Tax Regime Edge Case ────────────────────────────────
    console.print("\n[bold cyan]═══ SCENARIO PACK #2: Tax Regime Optimisation ═══[/bold cyan]")
    console.print("₹18L base, ₹3.6L HRA, ₹1.5L 80C, ₹50K NPS, ₹40K home loan interest\n")

    profile2 = UserFinancialProfile(
        name="Priya",
        age=32,
        annual_income=1_800_000,
        tax_inputs=TaxInputs(
            base_salary=1_800_000,
            hra_component=360_000,
            actual_rent_paid=25_000,    # monthly
            city_type="metro",
            investments_80c=150_000,
            nps_self=50_000,
            home_loan_interest=40_000,
            medical_insurance=20_000,
        ),
    )

    from agents.tax_wizard import TaxWizardAgent
    agent2 = TaxWizardAgent(None)
    result2 = agent2.run(profile2)
    console.print(result2)

    # ── Scenario Pack #3: MF Portfolio X-Ray ─────────────────────────────────
    console.print("\n[bold cyan]═══ SCENARIO PACK #3: MF Portfolio X-Ray ═══[/bold cyan]")
    console.print("6 funds, 4 AMCs, 3 with heavy large-cap overlap (Reliance, HDFC, Infosys)\n")

    profile3 = UserFinancialProfile(name="Rahul", age=38, annual_income=3_000_000)
    from agents.mf_xray import MFXRayAgent
    agent3 = MFXRayAgent(None)
    result3 = agent3.run(profile3)
    console.print(result3)

    console.print("\n[bold green]✅ All scenario packs completed autonomously.[/bold green]")


def run_interactive():
    """Interactive conversational mode."""
    from agents.orchestrator import create_mentor
    mentor = create_mentor()

    config = {"configurable": {"thread_id": "demo_session_1"}}
    console.print(Panel.fit(
        "[bold]Hi! I'm your ET AI Money Mentor.[/bold]\n"
        "I can help with: retirement planning, tax optimisation,\n"
        "portfolio analysis, financial health score, and more.\n\n"
        "What's on your financial mind today?",
        title="💰 ET Money Mentor"
    ))

    while True:
        user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        if user_input.lower() in ("exit", "quit", "bye"):
            console.print("[dim]Goodbye! Remember to review your financial plan annually.[/dim]")
            break

        from models.user_profile import UserFinancialProfile
        from langgraph.graph.message import HumanMessage

        result = mentor.invoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "profile": UserFinancialProfile(),
                "current_module": "",
                "completed_steps": [],
                "next_action": "",
                "output_ready": False,
            },
            config=config,
        )

        last_ai = [m for m in result["messages"] if hasattr(m, "content") and m.type == "ai"]
        if last_ai:
            console.print(Panel(last_ai[-1].content, title="💡 Mentor"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_scenario_pack_demo()
    else:
        run_interactive()
