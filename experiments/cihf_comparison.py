"""
CIRAH: CIHF Controlled Comparison Experiment (Phase C)

Compares 6 scoring modes under paired scenarios:
1. cihf: Original Laplacian diffusion
2. none: Zero field (ablation)
3. local_only: Raw impulse, no diffusion
4. centrality: Betweenness-weighted
5. congestion: Utilization-only (no diffusion)
6. csrf: Counterfactual stress-reduction field (proposed)

Uses both standard (wide capacity) and tight-capacity scenarios.
Independent evaluation via StandardizedEvaluator (not the selection score).
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topologies import get_topology, generate_traffic_demands
from src.causal_engine import StructuralCausalModel
from src.healing_field import HealingFieldPropagator
from src.cost_model import InterventionCostModel
from src.risk_assessment import RiskAssessmentModule
from src.optimizer import RiskConstrainedOptimizer
from src.fault_generator import FaultGenerator
from src.controller_sim import CIRAHController
from src.evaluator import StandardizedEvaluator

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(RESULTS_DIR, exist_ok=True)

SCORING_MODES = [
    ("cihf", "Laplacian diffusion"),
    ("none", "No field (ablation)"),
    ("local_only", "Local impulse only"),
    ("centrality", "Betweenness-weighted"),
    ("congestion", "Utilization-only"),
    ("csrf", "Counterfactual stress-reduction"),
]


def make_scenario(
    G: nx.DiGraph, fg: FaultGenerator, flows: List[Dict], target_flow: Dict,
    scenario_type: str
) -> nx.DiGraph:
    """Create a fault scenario on the topology."""
    G_fault = G.copy()
    curr_p = target_flow["current_path"]

    # Always sever the first edge of the target flow's current path
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G_fault[e[0]][e[1]]["status"] = 0
        G_fault[e[0]][e[1]]["loss"] = 100.0
        if G_fault.has_edge(e[1], e[0]):
            G_fault[e[1]][e[0]]["status"] = 0
            G_fault[e[1]][e[0]]["loss"] = 100.0

    if scenario_type == "standard":
        # Standard scenario: wide capacity, low cross-traffic
        # (original ablation campaign conditions)
        for u, v in G_fault.edges():
            if fg.rng.random() < 0.25:
                G_fault[u][v]["capacity"] = 30.0

    elif scenario_type == "tight_capacity":
        # Tight capacity: all links at 80 Mbps, high cross-traffic
        for u, v in G_fault.edges():
            if G_fault[u][v].get("status", 1) == 1:
                G_fault[u][v]["capacity"] = 80.0
        for f in flows:
            if f["flow_id"] != target_flow["flow_id"]:
                f["bandwidth_mbps"] = 40.0

    elif scenario_type == "mixed_stress":
        # Mixed stress: varying capacity reduction + loss on some links
        for u, v in G_fault.edges():
            if G_fault[u][v].get("status", 1) == 1:
                if fg.rng.random() < 0.3:
                    G_fault[u][v]["capacity"] = max(20.0, 100.0 * fg.rng.uniform(0.2, 0.5))
                if fg.rng.random() < 0.15:
                    G_fault[u][v]["loss"] = fg.rng.uniform(2.0, 8.0)

    elif scenario_type == "multi_fault":
        # Multi-fault: 2 additional link cuts
        edges = list(G_fault.edges())
        for _ in range(2):
            idx = fg.rng.integers(0, len(edges))
            u, v = edges[idx]
            if G_fault[u][v].get("status", 1) == 1:
                G_fault[u][v]["status"] = 0
                G_fault[u][v]["loss"] = 100.0
                if G_fault.has_edge(v, u):
                    G_fault[v][u]["status"] = 0
                    G_fault[v][u]["loss"] = 100.0

    return G_fault


def run_cihf_comparison(
    topologies=["abilene"],
    scenario_types=["standard", "tight_capacity", "mixed_stress", "multi_fault"],
    num_runs=30,
    gamma_values=[0.8],
):
    """
    Run controlled comparison of CIHF scoring modes.
    For each topology, scenario, seed, and gamma, evaluate all 6 scoring modes.
    """
    all_records = []

    for topo_name in topologies:
        G = get_topology(topo_name)
        evaluator = StandardizedEvaluator(G, r_max=35.0)

        for scenario_type in scenario_types:
            for gamma_val in gamma_values:
                for run_idx in range(num_runs):
                    seed = 7000 + run_idx * 37 + hash(scenario_type) % 1000
                    fg = FaultGenerator(rng_seed=seed)

                    # Generate flows
                    flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
                    for f in flows:
                        f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")
                    target_flow = flows[0]

                    # Create scenario
                    G_fault = make_scenario(G, fg, flows, target_flow, scenario_type)
                    telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.04)

                    # Track selected actions for disagreement analysis
                    selected_actions = {}

                    for mode_key, mode_desc in SCORING_MODES:
                        # Create controller with this scoring mode
                        ctrl = CIRAHController(
                            G_fault, mode="full",
                            gamma=gamma_val, r_max=35.0,
                            cihf_mode=mode_key
                        )

                        t0 = time.perf_counter()
                        res = ctrl.execute_self_healing_cycle(
                            G_fault, flows, telemetry, target_flow
                        )
                        dt_ms = (time.perf_counter() - t0) * 1000.0

                        # Also evaluate with the independent evaluator
                        # (uses the same SCM but measures outcomes independently)
                        ind_eval = evaluator.evaluate_action(
                            f"CIHF-{mode_key}",
                            res,  # The selected action result
                            flows, telemetry, target_flow,
                            decision_latency_ms=dt_ms
                        )

                        selected_actions[mode_key] = res.get("action_id", "unknown")

                        all_records.append({
                            "topology": topo_name,
                            "scenario": scenario_type,
                            "gamma": gamma_val,
                            "run_id": run_idx,
                            "seed": seed,
                            "scoring_mode": mode_key,
                            "scoring_desc": mode_desc,
                            "selected_action": res.get("action_id", "unknown"),
                            "success": int(res["success"]),
                            "connected": int(res["connected"]),
                            "sla_met": int(res["sla_met"]),
                            "latency_ms": res["latency_ms"],
                            "loss_pct": res["loss_pct"],
                            "risk_post": res["risk_post"],
                            "risk_robust": res.get("risk_robust", res["risk_post"]),
                            "switches_modified": res["switches_modified"],
                            "intervention_cost": res["intervention_cost"],
                            "recovery_time_ms": res["recovery_time_ms"],
                            "decision_latency_ms": dt_ms,
                            "healing_psi": res.get("healing_psi", 0.0),
                            "fallback_triggered": int(res.get("fallback_triggered", False)),
                            # Independent evaluation metrics
                            "ind_success": int(ind_eval["success"]),
                            "ind_risk_post": ind_eval["risk_post"],
                            "ind_recovery_time_ms": ind_eval["recovery_time_ms"],
                        })

                    # Record action-selection disagreement
                    actions = list(selected_actions.values())
                    unique_actions = len(set(actions))

    df = pd.DataFrame(all_records)

    # Add disagreement column
    # For each (topology, scenario, gamma, run_id), compute whether all modes agree
    grouped = df.groupby(["topology", "scenario", "gamma", "run_id"])
    df["all_modes_agree"] = df.groupby(["topology", "scenario", "gamma", "run_id"])["selected_action"].transform(
        lambda x: 1 if len(set(x)) == 1 else 0
    )

    out_path = os.path.join(RESULTS_DIR, "cihf_comparison_results.csv")
    df.to_csv(out_path, index=False)
    print(f"CIHF comparison: {len(df)} records saved to {out_path}")
    return df


def run_gamma_sensitivity(
    topologies=["abilene"],
    scenario_types=["tight_capacity", "mixed_stress"],
    num_runs=20,
    gamma_values=[0.0, 0.4, 0.8, 1.6, 3.2, 6.4],
):
    """
    Phase D: Gamma sensitivity analysis.
    Tests whether increasing gamma makes CIHF modes change candidate selection
    and whether any changes translate to improved independent outcomes.
    """
    all_records = []

    for topo_name in topologies:
        G = get_topology(topo_name)
        evaluator = StandardizedEvaluator(G, r_max=35.0)

        for scenario_type in scenario_types:
            for gamma_val in gamma_values:
                for run_idx in range(num_runs):
                    seed = 8000 + run_idx * 41 + int(gamma_val * 100)
                    fg = FaultGenerator(rng_seed=seed)

                    flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
                    for f in flows:
                        f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")
                    target_flow = flows[0]

                    G_fault = make_scenario(G, fg, flows, target_flow, scenario_type)
                    telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.04)

                    for mode_key, mode_desc in [("cihf", "Laplacian"), ("csrf", "CSRF"), ("none", "None")]:
                        ctrl = CIRAHController(
                            G_fault, mode="full",
                            gamma=gamma_val, r_max=35.0,
                            cihf_mode=mode_key
                        )
                        res = ctrl.execute_self_healing_cycle(
                            G_fault, flows, telemetry, target_flow
                        )

                        all_records.append({
                            "topology": topo_name,
                            "scenario": scenario_type,
                            "gamma": gamma_val,
                            "run_id": run_idx,
                            "seed": seed,
                            "scoring_mode": mode_key,
                            "selected_action": res.get("action_id", "unknown"),
                            "success": int(res["success"]),
                            "switches_modified": res["switches_modified"],
                            "intervention_cost": res["intervention_cost"],
                            "risk_post": res["risk_post"],
                            "healing_psi": res.get("healing_psi", 0.0),
                            "latency_ms": res["latency_ms"],
                            "loss_pct": res["loss_pct"],
                        })

    df = pd.DataFrame(all_records)
    df["all_modes_agree"] = df.groupby(["topology", "scenario", "gamma", "run_id"])["selected_action"].transform(
        lambda x: 1 if len(set(x)) == 1 else 0
    )

    out_path = os.path.join(RESULTS_DIR, "cihf_gamma_sensitivity.csv")
    df.to_csv(out_path, index=False)
    print(f"Gamma sensitivity: {len(df)} records saved to {out_path}")
    return df


def analyze_results(df: pd.DataFrame, label: str = ""):
    """Print summary statistics for the comparison."""
    print(f"\n{'='*80}")
    print(f"CIHF COMPARISON ANALYSIS {label}")
    print(f"{'='*80}")

    # 1. Action-selection agreement
    agree = df.groupby(["topology", "scenario"])["all_modes_agree"].mean().reset_index()
    print("\nAction-selection agreement rate (all 6 modes select same action):")
    print(agree.to_string(index=False))

    # 2. Per-mode outcome summary
    print("\nPer-mode outcome summary (averaged across all scenarios):")
    summary = df.groupby("scoring_mode").agg(
        success_mean=("success", "mean"),
        switches_mean=("switches_modified", "mean"),
        cost_mean=("intervention_cost", "mean"),
        risk_mean=("risk_post", "mean"),
        psi_mean=("healing_psi", "mean"),
        latency_mean=("latency_ms", "mean"),
    ).reset_index()
    print(summary.to_string(index=False))

    # 3. Per-scenario per-mode summary
    print("\nPer-scenario per-mode success rate:")
    pivot = df.groupby(["scenario", "scoring_mode"])["success"].mean().unstack()
    print(pivot.to_string())

    # 4. Disagreement cases
    disagree = df[df["all_modes_agree"] == 0]
    if len(disagree) > 0:
        print(f"\nDisagreement cases: {len(disagree.groupby(['topology','scenario','run_id']))} runs")
        for (topo, scen, rid), group in disagree.groupby(["topology", "scenario", "run_id"]):
            actions = group[["scoring_mode", "selected_action", "success", "healing_psi"]].values
            print(f"  {topo}/{scen}/run={rid}:")
            for row in actions:
                print(f"    {row[0]:15s} -> {row[1]:20s} success={row[2]} psi={row[3]:.4f}")
    else:
        print("\nNo disagreement cases found.")


if __name__ == "__main__":
    print("Phase C: CIHF Controlled Comparison")
    print("=" * 80)

    # Main comparison: 4 scenario types × 30 runs × 6 modes
    df = run_cihf_comparison(
        topologies=["abilene"],
        scenario_types=["standard", "tight_capacity", "mixed_stress", "multi_fault"],
        num_runs=30,
        gamma_values=[0.8],
    )
    analyze_results(df, "(gamma=0.8)")

    # Phase D: Gamma sensitivity
    print("\n\nPhase D: Gamma Sensitivity Analysis")
    print("=" * 80)
    df_gamma = run_gamma_sensitivity(
        topologies=["abilene"],
        scenario_types=["tight_capacity", "mixed_stress"],
        num_runs=20,
        gamma_values=[0.0, 0.4, 0.8, 1.6, 3.2, 6.4],
    )

    # Analyze gamma sensitivity
    print("\nGamma sensitivity: disagreement rate by gamma")
    gamma_disagree = df_gamma.groupby(["scenario", "gamma"])["all_modes_agree"].mean().reset_index()
    print(gamma_disagree.to_string(index=False))

    print("\nGamma sensitivity: mean success by gamma and mode")
    gamma_success = df_gamma.groupby(["gamma", "scoring_mode"])["success"].mean().unstack()
    print(gamma_success.to_string())

    print("\nGamma sensitivity: mean Psi by gamma and mode")
    gamma_psi = df_gamma.groupby(["gamma", "scoring_mode"])["healing_psi"].mean().unstack()
    print(gamma_psi.to_string())
