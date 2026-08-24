"""
Unit tests for the Nash Bargaining Decision Engine.
"""

import unittest
from src.contract import AgentOutput, AgentStatus
from src.engine import NashBargainingEngine, nash_bargaining_decision


class TestNashBargainingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = NashBargainingEngine()

    def test_clear_hire_decision(self):
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.9, utility_reject=0.1, disagreement_point=0.3),
            "experience_agent": AgentOutput("experience_agent", utility_hire=0.8, utility_reject=0.2, disagreement_point=0.3),
            "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.85, utility_reject=0.15, disagreement_point=0.3),
            "economic_agent": AgentOutput("economic_agent", utility_hire=0.75, utility_reject=0.25, disagreement_point=0.3),
        }
        res = self.engine.compute_decision(outputs)
        self.assertEqual(res["decision"], "hire")
        self.assertGreater(res["nash_product_hire"], res["nash_product_reject"])
        self.assertGreater(res["log_nash_product_hire"], res["log_nash_product_reject"])

    def test_clear_reject_decision(self):
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.2, utility_reject=0.8, disagreement_point=0.3),
            "experience_agent": AgentOutput("experience_agent", utility_hire=0.1, utility_reject=0.9, disagreement_point=0.3),
            "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.3, utility_reject=0.7, disagreement_point=0.3),
            "economic_agent": AgentOutput("economic_agent", utility_hire=0.25, utility_reject=0.75, disagreement_point=0.3),
        }
        res = self.engine.compute_decision(outputs)
        self.assertEqual(res["decision"], "reject")
        self.assertGreater(res["nash_product_reject"], res["nash_product_hire"])

    def test_custom_weights_effect(self):
        # Skills agent strongly favors hire, economic agent strongly favors reject
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.95, utility_reject=0.05, disagreement_point=0.2, weight=0.25),
            "experience_agent": AgentOutput("experience_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3, weight=0.25),
            "diversity_agent": AgentOutput("diversity_agent", utility_hire=0.5, utility_reject=0.5, disagreement_point=0.3, weight=0.25),
            "economic_agent": AgentOutput("economic_agent", utility_hire=0.10, utility_reject=0.90, disagreement_point=0.2, weight=0.25),
        }

        # Case 1: Skills agent given 90% weight -> HIRE
        res_skills_heavy = self.engine.compute_decision(outputs, custom_weights={"skills_agent": 0.9, "economic_agent": 0.1})
        self.assertEqual(res_skills_heavy["decision"], "hire")

        # Case 2: Economic agent given 90% weight -> REJECT
        res_econ_heavy = self.engine.compute_decision(outputs, custom_weights={"skills_agent": 0.1, "economic_agent": 0.9})
        self.assertEqual(res_econ_heavy["decision"], "reject")

    def test_surplus_gain_clamping(self):
        # Utility below disagreement point should clamp gain to epsilon
        outputs = {
            "skills_agent": AgentOutput("skills_agent", utility_hire=0.1, utility_reject=0.9, disagreement_point=0.5),
        }
        res = self.engine.compute_decision(outputs)
        self.assertEqual(res["surplus_hire"]["skills_agent"], self.engine.epsilon)
        self.assertAlmostEqual(res["surplus_reject"]["skills_agent"], 0.4)

    def test_convenience_function_signature(self):
        u_hire = {"skills": 0.8, "exp": 0.7}
        u_reject = {"skills": 0.2, "exp": 0.3}
        d_pts = {"skills": 0.3, "exp": 0.3}
        weights = {"skills": 0.5, "exp": 0.5}

        decision = nash_bargaining_decision(u_hire, u_reject, d_pts, weights)
        self.assertEqual(decision, "hire")


if __name__ == "__main__":
    unittest.main()
