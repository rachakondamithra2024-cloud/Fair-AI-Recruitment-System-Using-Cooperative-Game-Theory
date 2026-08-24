"""
Shapley Value Module (Pure Code, Zero LLM Calls).

Calculates exact Shapley values for N=4 agents (2^4 = 16 coalition subsets).
- Online mode: Computes per-candidate quantitative feature contribution & decision breakdown.
- Offline mode: Calibrates agent weights over a batch of validation candidate records.
"""

import math
import itertools
from typing import Dict, List, Any, Tuple, Optional
from src.contract import AgentOutput, DEFAULT_DISAGREEMENT_POINT, DEFAULT_WEIGHT
from src.engine import NashBargainingEngine


class ShapleyValueModule:
    """
    Exact Shapley value solver for committee decision game (N=4).
    """

    def __init__(self, epsilon: float = 1e-6):
        self.epsilon = epsilon
        self.engine = NashBargainingEngine(epsilon=epsilon)

    @staticmethod
    def _factorial(n: int) -> int:
        return math.factorial(n)

    def compute_coalition_value(
        self,
        coalition: Tuple[str, ...],
        agent_outputs: Dict[str, AgentOutput],
        base_weights: Dict[str, float]
    ) -> float:
        """
        Computes coalition characteristic function v(S).
        v(S) = sum_{i in S} w_i * (log G_i(hire) - log G_i(reject))
        v({}) = 0.0
        """
        if not coalition:
            return 0.0

        v_S = 0.0
        for aid in coalition:
            if aid in agent_outputs:
                out = agent_outputs[aid]
                w_i = base_weights.get(aid, DEFAULT_WEIGHT)
                g_hire = max(out.utility_hire - out.disagreement_point, self.epsilon)
                g_reject = max(out.utility_reject - out.disagreement_point, self.epsilon)
                v_S += w_i * (math.log(g_hire) - math.log(g_reject))
        return v_S

    def compute_shapley_values(
        self,
        agent_outputs: Dict[str, AgentOutput],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Computes exact online Shapley values for each agent in agent_outputs.

        :param agent_outputs: Dictionary mapping agent_id -> AgentOutput.
        :param custom_weights: Optional weights dict.
        :return: Dictionary mapping agent_id -> exact Shapley value phi_i.
        """
        all_agents = sorted(list(agent_outputs.keys()))
        n = len(all_agents)
        if n == 0:
            return {}

        base_weights = {}
        for aid in all_agents:
            if custom_weights and aid in custom_weights and custom_weights[aid] > 0:
                base_weights[aid] = custom_weights[aid]
            else:
                base_weights[aid] = agent_outputs[aid].weight if agent_outputs[aid].weight > 0 else DEFAULT_WEIGHT

        # Precompute v(S) for all 2^N subsets
        coalition_values: Dict[Tuple[str, ...], float] = {}

        for k in range(n + 1):
            for subset in itertools.combinations(all_agents, k):
                coalition_values[subset] = self.compute_coalition_value(subset, agent_outputs, base_weights)

        # Compute exact Shapley formula for each agent
        shapley_values: Dict[str, float] = {}
        fact_n = self._factorial(n)

        for agent in all_agents:
            phi_i = 0.0
            other_agents = [a for a in all_agents if a != agent]
            n_others = len(other_agents)

            for k in range(n_others + 1):
                for subset in itertools.combinations(other_agents, k):
                    s_len = len(subset)
                    weight = (self._factorial(s_len) * self._factorial(n - s_len - 1)) / fact_n

                    subset_with_i = tuple(sorted(list(subset) + [agent]))
                    subset_without_i = tuple(sorted(list(subset)))

                    marginal_contribution = coalition_values[subset_with_i] - coalition_values[subset_without_i]
                    phi_i += weight * marginal_contribution

            shapley_values[agent] = phi_i

        return shapley_values

    def generate_explanation(
        self,
        decision: str,
        shapley_values: Dict[str, float],
        agent_outputs: Dict[str, AgentOutput]
    ) -> str:
        """
        Generates human-readable, quantitative explanation breakdown based on Shapley values.
        """
        total_abs = sum(abs(v) for v in shapley_values.values())
        if total_abs == 0:
            pct_contributions = {aid: 0.0 for aid in shapley_values}
        else:
            pct_contributions = {aid: (abs(v) / total_abs) * 100.0 for aid, v in shapley_values.items()}

        lines = [
            f"=== AGGREGATION ENGINE DECISION EXPLANATION ===",
            f"Final Outcome: {decision.upper()}",
            f"\nQuantitative Agent Shapley Contributions (Net Surplus Impact):"
        ]

        # Sort agents by absolute influence
        sorted_agents = sorted(shapley_values.items(), key=lambda item: abs(item[1]), reverse=True)

        for aid, phi in sorted_agents:
            pct = pct_contributions[aid]
            direction = "FAVORED HIRE" if phi > 0 else ("FAVORED REJECT" if phi < 0 else "NEUTRAL")
            reason = agent_outputs[aid].reasoning if aid in agent_outputs else ""
            status = agent_outputs[aid].status.value if aid in agent_outputs else "UNKNOWN"

            lines.append(
                f" - [{aid}] ({status}): Shapley Value = {phi:+.4f} ({pct:.1f}% relative impact) -> {direction}."
            )
            if reason:
                lines.append(f"   Reasoning: {reason}")

        return "\n".join(lines)

    def calibrate_weights_offline(
        self,
        batch_agent_outputs: List[Dict[str, AgentOutput]],
        target_equalization: bool = True
    ) -> Dict[str, float]:
        """
        Offline calibration over a batch of validation candidate outputs.
        Adjusts weights so that agent influence (average absolute Shapley value) is balanced.

        :param batch_agent_outputs: List of dicts of agent outputs for historical candidates.
        :param target_equalization: If True, recalibrates weights to equalize mean impact across agents.
        :return: Calibrated agent weights dict (normalized to sum=1.0).
        """
        if not batch_agent_outputs:
            return {aid: DEFAULT_WEIGHT for aid in {"skills_agent", "experience_agent", "diversity_agent", "economic_agent"}}

        all_agent_ids = set()
        for sample in batch_agent_outputs:
            all_agent_ids.update(sample.keys())

        agent_ids = sorted(list(all_agent_ids))
        agent_abs_shapley_sum = {aid: 0.0 for aid in agent_ids}
        count = len(batch_agent_outputs)

        for sample in batch_agent_outputs:
            sample_shapley = self.compute_shapley_values(sample)
            for aid in agent_ids:
                agent_abs_shapley_sum[aid] += abs(sample_shapley.get(aid, 0.0))

        mean_abs_shapley = {aid: agent_abs_shapley_sum[aid] / count for aid in agent_ids}

        if not target_equalization or sum(mean_abs_shapley.values()) == 0:
            return {aid: 1.0 / len(agent_ids) for aid in agent_ids}

        # Inverse influence calibration: agents with higher unweighted dominance get reduced weight,
        # agents with lower dominance get increased weight to achieve fair equilibrium.
        total_mean = sum(mean_abs_shapley.values())
        raw_inv_weights = {}
        for aid in agent_ids:
            avg = mean_abs_shapley[aid]
            if avg > 0:
                raw_inv_weights[aid] = 1.0 / avg
            else:
                raw_inv_weights[aid] = 1.0

        total_inv = sum(raw_inv_weights.values())
        calibrated_weights = {aid: raw_inv_weights[aid] / total_inv for aid in agent_ids}
        return calibrated_weights
