"""
CIRAH: Risk-Constrained Minimum-Causal-Intervention Optimizer
Solves:
    min_{a in A} [ lambda_I * C_I(a) + lambda_D * C_D(a) + lambda_L * C_L(a) + beta * R_post(a) - gamma * Psi(a) ]
    s.t.
        R_post(a) <= R_max
        P(F_recovered | do(a)) >= tau
        Connectivity(a) == 1

Includes Safe Fallback Mechanism for zero-feasible edge cases.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

class RiskConstrainedOptimizer:
    """
    Solves the combinatorial action selection problem over candidate intervention space.
    """

    def __init__(self,
                 lambda_I: float = 1.0,   # Weight on direct intervention cost C_I
                 lambda_D: float = 0.5,   # Weight on transient disruption cost C_D
                 lambda_L: float = 0.2,   # Weight on latency degradation C_L
                 beta: float = 1.2,       # Weight on residual risk
                 gamma: float = 0.8,      # Weight on healing field aggregate benefit Psi(a)
                 tau: float = 0.75,       # Minimum recovery confidence
                 r_max: float = 35.0):    # Risk ceiling
        self.lambda_I = lambda_I
        self.lambda_D = lambda_D
        self.lambda_L = lambda_L
        self.beta = beta
        self.gamma = gamma
        self.tau = tau
        self.r_max = r_max

    def generate_candidate_interventions(self,
                                         topology: nx.DiGraph,
                                         target_flow: Dict[str, Any],
                                         causal_fault_posteriors: Dict[Tuple[str, str], float],
                                         k_paths: int = 5) -> List[Dict[str, Any]]:
        """
        Generates candidate interventions:
        1. Baseline null action a_0 (keep current path)
        2. K-shortest loop-free alternative paths avoiding high-probability causal fault edges
        3. Local bypass detours
        4. Ingress rate-throttling actions (alleviates queue congestion)
        """
        src = target_flow["src"]
        dst = target_flow["dst"]
        current_path = target_flow.get("current_path")
        candidates = []

        # Action 0: Null intervention (No change)
        candidates.append({
            "action_id": "act_null",
            "type": "no_change",
            "flow_id": target_flow["flow_id"],
            "path": current_path,
            "throttle_ratio": 1.0,
            "is_fallback": False
        })

        # Identify healthy edges: penalize edges with high causal fault probability
        H = topology.copy()
        for u, v in H.edges():
            p_fault = causal_fault_posteriors.get((u, v), 0.0)
            base_w = H[u][v].get("latency", 10.0)
            # Severe penalty if edge is causally diagnosed as faulty or severed
            if p_fault > 0.5 or H[u][v].get("status", 1) == 0:
                H[u][v]["opt_weight"] = base_w + 10000.0 * (p_fault + 1.0)
            else:
                H[u][v]["opt_weight"] = base_w * (1.0 + 2.0 * p_fault)

        # K-shortest simple paths under penalized weights
        try:
            path_generator = nx.shortest_simple_paths(H, src, dst, weight="opt_weight")
            found = 0
            for p in path_generator:
                if found >= k_paths:
                    break
                # Only include valid paths
                if len(p) >= 2:
                    candidates.append({
                        "action_id": f"act_path_{found+1}",
                        "type": "reroute",
                        "flow_id": target_flow["flow_id"],
                        "path": p,
                        "throttle_ratio": 1.0,
                        "is_fallback": False
                    })
                    found += 1
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Also add throttled variants for top paths to mitigate congestion
        if len(candidates) > 1:
            top_path = candidates[1]["path"]
            candidates.append({
                "action_id": "act_reroute_throttled",
                "type": "reroute_and_throttle",
                "flow_id": target_flow["flow_id"],
                "path": top_path,
                "throttle_ratio": 0.8,
                "is_fallback": False
            })

        return candidates

    def optimize(self,
                 candidates: List[Dict[str, Any]],
                 causal_engine: Any,
                 healing_propagator: Any,
                 risk_module: Any,
                 cost_model: Any,
                 all_flows: List[Dict[str, Any]],
                 current_telemetry: Dict[Tuple[str, str], Dict[str, float]],
                 target_flow: Dict[str, Any],
                 pre_node_stress: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes constrained combinatorial optimization over candidates.
        """
        evaluated_candidates = []
        feasible_candidates = []

        for cand in candidates:
            # 1. Pearl Counterfactual Evaluation
            cf_res = causal_engine.evaluate_counterfactual(cand, all_flows, current_telemetry)
            
            # 2. Risk Assessment
            risk_res = risk_module.evaluate_risk(causal_engine.G, cand, cf_res, target_flow)

            # 3. Intervention Cost Model
            cost_res = cost_model.compute_intervention_cost(
                old_path=target_flow.get("current_path"),
                new_path=cand.get("path"),
                flow_demand_mbps=target_flow["bandwidth_mbps"],
                is_reassigned=(cand["type"] != "no_change")
            )

            # 4. Healing Field Propagation
            # Post-stress approximation per node
            post_node_stress = {}
            for n in causal_engine.G.nodes():
                # sum incoming/outgoing link loss
                out_loss = sum(cf_res["cf_link_losses"].get((n, v), 0.0) for v in causal_engine.G.successors(n))
                post_node_stress[n] = float(out_loss)

            h_field = healing_propagator.construct_healing_field(cand, pre_node_stress, post_node_stress)
            psi = healing_propagator.compute_aggregate_healing_gain(h_field)

            # Latency SLA penalty
            t_out = cf_res["flow_outcomes"].get(target_flow["flow_id"], {})
            actual_lat = t_out.get("latency", 1e5)
            c_lat = max(0.0, actual_lat - target_flow["sla_max_latency_ms"])

            # Compute Objective Score: J(a)
            # J(a) = lambda_I * C_I + lambda_D * C_D + lambda_L * C_L + beta * R_post - gamma * Psi
            j_score = (self.lambda_I * cost_res["C_I"] +
                       self.lambda_D * cost_res["C_D"] +
                       self.lambda_L * c_lat +
                       self.beta * risk_res["R_post"] -
                       self.gamma * psi)

            cand_record = {
                "action": cand,
                "cf_res": cf_res,
                "risk_res": risk_res,
                "cost_res": cost_res,
                "psi": psi,
                "j_score": j_score,
                "P_recovered": cf_res["P_recovered"],
                "R_post": risk_res["R_post"],
                "is_connected": t_out.get("connected", False)
            }
            evaluated_candidates.append(cand_record)

            # Hard Constraint Verification:
            # 1. R_post <= R_max
            # 2. P_recovered >= tau
            # 3. is_connected == True
            if (risk_res["R_post"] <= self.r_max and 
                cf_res["P_recovered"] >= self.tau and 
                t_out.get("connected", False)):
                feasible_candidates.append(cand_record)

        # Action Selection
        if feasible_candidates:
            # Select action that minimizes objective J(a)
            best = min(feasible_candidates, key=lambda x: x["j_score"])
            return {
                "selected_action": best["action"],
                "best_record": best,
                "all_evaluated": evaluated_candidates,
                "fallback_triggered": False,
                "status": "OPTIMAL_FEASIBLE"
            }
        else:
            # Trigger Safe Fallback Mechanism (Section 5.6)
            fallback_rec = self._execute_safe_fallback(
                candidates, evaluated_candidates, causal_engine, target_flow
            )
            return {
                "selected_action": fallback_rec["action"],
                "best_record": fallback_rec,
                "all_evaluated": evaluated_candidates,
                "fallback_triggered": True,
                "status": "SAFE_FALLBACK"
            }

    def _execute_safe_fallback(self, 
                               candidates: List[Dict[str, Any]], 
                               evaluated: List[Dict[str, Any]],
                               causal_engine: Any,
                               target_flow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes bounded graceful degradation:
        Finds the action that maximizes connectivity and minimizes post risk,
        even if exceeding R_max or falling below tau.
        """
        connected_cands = [r for r in evaluated if r["is_connected"]]
        if connected_cands:
            # Select lowest risk amongst connected candidates
            best_connected = min(connected_cands, key=lambda x: x["R_post"])
            best_connected["action"]["is_fallback"] = True
            return best_connected
        
        # Absolute emergency: keep null action with 50% rate limiting
        null_action = candidates[0]
        null_action["throttle_ratio"] = 0.5
        null_action["is_fallback"] = True
        return evaluated[0]
