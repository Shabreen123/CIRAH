"""
CIRAH: Risk-Constrained Minimum-Causal-Intervention Optimizer
Updated per Faculty Revision 2 requirements:
1. Normalized, scale-free objective function with formally defined reference budgets:
     min_{a in A_feas} [ lambda_I * (C_I / C_I_ref) + lambda_D * (C_D / C_D_ref) + 
                         lambda_L * (C_L / C_L_ref) + beta * (R_post / R_max) - gamma * (Psi / Psi_ref) ]
2. Formal chance/robust constraint with uncertainty buffer:
     R_post(a) + z_alpha * sigma_R(a) <= R_max
3. Hard constraint admission filter strictly separated from soft risk steering penalty.
4. Physical network partition detection (avoids false recovery claims during topological cuts).
5. Exact oracle enumeration benchmark on small networks to quantify the optimality gap.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

class RiskConstrainedOptimizer:
    """
    Combinatorial optimizer over candidate recovery interventions.
    """

    def __init__(self,
                 lambda_I: float = 1.0,   # Weight on normalized control-plane intervention cost
                 lambda_D: float = 0.5,   # Weight on normalized transient disruption cost
                 lambda_L: float = 0.3,   # Weight on normalized latency SLA degradation
                 beta: float = 1.2,       # Weight on normalized residual risk
                 gamma: float = 0.8,      # Weight on normalized aggregate healing gain Psi
                 tau: float = 0.75,       # Minimum recovery confidence
                 r_max: float = 35.0,     # Hard risk ceiling
                 z_alpha: float = 1.645,  # 95% one-sided Gaussian confidence quantile
                 cihf_mode: str = "cihf"  # "cihf", "none" (ablation), "centrality", "local_only"
                 ):
        self.lambda_I = lambda_I
        self.lambda_D = lambda_D
        self.lambda_L = lambda_L
        self.beta = beta
        self.gamma = gamma
        self.tau = tau
        self.r_max = r_max
        self.z_alpha = z_alpha
        self.cihf_mode = cihf_mode

        # Reference scale normalizers (derived from network capacity and SLA limits)
        self.c_i_ref = 30.0   # Reference maximum FLOW_MOD + switch modification score
        self.c_d_ref = 50.0   # Reference maximum transient disruption penalty
        self.c_l_ref = 40.0   # Reference maximum latency excess penalty (ms)
        self.psi_ref = 10.0   # Reference aggregate healing potential

    def generate_candidate_interventions(self,
                                         topology: nx.DiGraph,
                                         target_flow: Dict[str, Any],
                                         causal_fault_posteriors: Dict[Tuple[str, str], Dict[str, float]],
                                         k_paths: int = 6) -> List[Dict[str, Any]]:
        """
        Generates candidate interventions:
        1. Null action a_0 (keep current path)
        2. K-shortest loop-free alternative paths avoiding high-probability causal fault edges
        3. Paced / rate-throttled variants to alleviate congestive bottlenecks
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

        # Weight penalization based on Bayesian fault probability
        H = topology.copy()
        for u, v in H.edges():
            fault_info = causal_fault_posteriors.get((u, v), {"P_fault": 0.0, "P_severed": 0.0})
            p_fault = fault_info.get("P_fault", 0.0)
            p_sev = fault_info.get("P_severed", 0.0)
            base_w = H[u][v].get("latency", 10.0)

            if p_sev > 0.8 or H[u][v].get("status", 1) == 0:
                # Completely severed link: assign near-infinite penalty
                H[u][v]["opt_weight"] = 1e6
            else:
                # Degraded / risky link: penalty scales with posterior fault probability
                H[u][v]["opt_weight"] = base_w * (1.0 + 5.0 * p_fault)

        # K-shortest loop-free simple paths
        try:
            path_generator = nx.shortest_simple_paths(H, src, dst, weight="opt_weight")
            found = 0
            for p in path_generator:
                if found >= k_paths:
                    break
                # Verify that path does not traverse an infinite weight severed link
                path_has_cut = any(H[p[i]][p[i+1]]["opt_weight"] >= 1e5 for i in range(len(p)-1))
                if path_has_cut:
                    continue

                candidates.append({
                    "action_id": f"act_path_{found+1}",
                    "type": "reroute",
                    "flow_id": target_flow["flow_id"],
                    "path": p,
                    "throttle_ratio": 1.0,
                    "is_fallback": False
                })
                # Add a throttled alternative for high-load mitigation
                candidates.append({
                    "action_id": f"act_path_{found+1}_paced",
                    "type": "reroute_paced",
                    "flow_id": target_flow["flow_id"],
                    "path": p,
                    "throttle_ratio": 0.85,
                    "is_fallback": False
                })
                found += 1
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

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
                 pre_node_stress: Dict[str, float],
                 is_myopic: bool = False,
                 is_causal: bool = True,
                 enforce_risk_constraint: bool = True) -> Dict[str, Any]:
        """
        Executes normalized constrained optimization over candidate action set.
        """
        evaluated_candidates = []
        feasible_candidates = []

        for cand in candidates:
            # 1. Counterfactual Outcome Evaluation (SCM or Myopic)
            cf_res = causal_engine.evaluate_counterfactual(
                cand, all_flows, current_telemetry, is_myopic=is_myopic
            )
            
            # 2. Risk Assessment
            risk_res = risk_module.evaluate_risk(causal_engine.G, cand, cf_res, target_flow)

            # 3. Control-Plane Intervention Cost
            cost_res = cost_model.compute_intervention_cost(
                old_path=target_flow.get("current_path"),
                new_path=cand.get("path"),
                flow_demand_mbps=target_flow["bandwidth_mbps"],
                is_reassigned=(cand["type"] != "no_change")
            )

            # 4. CIHF Healing Field Propagation
            post_node_stress = {}
            for n in causal_engine.G.nodes():
                out_loss = sum(cf_res["cf_link_losses"].get((n, v), 0.0) for v in causal_engine.G.successors(n))
                post_node_stress[n] = float(out_loss)

            h_field = healing_propagator.construct_healing_field(
                cand, pre_node_stress, post_node_stress, scoring_mode=self.cihf_mode
            )
            psi = healing_propagator.compute_aggregate_healing_gain(h_field)

            # Target flow latency penalty: normalized path latency + SLA excess penalty
            t_out = cf_res["flow_outcomes"].get(target_flow["flow_id"], {})
            actual_lat = t_out.get("latency", 1e5)
            sla_lat = max(1.0, target_flow["sla_max_latency_ms"])
            norm_c_l = float((actual_lat / sla_lat) + (max(0.0, actual_lat - sla_lat) / self.c_l_ref))

            # Robust Risk Bound with Uncertainty Buffer: R_robust = R_post + z_alpha * sigma_R
            sigma_r = 0.08 * risk_res["R_post"] # 8% estimation uncertainty
            r_robust = risk_res["R_post"] + (self.z_alpha * sigma_r if enforce_risk_constraint else 0.0)

            # Normalized Objective Function J(a)
            norm_c_i = cost_res["C_I"] / self.c_i_ref
            norm_c_d = cost_res["C_D"] / self.c_d_ref
            if not is_causal:
                # CIRAH-noCausal ablation: lacks SCM Bayesian traceback, evaluating risk purely via naive telemetry loss
                cand_p = cand.get("path", [])
                corr_penalty = 0.0
                if cand_p and len(cand_p) > 1:
                    for i in range(len(cand_p)-1):
                        e = (cand_p[i], cand_p[i+1])
                        t_loss = current_telemetry.get(e, {}).get("loss", 0.0)
                        corr_penalty += t_loss * 2.5
                norm_r = (risk_res["R_post"] + corr_penalty) / self.r_max
            else:
                norm_r = risk_res["R_post"] / self.r_max
            norm_psi = psi / self.psi_ref

            j_score = (self.lambda_I * norm_c_i +
                       self.lambda_D * norm_c_d +
                       self.lambda_L * norm_c_l +
                       self.beta * norm_r -
                       self.gamma * norm_psi)

            is_connected = t_out.get("connected", False)
            sla_met = t_out.get("sla_met", False)

            # Risk Constraint Check: R_robust <= R_max (or R_post <= R_max if unconstrained)
            violates_risk = bool((r_robust > self.r_max) if enforce_risk_constraint else (risk_res["R_post"] > self.r_max))

            cand_record = {
                "action": cand,
                "cf_res": cf_res,
                "risk_res": risk_res,
                "cost_res": cost_res,
                "psi": psi,
                "j_score": j_score,
                "P_recovered": cf_res["P_recovered"],
                "R_post": risk_res["R_post"],
                "R_robust": r_robust,
                "is_connected": is_connected,
                "sla_met": sla_met,
                "violates_risk": violates_risk
            }
            evaluated_candidates.append(cand_record)

            # Strict Feasibility Filtering (unless enforce_risk_constraint is False in CIRAH-noRisk)
            if enforce_risk_constraint:
                if (r_robust <= self.r_max and 
                    cf_res["P_recovered"] >= self.tau and 
                    is_connected):
                    feasible_candidates.append(cand_record)
            else:
                # CIRAH-noRisk ablation: ignores risk bounds completely
                if is_connected:
                    feasible_candidates.append(cand_record)

        # Action Selection
        if feasible_candidates:
            best = min(feasible_candidates, key=lambda x: x["j_score"])
            return {
                "selected_action": best["action"],
                "best_record": best,
                "all_evaluated": evaluated_candidates,
                "fallback_triggered": False,
                "status": "OPTIMAL_FEASIBLE",
                "partition_detected": False
            }
        else:
            # Trigger Safe Fallback Mechanism
            fallback_rec, is_partition = self._execute_safe_fallback(
                candidates, evaluated_candidates, causal_engine, target_flow
            )
            return {
                "selected_action": fallback_rec["action"],
                "best_record": fallback_rec,
                "all_evaluated": evaluated_candidates,
                "fallback_triggered": True,
                "status": "SAFE_FALLBACK" if not is_partition else "PARTITION_UNAVAILABLE",
                "partition_detected": is_partition
            }

    def _execute_safe_fallback(self, 
                               candidates: List[Dict[str, Any]], 
                               evaluated: List[Dict[str, Any]],
                               causal_engine: Any,
                               target_flow: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Genuinely Safe Fallback Execution:
        1. Checks if topological network partition exists between src and dst.
        2. If partitioned: does NOT falsely claim recovery. Sets partition_detected=True,
           declares service unavailable, and throttles ingress traffic by 50% to prevent
           cascading buffer bloat across surviving core links.
        3. If connected path exists but violates R_max: selects the lowest-risk connected
           candidate with 25% ingress rate limiting to bound secondary degradation.
        """
        src, dst = target_flow["src"], target_flow["dst"]
        
        # Check graph reachability on non-severed physical links
        active_graph = nx.DiGraph()
        for u, v in causal_engine.G.edges():
            if causal_engine.G[u][v].get("status", 1) == 1:
                active_graph.add_edge(u, v)

        if not active_graph.has_node(src) or not active_graph.has_node(dst) or not nx.has_path(active_graph, src, dst):
            # Physical Network Partition Detected
            null_cand = evaluated[0]
            null_cand["action"]["throttle_ratio"] = 0.50 # Bounded ingress throttling
            null_cand["action"]["is_fallback"] = True
            null_cand["is_connected"] = False
            null_cand["sla_met"] = False
            return null_cand, True

        # Non-partitioned fallback: Pick candidate that minimizes residual risk
        connected_cands = [r for r in evaluated if r["is_connected"]]
        if connected_cands:
            best_connected = min(connected_cands, key=lambda x: x["R_post"])
            best_connected["action"]["throttle_ratio"] = 0.75 # Paced detour
            best_connected["action"]["is_fallback"] = True
            return best_connected, False

        # Worst-case emergency fallback
        fallback = evaluated[0]
        fallback["action"]["throttle_ratio"] = 0.50
        fallback["action"]["is_fallback"] = True
        return fallback, False
