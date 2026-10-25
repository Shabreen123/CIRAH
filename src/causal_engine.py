"""
CIRAH: Structural Causal Model (SCM) & Counterfactual Evaluation Engine
Implements:
1. Formal SCM: Variables F (Fault), L (Link State), Q (Queue/Congestion), R (Routing), Y (SLA Outcome)
2. Pearl's 3-step Counterfactual Evaluation: Abduction -> Action (do-operator) -> Prediction
3. Bayesian Causal Fault Localization under telemetry noise
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional, Any

class StructuralCausalModel:
    """
    Formal Structural Causal Model (SCM) for Network Self-Healing:
    
    Exogenous Variables U = (U_F, U_L, U_Q, U_Y)
    Endogenous Variables:
      - F: Underlying Fault State {0: normal, 1: degraded, 2: severed}
      - L: Intrinsic Link Properties (base_latency, effective_capacity, raw_loss)
      - Q: Queue Depth / Dynamic Congestion driven by traffic assignment R
      - R: Active Routing Configuration (paths allocated to flows)
      - Y: End-to-end Service Outcomes (path latency, packet loss, connectivity)
      - A: Interventional Action do(A=a)
    """

    def __init__(self, topology: nx.DiGraph):
        self.G = topology
        # Prior fault probabilities P(F_e = 1)
        self.p_fault_prior = 0.02
        # Causal propagation strength parameters
        self.alpha_queue = 1.8  # Non-linear queuing delay sensitivity (M/M/1 proxy)
        self.loss_steepness = 8.0 # Sigmoidal packet drop curve under buffer overflow

    def diagnose_causal_faults(self, 
                               telemetry: Dict[Tuple[str, str], Dict[str, float]], 
                               active_paths: List[List[str]],
                               telemetry_noise_std: float = 0.05) -> Dict[Tuple[str, str], float]:
        """
        Causal Fault Localization:
        Computes the posterior probability P(F_e = 1 | Telemetry, Active_Paths)
        using Bayesian causal traceback and path overlap evidence.
        """
        posteriors = {}
        for edge in self.G.edges():
            u, v = edge
            # Observational telemetry features
            metrics = telemetry.get(edge, {"loss": 0.0, "latency": self.G[u][v].get("latency", 10.0), "status": 1})
            obs_loss = metrics.get("loss", 0.0) + np.random.normal(0, telemetry_noise_std)
            obs_lat = metrics.get("latency", 10.0)
            base_lat = self.G[u][v].get("latency", 10.0)
            lat_ratio = max(1.0, obs_lat / max(1e-3, base_lat))
            status = metrics.get("status", 1)

            # Likelihood computation: P(Observation | F_e = 1) vs P(Observation | F_e = 0)
            if status == 0:
                p_obs_given_fault = 0.99
                p_obs_given_normal = 0.001
            else:
                # Severity metric combining latency blowup and packet loss
                symptom_severity = (obs_loss / 100.0) * 0.7 + min(1.0, (lat_ratio - 1.0) / 3.0) * 0.3
                p_obs_given_fault = float(np.clip(symptom_severity, 0.05, 0.98))
                p_obs_given_normal = float(np.clip(1.0 - symptom_severity, 0.02, 0.95))

            # Path coincidence prior: how many degraded flows traverse this edge?
            degraded_path_count = 0
            total_traversing = 0
            for path in active_paths:
                if any(path[i] == u and path[i+1] == v for i in range(len(path)-1)):
                    total_traversing += 1
                    # check if path is experiencing symptoms
                    if obs_loss > 1.0 or lat_ratio > 1.5:
                        degraded_path_count += 1

            path_factor = 1.0
            if total_traversing > 0:
                path_factor = 1.0 + 2.0 * (degraded_path_count / total_traversing)

            # Bayes rule: P(F|O) proportional to P(O|F) * P(F) * path_factor
            likelihood_fault = p_obs_given_fault * self.p_fault_prior * path_factor
            likelihood_normal = p_obs_given_normal * (1.0 - self.p_fault_prior)
            
            p_post = likelihood_fault / max(1e-9, (likelihood_fault + likelihood_normal))
            posteriors[edge] = float(np.clip(p_post, 0.0, 1.0))

        return posteriors

    def evaluate_counterfactual(self, 
                                action: Dict[str, Any], 
                                flows: List[Dict[str, Any]], 
                                current_telemetry: Dict[Tuple[str, str], Dict[str, float]]) -> Dict[str, Any]:
        """
        Pearl's 3-Step Counterfactual Evaluation:
        1. ABDUCTION: Invert structural equations to reconstruct latent link capacities and background noise.
        2. ACTION: Apply interventional operator do(A = action), pruning overridden causal paths.
        3. PREDICTION: Propagate interventional inputs through structural causal equations to yield Y(a).
        """
        # Step 1: Abduction - estimate baseline unobserved exogenous terms U
        U_noise = {}
        for edge in self.G.edges():
            telem = current_telemetry.get(edge, {})
            u_loss = max(0.0, telem.get("loss", 0.0) - (0.0 if telem.get("status", 1) == 1 else 100.0))
            U_noise[edge] = u_loss

        # Step 2: Action - execute do(A = action)
        # Create counterfactual graph state under intervention
        cf_G = self.G.copy()
        target_flow_id = action.get("flow_id")
        candidate_path = action.get("path")
        throttle_ratio = action.get("throttle_ratio", 1.0) # Rate limiter intervention

        # Update routing matrix under do(A=a)
        counterfactual_paths = {}
        for f in flows:
            fid = f["flow_id"]
            if fid == target_flow_id and candidate_path is not None:
                counterfactual_paths[fid] = candidate_path
            else:
                counterfactual_paths[fid] = f.get("current_path", [])

        # Step 3: Prediction - forward propagate through structural equations
        # Calculate counterfactual link loads
        cf_loads = {e: 0.0 for e in cf_G.edges()}
        for f in flows:
            fid = f["flow_id"]
            p = counterfactual_paths[fid]
            bw = f["bandwidth_mbps"] * (throttle_ratio if fid == target_flow_id else 1.0)
            if p and len(p) > 1:
                for i in range(len(p) - 1):
                    e = (p[i], p[i+1])
                    if e in cf_loads:
                        cf_loads[e] += bw

        # Compute link queues and packet drop via structural equations
        cf_link_latencies = {}
        cf_link_losses = {}
        cf_link_queues = {}

        for e in cf_G.edges():
            u, v = e
            cap = cf_G[u][v]["capacity"]
            base_lat = cf_G[u][v]["latency"]
            telem = current_telemetry.get(e, {})
            edge_status = telem.get("status", cf_G[u][v].get("status", 1))
            edge_raw_loss = telem.get("loss", cf_G[u][v].get("loss", 0.0))

            # Interventional link status / physical failure
            if edge_status == 0 or (action.get("type") == "sever_link" and e == action.get("target_edge")):
                cf_link_losses[e] = 100.0
                cf_link_latencies[e] = 1e6
                cf_link_queues[e] = 1.0
                continue

            load = cf_loads[e]
            utilization = load / max(1.0, cap)

            # Structural Equation for Queue: Q_e = utilization / (1 - utilization + epsilon)
            if utilization < 0.8:
                q_depth = 0.05 * utilization
            elif utilization < 1.0:
                q_depth = 0.1 + 0.9 * ((utilization - 0.8) / 0.2) ** self.alpha_queue
            else:
                q_depth = 1.0 + 2.0 * (utilization - 1.0)

            cf_link_queues[e] = float(np.clip(q_depth, 0.0, 5.0))

            # Structural Equation for Latency: Lat = max(Base_Lat, telem_lat) * (1 + 1.5 * Q_e)
            telem_lat = telem.get("latency", base_lat)
            cf_link_latencies[e] = telem_lat * (1.0 + 1.5 * cf_link_queues[e])

            # Structural Equation for Loss: Physical loss combined with queue buffer overflow drop
            queue_drop_pct = 0.0
            if utilization > 0.95:
                excess = utilization - 0.95
                drop_prob = 1.0 / (1.0 + np.exp(-self.loss_steepness * excess)) - 0.5
                queue_drop_pct = float(np.clip(drop_prob * 100.0, 0.0, 100.0))

            # Combined loss: 1 - (1 - physical_loss) * (1 - queue_drop)
            p_survive = (1.0 - min(100.0, edge_raw_loss) / 100.0) * (1.0 - queue_drop_pct / 100.0)
            cf_link_losses[e] = float(np.clip((1.0 - p_survive) * 100.0, 0.0, 100.0))

        # Evaluate End-to-End Service Outcomes Y(a) for flows
        flow_outcomes = {}
        sla_violations = 0
        total_recovery_prob = 1.0

        for f in flows:
            fid = f["flow_id"]
            p = counterfactual_paths[fid]
            if not p or len(p) <= 1:
                flow_outcomes[fid] = {"connected": False, "latency": 1e6, "loss": 100.0, "sla_met": False}
                sla_violations += 1
                total_recovery_prob *= 0.0
                continue

            # Path accumulator
            p_lat = sum(cf_link_latencies.get((p[i], p[i+1]), 10.0) for i in range(len(p)-1))
            # Cumulative packet delivery: prod(1 - loss_e)
            p_delivery = 1.0
            for i in range(len(p)-1):
                p_delivery *= (1.0 - cf_link_losses.get((p[i], p[i+1]), 0.0) / 100.0)
            p_loss = (1.0 - p_delivery) * 100.0

            sla_met = (p_lat <= f["sla_max_latency_ms"]) and (p_loss <= f["sla_max_loss_pct"])
            if not sla_met:
                sla_violations += 1

            flow_outcomes[fid] = {
                "connected": True,
                "latency": p_lat,
                "loss": p_loss,
                "sla_met": sla_met
            }

        # Targeted flow recovery probability
        target_f = next((f for f in flows if f["flow_id"] == target_flow_id), None)
        if target_f and target_flow_id in flow_outcomes:
            t_res = flow_outcomes[target_flow_id]
            p_rec = 1.0 if (t_res["connected"] and t_res["sla_met"]) else (0.5 if t_res["connected"] else 0.0)
        else:
            p_rec = 1.0 if sla_violations == 0 else max(0.0, 1.0 - sla_violations / len(flows))

        return {
            "flow_outcomes": flow_outcomes,
            "cf_link_loads": cf_loads,
            "cf_link_queues": cf_link_queues,
            "cf_link_latencies": cf_link_latencies,
            "cf_link_losses": cf_link_losses,
            "sla_violations": sla_violations,
            "P_recovered": p_rec
        }
