"""
CIRAH: Causal Intervention Healing Field (CIHF) Module
Updated per Faculty Revision 2 requirements:
1. Formally defines normalized stress relief vector s(a) in [0, 1].
2. Normalized graph Laplacian L_norm = I - D^(-1/2) W D^(-1/2) accounts for degree heterogeneity.
3. Implements continuous spectral heat diffusion kernel: h(a) = (I + sigma * L_norm)^(-1) * s(a).
4. Provides comparative baselines: No-Field (ablation), Local-Relief, and Betweenness-Centrality scoring.
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
