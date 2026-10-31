"""
CIRAH: Revision 3 Completion Experiments

Addresses:
- Rev3-2: Counterfactual tight-capacity ablation (CF vs noCF under tight capacity)
- Rev3-5: Constrained minimum-change baseline comparison
- Rev3-6: Fat-tree topology experiments (scalability)
- Rev3-M2: Fault localization precision/recall/F1 evaluation
- Rev3-3: Risk threshold sensitivity analysis
- Rev3-S1: Exact run count reconciliation
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Tuple
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topologies import get_topology, generate_traffic_demands, create_abilene_topology
from src.causal_engine import StructuralCausalModel
from src.healing_field import HealingFieldPropagator
from src.cost_model import InterventionCostModel
from src.risk_assessment import RiskAssessmentModule
from src.optimizer import RiskConstrainedOptimizer
from src.fault_generator import FaultGenerator
from src.controller_sim import CIRAHController
from src.evaluator import StandardizedEvaluator
from src.baselines import (
    StaticSP, DynamicSP, BackupPathRecovery, RiskAwareRouting,
    MinChangeHeuristic, ConstrainedMinChangeOptimizer
)

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(RESULTS_DIR, exist_ok=True)


def create_fattree_topology(k=4):
    """Create a fat-tree topology with k=4 (20 switches, 48 links).
    Fat-tree k=4 has k^2/4 = 4 core, k^2 = 16 edge/aggregation = 20 total switches.
    """
    G = nx.DiGraph()
    cores = [f"core_{i}" for i in range((k//2)**2)]
    aggs = [f"agg_{i}" for i in range(k * k // 2)]
    edges = [f"edge_{i}" for i in range(k * k // 2)]
    hosts = [f"host_{i}" for i in range(k**3 // 4)]

    # Add nodes with attributes
    for n in cores:
        G.add_node(n, type="core", flow_table_capacity=16000, buffer_size=1000)
    for n in aggs:
        G.add_node(n, type="aggregation", flow_table_capacity=8000, buffer_size=500)
    for n in edges:
        G.add_node(n, type="edge", flow_table_capacity=4000, buffer_size=200)

    # Core to aggregation links
    pod_count = k
    cores_per_pod = (k // 2) ** 2
    aggs_per_pod = k // 2
    edges_per_pod = k // 2

    for pod in range(pod_count):
        pod_aggs = aggs[pod * aggs_per_pod:(pod + 1) * aggs_per_pod]
        pod_edges = edges[pod * edges_per_pod:(pod + 1) * edges_per_pod]

        # Core to aggregation
        for ci, core in enumerate(cores):
            ai = ci % aggs_per_pod
            agg = pod_aggs[ai]
            lat = 4.0 + (pod * 0.5)
            cap = 1000.0
            G.add_edge(core, agg, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)
            G.add_edge(agg, core, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)

        # Aggregation to edge
        for ai, agg in enumerate(pod_aggs):
            for ei, edge in enumerate(pod_edges):
                lat = 2.0
                cap = 500.0
                G.add_edge(agg, edge, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)
                G.add_edge(edge, agg, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)

    return G


# ============================================================
# Experiment 1: Tight-Capacity CF vs noCF Ablation (Rev3-2)
# ============================================================

def run_cf_tight_capacity_ablation(num_runs=50):
    """Compare CIRAH-full vs CIRAH-noCF under tight capacity constraints."""
    print("\n" + "=" * 70)
    print("Experiment 1: CF vs noCF under tight capacity (Rev3-2)")
    print("=" * 70)

    G = get_topology("abilene")
    evaluator = StandardizedEvaluator(G, r_max=35.0)

    records = []

    for run_idx in range(num_runs):
        seed = 9000 + run_idx * 29
        fg = FaultGenerator(rng_seed=seed)

        flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
        for f in flows:
            f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")
        target_flow = flows[0]

        # Tight capacity scenario
        G_fault = G.copy()
        curr_p = target_flow["current_path"]
        if len(curr_p) > 1:
            G_fault[curr_p[0]][curr_p[1]]["status"] = 0
            G_fault[curr_p[0]][curr_p[1]]["loss"] = 100.0
            if G_fault.has_edge(curr_p[1], curr_p[0]):
                G_fault[curr_p[1]][curr_p[0]]["status"] = 0
                G_fault[curr_p[1]][curr_p[0]]["loss"] = 100.0

        # Tight capacity on all surviving links
        for u, v in G_fault.edges():
            if G_fault[u][v].get("status", 1) == 1:
                G_fault[u][v]["capacity"] = 80.0

        # High cross-traffic
        for f in flows:
            if f["flow_id"] != target_flow["flow_id"]:
                f["bandwidth_mbps"] = 40.0

        telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.04)

        for mode_name, mode in [("CIRAH-full", "full"), ("CIRAH-noCF", "no_cf")]:
            ctrl = CIRAHController(G_fault, mode=mode, gamma=0.8, r_max=35.0)
            res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)

            records.append({
                "experiment": "cf_tight_capacity",
                "run_id": run_idx,
                "seed": seed,
                "method": mode_name,
                "selected_action": res.get("action_id", "unknown"),
                "success": int(res["success"]),
                "connected": int(res["connected"]),
                "sla_met": int(res["sla_met"]),
                "latency_ms": res["latency_ms"],
                "loss_pct": res["loss_pct"],
                "risk_post": res["risk_post"],
                "switches_modified": res["switches_modified"],
                "intervention_cost": res["intervention_cost"],
                "recovery_time_ms": res["recovery_time_ms"],
                "healing_psi": res.get("healing_psi", 0.0),
            })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "rev3_cf_tight_capacity.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} records to {out_path}")

    # Analysis
    full = df[df["method"] == "CIRAH-full"]
    nocf = df[df["method"] == "CIRAH-noCF"]

    action_disagree = (full.set_index("run_id")["selected_action"] !=
                       nocf.set_index("run_id")["selected_action"]).sum()

    print(f"\n  Action disagreement: {action_disagree}/{num_runs} ({100*action_disagree/num_runs:.0f}%)")
    print(f"  CIRAH-full:  success={full['success'].mean():.3f}, switches={full['switches_modified'].mean():.2f}, "
          f"risk={full['risk_post'].mean():.2f}")
    print(f"  CIRAH-noCF:  success={nocf['success'].mean():.3f}, switches={nocf['switches_modified'].mean():.2f}, "
          f"risk={nocf['risk_post'].mean():.2f}")

    # Paired tests
    paired = full.set_index("run_id")[["success", "switches_modified", "intervention_cost", "risk_post"]].join(
        nocf.set_index("run_id")[["success", "switches_modified", "intervention_cost", "risk_post"]],
        lsuffix="_full", rsuffix="_nocf"
    )

    for metric in ["switches_modified", "intervention_cost", "risk_post"]:
        diff = paired[f"{metric}_full"] - paired[f"{metric}_nocf"]
        if diff.std() > 1e-9:
            w_p = stats.wilcoxon(paired[f"{metric}_full"], paired[f"{metric}_nocf"]).pvalue
            ci = [diff.mean() - 1.96 * diff.std() / np.sqrt(len(diff)),
                  diff.mean() + 1.96 * diff.std() / np.sqrt(len(diff))]
            print(f"  {metric}: diff={diff.mean():.4f}, CI=[{ci[0]:.4f}, {ci[1]:.4f}], Wilcoxon p={w_p:.4f}")
        else:
            print(f"  {metric}: no variance in differences")

    return df


# ============================================================
# Experiment 2: Constrained MinChange Baseline (Rev3-5)
# ============================================================

def run_constrained_baseline_comparison(num_runs=50):
    """Compare CIRAH against constrained minimum-change baseline."""
    print("\n" + "=" * 70)
    print("Experiment 2: Constrained MinChange baseline (Rev3-5)")
    print("=" * 70)

    G = get_topology("abilene")
    evaluator = StandardizedEvaluator(G, r_max=35.0)

    controllers = [
        ("Static-SP", StaticSP()),
        ("Dynamic-SP", DynamicSP()),
        ("MinChange-SP", MinChangeHeuristic()),
        ("Constrained-MinChange", ConstrainedMinChangeOptimizer(G, r_max=35.0)),
        ("CIRAH", CIRAHController(G, mode="full", gamma=0.8, r_max=35.0)),
    ]

    records = []

    for k in [1, 2, 3]:
        for run_idx in range(num_runs):
            seed = 1000 + run_idx * 17 + k * 101
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")

            G_fault, _ = fg.inject_multi_link_failure(G, k=k)
            telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

            target_flow = flows[0]
            for f in flows:
                p = f["current_path"]
                if any(G_fault.has_edge(p[i], p[i+1]) and
                       G_fault[p[i]][p[i+1]].get("status", 1) == 0
                       for i in range(len(p)-1)):
                    target_flow = f
                    break

            for c_name, ctrl in controllers:
                t0 = time.perf_counter()
                if hasattr(ctrl, "execute_self_healing_cycle"):
                    res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
                else:
                    act = ctrl.compute_recovery_action(G_fault, flows, telemetry, target_flow)
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    res = evaluator.evaluate_action(c_name, act, flows, telemetry, target_flow,
                                                   decision_latency_ms=dt_ms)

                records.append({
                    "experiment": "constrained_baseline",
                    "k_failures": k,
                    "run_id": run_idx,
                    "seed": seed,
                    "method": c_name,
                    "success": int(res["success"]),
                    "connected": int(res.get("connected", res.get("success", 0))),
                    "latency_ms": res["latency_ms"],
                    "loss_pct": res.get("loss_pct", 0.0),
                    "risk_post": res["risk_post"],
                    "switches_modified": res["switches_modified"],
                    "intervention_cost": res["intervention_cost"],
                    "recovery_time_ms": res["recovery_time_ms"],
                })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "rev3_constrained_baseline.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} records to {out_path}")

    # Summary
    print("\n  Per-method summary:")
    summary = df.groupby("method").agg(
        success_mean=("success", "mean"),
        switches_mean=("switches_modified", "mean"),
        cost_mean=("intervention_cost", "mean"),
        risk_mean=("risk_post", "mean"),
    ).reset_index()
    print(summary.to_string(index=False))

    return df


# ============================================================
# Experiment 3: Fat-Tree Topology Scalability (Rev3-6)
# ============================================================

def run_fattree_experiments(num_runs=30):
    """Run experiments on fat-tree k=4 topology (20 switches)."""
    print("\n" + "=" * 70)
    print("Experiment 3: Fat-tree topology scalability (Rev3-6)")
    print("=" * 70)

    G = create_fattree_topology(k=4)
    print(f"  Fat-tree k=4: {len(G.nodes())} nodes, {len(G.edges())} directed edges")

    evaluator = StandardizedEvaluator(G, r_max=35.0)

    controllers = [
        ("Dynamic-SP", DynamicSP()),
        ("MinChange-SP", MinChangeHeuristic()),
        ("Constrained-MinChange", ConstrainedMinChangeOptimizer(G, r_max=35.0)),
        ("CIRAH", CIRAHController(G, mode="full", gamma=0.8, r_max=35.0)),
    ]

    records = []

    for k in [1, 2, 3]:
        for run_idx in range(num_runs):
            seed = 11000 + run_idx * 23 + k * 101
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(G, num_flows=12, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")

            G_fault, _ = fg.inject_multi_link_failure(G, k=k)
            telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

            target_flow = flows[0]
            for f in flows:
                p = f["current_path"]
                if any(G_fault.has_edge(p[i], p[i+1]) and
                       G_fault[p[i]][p[i+1]].get("status", 1) == 0
                       for i in range(len(p)-1)):
                    target_flow = f
                    break

            for c_name, ctrl in controllers:
                t0 = time.perf_counter()
                if hasattr(ctrl, "execute_self_healing_cycle"):
                    res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
                else:
                    act = ctrl.compute_recovery_action(G_fault, flows, telemetry, target_flow)
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    res = evaluator.evaluate_action(c_name, act, flows, telemetry, target_flow,
                                                   decision_latency_ms=dt_ms)

                records.append({
                    "experiment": "fattree_scalability",
                    "topology": "fattree_k4",
                    "num_nodes": len(G.nodes()),
                    "k_failures": k,
                    "run_id": run_idx,
                    "seed": seed,
                    "method": c_name,
                    "success": int(res["success"]),
                    "latency_ms": res["latency_ms"],
                    "risk_post": res["risk_post"],
                    "switches_modified": res["switches_modified"],
                    "intervention_cost": res["intervention_cost"],
                    "recovery_time_ms": res["recovery_time_ms"],
                })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "rev3_fattree_scalability.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} records to {out_path}")

    # Summary
    print("\n  Fat-tree per-method summary:")
    summary = df.groupby("method").agg(
        success_mean=("success", "mean"),
        switches_mean=("switches_modified", "mean"),
        risk_mean=("risk_post", "mean"),
        recovery_mean=("recovery_time_ms", "mean"),
    ).reset_index()
    print(summary.to_string(index=False))

    return df


# ============================================================
# Experiment 4: Fault Localization Evaluation (Rev3-M2)
# ============================================================

def run_fault_localization_evaluation(num_runs=100):
    """Evaluate Bayesian fault localization precision/recall/F1."""
    print("\n" + "=" * 70)
    print("Experiment 4: Fault localization precision/recall/F1 (Rev3-M2)")
    print("=" * 70)

    G = get_topology("abilene")

    records = []

    for run_idx in range(num_runs):
        seed = 12000 + run_idx * 31
        fg = FaultGenerator(rng_seed=seed)

        # Inject known faults
        k = 1 + (run_idx % 3)  # k=1,2,3 cycling
        G_fault, meta = fg.inject_multi_link_failure(G, k=k)

        # Ground truth: which edges are actually severed
        true_severed = set()
        for u, v in G_fault.edges():
            if G_fault[u][v].get("status", 1) == 0:
                true_severed.add((u, v))

        true_degraded = set()
        for u, v in G_fault.edges():
            if G_fault[u][v].get("loss", 0.0) > 3.0 and G_fault[u][v].get("status", 1) == 1:
                true_degraded.add((u, v))

        # Generate telemetry
        telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.04)

        # Run Bayesian diagnosis
        scm = StructuralCausalModel(G_fault)
        active_paths = []
        flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
        for f in flows:
            f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")
            active_paths.append(f["current_path"])

        posteriors = scm.diagnose_causal_faults(telemetry, active_paths, telemetry_noise_std=0.04)

        # Classify: P_severed > 0.5 → predicted severed; P_degraded > 0.5 → predicted degraded
        for edge, post in posteriors.items():
            pred_severed = post["P_severed"] > 0.5
            pred_degraded = post["P_degraded"] > 0.5
            pred_normal = post["P_normal"] > 0.5

            is_severed = edge in true_severed
            is_degraded = edge in true_degraded
            is_normal = not is_severed and not is_degraded

            records.append({
                "run_id": run_idx,
                "k_failures": k,
                "edge": f"{edge[0]}-{edge[1]}",
                "true_state": 2 if is_severed else (1 if is_degraded else 0),
                "pred_state": 2 if pred_severed else (1 if pred_degraded else 0),
                "P_normal": post["P_normal"],
                "P_degraded": post["P_degraded"],
                "P_severed": post["P_severed"],
            })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "rev3_fault_localization.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} edge evaluations to {out_path}")

    # Compute precision/recall/F1 for each state
    for state_name, state_val in [("Normal", 0), ("Degraded", 1), ("Severed", 2)]:
        tp = int(((df["true_state"] == state_val) & (df["pred_state"] == state_val)).sum())
        fp = int(((df["true_state"] != state_val) & (df["pred_state"] == state_val)).sum())
        fn = int(((df["true_state"] == state_val) & (df["pred_state"] != state_val)).sum())

        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(1e-9, precision + recall)

        print(f"  {state_name}: TP={tp}, FP={fp}, FN={fn}, "
              f"Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")

    # Overall accuracy
    accuracy = (df["true_state"] == df["pred_state"]).mean()
    print(f"  Overall accuracy: {accuracy:.3f}")

    return df


# ============================================================
# Experiment 5: Risk Threshold Sensitivity (Rev3-3)
# ============================================================

def run_risk_threshold_sensitivity(num_runs=30):
    """Test sensitivity to R_max values."""
    print("\n" + "=" * 70)
    print("Experiment 5: Risk threshold sensitivity (Rev3-3)")
    print("=" * 70)

    G = get_topology("abilene")
    evaluator = StandardizedEvaluator(G, r_max=35.0)

    r_max_values = [10.0, 20.0, 35.0, 50.0, 100.0]
    records = []

    for r_max in r_max_values:
        for run_idx in range(num_runs):
            seed = 13000 + run_idx * 37 + int(r_max * 10)
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")

            G_fault, _ = fg.inject_multi_link_failure(G, k=2)
            telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

            target_flow = flows[0]
            for f in flows:
                p = f["current_path"]
                if any(G_fault.has_edge(p[i], p[i+1]) and
                       G_fault[p[i]][p[i+1]].get("status", 1) == 0
                       for i in range(len(p)-1)):
                    target_flow = f
                    break

            ctrl = CIRAHController(G_fault, mode="full", gamma=0.8, r_max=r_max)
            res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)

            records.append({
                "experiment": "risk_sensitivity",
                "r_max": r_max,
                "run_id": run_idx,
                "seed": seed,
                "success": int(res["success"]),
                "risk_post": res["risk_post"],
                "risk_robust": res.get("risk_robust", res["risk_post"]),
                "constraint_violation": int(res.get("constraint_violation", False)),
                "switches_modified": res["switches_modified"],
                "intervention_cost": res["intervention_cost"],
                "fallback_triggered": int(res.get("fallback_triggered", False)),
            })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "rev3_risk_sensitivity.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} records to {out_path}")

    # Summary
    print("\n  Per-R_max summary:")
    summary = df.groupby("r_max").agg(
        success_mean=("success", "mean"),
        violation_rate=("constraint_violation", "mean"),
        fallback_rate=("fallback_triggered", "mean"),
        risk_mean=("risk_post", "mean"),
        switches_mean=("switches_modified", "mean"),
    ).reset_index()
    print(summary.to_string(index=False))

    return df


# ============================================================
# Run Count Reconciliation (Rev3-S1)
# ============================================================

def reconcile_run_counts():
    """Compute exact run counts from all experiment campaigns."""
    print("\n" + "=" * 70)
    print("Run Count Reconciliation (Rev3-S1)")
    print("=" * 70)

    counts = {}

    # Campaign 1: Failure Severity
    # 2 topologies × 5 k_values × 50 runs × 6 methods = 3000
    counts["C1_failure_severity"] = 2 * 5 * 50 * 6

    # Campaign 2: Stress Sweep
    # 5 stress_levels × 50 runs × 4 methods = 1000
    counts["C2_stress_sweep"] = 5 * 50 * 4

    # Campaign 3: Telemetry Noise
    # 5 noise_levels × 50 runs × 3 methods = 750
    counts["C3_telemetry_noise"] = 5 * 50 * 3

    # Campaign 4: Ablation
    # 60 runs × 6 variants = 360
    counts["C4_ablation"] = 60 * 6

    # Campaign 5: Counterfactual Validation
    # 60 evaluations
    counts["C5_cf_validation"] = 60

    # Campaign 6: Latency Profiling
    # 2 topologies × 60 runs = 120
    counts["C6_latency_profiling"] = 2 * 60

    total = sum(counts.values())

    print("  Campaign breakdown:")
    for name, count in counts.items():
        print(f"    {name}: {count}")
    print(f"  TOTAL: {total}")

    # Verify against CSVs
    csv_counts = {}
    for csv_name, csv_file in [
        ("C1", "exp1_failure_severity.csv"),
        ("C2", "exp2_stress_sweep.csv"),
        ("C3", "exp3_telemetry_noise.csv"),
        ("C4", "exp4_rebuilt_ablations.csv"),
        ("C5", "exp5_counterfactual_validation.csv"),
    ]:
        path = os.path.join(RESULTS_DIR, csv_file)
        if os.path.exists(path):
            df = pd.read_csv(path)
            csv_counts[csv_name] = len(df)
            print(f"    {csv_name} CSV rows: {len(df)}")
        else:
            print(f"    {csv_name} CSV: NOT FOUND")

    print(f"\n  CSV total: {sum(csv_counts.values())}")
    print(f"  Manuscript claims: 'approximately 4,920' (now corrected to 'over 4,900')")
    print(f"  Actual total (all campaigns): {total}")

    return counts, total


if __name__ == "__main__":
    print("CIRAH Revision 3 Completion Experiments")
    print("=" * 70)

    # Run count reconciliation
    counts, total = reconcile_run_counts()

    # Experiment 1: CF tight-capacity ablation
    df1 = run_cf_tight_capacity_ablation(num_runs=50)

    # Experiment 2: Constrained baseline comparison
    df2 = run_constrained_baseline_comparison(num_runs=50)

    # Experiment 3: Fat-tree topology
    df3 = run_fattree_experiments(num_runs=30)

    # Experiment 4: Fault localization
    df4 = run_fault_localization_evaluation(num_runs=100)

    # Experiment 5: Risk threshold sensitivity
    df5 = run_risk_threshold_sensitivity(num_runs=30)

    print("\n" + "=" * 70)
    print("ALL REV3 EXPERIMENTS COMPLETE")
    print("=" * 70)
