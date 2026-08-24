"""
Unit tests for the Shapley Value Module.
Tests exact Shapley axioms (Efficiency, Symmetry, Dummy Player), online explanations, and offline calibration.
"""

import unittest
from src.contract import AgentOutput
from src.shapley import ShapleyValueModule


class TestShapleyValueModule(unittest.TestCase):

    def setUp(self):
        self.module = ShapleyValueModule()

    def test_efficiency_axiom(self):
        """Axiom 1: Sum of all Shapley values MUST equal v(N) - v({})."""
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.9, utility_reject=0.1, disagreement_point=0.3, weight=0.25),
            "experience_agent": AgentOutput("experience_agent", utility_hire=0.8, utility_reject=0.2, disagreement_point=0.3, weight=0.25),
            "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.7, utility_reject=0.3, disagreement_point=0.3, weight=0.25),
            "economic_agent": AgentOutput("economic_agent", utility_hire=0.4, utility_reject=0.6, disagreement_point=0.3, weight=0.25),
        }
        shapley_vals = self.module.compute_shapley_values(outputs)
        sum_phi = sum(shapley_vals.values())

        # v(N)
        all_agents = tuple(sorted(outputs.keys()))
        v_N = self.module.compute_coalition_value(all_agents, outputs, {aid: 0.25 for aid in outputs})

        self.assertAlmostEqual(sum_phi, v_N, places=5)

    def test_symmetry_axiom(self):
        """Axiom 2: Symmetric players (identical utilities & weights) MUST have equal Shapley values."""
        outputs = {
            "agent1": AgentOutput("agent1", utility_hire=0.8, utility_reject=0.2, disagreement_point=0.3, weight=0.25),
            "agent2": AgentOutput("agent2", utility_hire=0.8, utility_reject=0.2, disagreement_point=0.3, weight=0.25),
            "agent3": AgentOutput("agent3", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3, weight=0.25),
            "agent4": AgentOutput("agent4", utility_hire=0.3, utility_reject=0.7, disagreement_point=0.3, weight=0.25),
        }
        shapley_vals = self.module.compute_shapley_values(outputs)
        self.assertAlmostEqual(shapley_vals["agent1"], shapley_vals["agent2"], places=5)

    def test_dummy_player_axiom(self):
        """Axiom 3: Dummy player (utility hire == utility reject == disagreement point) MUST get Shapley value == 0."""
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.9, utility_reject=0.1, disagreement_point=0.3, weight=0.333),
            "experience_agent": AgentOutput("experience_agent", utility_hire=0.7, utility_reject=0.3, disagreement_point=0.3, weight=0.333),
            "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3, weight=0.333),
            "dummy_agent": AgentOutput("dummy_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3, weight=0.25),
        }
        shapley_vals = self.module.compute_shapley_values(outputs)
        self.assertAlmostEqual(shapley_vals["dummy_agent"], 0.0, places=5)

    def test_generate_explanation_string(self):
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.9, utility_reject=0.1, reasoning="Great coder"),
            "economic_agent": AgentOutput("economic_agent", utility_hire=0.2, utility_reject=0.8, reasoning="Too expensive"),
        }
        shapley_vals = self.module.compute_shapley_values(outputs)
        explanation = self.module.generate_explanation("hire", shapley_vals, outputs)

        self.assertIn("AGGREGATION ENGINE DECISION EXPLANATION", explanation)
        self.assertIn("skills_agent", explanation)
        self.assertIn("economic_agent", explanation)

    def test_offline_weight_calibration(self):
        # Create a batch of candidate runs
        batch = [
            {
                "skills_agent": AgentOutput("skills_agent", utility_hire=0.95, utility_reject=0.05, disagreement_point=0.3),
                "experience_agent": AgentOutput("experience_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3),
                "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3),
                "economic_agent": AgentOutput("economic_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3),
            }
        ]
        calibrated_weights = self.module.calibrate_weights_offline(batch, target_equalization=True)
        self.assertAlmostEqual(sum(calibrated_weights.values()), 1.0, places=5)
        # Skills agent had huge impact, so its inverse weight should be lower to promote balance
        self.assertLess(calibrated_weights["skills_agent"], calibrated_weights["experience_agent"])


if __name__ == "__main__":
    unittest.main()
