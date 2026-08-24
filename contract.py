"""
Interface Contract v1.0.0 — Data Models and Validation / Fallback Logic.

This module defines the data structures and validation functions for agent communication
and contract enforcement within the Fair AI Recruitment System.
"""

import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional, Union

CONTRACT_VERSION = "1.0.0"
EXPECTED_AGENTS = {"skills_agent", "experience_agent", "diversity_agent", "economic_agent"}
DEFAULT_DISAGREEMENT_POINT = 0.30
DEFAULT_WEIGHT = 0.25


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    FALLBACK = "FALLBACK"


@dataclass
class CandidateProfile:
    candidate_id: str
    resume_text: str
    job_description: str
    target_budget: float = 100000.0
    salary_expectation: float = 100000.0
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentOutput:
    agent_id: str
    utility_hire: float
    utility_reject: float
    disagreement_point: float = DEFAULT_DISAGREEMENT_POINT
    weight: float = DEFAULT_WEIGHT
    status: AgentStatus = AgentStatus.SUCCESS
    reasoning: Union[str, Dict[str, Any]] = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    version: str = CONTRACT_VERSION

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, AgentStatus) else str(self.status)
        return d


@dataclass
class DecisionResult:
    candidate_id: str
    decision: str  # "hire" or "reject"
    contract_version: str
    nash_product_hire: float
    nash_product_reject: float
    log_nash_product_hire: float
    log_nash_product_reject: float
    surplus_hire: Dict[str, float]
    surplus_reject: Dict[str, float]
    agent_utilities: Dict[str, Dict[str, float]]
    agent_weights: Dict[str, float]
    disagreement_points: Dict[str, float]
    shapley_values: Dict[str, float]
    agent_statuses: Dict[str, str]
    explanation: str
    execution_timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_and_sanitize_agent_output(
    raw_output: Any,
    expected_agent_id: str,
    default_weight: float = DEFAULT_WEIGHT
) -> AgentOutput:
    """
    Validates a raw agent response against Contract v1.0.0.
    If the response is missing, timing out, malformed, or out of bounds,
    applies the resilient fallback policy to return a valid AgentOutput object.
    """
    if not isinstance(raw_output, dict):
        return AgentOutput(
            agent_id=expected_agent_id,
            utility_hire=DEFAULT_DISAGREEMENT_POINT,
            utility_reject=DEFAULT_DISAGREEMENT_POINT,
            disagreement_point=DEFAULT_DISAGREEMENT_POINT,
            weight=default_weight,
            status=AgentStatus.FALLBACK,
            reasoning=f"[FALLBACK TRIGGERED] Raw output is not a dictionary. Got: {type(raw_output).__name__}",
            version=CONTRACT_VERSION
        )

    agent_id = str(raw_output.get("agent_id", expected_agent_id))
    raw_status = str(raw_output.get("status", "SUCCESS")).upper()

    # If explicit timeout or error
    if raw_status in (AgentStatus.TIMEOUT.value, AgentStatus.ERROR.value):
        return AgentOutput(
            agent_id=expected_agent_id,
            utility_hire=DEFAULT_DISAGREEMENT_POINT,
            utility_reject=DEFAULT_DISAGREEMENT_POINT,
            disagreement_point=DEFAULT_DISAGREEMENT_POINT,
            weight=default_weight,
            status=AgentStatus.FALLBACK,
            reasoning=f"[FALLBACK TRIGGERED] Agent returned status {raw_status}. Original reasoning: {raw_output.get('reasoning', '')}",
            version=CONTRACT_VERSION
        )

    # Validate numbers
    try:
        u_hire = float(raw_output["utility_hire"])
        u_reject = float(raw_output.get("utility_reject", 1.0 - u_hire))
        d_point = float(raw_output.get("disagreement_point", DEFAULT_DISAGREEMENT_POINT))
        weight = float(raw_output.get("weight", default_weight))
    except (KeyError, ValueError, TypeError) as e:
        return AgentOutput(
            agent_id=expected_agent_id,
            utility_hire=DEFAULT_DISAGREEMENT_POINT,
            utility_reject=DEFAULT_DISAGREEMENT_POINT,
            disagreement_point=DEFAULT_DISAGREEMENT_POINT,
            weight=default_weight,
            status=AgentStatus.FALLBACK,
            reasoning=f"[FALLBACK TRIGGERED] Malformed numerical fields in output: {e}",
            version=CONTRACT_VERSION
        )

    # Bound checking [0.0, 1.0] for utilities and disagreement point
    is_valid = True
    issues = []
    if not (0.0 <= u_hire <= 1.0):
        is_valid = False
        issues.append(f"utility_hire ({u_hire}) out of bounds [0, 1]")
    if not (0.0 <= u_reject <= 1.0):
        is_valid = False
        issues.append(f"utility_reject ({u_reject}) out of bounds [0, 1]")
    if not (0.0 <= d_point <= 1.0):
        is_valid = False
        issues.append(f"disagreement_point ({d_point}) out of bounds [0, 1]")
    if weight <= 0.0:
        weight = default_weight

    if not is_valid:
        return AgentOutput(
            agent_id=expected_agent_id,
            utility_hire=max(0.0, min(1.0, u_hire)) if isinstance(u_hire, float) else DEFAULT_DISAGREEMENT_POINT,
            utility_reject=max(0.0, min(1.0, u_reject)) if isinstance(u_reject, float) else DEFAULT_DISAGREEMENT_POINT,
            disagreement_point=max(0.0, min(1.0, d_point)) if isinstance(d_point, float) else DEFAULT_DISAGREEMENT_POINT,
            weight=weight,
            status=AgentStatus.FALLBACK,
            reasoning=f"[FALLBACK TRIGGERED] Range violations: {', '.join(issues)}",
            version=CONTRACT_VERSION
        )

    reasoning = raw_output.get("reasoning", "")
    timestamp = str(raw_output.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()))

    return AgentOutput(
        agent_id=expected_agent_id,
        utility_hire=u_hire,
        utility_reject=u_reject,
        disagreement_point=d_point,
        weight=weight,
        status=AgentStatus.SUCCESS,
        reasoning=reasoning,
        timestamp=timestamp,
        version=CONTRACT_VERSION
    )
