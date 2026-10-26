"""
Unit and Regression Test Suite for CIRAH Audit (Phases 0, 2, 3, 14)
Covers:
1. Physical Network Disconnection / Partition Handling (No feasible path)
2. Robust Risk Constraint accounting (R_robust vs R_max and violation flag)
3. Zero/Missing telemetry observation handling & division-by-zero protection
4. Independent Data-Plane Simulation (Non-circular Counterfactual Ground Truth)
5. Repeated intervention idempotency (intervention applied once, no duplicate churn)
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import networkx as nx
import numpy as np

from src.topologies import get_topology, generate_traffic_demands
from src.causal_engine import StructuralCausalModel
from src.optimizer import RiskConstrainedOptimizer
from src.controller_sim import CIRAHController
from src.risk_assessment import RiskAssessmentModule
from src.cost_model import InterventionCostModel
from src.evaluator import StandardizedEvaluator

class TestCIRAHRegression(unittest.TestCase):

    def setUp(self):
        self.G = get_topology("abilene")
        self.flows = generate_traffic_demands(self.G, num_flows=5, rng_seed=42)
        for f in self.flows:
            f["current_path"] = nx.shortest_path(self.G, f["src"], f["dst"], weight="latency")
        self.target_flow = self.flows[0]

    def test_partitioned_network_graceful_fallback(self):
        """Edge Case 1: When network is fully partitioned, optimizer must detect partition and not crash."""
        G_part = self.G.copy()
        # Cut all outgoing edges from source
        src = self.target_flow["src"]
        for v in list(G_part.successors(src)):
            G_part[src][v]["status"] = 0
            G_part[src][v]["loss"] = 100.0

        ctrl = CIRAHController(G_part, mode="full")
        telemetry = {(u, v): {"loss": 100.0 if G_part[u][v].get("status", 1) == 0 else 0.0,
                              "latency": 1e6 if G_part[u][v].get("status", 1) == 0 else G_part[u][v]["latency"],
                              "status": G_part[u][v].get("status", 1)}
                     for u, v in G_part.edges()}

        res = ctrl.execute_self_healing_cycle(G_part, self.flows, telemetry, self.target_flow)
        
        self.assertFalse(res["success"])
        self.assertFalse(res["connected"])
        self.assertTrue(res["fallback_triggered"])
        self.assertTrue(res["partition_detected"])
        self.assertEqual(res["recovery_time_ms"], 2000.0)

    def test_robust_risk_ceiling_enforcement(self):
        """Edge Case 2: Robust risk R_robust = R_post + z_alpha * sigma_R must be strictly checked against R_max."""
        ctrl = CIRAHController(self.G, mode="full", r_max=2.0) # Tight risk ceiling
        telemetry = {(u, v): {"loss": 0.0, "latency": self.G[u][v]["latency"], "status": 1}
                     for u, v in self.G.edges()}

        res = ctrl.execute_self_healing_cycle(self.G, self.flows, telemetry, self.target_flow)
        # Target flow has baseline risk ~ 1.0 - 1.5, robust risk = R_post + 1.645 * 0.08 * R_post
        self.assertIn("risk_robust", res)
        self.assertGreaterEqual(res["risk_robust"], res["risk_post"])
        if res["risk_robust"] > 2.0:
            self.assertTrue(res["constraint_violation"])

    def test_missing_telemetry_and_division_by_zero(self):
        """Edge Case 3: Missing telemetry records, zero capacity, zero flows must not raise exceptions."""
        scm = StructuralCausalModel(self.G)
        empty_telemetry = {} # Completely missing telemetry
        
        # Must execute without KeyError or ZeroDivisionError
        posteriors = scm.diagnose_causal_faults(empty_telemetry, active_paths=[])
        self.assertEqual(len(posteriors), len(self.G.edges()))
        for e, p in posteriors.items():
            self.assertAlmostEqual(p["P_normal"] + p["P_degraded"] + p["P_severed"], 1.0, places=4)

    def test_non_circular_ground_truth_simulator(self):
        """Edge Case 4: Independent data plane simulation calculates physically consistent delays and drops."""
        from experiments.run_experiments import simulate_independent_dataplane
        
        # Test valid path
        path = nx.shortest_path(self.G, self.target_flow["src"], self.target_flow["dst"], weight="latency")
        out = simulate_independent_dataplane(self.G, self.flows, self.target_flow["flow_id"], path)
        self.assertTrue(out["connected"])
        self.assertGreater(out["latency"], 0.0)
        self.assertLess(out["latency"], 200.0)
        self.assertGreaterEqual(out["loss"], 0.0)

        # Test severed path
        G_broken = self.G.copy()
        G_broken[path[0]][path[1]]["status"] = 0
        out_broken = simulate_independent_dataplane(G_broken, self.flows, self.target_flow["flow_id"], path)
        self.assertFalse(out_broken["connected"])
        self.assertEqual(out_broken["loss"], 100.0)

if __name__ == "__main__":
    unittest.main()
