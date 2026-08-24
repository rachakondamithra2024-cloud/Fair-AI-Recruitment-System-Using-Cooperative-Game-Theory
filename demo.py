"""
Demo Script — Fair AI Recruitment System Aggregation Engine.

Demonstrates end-to-end processing of candidate profiles through:
1. Four domain agents (Skills, Experience, Diversity, Economic)
2. Contract v1.0.0 validation & fallback manager
3. Pure Nash Bargaining decision engine
4. Exact Shapley value explanation module
"""

import json
from src import (
    CandidateProfile,
    IntegrationHarness,
    SkillsAgent,
    ExperienceAgent,
    DiversityAgent,
    EconomicAgent,
    FaultyTimeoutAgent
)


def run_demo():
    print("=" * 80)
    print("         FAIR AI RECRUITMENT SYSTEM — AGGREGATION ENGINE DEMO")
    print("=" * 80)

    # 1. Create a candidate profile
    candidate = CandidateProfile(
        candidate_id="CAND-2026-889",
        resume_text="Senior Full-Stack & ML Specialist with 6 years experience in Python, PyTorch, and Game Theory.",
        job_description="Seeking Senior AI Engineer with Python, Machine Learning, and Game Theory expertise.",
        target_budget=125000.0,
        salary_expectation=120000.0,
        attributes={
            "skills": ["python", "machine_learning", "cooperative_game_theory", "pytorch"],
            "years_experience": 6,
            "diversity_flag": True
        }
    )

    print(f"\n[+] Candidate Profile: {candidate.candidate_id}")
    print(f"    Salary Expectation: ${candidate.salary_expectation:,.2f} | Budget: ${candidate.target_budget:,.2f}")
    print(f"    Experience: {candidate.attributes['years_experience']} years")
    print(f"    Skills: {', '.join(candidate.attributes['skills'])}")

    # 2. Instantiate Integration Harness with standard mock agents
    harness = IntegrationHarness()

    # 3. Evaluate candidate
    result = harness.evaluate_candidate(candidate)

    print("\n" + "=" * 80)
    print(f"DECISION OUTCOME: {result.decision.upper()}")
    print("=" * 80)
    print(f"Contract Version:    {result.contract_version}")
    print(f"Nash Product (Hire): {result.nash_product_hire:.6e} (Log: {result.log_nash_product_hire:+.4f})")
    print(f"Nash Product (Reject): {result.nash_product_reject:.6e} (Log: {result.log_nash_product_reject:+.4f})")

    print("\n--- AGENT UTILITIES & SURPLUS GAINS ---")
    for aid, utils in result.agent_utilities.items():
        weight = result.agent_weights[aid]
        status = result.agent_statuses[aid]
        surplus_h = result.surplus_hire[aid]
        surplus_r = result.surplus_reject[aid]
        print(f" * {aid:18s} [{status:7s}] Weight: {weight:.2f} | U(Hire): {utils['hire']:.2f}, U(Reject): {utils['reject']:.2f} | Gain(Hire): {surplus_h:.4f}, Gain(Reject): {surplus_r:.4f}")

    print("\n--- SHAPLEY VALUE EXPLANATION BREAKDOWN ---")
    print(result.explanation)

    # 4. Demonstrate Resilient Fallback when an agent times out
    print("\n" + "=" * 80)
    print("DEMO: RESILIENT FALLBACK HANDLING (ECONOMIC AGENT TIMEOUT)")
    print("=" * 80)

    faulty_harness = IntegrationHarness(agents={
        "skills_agent": SkillsAgent().evaluate,
        "experience_agent": ExperienceAgent().evaluate,
        "diversity_agent": DiversityAgent().evaluate,
        "economic_agent": FaultyTimeoutAgent("economic_agent").evaluate
    })

    fallback_result = faulty_harness.evaluate_candidate(candidate)
    print(f"Decision with Timeout Agent: {fallback_result.decision.upper()}")
    print(f"Economic Agent Status:      {fallback_result.agent_statuses['economic_agent']}")
    print(f"Explanation Preview:\n{fallback_result.explanation}")


if __name__ == "__main__":
    run_demo()
