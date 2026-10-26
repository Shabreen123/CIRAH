"""
CIRAH: Standardized Network Evaluation Engine
Evaluates any candidate action (from CIRAH or Baselines) using the exact same
SCM counterfactual model, cost model, risk assessment, and telemetry verification.
Ensures 100% fair, unbiased, apples-to-apples comparison across all methods.
"""

import networkx as nx
import numpy as np
import time
from typing import Dict, List, Tuple, Any

from src.causal_engine import StructuralCausalModel
from src.healing_field import HealingFieldPropagator
from src.cost_model import InterventionCostModel
from src.risk_assessment import RiskAssessmentModule

class StandardizedEvaluator:
    """
    Evaluator that executes an identical measurement protocol on all candidate actions.
    """

    def __init__(self, topology: nx.DiGraph, r_max: float = 35.0):
        self.topology = topology
        self.causal_engine = StructuralCausalModel(topology)
        self.healing_propagator = HealingFieldPropagator(topology, sigma=1.5)
        self.cost_model = InterventionCostModel()
        self.risk_module = RiskAssessmentModule(r_max_default=r_max)

    def evaluate_action(self,
                        method_name: str,
                        action: Dict[str, Any],
                        flows: List[Dict[str, Any]],
                        telemetry: Dict[Tuple[str, str], Dict[str, float]],
                        target_flow: Dict[str, Any],
                        decision_latency_ms: float = 0.0) -> Dict[str, Any]:
        """
        Calculates all primary and secondary metrics for an action selected by any method.
        """
        # 1. Counterfactual evaluation under SCM
        cf_res = self.causal_engine.evaluate_counterfactual(action, flows, telemetry)

        # 2. Risk evaluation
        risk_res = self.risk_module.evaluate_risk(self.topology, action, cf_res, target_flow)

        # 3. Cost evaluation
        is_reassigned = (action["type"] not in ["no_change", "failed"])
        cost_res = self.cost_model.compute_intervention_cost(
            old_path=target_flow.get("current_path"),
            new_path=action.get("path"),
            flow_demand_mbps=target_flow["bandwidth_mbps"],
            is_reassigned=is_reassigned
        )

        # 4. Target flow performance
        target_res = cf_res["flow_outcomes"].get(target_flow["flow_id"], {})
        connected = bool(target_res.get("connected", False))
        sla_met = bool(target_res.get("sla_met", False))
        success = connected and sla_met

        # Check if action was a failed routing attempt
        if action.get("type") == "failed":
            success = False
            connected = False

        lat = float(target_res.get("latency", 1e4)) if connected else 1e4
        loss = float(target_res.get("loss", 100.0)) if connected else 100.0

        # Modeled recovery time: detection (15ms) + decision latency + hardware rule commit
        recovery_time_ms = 15.0 + decision_latency_ms + cost_res["disruption_time_ms"]
        if not success and action.get("type") == "no_change":
            # If static path failed, recovery time is infinite / capped penalty
            recovery_time_ms = 2000.0

        return {
            "method": method_name,
            "action_id": action.get("action_id", "act_unknown"),
            "success": success,
            "connected": connected,
            "latency_ms": lat,
            "loss_pct": loss,
            "risk_post": float(risk_res["R_post"]),
            "is_risk_feasible": bool(risk_res["is_risk_feasible"]),
            "constraint_violation": bool(risk_res["R_post"] > self.risk_module.r_max),
            "flow_mods": cost_res["flow_mods"],
            "switches_modified": cost_res["switches_modified"],
            "links_changed": cost_res["links_changed"],
            "ctrl_messages": cost_res["ctrl_messages"],
            "intervention_cost": cost_res["C_I"],
            "disruption_cost": cost_res["C_D"],
            "recovery_time_ms": float(recovery_time_ms),
            "decision_latency_ms": float(decision_latency_ms)
        }
