"""
Nash Bargaining Decision Engine (Pure Code, Zero LLM Calls).

Implements the multi-agent Nash Bargaining Solution for binary hiring decisions {hire, reject}.
Mathematically calculates surplus gains over disagreement points, computes weighted Nash products,
and selects the decision that maximizes collective utility surplus.
"""

import math
from typing import Dict, Any, Tuple, Optional
from src.contract import AgentOutput, DEFAULT_DISAGREEMENT_POINT, DEFAULT_WEIGHT


class NashBargainingEngine:
    """
    Pure deterministic Nash Bargaining decision engine.
    """

    def __init__(self, epsilon: float = 1e-6):
        """
        :param epsilon: Small positive offset to avoid log(0) or division by zero.
        """
        self.epsilon = epsilon

    def compute_decision(
        self,
        agent_outputs: Dict[str, AgentOutput],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes the Nash Bargaining outcome for decision space {hire, reject}.

        :param agent_outputs: Dictionary mapping agent_id -> AgentOutput.
        :param custom_weights: Optional dict overriding default agent weights.
        :return: Structured result dictionary with decision, products, gains, and logs.
        """
        if not agent_outputs:
            raise ValueError("agent_outputs dictionary cannot be empty.")

        agent_ids = list(agent_outputs.keys())

        # Extract weights and normalize
        raw_weights = {}
        for aid in agent_ids:
            if custom_weights and aid in custom_weights and custom_weights[aid] > 0:
                raw_weights[aid] = custom_weights[aid]
            else:
                raw_weights[aid] = agent_outputs[aid].weight if agent_outputs[aid].weight > 0 else DEFAULT_WEIGHT

        total_weight = sum(raw_weights.values())
        if total_weight <= 0:
            total_weight = len(agent_ids)
            weights = {aid: 1.0 / len(agent_ids) for aid in agent_ids}
        else:
            weights = {aid: raw_weights[aid] / total_weight for aid in agent_ids}

        # Calculate surplus gains & log Nash product
        surplus_hire: Dict[str, float] = {}
        surplus_reject: Dict[str, float] = {}
        utilities_hire: Dict[str, float] = {}
        utilities_reject: Dict[str, float] = {}
        disagreement_points: Dict[str, float] = {}

        log_product_hire = 0.0
        log_product_reject = 0.0

        for aid, output in agent_outputs.items():
            u_hire = output.utility_hire
            u_reject = output.utility_reject
            d_i = output.disagreement_point
            w_i = weights[aid]

            utilities_hire[aid] = u_hire
            utilities_reject[aid] = u_reject
            disagreement_points[aid] = d_i

            # Gain calculation: max(Utility - DisagreementPoint, epsilon)
            gain_hire = max(u_hire - d_i, self.epsilon)
            gain_reject = max(u_reject - d_i, self.epsilon)

            surplus_hire[aid] = gain_hire
            surplus_reject[aid] = gain_reject

            log_product_hire += w_i * math.log(gain_hire)
            log_product_reject += w_i * math.log(gain_reject)

        # Exponentiate for exact Nash product values
        # Math safety: clamp log value to prevent float overflow under large exponents
        clamped_log_hire = max(-700.0, min(700.0, log_product_hire))
        clamped_log_reject = max(-700.0, min(700.0, log_product_reject))

        nash_product_hire = math.exp(clamped_log_hire)
        nash_product_reject = math.exp(clamped_log_reject)

        # Decision Rule: Pick action with higher Nash Product (or higher Log Nash Product)
        # If exact tie, default to "reject" (risk-averse baseline)
        if log_product_hire > log_product_reject:
            decision = "hire"
        else:
            decision = "reject"

        return {
            "decision": decision,
            "nash_product_hire": nash_product_hire,
            "nash_product_reject": nash_product_reject,
            "log_nash_product_hire": log_product_hire,
            "log_nash_product_reject": log_product_reject,
            "surplus_hire": surplus_hire,
            "surplus_reject": surplus_reject,
            "utilities_hire": utilities_hire,
            "utilities_reject": utilities_reject,
            "disagreement_points": disagreement_points,
            "normalized_weights": weights,
        }


def nash_bargaining_decision(
    utilities_hire: Dict[str, float],
    utilities_reject: Dict[str, float],
    disagreement_points: Dict[str, float],
    weights: Dict[str, float]
) -> str:
    """
    Convenience function matching standard signature for direct decision evaluation.
    """
    outputs = {}
    for aid in utilities_hire:
        outputs[aid] = AgentOutput(
            agent_id=aid,
            utility_hire=utilities_hire[aid],
            utility_reject=utilities_reject.get(aid, 1.0 - utilities_hire[aid]),
            disagreement_point=disagreement_points.get(aid, DEFAULT_DISAGREEMENT_POINT),
            weight=weights.get(aid, DEFAULT_WEIGHT)
        )
    engine = NashBargainingEngine()
    result = engine.compute_decision(outputs)
    return result["decision"]
