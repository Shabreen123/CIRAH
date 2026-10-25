"""
CIRAH: Network Fault Injection and Scenario Generator
Implements diverse, realistic failure and degradation modes:
1. Single-Link Failure
2. Multiple Simultaneous Link Failures (k in [1, 2, 3, 4])
3. Switch / Node Failure
4. Link Capacity Degradation (Brownout)
5. Delay and Loss Spikes (Bufferbloat)
6. Bursty Traffic Congestion (Flash crowd)
7. Telemetry Uncertainty / Observation Noise
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class FaultGenerator:
    """
    Injects reproducible, realistic operational faults into network topologies.
    """

    def __init__(self, rng_seed: int = 42):
        self.rng = np.random.default_rng(rng_seed)

    def set_seed(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def inject_single_link_failure(self, G: nx.DiGraph, target_edge: Optional[Tuple[str, str]] = None) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Sever a single link (both directions)."""
        G_fault = G.copy()
        edges = list(G.edges())
        if target_edge is None:
            # Pick a link that does not immediately disconnect the entire graph if possible
            idx = self.rng.integers(0, len(edges))
            target_edge = edges[idx]

        u, v = target_edge
        # Sever forward and reverse links
        if G_fault.has_edge(u, v):
            G_fault[u][v]["status"] = 0
            G_fault[u][v]["loss"] = 100.0
            G_fault[u][v]["latency"] = 1e6
        if G_fault.has_edge(v, u):
            G_fault[v][u]["status"] = 0
            G_fault[v][u]["loss"] = 100.0
            G_fault[v][u]["latency"] = 1e6

        meta = {
            "type": "single_link_failure",
            "failed_links": [(u, v), (v, u)],
            "failed_nodes": []
        }
        return G_fault, meta

    def inject_multi_link_failure(self, G: nx.DiGraph, k: int = 2) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Simultaneously sever k distinct bi-directional links."""
        G_fault = G.copy()
        # Get unique undirected edge pairs
        unique_edges = []
        seen = set()
        for u, v in G.edges():
            pair = tuple(sorted([u, v]))
            if pair not in seen:
                seen.add(pair)
                unique_edges.append((u, v))

        k_actual = min(k, len(unique_edges))
        chosen_indices = self.rng.choice(len(unique_edges), size=k_actual, replace=False)
        failed_links = []

        for idx in chosen_indices:
            u, v = unique_edges[idx]
            if G_fault.has_edge(u, v):
                G_fault[u][v]["status"] = 0
                G_fault[u][v]["loss"] = 100.0
                G_fault[u][v]["latency"] = 1e6
                failed_links.append((u, v))
            if G_fault.has_edge(v, u):
                G_fault[v][u]["status"] = 0
                G_fault[v][u]["loss"] = 100.0
                G_fault[v][u]["latency"] = 1e6
                failed_links.append((v, u))

        meta = {
            "type": "multi_link_failure",
            "k": k_actual,
            "failed_links": failed_links,
            "failed_nodes": []
        }
        return G_fault, meta

    def inject_switch_failure(self, G: nx.DiGraph, target_node: Optional[str] = None) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Fails a switch, severing all adjacent incident links."""
        G_fault = G.copy()
        nodes = list(G.nodes())
        if target_node is None:
            target_node = str(self.rng.choice(nodes))

        failed_links = []
        for v in list(G_fault.successors(target_node)):
            G_fault[target_node][v]["status"] = 0
            G_fault[target_node][v]["loss"] = 100.0
            G_fault[target_node][v]["latency"] = 1e6
            failed_links.append((target_node, v))
        for u in list(G_fault.predecessors(target_node)):
            G_fault[u][target_node]["status"] = 0
            G_fault[u][target_node]["loss"] = 100.0
            G_fault[u][target_node]["latency"] = 1e6
            failed_links.append((u, target_node))

        meta = {
            "type": "switch_failure",
            "failed_nodes": [target_node],
            "failed_links": failed_links
        }
        return G_fault, meta

    def inject_capacity_degradation(self, G: nx.DiGraph, degradation_factor: float = 0.25) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Degrades bandwidth capacity on random core links (partial brownout)."""
        G_fault = G.copy()
        edges = list(G.edges())
        idx = self.rng.integers(0, len(edges))
        u, v = edges[idx]

        orig_cap = G_fault[u][v]["capacity"]
        G_fault[u][v]["capacity"] = max(5.0, orig_cap * degradation_factor)
        if G_fault.has_edge(v, u):
            G_fault[v][u]["capacity"] = max(5.0, orig_cap * degradation_factor)

        meta = {
            "type": "capacity_degradation",
            "degraded_links": [(u, v), (v, u)],
            "degradation_factor": degradation_factor
        }
        return G_fault, meta

    def inject_delay_loss_spike(self, G: nx.DiGraph, added_latency: float = 80.0, loss_pct: float = 12.0) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Simulates localized bufferbloat or physical fiber degradation."""
        G_fault = G.copy()
        edges = list(G.edges())
        idx = self.rng.integers(0, len(edges))
        u, v = edges[idx]

        G_fault[u][v]["latency"] += added_latency
        G_fault[u][v]["loss"] = max(G_fault[u][v].get("loss", 0.0), loss_pct)
        if G_fault.has_edge(v, u):
            G_fault[v][u]["latency"] += added_latency
            G_fault[v][u]["loss"] = max(G_fault[v][u].get("loss", 0.0), loss_pct)

        meta = {
            "type": "delay_loss_spike",
            "affected_links": [(u, v), (v, u)],
            "added_latency": added_latency,
            "loss_pct": loss_pct
        }
        return G_fault, meta

    def inject_burst_congestion(self, flows: List[Dict[str, Any]], burst_multiplier: float = 3.5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Creates sudden bursty traffic load on active flows."""
        flows_burst = [dict(f) for f in flows]
        target_idx = self.rng.integers(0, len(flows_burst))
        orig_bw = flows_burst[target_idx]["bandwidth_mbps"]
        flows_burst[target_idx]["bandwidth_mbps"] = orig_bw * burst_multiplier

        meta = {
            "type": "burst_congestion",
            "burst_flow_id": flows_burst[target_idx]["flow_id"],
            "multiplier": burst_multiplier
        }
        return flows_burst, meta

    def generate_noisy_telemetry(self, G: nx.DiGraph, noise_std: float = 0.08) -> Dict[Tuple[str, str], Dict[str, float]]:
        """
        Produces realistic telemetry readings with measurement noise and jitter.
        """
        telemetry = {}
        for u, v in G.edges():
            true_lat = G[u][v].get("latency", 10.0)
            true_loss = G[u][v].get("loss", 0.0)
            status = G[u][v].get("status", 1)

            # Add zero-mean Gaussian noise to telemetry
            telem_lat = max(1.0, true_lat * (1.0 + self.rng.normal(0, noise_std)))
            telem_loss = max(0.0, true_loss + self.rng.normal(0, noise_std * 5.0))
            if status == 0:
                telem_loss = 100.0
                telem_lat = 1e6

            telemetry[(u, v)] = {
                "latency": float(telem_lat),
                "loss": float(telem_loss),
                "capacity": float(G[u][v].get("capacity", 1000.0)),
                "status": status
            }
        return telemetry
