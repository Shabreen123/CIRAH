"""
CIRAH: Causal Intervention Healing Field (CIHF) Module
Implements the continuous graph diffusion healing field H(a, v) over graph topology G.
Uses graph Laplacian heat diffusion:
    h(a) = (I + sigma * L_norm)^(-1) * s(a)
where:
    - L_norm is the normalized graph Laplacian
    - s(a) is the spatial intervention impulse vector
    - sigma is the spatial diffusion / propagation coefficient
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any

class HealingFieldPropagator:
    """
    Computes the spatial and spectral propagation of recovery effects
    induced by candidate interventions over network topology G = (V, E).
    """

    def __init__(self, topology: nx.DiGraph, sigma: float = 1.5):
        self.G = topology
        self.sigma = sigma
        self.nodes = sorted(list(topology.nodes()))
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
        self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
        self.N = len(self.nodes)
        self._compute_laplacian()

    def _compute_laplacian(self):
        """Constructs the undirected projection and normalized graph Laplacian."""
        # Project DiGraph onto symmetric capacity-weighted graph for spectral diffusion
        adj = np.zeros((self.N, self.N))
        for u, v, data in self.G.edges(data=True):
            i, j = self.node_to_idx[u], self.node_to_idx[v]
            w = 1.0 / max(1.0, data.get("latency", 10.0))
            adj[i, j] += w
            adj[j, i] += w

        deg = np.sum(adj, axis=1)
        deg_inv_sqrt = np.power(deg, -0.5, where=deg > 1e-9)
        deg_inv_sqrt[deg <= 1e-9] = 0.0

        D_inv_sqrt = np.diag(deg_inv_sqrt)
        self.L_norm = np.eye(self.N) - D_inv_sqrt @ adj @ D_inv_sqrt
        # Pre-invert diffusion operator (I + sigma * L_norm)
        self.diffusion_kernel = np.linalg.inv(np.eye(self.N) + self.sigma * self.L_norm)

    def construct_healing_field(self, 
                                action: Dict[str, Any], 
                                pre_stress: Dict[str, float], 
                                post_stress: Dict[str, float]) -> Dict[str, float]:
        """
        Constructs the continuous healing field H(a, v) for all nodes v in V.
        
        Parameters:
            action: Candidate intervention details (e.g. path, throttles)
            pre_stress: Node-level stress before intervention
            post_stress: Predicted node-level stress after intervention
            
        Returns:
            Dictionary mapping each node v to its healing field value H(a, v).
        """
        # Step 1: Compute local impulse vector s(a)
        s = np.zeros(self.N)
        path = action.get("path", [])
        
        # Nodes directly reconfigured or relieved receive primary healing impulses
        for node in self.nodes:
            idx = self.node_to_idx[node]
            delta_stress = max(0.0, pre_stress.get(node, 0.0) - post_stress.get(node, 0.0))
            # If node is on the newly allocated path or repaired site
            in_action = (node in path)
            weight = 1.5 if in_action else 1.0
            s[idx] = delta_stress * weight

        # If impulse is flat (no delta measured), assign baseline impulse to path nodes
        if np.sum(s) < 1e-6 and path:
            for p_node in path:
                if p_node in self.node_to_idx:
                    s[self.node_to_idx[p_node]] = 1.0

        # Step 2: Propagate via Graph Laplacian Kernel: h(a) = (I + sigma * L_norm)^(-1) * s
        h_vec = self.diffusion_kernel @ s

        # Step 3: Format as dictionary
        healing_field = {self.idx_to_node[i]: float(h_vec[i]) for i in range(self.N)}
        return healing_field

    def compute_aggregate_healing_gain(self, healing_field: Dict[str, float]) -> float:
        """Computes aggregate scalar healing value Psi(a) = sum_{v in V} H(a, v)."""
        return float(np.sum(list(healing_field.values())))
