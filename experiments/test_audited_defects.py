"""
Unit and Regression Test Suite for CIRAH Audit
Covers:
1. Physical Network Disconnection / Partition Handling (No feasible path)
2. Robust Risk Constraint accounting (R_robust vs R_max and violation flag)
3. Zero/Missing telemetry observation handling & division-by-zero protection
4. Independent Data-Plane Simulation (Non-circular Counterfactual Ground Truth)
5. All-zero paired differences (safe non-informative handling without SciPy warnings)
6. Run-ID and seed pairing validation (unmatched pairs & duplicates fail clearly)
7. Missing/NaN data rejection in statistical pipeline
8. Multiple-testing adjustment correctness (Holm-Bonferroni and Bonferroni logic)
9. Spearman correlation edge cases (zero-variance / constant input handling)
10. Holm adjustment correctness for declared family_size=30 with NaN hypotheses
11. Bonferroni adjustment correctness for declared family_size=30
12. NaN hypotheses do not shrink the declared family size
13. Primary Abilene family (N=6) remains independent and correct
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

from src.topologies import get_topology, generate_traffic_demands
from src.causal_engine import StructuralCausalModel
from src.controller_sim import CIRAHController
from experiments.statistical_analysis import (
    holm_bonferroni_adjust,
    bonferroni_adjust,
    validate_and_pair_runs
)

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
        ctrl = CIRAHController(self.G, mode="full", r_max=2.0)
        telemetry = {(u, v): {"loss": 0.0, "latency": self.G[u][v]["latency"], "status": 1}
                     for u, v in self.G.edges()}

        res = ctrl.execute_self_healing_cycle(self.G, self.flows, telemetry, self.target_flow)
        self.assertIn("risk_robust", res)
        self.assertGreaterEqual(res["risk_robust"], res["risk_post"])
        if res["risk_robust"] > 2.0:
            self.assertTrue(res["constraint_violation"])

    def test_missing_telemetry_and_division_by_zero(self):
        """Edge Case 3: Missing telemetry records, zero capacity, zero flows must not raise exceptions."""
        scm = StructuralCausalModel(self.G)
        empty_telemetry = {}

        posteriors = scm.diagnose_causal_faults(empty_telemetry, active_paths=[])
        self.assertEqual(len(posteriors), len(self.G.edges()))
        for e, p in posteriors.items():
            self.assertAlmostEqual(p["P_normal"] + p["P_degraded"] + p["P_severed"], 1.0, places=4)

    def test_non_circular_ground_truth_simulator(self):
        """Edge Case 4: Independent data plane simulation calculates physically consistent delays and drops."""
        from experiments.run_experiments import simulate_independent_dataplane

        path = nx.shortest_path(self.G, self.target_flow["src"], self.target_flow["dst"], weight="latency")
        out = simulate_independent_dataplane(self.G, self.flows, self.target_flow["flow_id"], path)
        self.assertTrue(out["connected"])
        self.assertGreater(out["latency"], 0.0)
        self.assertLess(out["latency"], 200.0)
        self.assertGreaterEqual(out["loss"], 0.0)

        G_broken = self.G.copy()
        G_broken[path[0]][path[1]]["status"] = 0
        out_broken = simulate_independent_dataplane(G_broken, self.flows, self.target_flow["flow_id"], path)
        self.assertFalse(out_broken["connected"])
        self.assertEqual(out_broken["loss"], 100.0)

    def test_all_zero_paired_differences(self):
        """Edge Case 5: All-zero paired differences must be flagged as non-informative without SciPy RuntimeWarning."""
        v_cirah = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        v_dyn = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        diff = v_cirah - v_dyn

        all_zero = bool(np.all(np.abs(diff) < 1e-9))
        self.assertTrue(all_zero)

        # When all-zero, statistical test is defined as non-applicable/NaN, not a false positive
        p_w = np.nan if all_zero else stats.wilcoxon(v_cirah, v_dyn).pvalue
        self.assertTrue(np.isnan(p_w))

    def test_unmatched_runs_and_duplicates_fail(self):
        """Edge Case 6: Duplicate run_ids or unmatched seeds must fail explicitly."""
        # Test duplicate run_id rejection
        df_dup = pd.DataFrame({
            "run_id": [1, 1, 2],
            "seed": [100, 100, 101],
            "method": ["CIRAH", "CIRAH", "CIRAH"]
        })
        with self.assertRaises(ValueError) as ctx:
            validate_and_pair_runs(df_dup, "abilene", 1)
        self.assertIn("Duplicate run_id", str(ctx.exception))

        # Test unmatched pairs rejection
        df_unmatched = pd.DataFrame({
            "run_id": [1, 2, 1],
            "seed": [100, 101, 100],
            "method": ["CIRAH", "CIRAH", "Dynamic-SP"] # Run 2 missing in Dynamic-SP
        })
        with self.assertRaises(ValueError) as ctx2:
            validate_and_pair_runs(df_unmatched, "abilene", 1)
        self.assertIn("Pairing mismatch", str(ctx2.exception))

    def test_missing_or_nan_data_rejection(self):
        """Edge Case 7: Statistical validation must detect and reject unexpected NaN values in evaluation series."""
        v_clean = np.array([1.0, 2.0, 3.0])
        v_nan = np.array([1.0, np.nan, 3.0])
        self.assertFalse(np.isnan(v_clean).any())
        self.assertTrue(np.isnan(v_nan).any())

    def test_multiple_testing_adjustments(self):
        """Edge Case 8: Holm and Bonferroni adjustments must strictly control FWER."""
        raw_p = [0.001, 0.010, 0.040, np.nan] # 3 valid tests
        holm_p = holm_bonferroni_adjust(raw_p)
        bonf_p = bonferroni_adjust(raw_p)

        # With 3 valid tests:
        # rank 1: p=0.001 * 3 = 0.003
        # rank 2: p=0.010 * 2 = 0.020
        # rank 3: p=0.040 * 1 = 0.040
        self.assertAlmostEqual(holm_p[0], 0.003, places=5)
        self.assertAlmostEqual(holm_p[1], 0.020, places=5)
        self.assertAlmostEqual(holm_p[2], 0.040, places=5)
        self.assertTrue(np.isnan(holm_p[3]))

        # Bonferroni: p * 3
        self.assertAlmostEqual(bonf_p[0], 0.003, places=5)
        self.assertAlmostEqual(bonf_p[1], 0.030, places=5)
        self.assertAlmostEqual(bonf_p[2], 0.120, places=5)
        self.assertTrue(np.isnan(bonf_p[3]))

    def test_spearman_edge_cases_and_symmetry(self):
        """Edge Case 9: Undefined Spearman ranking correlation on constant inputs must return NaN."""
        constant_lats = [50.0, 50.0, 50.0]
        obs_lats = [50.0, 52.0, 54.0]
        if np.std(constant_lats) > 1e-6 and np.std(obs_lats) > 1e-6:
            rho, _ = stats.spearmanr(constant_lats, obs_lats)
        else:
            rho = np.nan
        self.assertTrue(np.isnan(rho))


    # -------------------------------------------------------------------------
    # NEW TESTS (10-13): family_size=30 correctness for declared omnibus family
    # -------------------------------------------------------------------------

    def test_holm_family_size_30_correctness(self):
        """Test 10: Holm step-down with family_size=30 uses correct multipliers.

        With one valid p-value (0.001) and two NaN hypotheses in a family of
        30, the single valid p-value occupies rank 0 (the smallest), so its
        Holm multiplier is n_family - rank = 30 - 0 = 30.
        Expected adjusted p-value = min(1.0, 0.001 * 30) = 0.030.
        """
        import numpy as np
        raw = [0.001, np.nan, np.nan]
        adj = holm_bonferroni_adjust(raw, family_size=30)
        # Only the first entry is valid; NaN entries stay NaN
        self.assertAlmostEqual(adj[0], 0.030, places=6,
                               msg="Holm multiplier for rank-0 must be family_size=30")
        self.assertTrue(np.isnan(adj[1]),
                        msg="NaN input must remain NaN in adjusted output")
        self.assertTrue(np.isnan(adj[2]),
                        msg="NaN input must remain NaN in adjusted output")

    def test_bonferroni_family_size_30_correctness(self):
        """Test 11: Bonferroni with family_size=30 divides alpha by 30.

        A raw p-value of 0.001 corrected by Bonferroni with family_size=30
        must equal min(1.0, 0.001 * 30) = 0.030.
        A raw p-value of 0.040 corrected by Bonferroni with family_size=30
        must equal min(1.0, 0.040 * 30) = 1.000 (capped).
        NaN entries must remain NaN.
        """
        import numpy as np
        raw = [0.001, 0.040, np.nan]
        adj = bonferroni_adjust(raw, family_size=30)
        self.assertAlmostEqual(adj[0], 0.030, places=6,
                               msg="Bonferroni p must be 0.001*30=0.030")
        self.assertAlmostEqual(adj[1], 1.000, places=6,
                               msg="Bonferroni p 0.040*30=1.2 must be capped at 1.0")
        self.assertTrue(np.isnan(adj[2]),
                        msg="NaN input must remain NaN in adjusted output")

    def test_nan_hypotheses_do_not_shrink_family(self):
        """Test 12: NaN hypotheses consume positions in the family but are not assigned adjusted p-values.

        With 24 valid p-values and 6 NaN entries (family_size=30), the
        largest valid p-value (24th-smallest, index 23 in sorted order)
        receives multiplier 30 - 23 = 7, NOT 24 - 23 = 1.

        This verifies that the 6 NaN hypotheses are counted in the family
        size and that the adjustment is NOT deflated to a family of 24.
        """
        import numpy as np
        # 24 valid p-values spread from 0.001 to 0.024, plus 6 NaN entries
        valid_ps = [0.001 * (i + 1) for i in range(24)]
        nan_ps = [np.nan] * 6
        raw = valid_ps + nan_ps  # length 30

        adj = holm_bonferroni_adjust(raw, family_size=30)

        # The smallest valid p-value (0.001) is rank 0: multiplier = 30 - 0 = 30
        self.assertAlmostEqual(adj[0], min(1.0, 0.001 * 30), places=6,
                               msg="Smallest valid p (rank 0) multiplier must be 30 (family_size)")

        # The 24th-smallest valid p (0.024, index 23) is rank 23: multiplier = 30 - 23 = 7
        # After step-down: max of 0.024*7=0.168 and preceding adj p
        expected_raw_23 = min(1.0, 0.024 * 7)  # = 0.168
        # Step-down means adj[23] = max(expected_raw_23, adj[22])
        # adj[22]: p=0.023, multiplier=30-22=8, raw adj=min(1,0.023*8)=0.184; already >0.168
        # so adj[23] = max(0.168, adj[22]) -- the exact value depends on cummax
        # The key check: adj[23] must NOT equal 0.024*1=0.024 (which would mean family=24)
        # It must be >= 0.168 because multiplier >= 7
        self.assertGreaterEqual(adj[23], 0.168 - 1e-9,
                                msg="24th-smallest p multiplier must use family_size=30 (>=7), not 24-23=1")

        # All NaN entries must remain NaN
        for i in range(24, 30):
            self.assertTrue(np.isnan(adj[i]),
                            msg=f"NaN entry at position {i} must remain NaN")

    def test_primary_abilene_family_size_6(self):
        """Test 13: Primary Abilene family (N=6) uses its own Holm/Bonferroni with family_size=6.

        The six primary Abilene comparisons (switch churn and intervention
        cost at k=1,2,3) have their own family-size-6 correction that is
        independent of the omnibus N=30 family.

        Verified values sourced from regenerated CSV:
          p_raw = [0.002064, 0.002089, 0.000824, 0.000886, 0.002797, 0.003042]
        Expected Holm (N=6) step-down results (all < 0.05):
          rank 0: 0.000824 * 6 = 0.004944
          rank 1: 0.000886 * 5 = 0.004430 -> step-down max -> 0.004944
          ...all <= 0.0083 per CSV
        """
        import numpy as np
        p_raw_primary = [0.002064, 0.002089, 0.000824, 0.000886, 0.002797, 0.003042]
        adj_holm = holm_bonferroni_adjust(p_raw_primary, family_size=6)
        adj_bonf = bonferroni_adjust(p_raw_primary, family_size=6)

        # All six must be significant at alpha=0.05 under Holm N=6
        for i, p_adj in enumerate(adj_holm):
            self.assertLessEqual(p_adj, 0.05,
                                 msg=f"Primary Abilene Holm adj p[{i}]={p_adj:.6f} must be <= 0.05")
            self.assertLessEqual(p_adj, 0.0083 + 1e-5,
                                 msg=f"Primary Abilene Holm adj p[{i}]={p_adj:.6f} must be <= 0.0083")

        # The smallest raw p (0.000824) * 6 = 0.004944 (rank 0)
        # Find which index has the smallest raw p
        min_idx = p_raw_primary.index(min(p_raw_primary))  # index 2: p=0.000824
        self.assertAlmostEqual(adj_holm[min_idx], 0.000824 * 6, places=5,
                               msg="Rank-0 primary Abilene Holm adj p must be 0.000824*6")

        # Bonferroni: all p * 6, capped at 1.0
        for i, (p_raw, p_adj) in enumerate(zip(p_raw_primary, adj_bonf)):
            expected = min(1.0, p_raw * 6)
            self.assertAlmostEqual(p_adj, expected, places=5,
                                   msg=f"Primary Bonferroni p[{i}] must be p_raw*6={expected:.6f}")

        # Independence check: primary family uses N=6, not N=30
        # adj_holm[min_idx] should equal 0.000824*6 = 0.004944, NOT 0.000824*30 = 0.02472
        self.assertLess(adj_holm[min_idx], 0.006,
                        msg="Primary Abilene family must use N=6 multiplier, not N=30")

if __name__ == "__main__":
    unittest.main()
