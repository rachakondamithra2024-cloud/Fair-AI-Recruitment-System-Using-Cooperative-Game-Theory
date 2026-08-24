"""
Integration Harness (Person C Lead).

Wires candidate profiles and domain agents into the Nash Bargaining Engine and Shapley Explainer.
Validates all outputs against Contract v1.0.0, enforces resilient fallbacks, and outputs structured decision results.
"""

import datetime
from typing import Dict, List, Any, Callable, Optional, Union
from src.contract import (
    CandidateProfile,
    AgentOutput,
    DecisionResult,
    AgentStatus,
    CONTRACT_VERSION,
    EXPECTED_AGENTS,
    validate_and_sanitize_agent_output
)
from src.engine import NashBargainingEngine
from src.shapley import ShapleyValueModule
from src.mocks import SkillsAgent, ExperienceAgent, DiversityAgent, EconomicAgent


AgentCallable = Callable[[CandidateProfile], Union[AgentOutput, Dict[str, Any]]]


class IntegrationHarness:
    """
    Main Integration Harness wiring 4 agents to the aggregation engine.
    """

    def __init__(
        self,
        agents: Optional[Dict[str, AgentCallable]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        epsilon: float = 1e-6
    ):
        """
        :param agents: Map of agent_id -> callable function taking CandidateProfile and returning output.
        :param custom_weights: Optional weights dict overriding agent-provided weights.
        :param epsilon: Numerical offset for log calculations.
        """
        self.custom_weights = custom_weights
        self.engine = NashBargainingEngine(epsilon=epsilon)
        self.shapley_module = ShapleyValueModule(epsilon=epsilon)

        # Default to standard mock agents if none provided
        if agents is None:
            mock_skills = SkillsAgent()
            mock_exp = ExperienceAgent()
            mock_div = DiversityAgent()
            mock_econ = EconomicAgent()
            self.agents: Dict[str, AgentCallable] = {
                "skills_agent": mock_skills.evaluate,
                "experience_agent": mock_exp.evaluate,
                "diversity_agent": mock_div.evaluate,
                "economic_agent": mock_econ.evaluate
            }
        else:
            self.agents = agents

    def evaluate_candidate(
        self,
        profile: CandidateProfile,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> DecisionResult:
        """
        Runs full integration pipeline for a single candidate profile.

        :param profile: CandidateProfile object.
        :param custom_weights: Optional weights override.
        :return: DecisionResult dataclass containing decision, Nash products, Shapley breakdown, and status.
        """
        effective_weights = custom_weights or self.custom_weights
        agent_outputs: Dict[str, AgentOutput] = {}
        agent_statuses: Dict[str, str] = {}

        # 1. Query all 4 agents and validate outputs against Contract v1.0.0
        for expected_aid in sorted(list(EXPECTED_AGENTS)):
            if expected_aid in self.agents:
                agent_fn = self.agents[expected_aid]
                try:
                    raw_out = agent_fn(profile)
                except Exception as ex:
                    raw_out = {
                        "agent_id": expected_aid,
                        "status": "ERROR",
                        "reasoning": f"Unhandled agent exception: {str(ex)}"
                    }
            else:
                raw_out = {
                    "agent_id": expected_aid,
                    "status": "TIMEOUT",
                    "reasoning": "Agent callable missing from harness configuration."
                }

            # Enforce Contract v1.0.0 validation and fallback policy
            validated_output = validate_and_sanitize_agent_output(raw_out, expected_aid)
            if isinstance(raw_out, AgentOutput):
                # Ensure dataclass format is preserved if already outputted as AgentOutput
                validated_output = raw_out

            agent_outputs[expected_aid] = validated_output
            agent_statuses[expected_aid] = validated_output.status.value if isinstance(validated_output.status, AgentStatus) else str(validated_output.status)

        # 2. Execute Nash Bargaining Decision Engine
        engine_res = self.engine.compute_decision(agent_outputs, custom_weights=effective_weights)

        # 3. Execute Shapley Explainer Module
        shapley_values = self.shapley_module.compute_shapley_values(agent_outputs, custom_weights=effective_weights)
        explanation_text = self.shapley_module.generate_explanation(
            decision=engine_res["decision"],
            shapley_values=shapley_values,
            agent_outputs=agent_outputs
        )

        # 4. Construct final structured DecisionResult payload
        agent_utilities_formatted = {
            aid: {
                "hire": agent_outputs[aid].utility_hire,
                "reject": agent_outputs[aid].utility_reject
            }
            for aid in agent_outputs
        }

        return DecisionResult(
            candidate_id=profile.candidate_id,
            decision=engine_res["decision"],
            contract_version=CONTRACT_VERSION,
            nash_product_hire=engine_res["nash_product_hire"],
            nash_product_reject=engine_res["nash_product_reject"],
            log_nash_product_hire=engine_res["log_nash_product_hire"],
            log_nash_product_reject=engine_res["log_nash_product_reject"],
            surplus_hire=engine_res["surplus_hire"],
            surplus_reject=engine_res["surplus_reject"],
            agent_utilities=agent_utilities_formatted,
            agent_weights=engine_res["normalized_weights"],
            disagreement_points=engine_res["disagreement_points"],
            shapley_values=shapley_values,
            agent_statuses=agent_statuses,
            explanation=explanation_text
        )

    def evaluate_candidate_batch(
        self,
        profiles: List[CandidateProfile]
    ) -> List[DecisionResult]:
        """
        Evaluates a batch of candidates and returns a list of DecisionResult objects.
        """
        return [self.evaluate_candidate(p) for p in profiles]
