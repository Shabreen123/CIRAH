"""
CIRAH: Causal Intervention Healing Field (CIHF) Module
Updated per Faculty Revision 2 requirements:
1. Formally defines normalized stress relief vector s(a) in [0, 1].
2. Normalized graph Laplacian L_norm = I - D^(-1/2) W D^(-1/2) accounts for degree heterogeneity.
3. Implements continuous spectral heat diffusion kernel: h(a) = (I + sigma * L_norm)^(-1) * s(a).
4. Provides comparative baselines: No-Field (ablation), Local-Relief, and Betweenness-Centrality scoring.

Extended (Phase B/C): Added Counterfactual Stress-Reduction Field (CSRF) and congestion-only modes.
5. CSRF: edge-level stress from utilization, queuing delay, and packet loss; flow-weighted
   network-wide stress reduction without Laplacian dampening.
6. Congestion-only: utilization-based scoring without spatial diffusion.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any

class HealingFieldPropagator:
    """
    Computes the spatial diffusion of stress relief induced by candidate interventions.
    """

    def __init__(self, topology: nx.DiGraph, sigma: float = 1.5):
        self.G = topology
        self.sigma = sigma
        self.nodes = sorted(list(topology.nodes()))
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
        self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
        self.N = len(self.nodes)
        
        # Precompute normalized Laplacian and inverse diffusion kernel
        self._compute_spectral_diffusion_operator()
        # Precompute betweenness centrality for comparative baseline
        self.betweenness = nx.betweenness_centrality(topology.to_undirected(), weight="latency")

    def _compute_spectral_diffusion_operator(self):
        """Constructs degree-normalized graph Laplacian and pre-inverts the diffusion kernel."""
        adj = np.zeros((self.N, self.N))
        for u, v, data in self.G.edges(data=True):
            i, j = self.node_to_idx[u], self.node_to_idx[v]
            # Link conductance w_ij is inversely proportional to propagation delay
            w = 1.0 / max(1.0, data.get("latency", 10.0))
            adj[i, j] += w
            adj[j, i] += w

        deg = np.sum(adj, axis=1)
        deg_inv_sqrt = np.power(deg, -0.5, where=deg > 1e-9)
        deg_inv_sqrt[deg <= 1e-9] = 0.0

        D_inv_sqrt = np.diag(deg_inv_sqrt)
        self.L_norm = np.eye(self.N) - D_inv_sqrt @ adj @ D_inv_sqrt
        # Steady-state Green's function / diffusion operator: (I + sigma * L_norm)^(-1)
        self.diffusion_kernel = np.linalg.inv(np.eye(self.N) + self.sigma * self.L_norm)

    def construct_healing_field(self, 
                                action: Dict[str, Any], 
                                pre_stress: Dict[str, float], 
                                post_stress: Dict[str, float],
                                scoring_mode: str = "cihf") -> Dict[str, float]:
        """
        Constructs the spatial healing field H(a, v) for all nodes v in V.
        Modes:
          - 'cihf': Graph Laplacian spectral heat diffusion
          - 'local_only': Pure local stress relief without spatial propagation
          - 'centrality': Betweenness-centrality weighted relief
          - 'none': Zero field (CIRAH-noCIHF ablation)
        """
        if scoring_mode == "none":
            return {n: 0.0 for n in self.nodes}

        # Step 1: Compute normalized local stress relief impulse s(a) in [0, 1]
        s = np.zeros(self.N)
        path = action.get("path", [])
        
        for node in self.nodes:
            idx = self.node_to_idx[node]
            raw_delta = max(0.0, pre_stress.get(node, 0.0) - post_stress.get(node, 0.0))
            # Normalize by 100.0 (maximum possible loss-percentage stress)
            norm_delta = min(1.0, raw_delta / 100.0)
            
            # Nodes along the newly active path receive a baseline engagement weight
            in_action = (node in path)
            weight = 1.5 if in_action else 1.0
            s[idx] = norm_delta * weight

        if np.sum(s) < 1e-6 and path:
            # If delta is minimal, provide baseline impulse along candidate hops
            for p_node in path:
                if p_node in self.node_to_idx:
                    s[self.node_to_idx[p_node]] = 0.2

        # Step 2: Evaluate according to scoring mode
        if scoring_mode == "cihf":
            # Propagate via Normalized Laplacian Kernel: h(a) = (I + sigma * L_norm)^(-1) * s
            h_vec = self.diffusion_kernel @ s
        elif scoring_mode == "centrality":
            # Weight local impulse by topological betweenness
            c_weights = np.array([self.betweenness.get(self.idx_to_node[i], 0.1) for i in range(self.N)])
            h_vec = s * (1.0 + 2.0 * c_weights)
        elif scoring_mode == "local_only":
            h_vec = s
        else:
            h_vec = s

        return {self.idx_to_node[i]: float(h_vec[i]) for i in range(self.N)}

    def compute_aggregate_healing_gain(self, healing_field: Dict[str, float]) -> float:
        """Computes aggregate scalar healing value Psi(a) = sum_{v in V} H(a, v)."""
        return float(np.sum(list(healing_field.values())))

    # -------------------------------------------------------------------------
    # Phase B/C Extension: Counterfactual Stress-Reduction Field (CSRF)
    # -------------------------------------------------------------------------

    @staticmethod
    def compute_edge_stress(load: float, capacity: float, queue_delay: float,
                            loss_pct: float, base_latency: float,
                            w_q: float = 0.4, w_d: float = 0.3, w_l: float = 0.3) -> float:
        """
        Computes a composite edge stress measure from utilization, queuing delay, and loss.

        sigma_e = w_q * min(1, Q_e) + w_d * min(1, D_e/D_ref) + w_l * L_e/100

        where:
          Q_e = load / cap (utilization, clipped to [0,1])
          D_e = queueing delay (ms)
          D_ref = base_latency (reference delay for relative normalization)
          L_e = packet loss (0-100%)

        Returns stress in [0, ~1.3]. Weights sum to 1.0.
        """
        cap = max(1.0, capacity)
        utilization = min(1.0, load / cap)
        delay_ref = max(1.0, base_latency)
        delay_ratio = min(1.0, queue_delay / delay_ref)
        loss_ratio = min(1.0, max(0.0, loss_pct) / 100.0)
        return float(w_q * utilization + w_d * delay_ratio + w_l * loss_ratio)

    def _compute_pre_intervention_edge_stress(
        self, telemetry: Dict, topology: nx.DiGraph
    ) -> Dict:
        """Computes edge stress from observed telemetry (before intervention)."""
        edge_stress = {}
        for u, v in topology.edges():
            telem = telemetry.get((u, v), {})
            load = telem.get("load", 15.0)
            cap = topology[u][v].get("capacity", 100.0)
            base_lat = topology[u][v].get("latency", 10.0)
            obs_lat = telem.get("latency", base_lat)
            queue_delay = max(0.0, obs_lat - base_lat)
            loss_pct = telem.get("loss", 0.0)
            edge_stress[(u, v)] = self.compute_edge_stress(
                load, cap, queue_delay, loss_pct, base_lat
            )
        return edge_stress

    def _compute_post_intervention_edge_stress(
        self, cf_result: Dict, topology: nx.DiGraph
    ) -> Dict:
        """Computes edge stress from counterfactual prediction (after intervention)."""
        cf_loads = cf_result.get("cf_link_loads", {})
        cf_queues = cf_result.get("cf_link_queues", {})
        cf_latencies = cf_result.get("cf_link_latencies", {})
        cf_losses = cf_result.get("cf_link_losses", {})

        edge_stress = {}
        for u, v in topology.edges():
            e = (u, v)
            load = cf_loads.get(e, 0.0)
            cap = topology[u][v].get("capacity", 100.0)
            base_lat = topology[u][v].get("latency", 10.0)
            cf_lat = cf_latencies.get(e, base_lat)
            queue_delay = max(0.0, cf_lat - base_lat)
            loss_pct = cf_losses.get(e, 0.0)
            edge_stress[e] = self.compute_edge_stress(
                load, cap, queue_delay, loss_pct, base_lat
            )
        return edge_stress

    @staticmethod
    def _compute_flow_counts(flows: List[Dict], topology: nx.DiGraph) -> Dict:
        """Counts the number of flows traversing each edge."""
        flow_count = {e: 0 for e in topology.edges()}
        for f in flows:
            p = f.get("current_path", [])
            if p and len(p) > 1:
                for i in range(len(p) - 1):
                    e = (p[i], p[i + 1])
                    if e in flow_count:
                        flow_count[e] += 1
        return flow_count

    def _node_outgoing_flow_count(self, flows: List[Dict], topology: nx.DiGraph) -> Dict:
        """Counts flows whose paths include at least one outgoing edge from node v."""
        flow_counts = {e: 0 for e in topology.edges()}
        for f in flows:
            p = f.get("current_path", [])
            if p and len(p) > 1:
                for i in range(len(p) - 1):
                    e = (p[i], p[i + 1])
                    if e in flow_counts:
                        flow_counts[e] += 1

        node_flow_count = {}
        for n in topology.nodes():
            node_flow_count[n] = sum(
                flow_counts.get((n, v), 0) for v in topology.successors(n)
            )
        return node_flow_count

    def construct_csrf_field(
        self,
        action: Dict,
        cf_result: Dict,
        flows: List[Dict],
        topology: nx.DiGraph,
        current_telemetry: Dict,
    ) -> Dict:
        """
        Constructs the Counterfactual Stress-Reduction Field (CSRF).

        For each edge e, compute composite stress sigma_e from utilization,
        queuing delay, and packet loss. Node stress is the max of outgoing
        edge stress. Stress reduction is the positive part of (before - after).
        The per-node field is weighted by the number of flows traversing
        outgoing edges from that node (multi-flow benefit).

        H(a, v) = max(0, S_before(v) - S_after(a, v)) * F_v

        where F_v = number of flows traversing outgoing edges from v.

        This avoids double-counting with R_post (which measures probabilistic
        cascade risk) by measuring deterministic, network-wide stress reduction.
        """
        pre_edge_stress = self._compute_pre_intervention_edge_stress(current_telemetry, topology)
        post_edge_stress = self._compute_post_intervention_edge_stress(cf_result, topology)
        node_flows = self._node_outgoing_flow_count(flows, topology)

        field = {}
        for n in self.nodes:
            # Node stress = max of outgoing edge stress
            successors = list(topology.successors(n))
            if not successors:
                field[n] = 0.0
                continue

            s_before = max(pre_edge_stress.get((n, v), 0.0) for v in successors)
            s_after = max(post_edge_stress.get((n, v), 0.0) for v in successors)
            delta_s = max(0.0, s_before - s_after)

            # Weight by number of flows benefiting from outgoing edges
            f_v = max(1, node_flows.get(n, 0))

            field[n] = float(delta_s * f_v)

        return field

    def construct_congestion_field(
        self,
        action: Dict,
        cf_result: Dict,
        topology: nx.DiGraph,
        current_telemetry: Dict,
    ) -> Dict:
        """
        Constructs a congestion-only field based on utilization reduction,
        without Laplacian diffusion. Tests whether utilization alone (without
        delay and loss components) can differentiate candidates.
        """
        field = {}
        for n in self.nodes:
            successors = list(topology.successors(n))
            if not successors:
                field[n] = 0.0
                continue

            # Pre-intervention max utilization
            pre_utils = []
            for v in successors:
                e = (n, v)
                telem = current_telemetry.get(e, {})
                cap = max(1.0, topology[n][v].get("capacity", 100.0))
                load = telem.get("load", 15.0)
                pre_utils.append(min(1.0, load / cap))
            s_before = max(pre_utils) if pre_utils else 0.0

            # Post-intervention max utilization
            cf_loads = cf_result.get("cf_link_loads", {})
            post_utils = []
            for v in successors:
                e = (n, v)
                cap = max(1.0, topology[n][v].get("capacity", 100.0))
                load = cf_loads.get(e, 0.0)
                post_utils.append(min(1.0, load / cap))
            s_after = max(post_utils) if post_utils else 0.0

            delta = max(0.0, s_before - s_after)
            field[n] = float(delta)

        return field
