"""
Fair AI Recruitment System Using Cooperative Game Theory.
Aggregation Engine & Integration Harness Package (Person C Lead).
"""

from src.contract import (
    CandidateProfile,
    AgentOutput,
    DecisionResult,
    AgentStatus,
    CONTRACT_VERSION,
    EXPECTED_AGENTS,
    validate_and_sanitize_agent_output
)
from src.engine import NashBargainingEngine, nash_bargaining_decision
from src.shapley import ShapleyValueModule
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

__all__ = [
    "CandidateProfile",
    "AgentOutput",
    "DecisionResult",
    "AgentStatus",
    "CONTRACT_VERSION",
    "EXPECTED_AGENTS",
    "validate_and_sanitize_agent_output",
    "NashBargainingEngine",
    "nash_bargaining_decision",
    "ShapleyValueModule",
    "IntegrationHarness",
    "SkillsAgent",
    "ExperienceAgent",
    "DiversityAgent",
    "EconomicAgent",
    "FaultyTimeoutAgent",
    "FaultyMalformedAgent",
    "FaultyExceptionAgent"
]
