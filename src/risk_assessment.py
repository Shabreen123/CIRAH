"""
CIRAH: Risk Assessment Module
Formulates explicit network risk quantification:
    R(a) = sum_{k=1}^M P(E_k | do(a)) * Impact(E_k)

Decomposes risk into:
1. Operational Risk R_op(a): Immediate service impairment (packet drops, latency blowup, reconfiguration failure)
2. Propagation Risk R_prop(a): Cascading congestion on adjacent un-intervened links
3. Global Risk Ceiling Verification: R_post(a) <= R_max
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Tuple

class RiskAssessmentModule:
    """
    Evaluates multi-hazard risk distributions under candidate recovery actions.
    """

    def __init__(self,
                 impact_disconnect: float = 100.0,
                 impact_congestion_spillover: float = 40.0,
                 impact_sla_violation: float = 25.0,
                 impact_route_flap: float = 15.0,
                 r_max_default: float = 35.0):
        self.impact_disconnect = impact_disconnect
        self.impact_congestion_spillover = impact_congestion_spillover
        self.impact_sla_violation = impact_sla_violation
        self.impact_route_flap = impact_route_flap
        self.r_max = r_max_default

    def evaluate_risk(self, 
                      topology: nx.DiGraph, 
                      action: Dict[str, Any], 
                      counterfactual_result: Dict[str, Any],
                      target_flow: Dict[str, Any]) -> Dict[str, float]:
        """
        Quantifies operational, propagation, and composite residual risk.
        """
        cf_loads = counterfactual_result["cf_link_loads"]
        cf_losses = counterfactual_result["cf_link_losses"]
        flow_outcomes = counterfactual_result["flow_outcomes"]
        target_id = target_flow["flow_id"]

        # --- 1. Operational Risk Events ---
        # Event E1: Disconnection / Path Unreachability
        target_res = flow_outcomes.get(target_id, {"connected": False})
        p_disconnect = 0.0 if target_res["connected"] else 1.0
        r_disconnect = p_disconnect * self.impact_disconnect

        # Event E2: SLA Delay/Loss Violation on Target Flow
        p_sla_violation = 0.0
        if target_res["connected"]:
            lat_excess = max(0.0, target_res["latency"] - target_flow["sla_max_latency_ms"])
            loss_excess = max(0.0, target_res["loss"] - target_flow["sla_max_loss_pct"])
            if lat_excess > 0 or loss_excess > 0:
                p_sla_violation = min(1.0, 0.4 + 0.6 * (lat_excess / max(1.0, target_flow["sla_max_latency_ms"]) + loss_excess / 10.0))
        r_sla = p_sla_violation * self.impact_sla_violation

        # Event E3: Route Flapping / Execution Transient Failure
        # Scales with path length and switch churn
        path = action.get("path", [])
        p_reconfig_fail = min(0.3, 0.02 * len(path))
        r_reconfig = p_reconfig_fail * self.impact_route_flap

        r_op = r_disconnect + r_sla + r_reconfig

        # --- 2. Propagation Risk Events (Secondary Cascade) ---
        # Event E4: Cascading Congestion Spillover on Non-Intervened Links
        cascade_risk_accum = 0.0
        congested_link_count = 0
        
        for e in topology.edges():
            u, v = e
            cap = topology[u][v]["capacity"]
            load = cf_loads.get(e, 0.0)
            utilization = load / max(1.0, cap)

            # If utilization exceeds 85%, probability of spillover grows exponentially
            if utilization > 0.85:
                excess_ratio = (utilization - 0.85) / 0.15
                p_cascade = float(np.clip(1.0 - np.exp(-1.8 * excess_ratio), 0.0, 1.0))
                cascade_risk_accum += p_cascade * (self.impact_congestion_spillover * min(2.0, utilization))
                congested_link_count += 1

        r_prop = cascade_risk_accum

        # --- 3. Composite Risk ---
        # Global risk is convex combination: R_post = R_op + R_prop
        r_post = float(r_op + r_prop)
        is_feasible = (r_post <= self.r_max) and (p_disconnect == 0.0)

        return {
            "R_op": float(r_op),
            "R_prop": float(r_prop),
            "R_post": float(r_post),
            "P_disconnect": float(p_disconnect),
            "P_sla_violation": float(p_sla_violation),
            "congested_links": float(congested_link_count),
            "is_risk_feasible": bool(is_feasible),
            "R_max": float(self.r_max)
        }
