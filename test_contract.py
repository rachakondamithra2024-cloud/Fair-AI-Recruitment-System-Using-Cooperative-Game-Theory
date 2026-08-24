"""
Unit tests for Contract v1.0.0 validation and fallback policy.
"""

import unittest
from src.contract import (
    AgentOutput,
    AgentStatus,
    CandidateProfile,
    CONTRACT_VERSION,
    DEFAULT_DISAGREEMENT_POINT,
    validate_and_sanitize_agent_output
)


class TestContractValidation(unittest.TestCase):

    def test_valid_agent_output(self):
        raw = {
            "agent_id": "skills_agent",
            "utility_hire": 0.85,
            "utility_reject": 0.15,
            "disagreement_point": 0.30,
            "weight": 0.25,
            "status": "SUCCESS",
            "reasoning": "Strong match",
            "version": "1.0.0"
        }
        validated = validate_and_sanitize_agent_output(raw, "skills_agent")
        self.assertEqual(validated.agent_id, "skills_agent")
        self.assertEqual(validated.utility_hire, 0.85)
        self.assertEqual(validated.utility_reject, 0.15)
        self.assertEqual(validated.status, AgentStatus.SUCCESS)
        self.assertEqual(validated.version, CONTRACT_VERSION)

    def test_timeout_fallback(self):
        raw = {
            "agent_id": "experience_agent",
            "status": "TIMEOUT",
            "reasoning": "Timed out after 5000ms"
        }
        validated = validate_and_sanitize_agent_output(raw, "experience_agent")
        self.assertEqual(validated.agent_id, "experience_agent")
        self.assertEqual(validated.status, AgentStatus.FALLBACK)
        self.assertEqual(validated.utility_hire, DEFAULT_DISAGREEMENT_POINT)
        self.assertIn("[FALLBACK TRIGGERED]", validated.reasoning)

    def test_out_of_bounds_utility_fallback(self):
        raw = {
            "agent_id": "diversity_agent",
            "utility_hire": 5.5,  # Invalid: > 1.0
            "utility_reject": -0.2, # Invalid: < 0.0
            "disagreement_point": 0.30,
            "status": "SUCCESS"
        }
        validated = validate_and_sanitize_agent_output(raw, "diversity_agent")
        self.assertEqual(validated.status, AgentStatus.FALLBACK)
        self.assertEqual(validated.utility_hire, 1.0)
        self.assertEqual(validated.utility_reject, 0.0)

    def test_non_dict_fallback(self):
        raw = "Invalid Non-Dict Output"
        validated = validate_and_sanitize_agent_output(raw, "economic_agent")
        self.assertEqual(validated.agent_id, "economic_agent")
        self.assertEqual(validated.status, AgentStatus.FALLBACK)
        self.assertEqual(validated.utility_hire, DEFAULT_DISAGREEMENT_POINT)

    def test_candidate_profile_serialization(self):
        profile = CandidateProfile(
            candidate_id="CAND-001",
            resume_text="Experienced engineer",
            job_description="Senior Lead",
            attributes={"skills": ["python"]}
        )
        d = profile.to_dict()
        self.assertEqual(d["candidate_id"], "CAND-001")
        self.assertEqual(d["attributes"]["skills"], ["python"])


if __name__ == "__main__":
    unittest.main()
