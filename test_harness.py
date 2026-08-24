"""
Integration tests for the Integration Harness (Person C Lead).
Verifies end-to-end flow with mock agents, timing-out stubs, malformed responses, and batch runs.
"""

import unittest
from src.contract import CandidateProfile, AgentStatus, CONTRACT_VERSION
from src.harness import IntegrationHarness
from src.mocks import (
    SkillsAgent,
    ExperienceAgent,
    DiversityAgent,
    EconomicAgent,
    FaultyTimeoutAgent,
    FaultyMalformedAgent,
    FaultyExceptionAgent
)


class TestIntegrationHarness(unittest.TestCase):

    def setUp(self):
        self.strong_candidate = CandidateProfile(
            candidate_id="CAND-STRONG-001",
            resume_text="Senior Python and Machine Learning Engineer with 8 years experience.",
            job_description="Looking for Python, Machine Learning, and Game Theory expert with 5+ years experience.",
            target_budget=130000.0,
            salary_expectation=120000.0,
            attributes={
                "skills": ["python", "machine_learning", "cooperative_game_theory"],
                "years_experience": 8,
                "diversity_flag": True
            }
        )

        self.weak_candidate = CandidateProfile(
            candidate_id="CAND-WEAK-002",
            resume_text="Junior intern with basic HTML experience.",
            job_description="Senior Lead Software Architect.",
            target_budget=100000.0,
            salary_expectation=180000.0,  # Far over budget
            attributes={
                "skills": ["html"],
                "years_experience": 0,
                "diversity_flag": False
            }
        )

    def test_full_harness_strong_candidate_hire(self):
        harness = IntegrationHarness()  # Default mock agents
        res = harness.evaluate_candidate(self.strong_candidate)

        self.assertEqual(res.candidate_id, "CAND-STRONG-001")
        self.assertEqual(res.decision, "hire")
        self.assertEqual(res.contract_version, CONTRACT_VERSION)
        self.assertGreater(res.nash_product_hire, res.nash_product_reject)
        self.assertEqual(len(res.shapley_values), 4)
        for aid, status in res.agent_statuses.items():
            self.assertEqual(status, AgentStatus.SUCCESS.value)

    def test_full_harness_weak_candidate_reject(self):
        harness = IntegrationHarness()
        res = harness.evaluate_candidate(self.weak_candidate)

        self.assertEqual(res.candidate_id, "CAND-WEAK-002")
        self.assertEqual(res.decision, "reject")
        self.assertGreater(res.nash_product_reject, res.nash_product_hire)

    def test_harness_with_timing_out_agent(self):
        mock_skills = SkillsAgent()
        mock_exp = ExperienceAgent()
        mock_div = DiversityAgent()
        faulty_econ = FaultyTimeoutAgent("economic_agent")

        harness = IntegrationHarness(agents={
            "skills_agent": mock_skills.evaluate,
            "experience_agent": mock_exp.evaluate,
            "diversity_agent": mock_div.evaluate,
            "economic_agent": faulty_econ.evaluate
        })

        res = harness.evaluate_candidate(self.strong_candidate)

        # Economic agent should trigger FALLBACK, but engine should complete successfully without crashing
        self.assertEqual(res.agent_statuses["economic_agent"], AgentStatus.FALLBACK.value)
        self.assertEqual(res.decision, "hire")

    def test_harness_with_malformed_agent_data(self):
        mock_skills = SkillsAgent()
        mock_exp = ExperienceAgent()
        mock_div = DiversityAgent()
        faulty_malformed = FaultyMalformedAgent("economic_agent")

        harness = IntegrationHarness(agents={
            "skills_agent": mock_skills.evaluate,
            "experience_agent": mock_exp.evaluate,
            "diversity_agent": mock_div.evaluate,
            "economic_agent": faulty_malformed.evaluate
        })

        res = harness.evaluate_candidate(self.strong_candidate)

        self.assertEqual(res.agent_statuses["economic_agent"], AgentStatus.FALLBACK.value)

    def test_harness_with_exception_agent(self):
        mock_skills = SkillsAgent()
        mock_exp = ExperienceAgent()
        faulty_exception = FaultyExceptionAgent("diversity_agent")
        mock_econ = EconomicAgent()

        harness = IntegrationHarness(agents={
            "skills_agent": mock_skills.evaluate,
            "experience_agent": mock_exp.evaluate,
            "diversity_agent": faulty_exception.evaluate,
            "economic_agent": mock_econ.evaluate
        })

        res = harness.evaluate_candidate(self.strong_candidate)

        self.assertEqual(res.agent_statuses["diversity_agent"], AgentStatus.FALLBACK.value)

    def test_batch_candidate_evaluation(self):
        harness = IntegrationHarness()
        batch_results = harness.evaluate_candidate_batch([self.strong_candidate, self.weak_candidate])

        self.assertEqual(len(batch_results), 2)
        self.assertEqual(batch_results[0].decision, "hire")
        self.assertEqual(batch_results[1].decision, "reject")


if __name__ == "__main__":
    unittest.main()
