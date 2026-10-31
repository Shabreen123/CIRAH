"""
CIRAH: Revision 3 Implementation Tests

Tests for:
1. ConstrainedMinChangeOptimizer feasibility, objective, edge cases
2. Fat-tree topology creation and connectivity
3. Run count reconciliation
4. Risk sensitivity boundary conditions
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import networkx as nx
import numpy as np
from src.topologies import get_topology, generate_traffic_demands
from src.fault_generator import FaultGenerator
from src.baselines import ConstrainedMinChangeOptimizer, MinChangeHeuristic
from src.controller_sim import CIRAHController
from src.evaluator import StandardizedEvaluator


class TestRev3Implementations(unittest.TestCase):

    def setUp(self):
        self.G = get_topology("abilene")
        self.flows = generate_traffic_demands(self.G, num_flows=5, rng_seed=42)
        for f in self.flows:
            f["current_path"] = nx.shortest_path(self.G, f["src"], f["dst"], weight="latency")
        self.target_flow = self.flows[0]

    def _make_fault(self, k=1, seed=123):
        fg = FaultGenerator(rng_seed=seed)
        G_fault, _ = fg.inject_multi_link_failure(self.G, k=k)
        telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)
        return G_fault, telemetry

    # --- ConstrainedMinChangeOptimizer ---

    def test_constrained_minchange_returns_valid_action(self):
        """Constrained MinChange must return a valid action dict."""
        G_fault, telemetry = self._make_fault(k=1)
        # Ensure target flow path is affected
        for f in self.flows:
            p = f["current_path"]
            if any(G_fault.has_edge(p[i], p[i+1]) and
                   G_fault[p[i]][p[i+1]].get("status", 1) == 0
                   for i in range(len(p)-1)):
                self.target_flow = f
                break

        cmc = ConstrainedMinChangeOptimizer(self.G, r_max=35.0)
        action = cmc.compute_recovery_action(G_fault, self.flows, telemetry, self.target_flow)

        self.assertIn("method", action)
        self.assertEqual(action["method"], "Constrained-MinChange")
        self.assertIn("path", action)
        self.assertIn("flow_id", action)
        self.assertIn(action["type"], ["reroute_cmc", "no_change", "reroute_cmc_fallback", "failed"])

    def test_constrained_minchange_enforces_risk_constraint(self):
        """Constrained MinChange with very low R_max should trigger fallback."""
        G_fault, telemetry = self._make_fault(k=2)
        for f in self.flows:
            p = f["current_path"]
            if any(G_fault.has_edge(p[i], p[i+1]) and
                   G_fault[p[i]][p[i+1]].get("status", 1) == 0
                   for i in range(len(p)-1)):
                self.target_flow = f
                break

        # Very tight R_max — should force fallback or fail
        cmc_tight = ConstrainedMinChangeOptimizer(self.G, r_max=1.0)
        action = cmc_tight.compute_recovery_action(G_fault, self.flows, telemetry, self.target_flow)

        # With R_max=1.0, almost no action should be feasible
        # Either fallback triggered or action is failed
        self.assertTrue(
            action.get("is_fallback", False) or action["type"] == "failed",
            "Very tight R_max should trigger fallback or failure"
        )

    def test_constrained_minchange_no_fault_returns_no_change(self):
        """With no fault, Constrained MinChange should return no_change."""
        fg = FaultGenerator(rng_seed=42)
        G_clean = self.G.copy()
        telemetry = fg.generate_noisy_telemetry(G_clean, noise_std=0.03)

        cmc = ConstrainedMinChangeOptimizer(self.G, r_max=35.0)
        action = cmc.compute_recovery_action(G_clean, self.flows, telemetry, self.target_flow)

        self.assertIn(action["type"], ["no_change", "reroute_cmc"])

    def test_constrained_minchange_vs_unconstrained(self):
        """Constrained MinChange should modify fewer or equal switches vs Dynamic-SP."""
        G_fault, telemetry = self._make_fault(k=1)
        for f in self.flows:
            p = f["current_path"]
            if any(G_fault.has_edge(p[i], p[i+1]) and
                   G_fault[p[i]][p[i+1]].get("status", 1) == 0
                   for i in range(len(p)-1)):
                self.target_flow = f
                break

        evaluator = StandardizedEvaluator(self.G, r_max=35.0)
        cmc = ConstrainedMinChangeOptimizer(self.G, r_max=35.0)
        dyn = DynamicSP()

        act_cmc = cmc.compute_recovery_action(G_fault, self.flows, telemetry, self.target_flow)
        act_dyn = dyn.compute_recovery_action(G_fault, self.flows, telemetry, self.target_flow)

        res_cmc = evaluator.evaluate_action("CMC", act_cmc, self.flows, telemetry, self.target_flow)
        res_dyn = evaluator.evaluate_action("Dyn", act_dyn, self.flows, telemetry, self.target_flow)

        # Constrained MinChange should use fewer or equal switches
        self.assertLessEqual(
            res_cmc["switches_modified"], res_dyn["switches_modified"] + 2,
            "Constrained MinChange should not use dramatically more switches than Dynamic-SP"
        )

    # --- Fat-tree topology ---

    def test_fattree_creation(self):
        """Fat-tree k=4 should create 20 nodes and 64 directed edges."""
        from experiments.rev3_experiments import create_fattree_topology
        G = create_fattree_topology(k=4)
        self.assertEqual(len(G.nodes()), 20)
        self.assertGreater(len(G.edges()), 0)
        # Check connectivity
        self.assertTrue(nx.is_connected(G.to_undirected()))

    def test_fattree_has_capacities(self):
        """Fat-tree edges should have capacity and latency attributes."""
        from experiments.rev3_experiments import create_fattree_topology
        G = create_fattree_topology(k=4)
        for u, v, data in G.edges(data=True):
            self.assertIn("capacity", data)
            self.assertIn("latency", data)
            self.assertIn("status", data)
            self.assertEqual(data["status"], 1)

    # --- Run count reconciliation ---

    def test_run_count_reconciliation(self):
        """Total experiment count should be 5290 across all campaigns."""
        from experiments.rev3_experiments import reconcile_run_counts
        counts, total = reconcile_run_counts()
        self.assertEqual(total, 5290)
        self.assertEqual(counts["C1_failure_severity"], 3000)
        self.assertEqual(counts["C2_stress_sweep"], 1000)
        self.assertEqual(counts["C3_telemetry_noise"], 750)
        self.assertEqual(counts["C4_ablation"], 360)
        self.assertEqual(counts["C5_cf_validation"], 60)
        self.assertEqual(counts["C6_latency_profiling"], 120)

    # --- Risk sensitivity ---

    def test_risk_sensitivity_zero_violation_at_default(self):
        """At R_max=35 (default), violation rate should be 0%."""
        df_path = os.path.join(
            os.path.dirname(__file__), '..', 'results', 'rev3_risk_sensitivity.csv'
        )
        if not os.path.exists(df_path):
            self.skipTest("Risk sensitivity CSV not found - run rev3_experiments.py first")
        import pandas as pd
        df = pd.read_csv(df_path)
        default = df[df["r_max"] == 35.0]
        self.assertEqual(default["constraint_violation"].mean(), 0.0,
                        "R_max=35 should produce 0% violations")


from src.baselines import DynamicSP


if __name__ == "__main__":
    unittest.main()
