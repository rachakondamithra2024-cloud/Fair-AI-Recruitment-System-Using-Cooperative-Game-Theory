"""
Mock and Stub Agents conforming to Contract v1.0.0.

Provides realistic deterministic mock agents for local development and testing,
plus fault-injecting stubs (timeout, malformed data, exceptions).
"""

import datetime
from typing import Dict, Any
from src.contract import CandidateProfile, AgentOutput, AgentStatus, CONTRACT_VERSION, DEFAULT_DISAGREEMENT_POINT


class BaseMockAgent:
    """Base class for mock agents conforming to Contract v1.0.0."""
    def __init__(self, agent_id: str, default_weight: float = 0.25):
        self.agent_id = agent_id
        self.default_weight = default_weight

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        raise NotImplementedError


class SkillsAgent(BaseMockAgent):
    """Evaluates candidate technical skills."""
    def __init__(self, weight: float = 0.25):
        super().__init__("skills_agent", weight)

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        skills = profile.attributes.get("skills", [])
        resume = profile.resume_text.lower()
        job_desc = profile.job_description.lower()

        # Count skill matches
        match_count = sum(1 for s in skills if s.lower() in job_desc or s.lower() in resume)
        total_skills = max(1, len(skills))
        skill_ratio = match_count / total_skills

        utility_hire = max(0.1, min(0.95, 0.2 + 0.75 * skill_ratio))
        utility_reject = 1.0 - utility_hire

        return AgentOutput(
            agent_id=self.agent_id,
            utility_hire=utility_hire,
            utility_reject=utility_reject,
            disagreement_point=0.30,
            weight=self.default_weight,
            status=AgentStatus.SUCCESS,
            reasoning=f"Technical skill match ratio: {match_count}/{total_skills} ({skill_ratio * 100:.0f}%).",
            version=CONTRACT_VERSION
        )


class ExperienceAgent(BaseMockAgent):
    """Evaluates years of relevant experience."""
    def __init__(self, weight: float = 0.25):
        super().__init__("experience_agent", weight)

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        years = profile.attributes.get("years_experience", 0)

        if years >= 7:
            u_hire = 0.90
        elif years >= 4:
            u_hire = 0.75
        elif years >= 2:
            u_hire = 0.50
        else:
            u_hire = 0.20

        u_reject = 1.0 - u_hire

        return AgentOutput(
            agent_id=self.agent_id,
            utility_hire=u_hire,
            utility_reject=u_reject,
            disagreement_point=0.30,
            weight=self.default_weight,
            status=AgentStatus.SUCCESS,
            reasoning=f"Candidate has {years} years of relevant industry experience.",
            version=CONTRACT_VERSION
        )


class DiversityAgent(BaseMockAgent):
    """Evaluates diversity, equity, and inclusion factors."""
    def __init__(self, weight: float = 0.25):
        super().__init__("diversity_agent", weight)

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        has_diversity_flag = profile.attributes.get("diversity_flag", False)

        if has_diversity_flag:
            u_hire = 0.85
            reason = "Candidate contributes to underrepresented team diversity perspective."
        else:
            u_hire = 0.60
            reason = "Candidate meets standard demographic representation baseline."

        u_reject = 1.0 - u_hire

        return AgentOutput(
            agent_id=self.agent_id,
            utility_hire=u_hire,
            utility_reject=u_reject,
            disagreement_point=0.25,
            weight=self.default_weight,
            status=AgentStatus.SUCCESS,
            reasoning=reason,
            version=CONTRACT_VERSION
        )


class EconomicAgent(BaseMockAgent):
    """Evaluates salary expectations vs target budget alignment."""
    def __init__(self, weight: float = 0.25):
        super().__init__("economic_agent", weight)

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        expectation = profile.salary_expectation
        budget = profile.target_budget

        if budget <= 0:
            u_hire = 0.50
        else:
            ratio = expectation / budget
            if ratio <= 0.90:
                u_hire = 0.90  # Under budget
            elif ratio <= 1.00:
                u_hire = 0.80  # Within budget
            elif ratio <= 1.10:
                u_hire = 0.40  # Slightly over budget
            else:
                u_hire = 0.15  # Significantly over budget

        u_reject = 1.0 - u_hire

        return AgentOutput(
            agent_id=self.agent_id,
            utility_hire=u_hire,
            utility_reject=u_reject,
            disagreement_point=0.30,
            weight=self.default_weight,
            status=AgentStatus.SUCCESS,
            reasoning=f"Salary expectation (${expectation:,.0f}) vs Budget (${budget:,.0f}).",
            version=CONTRACT_VERSION
        )


class FaultyTimeoutAgent(BaseMockAgent):
    """Fault injection: Simulates an agent timing out."""
    def __init__(self, agent_id: str = "skills_agent"):
        super().__init__(agent_id)

    def evaluate(self, profile: CandidateProfile) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": "TIMEOUT",
            "reasoning": "Agent execution timed out after 5000ms."
        }


class FaultyMalformedAgent(BaseMockAgent):
    """Fault injection: Simulates an agent returning broken/out-of-bounds JSON."""
    def __init__(self, agent_id: str = "economic_agent"):
        super().__init__(agent_id)

    def evaluate(self, profile: CandidateProfile) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "utility_hire": 99.9,  # Out of bounds!
            "utility_reject": "INVALID_NUMBER",
            "disagreement_point": -5.0,  # Out of bounds!
            "status": "SUCCESS"
        }


class FaultyExceptionAgent(BaseMockAgent):
    """Fault injection: Simulates an agent throwing an unhandled runtime error."""
    def __init__(self, agent_id: str = "diversity_agent"):
        super().__init__(agent_id)

    def evaluate(self, profile: CandidateProfile) -> AgentOutput:
        raise RuntimeError("Internal database connection failed inside agent!")
