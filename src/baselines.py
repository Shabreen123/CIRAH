"""
CIRAH: Baseline Recovery Algorithms and Ablation Models
Implements:
1. Static-SP: Static Shortest Path (non-adaptive)
2. Dynamic-SP: Conventional Reactive Shortest Path Rerouting
3. Backup-Path: Precomputed disjoint protection path (Fast Reroute / MPLS style)
4. Risk-SP: Multi-metric Risk-Aware Dijkstra (without intervention minimization)
5. MinChange-SP: Pure minimum-change heuristic (minimizing switch modifications blindly)
6. CIRAH-noCausal: CIRAH ablation using heuristic correlation-rule diagnosis
7. CIRAH-noRisk: CIRAH ablation without explicit risk constraints
8. CIRAH-noInterv: CIRAH ablation without intervention cost penalty (lambda_I = 0)
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class BaselineController:
    """Base class for recovery algorithms."""
    def __init__(self, name: str):
        self.name = name

    def compute_recovery_action(self, 
                                topology: nx.DiGraph, 
                                flows: List[Dict[str, Any]], 
                                telemetry: Dict[Tuple[str, str], Dict[str, float]], 
                                target_flow: Dict[str, Any],
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError

class StaticSP(BaselineController):
    """Static Shortest Path: never re-routes; retains initial path."""
    def __init__(self):
        super().__init__("Static-SP")

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        return {
            "method": self.name,
            "action_id": "act_static",
            "type": "no_change",
            "flow_id": target_flow["flow_id"],
            "path": target_flow.get("current_path"),
            "throttle_ratio": 1.0,
            "is_fallback": False
        }

class DynamicSP(BaselineController):
    """Dynamic Shortest Path: recomputes standard Dijkstra shortest path over active links."""
    def __init__(self):
        super().__init__("Dynamic-SP")

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        src = target_flow["src"]
        dst = target_flow["dst"]
        
        # Build graph of currently active links
        H = nx.DiGraph()
        for u, v in topology.edges():
            telem = telemetry.get((u, v), {})
            if telem.get("status", 1) == 1 and telem.get("loss", 0.0) < 95.0:
                lat = telem.get("latency", topology[u][v].get("latency", 10.0))
                H.add_edge(u, v, weight=lat)

        try:
            new_path = nx.shortest_path(H, src, dst, weight="weight")
            act_type = "reroute" if new_path != target_flow.get("current_path") else "no_change"
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            new_path = target_flow.get("current_path")
            act_type = "failed"

        return {
            "method": self.name,
            "action_id": "act_dynamic_sp",
            "type": act_type,
            "flow_id": target_flow["flow_id"],
            "path": new_path,
            "throttle_ratio": 1.0,
            "is_fallback": False
        }

class BackupPathRecovery(BaselineController):
    """Precomputed Backup Path: switches immediately to an edge-disjoint secondary path."""
    def __init__(self, base_topology: nx.DiGraph):
        super().__init__("Backup-Path")
        self.backup_paths = {}
        # Precompute disjoint backup paths
        for u in base_topology.nodes():
            for v in base_topology.nodes():
                if u != v:
                    try:
                        p1 = nx.shortest_path(base_topology, u, v, weight="latency")
                        # Remove interior edges to find disjoint path
                        H = base_topology.copy()
                        for i in range(len(p1)-1):
                            if H.has_edge(p1[i], p1[i+1]):
                                H.remove_edge(p1[i], p1[i+1])
                        try:
                            p2 = nx.shortest_path(H, u, v, weight="latency")
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            p2 = p1
                        self.backup_paths[(u, v)] = (p1, p2)
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        self.backup_paths[(u, v)] = (None, None)

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        src = target_flow["src"]
        dst = target_flow["dst"]
        current = target_flow.get("current_path")
        p1, p2 = self.backup_paths.get((src, dst), (None, None))

        # Check if current path has a severed link
        has_failure = False
        if current and len(current) > 1:
            for i in range(len(current)-1):
                telem = telemetry.get((current[i], current[i+1]), {})
                if telem.get("status", 1) == 0 or telem.get("loss", 0.0) > 80.0:
                    has_failure = True
                    break

        if has_failure and p2 is not None and p2 != current:
            new_path = p2
            act_type = "reroute_backup"
        else:
            new_path = current
            act_type = "no_change"

        return {
            "method": self.name,
            "action_id": "act_backup_path",
            "type": act_type,
            "flow_id": target_flow["flow_id"],
            "path": new_path,
            "throttle_ratio": 1.0,
            "is_fallback": False
        }

class RiskAwareRouting(BaselineController):
    """Risk-Aware Multi-Metric Dijkstra: selects path minimizing risk + latency, ignoring change footprint."""
    def __init__(self):
        super().__init__("Risk-Aware")

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        src = target_flow["src"]
        dst = target_flow["dst"]
        H = nx.DiGraph()

        for u, v in topology.edges():
            telem = telemetry.get((u, v), {})
            if telem.get("status", 1) == 1:
                lat = telem.get("latency", 10.0)
                loss = telem.get("loss", 0.0)
                # Risk weight: latency + exponential loss penalty
                w = lat * (1.0 + 0.1 * loss) + 50.0 * (loss / 100.0) ** 2
                H.add_edge(u, v, weight=w)

        try:
            new_path = nx.shortest_path(H, src, dst, weight="weight")
            act_type = "reroute_risk" if new_path != target_flow.get("current_path") else "no_change"
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            new_path = target_flow.get("current_path")
            act_type = "failed"

        return {
            "method": self.name,
            "action_id": "act_risk_aware",
            "type": act_type,
            "flow_id": target_flow["flow_id"],
            "path": new_path,
            "throttle_ratio": 1.0,
            "is_fallback": False
        }

class MinChangeHeuristic(BaselineController):
    """Minimum-Change Heuristic: prefers candidate paths sharing maximum edges with current path."""
    def __init__(self):
        super().__init__("MinChange-SP")

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        src = target_flow["src"]
        dst = target_flow["dst"]
        current = target_flow.get("current_path")
        current_edges = set((current[i], current[i+1]) for i in range(len(current)-1)) if current else set()

        # Build feasible candidate paths
        H = nx.DiGraph()
        for u, v in topology.edges():
            telem = telemetry.get((u, v), {})
            if telem.get("status", 1) == 1 and telem.get("loss", 0.0) < 50.0:
                H.add_edge(u, v, weight=topology[u][v].get("latency", 10.0))

        try:
            candidates = list(nx.all_simple_paths(H, src, dst, cutoff=7))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            candidates = []

        if not candidates:
            return {
                "method": self.name,
                "action_id": "act_minchange_fail",
                "type": "failed",
                "flow_id": target_flow["flow_id"],
                "path": current,
                "throttle_ratio": 1.0,
                "is_fallback": False
            }

        # Score candidate paths: minimize symmetric difference of edges + mild latency penalty
        best_path = None
        best_cost = 1e9

        for p in candidates:
            p_edges = set((p[i], p[i+1]) for i in range(len(p)-1))
            diff_edges = len(current_edges.symmetric_difference(p_edges))
            lat = sum(topology[p[i]][p[i+1]].get("latency", 10.0) for i in range(len(p)-1))
            score = diff_edges * 10.0 + lat * 0.1
            if score < best_cost:
                best_cost = score
                best_path = p

        act_type = "reroute_minchange" if best_path != current else "no_change"
        return {
            "method": self.name,
            "action_id": "act_minchange",
            "type": act_type,
            "flow_id": target_flow["flow_id"],
            "path": best_path,
            "throttle_ratio": 1.0,
            "is_fallback": False
        }


class ConstrainedMinChangeOptimizer(BaselineController):
    """
    Constrained Minimum-Change Optimizer: Minimizes switch modifications
    subject to a hard post-recovery risk ceiling R_post <= R_max.

    This baseline receives the same candidate paths and risk information as CIRAH
    but does NOT use Bayesian fault diagnosis, counterfactual evaluation, or
    the healing field. It uses the same RiskAssessmentModule for feasibility
    checking but selects purely by minimum change count.

    Purpose: Isolate the contribution of CIRAH's causal and counterfactual
    components from the effect of having a risk constraint at all.
    """

    def __init__(self, base_topology: nx.DiGraph, r_max: float = 35.0):
        super().__init__("Constrained-MinChange")
        self.base_topology = base_topology
        self.r_max = r_max

    def compute_recovery_action(self, topology, flows, telemetry, target_flow, context=None):
        src = target_flow["src"]
        dst = target_flow["dst"]
        current = target_flow.get("current_path")
        current_edges = set((current[i], current[i+1]) for i in range(len(current)-1)) if current else set()

        # Build feasible candidate paths (same as MinChangeHeuristic)
        H = nx.DiGraph()
        for u, v in topology.edges():
            telem = telemetry.get((u, v), {})
            if telem.get("status", 1) == 1 and telem.get("loss", 0.0) < 50.0:
                H.add_edge(u, v, weight=topology[u][v].get("latency", 10.0))

        try:
            candidates = list(nx.all_simple_paths(H, src, dst, cutoff=7))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            candidates = []

        if not candidates:
            return {
                "method": self.name,
                "action_id": "act_cmc_fail",
                "type": "failed",
                "flow_id": target_flow["flow_id"],
                "path": current,
                "throttle_ratio": 1.0,
                "is_fallback": False
            }

        # Evaluate risk for each candidate using simple (non-counterfactual) loads
        from src.risk_assessment import RiskAssessmentModule
        risk_module = RiskAssessmentModule(r_max_default=self.r_max)

        # Build a simple counterfactual result using current telemetry (myopic)
        feasible = []
        for p in candidates:
            # Simple myopic load estimate: use current telemetry loads
            cf_loads = {}
            for e in topology.edges():
                cf_loads[e] = telemetry.get(e, {}).get("load", 15.0)
            # Add target flow demand to new path
            bw = target_flow["bandwidth_mbps"]
            for i in range(len(p) - 1):
                e = (p[i], p[i+1])
                if e in cf_loads:
                    cf_loads[e] += bw

            # Simple loss estimate: use current losses
            cf_losses = {}
            for e in topology.edges():
                cf_losses[e] = telemetry.get(e, {}).get("loss", 0.0)

            # Simple latency estimate
            cf_latencies = {}
            for e in topology.edges():
                cf_latencies[e] = telemetry.get(e, {}).get("latency", topology[e[0]][e[1]].get("latency", 10.0))

            # Check target flow connectivity
            path_severed = any(
                cf_losses.get((p[i], p[i+1]), 0.0) >= 99.0
                for i in range(len(p) - 1)
            )

            if path_severed:
                continue

            # Compute flow outcomes
            p_lat = sum(cf_latencies.get((p[i], p[i+1]), 10.0) for i in range(len(p) - 1))
            p_deliv = 1.0
            for i in range(len(p) - 1):
                p_deliv *= (1.0 - cf_losses.get((p[i], p[i+1]), 0.0) / 100.0)
            p_loss = (1.0 - p_deliv) * 100.0

            sla_met = (p_lat <= target_flow["sla_max_latency_ms"]) and (p_loss <= target_flow["sla_max_loss_pct"])

            cf_result = {
                "flow_outcomes": {
                    target_flow["flow_id"]: {
                        "connected": True,
                        "latency": p_lat,
                        "loss": p_loss,
                        "sla_met": sla_met
                    }
                },
                "cf_link_loads": cf_loads,
                "cf_link_losses": cf_losses,
                "cf_link_latencies": cf_latencies,
                "cf_link_queues": {e: cf_loads[e] / max(1.0, topology[e[0]][e[1]].get("capacity", 100.0)) for e in topology.edges()},
                "sla_violations": 0 if sla_met else 1,
                "P_recovered": 1.0 if sla_met else 0.4
            }

            action = {
                "action_id": f"act_cmc_{len(feasible)}",
                "type": "reroute" if p != current else "no_change",
                "flow_id": target_flow["flow_id"],
                "path": p,
                "throttle_ratio": 1.0,
                "is_fallback": False
            }

            risk_res = risk_module.evaluate_risk(topology, action, cf_result, target_flow)

            if risk_res["R_post"] <= self.r_max and risk_res["P_disconnect"] == 0.0:
                diff = len(current_edges.symmetric_difference(
                    set((p[i], p[i+1]) for i in range(len(p) - 1))
                ))
                feasible.append((diff, p, risk_res["R_post"]))

        if feasible:
            # Select minimum change among feasible
            feasible.sort(key=lambda x: (x[0], x[2]))
            best_path = feasible[0][1]
            act_type = "reroute_cmc" if best_path != current else "no_change"
            return {
                "method": self.name,
                "action_id": "act_cmc",
                "type": act_type,
                "flow_id": target_flow["flow_id"],
                "path": best_path,
                "throttle_ratio": 1.0,
                "is_fallback": False
            }
        else:
            # Fallback: lowest-risk connected candidate
            connected = [p for p in candidates if not any(
                telemetry.get((p[i], p[i+1]), {}).get("loss", 0.0) >= 99.0
                for i in range(len(p) - 1)
            )]
            if connected:
                return {
                    "method": self.name,
                    "action_id": "act_cmc_fallback",
                    "type": "reroute_cmc_fallback",
                    "flow_id": target_flow["flow_id"],
                    "path": connected[0],
                    "throttle_ratio": 0.75,
                    "is_fallback": True
                }
            return {
                "method": self.name,
                "action_id": "act_cmc_fail",
                "type": "failed",
                "flow_id": target_flow["flow_id"],
                "path": current,
                "throttle_ratio": 1.0,
                "is_fallback": False
            }
