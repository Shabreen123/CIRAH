"""
CIRAH: Comprehensive Empirical Evaluation Campaign Runner
Executes 5 major experimental campaigns across paired seeds:
1. Multi-Failure Severity Sweep (k = 0, 1, 2, 3, 4) on Abilene and GEANT
2. Capacity & Load Stress Sweep (rho = 0.1, 0.3, 0.5, 0.7, 0.9)
3. Telemetry Uncertainty & Noise Sensitivity (sigma = 0.0 to 0.30)
4. Full Component-Level Ablation Study (CIRAH vs no-Causal, no-Risk, no-Interv)
5. Hyperparameter Sensitivity Analysis (gamma and R_max sweeps)

Saves all raw and aggregated records to results/*.csv
"""

import os
import sys
import time
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topologies import get_topology, generate_traffic_demands
from src.fault_generator import FaultGenerator
from src.evaluator import StandardizedEvaluator
from src.baselines import (
    StaticSP, DynamicSP, BackupPathRecovery, RiskAwareRouting, MinChangeHeuristic
)
from src.controller_sim import CIRAHController

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_failure_severity_campaign(topologies=["abilene", "geant"], num_runs=50, k_values=[0, 1, 2, 3, 4]):
    """
    Campaign 1: Multi-Link Failure Severity Sweep across diverse topologies.
    """
    print(f"\n=======================================================")
    print(f"Starting Campaign 1: Multi-Link Failure Severity Sweep")
    print(f"Topologies: {topologies}, Runs per level: {num_runs}, k in {k_values}")
    print(f"=======================================================")

    records = []

    for topo_name in topologies:
        base_G = get_topology(topo_name)
        evaluator = StandardizedEvaluator(base_G, r_max=35.0)

        # Baseline controllers
        static_sp = StaticSP()
        dynamic_sp = DynamicSP()
        backup_sp = BackupPathRecovery(base_G)
        risk_sp = RiskAwareRouting()
        minchange_sp = MinChangeHeuristic()

        # CIRAH controllers
        cirah_full = CIRAHController(base_G, mode="full", lambda_I=1.0, beta=1.2, r_max=35.0)
        cirah_no_causal = CIRAHController(base_G, mode="no_causal", lambda_I=1.0, beta=1.2, r_max=35.0)
        cirah_no_risk = CIRAHController(base_G, mode="no_risk", lambda_I=1.0, beta=0.0, r_max=35.0)
        cirah_no_interv = CIRAHController(base_G, mode="no_interv", lambda_I=0.0, beta=1.2, r_max=35.0)

        controllers = [
            ("Static-SP", static_sp),
            ("Dynamic-SP", dynamic_sp),
            ("Backup-Path", backup_sp),
            ("Risk-Aware", risk_sp),
            ("MinChange-SP", minchange_sp),
            ("CIRAH-noCausal", cirah_no_causal),
            ("CIRAH-noRisk", cirah_no_risk),
            ("CIRAH-noInterv", cirah_no_interv),
            ("CIRAH", cirah_full),
        ]

        for k in k_values:
            print(f"  [{topo_name.upper()}] Evaluating k={k} simultaneous failures across {num_runs} paired runs...")
            for run_idx in range(num_runs):
                seed = 1000 + run_idx * 17 + k * 101
                fg = FaultGenerator(rng_seed=seed)

                # Generate flows and establish initial shortest paths
                flows = generate_traffic_demands(base_G, num_flows=8, rng_seed=seed)
                for f in flows:
                    f["current_path"] = nx.shortest_path(base_G, f["src"], f["dst"], weight="latency")

                # Inject k simultaneous failures
                if k == 0:
                    G_fault = base_G.copy()
                else:
                    G_fault, _ = fg.inject_multi_link_failure(base_G, k=k)

                telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

                # Pick an affected flow if any, else pick first flow
                target_flow = flows[0]
                for f in flows:
                    p = f["current_path"]
                    if any(G_fault.has_edge(p[i], p[i+1]) and G_fault[p[i]][p[i+1]].get("status", 1) == 0 for i in range(len(p)-1)):
                        target_flow = f
                        break

                # Evaluate all controllers under IDENTICAL network state and seed
                for c_name, ctrl in controllers:
                    t0 = time.perf_counter()
                    if hasattr(ctrl, "execute_self_healing_cycle"):
                        res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
                    else:
                        act = ctrl.compute_recovery_action(G_fault, flows, telemetry, target_flow)
                        dt_ms = (time.perf_counter() - t0) * 1000.0
                        res = evaluator.evaluate_action(c_name, act, flows, telemetry, target_flow, decision_latency_ms=dt_ms)

                    rec = {
                        "campaign": "severity_sweep",
                        "topology": topo_name,
                        "k_failures": k,
                        "run_id": run_idx,
                        "seed": seed,
                        "method": c_name,
                        "success": int(res["success"]),
                        "connected": int(res["connected"]),
                        "latency_ms": res["latency_ms"],
                        "loss_pct": res["loss_pct"],
                        "risk_post": res["risk_post"],
                        "constraint_violation": int(res["constraint_violation"]),
                        "flow_mods": res["flow_mods"],
                        "switches_modified": res["switches_modified"],
                        "links_changed": res["links_changed"],
                        "ctrl_messages": res["ctrl_messages"],
                        "intervention_cost": res["intervention_cost"],
                        "disruption_cost": res["disruption_cost"],
                        "recovery_time_ms": res["recovery_time_ms"],
                        "decision_latency_ms": res["decision_latency_ms"]
                    }
                    records.append(rec)

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "exp1_failure_severity.csv")
    df.to_csv(out_path, index=False)
    print(f"Campaign 1 completed. Saved {len(df)} records to {out_path}")
    return df

def run_stress_sweep_campaign(topology_name="abilene", num_runs=50, stress_levels=[0.1, 0.3, 0.5, 0.7, 0.9]):
    """
    Campaign 2: Link Stress and Congestion Sweep (rho in [0.1, 0.9]).
    """
    print(f"\n=======================================================")
    print(f"Starting Campaign 2: Link Stress Sweep (rho in {stress_levels})")
    print(f"=======================================================")

    base_G = get_topology.get_topology(topology_name) if hasattr(get_topology, "get_topology") else get_topology(topology_name)
    evaluator = StandardizedEvaluator(base_G, r_max=35.0)

    static_sp = StaticSP()
    dynamic_sp = DynamicSP()
    backup_sp = BackupPathRecovery(base_G)
    risk_sp = RiskAwareRouting()
    cirah_full = CIRAHController(base_G, mode="full", lambda_I=1.0, beta=1.2, r_max=35.0)
    cirah_no_interv = CIRAHController(base_G, mode="no_interv", lambda_I=0.0, beta=1.2, r_max=35.0)

    controllers = [
        ("Static-SP", static_sp),
        ("Dynamic-SP", dynamic_sp),
        ("Backup-Path", backup_sp),
        ("Risk-Aware", risk_sp),
        ("CIRAH-noInterv", cirah_no_interv),
        ("CIRAH", cirah_full),
    ]

    records = []

    for rho in stress_levels:
        print(f"  Evaluating stress level rho={rho} across {num_runs} paired runs...")
        for run_idx in range(num_runs):
            seed = 2000 + run_idx * 13 + int(rho * 100)
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(base_G, num_flows=8, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(base_G, f["src"], f["dst"], weight="latency")

            # Apply stress condition: degrade capacity on random core links and add delay/loss spikes
            G_stress = base_G.copy()
            for u, v in G_stress.edges():
                if fg.rng.random() < rho * 0.5:
                    degrade = max(0.15, 1.0 - rho * 0.8)
                    G_stress[u][v]["capacity"] *= degrade
                    G_stress[u][v]["latency"] *= (1.0 + rho * 2.5)
                    G_stress[u][v]["loss"] = float(rho * 12.0)

            telemetry = fg.generate_noisy_telemetry(G_stress, noise_std=0.03)
            target_flow = flows[0]

            for c_name, ctrl in controllers:
                t0 = time.perf_counter()
                if hasattr(ctrl, "execute_self_healing_cycle"):
                    res = ctrl.execute_self_healing_cycle(G_stress, flows, telemetry, target_flow)
                else:
                    act = ctrl.compute_recovery_action(G_stress, flows, telemetry, target_flow)
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    res = evaluator.evaluate_action(c_name, act, flows, telemetry, target_flow, decision_latency_ms=dt_ms)

                rec = {
                    "campaign": "stress_sweep",
                    "topology": topology_name,
                    "stress_rho": rho,
                    "run_id": run_idx,
                    "seed": seed,
                    "method": c_name,
                    "success": int(res["success"]),
                    "connected": int(res["connected"]),
                    "latency_ms": res["latency_ms"],
                    "loss_pct": res["loss_pct"],
                    "risk_post": res["risk_post"],
                    "constraint_violation": int(res["constraint_violation"]),
                    "flow_mods": res["flow_mods"],
                    "switches_modified": res["switches_modified"],
                    "links_changed": res["links_changed"],
                    "intervention_cost": res["intervention_cost"],
                    "recovery_time_ms": res["recovery_time_ms"]
                }
                records.append(rec)

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "exp2_stress_sweep.csv")
    df.to_csv(out_path, index=False)
    print(f"Campaign 2 completed. Saved {len(df)} records to {out_path}")
    return df

def run_telemetry_noise_campaign(num_runs=50, noise_levels=[0.0, 0.05, 0.10, 0.20, 0.30]):
    """
    Campaign 3: Telemetry Uncertainty & Noise Sensitivity.
    Compares Causal Bayesian diagnosis against Rule-Based heuristic diagnosis.
    """
    print(f"\n=======================================================")
    print(f"Starting Campaign 3: Telemetry Uncertainty & Noise Sensitivity")
    print(f"=======================================================")

    base_G = get_topology("abilene")
    evaluator = StandardizedEvaluator(base_G, r_max=35.0)

    dynamic_sp = DynamicSP()
    cirah_full = CIRAHController(base_G, mode="full", lambda_I=1.0, beta=1.2, r_max=35.0)
    cirah_no_causal = CIRAHController(base_G, mode="no_causal", lambda_I=1.0, beta=1.2, r_max=35.0)

    controllers = [
        ("Dynamic-SP", dynamic_sp),
        ("CIRAH-noCausal (Rule-Based)", cirah_no_causal),
        ("CIRAH (Causal SCM)", cirah_full),
    ]

    records = []

    for sigma_n in noise_levels:
        print(f"  Evaluating telemetry noise sigma={sigma_n} across {num_runs} paired runs...")
        for run_idx in range(num_runs):
            seed = 3000 + run_idx * 23 + int(sigma_n * 100)
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(base_G, num_flows=8, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(base_G, f["src"], f["dst"], weight="latency")

            # Sever 1 link and inject partial degradation on another
            G_fault, _ = fg.inject_single_link_failure(base_G)
            G_fault, _ = fg.inject_delay_loss_spike(G_fault, added_latency=30.0, loss_pct=15.0)

            # Generate telemetry corrupted by noise sigma_n
            telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=sigma_n)

            target_flow = flows[0]
            for f in flows:
                p = f["current_path"]
                if any(G_fault.has_edge(p[i], p[i+1]) and G_fault[p[i]][p[i+1]].get("status", 1) == 0 for i in range(len(p)-1)):
                    target_flow = f
                    break

            for c_name, ctrl in controllers:
                t0 = time.perf_counter()
                if hasattr(ctrl, "execute_self_healing_cycle"):
                    res = ctrl.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
                else:
                    act = ctrl.compute_recovery_action(G_fault, flows, telemetry, target_flow)
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    res = evaluator.evaluate_action(c_name, act, flows, telemetry, target_flow, decision_latency_ms=dt_ms)

                rec = {
                    "campaign": "telemetry_noise",
                    "noise_sigma": sigma_n,
                    "run_id": run_idx,
                    "seed": seed,
                    "method": c_name,
                    "success": int(res["success"]),
                    "latency_ms": res["latency_ms"],
                    "loss_pct": res["loss_pct"],
                    "risk_post": res["risk_post"],
                    "switches_modified": res["switches_modified"],
                    "intervention_cost": res["intervention_cost"]
                }
                records.append(rec)

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "exp3_telemetry_noise.csv")
    df.to_csv(out_path, index=False)
    print(f"Campaign 3 completed. Saved {len(df)} records to {out_path}")
    return df

def run_parameter_sensitivity_campaign(num_runs=40, gamma_values=[0.0, 0.5, 1.0, 2.0, 4.0, 8.0]):
    """
    Campaign 4: Hyperparameter Sensitivity for Gamma (Healing Field Weight).
    """
    print(f"\n=======================================================")
    print(f"Starting Campaign 4: Gamma Parameter Sensitivity Sweep")
    print(f"=======================================================")

    base_G = get_topology("abilene")
    records = []

    for gamma in gamma_values:
        print(f"  Evaluating gamma={gamma} across {num_runs} runs...")
        controller = CIRAHController(base_G, mode="full", lambda_I=1.0, beta=1.2, gamma=gamma, r_max=35.0)

        for run_idx in range(num_runs):
            seed = 4000 + run_idx * 19 + int(gamma * 10)
            fg = FaultGenerator(rng_seed=seed)

            flows = generate_traffic_demands(base_G, num_flows=8, rng_seed=seed)
            for f in flows:
                f["current_path"] = nx.shortest_path(base_G, f["src"], f["dst"], weight="latency")

            G_fault, _ = fg.inject_single_link_failure(base_G)
            telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

            target_flow = flows[0]
            for f in flows:
                p = f["current_path"]
                if any(G_fault.has_edge(p[i], p[i+1]) and G_fault[p[i]][p[i+1]].get("status", 1) == 0 for i in range(len(p)-1)):
                    target_flow = f
                    break

            res = controller.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)

            records.append({
                "campaign": "gamma_sweep",
                "gamma": gamma,
                "run_id": run_idx,
                "seed": seed,
                "success": int(res["success"]),
                "latency_ms": res["latency_ms"],
                "loss_pct": res["loss_pct"],
                "risk_post": res["risk_post"],
                "flow_mods": res["flow_mods"],
                "switches_modified": res["switches_modified"],
                "links_changed": res["links_changed"],
                "intervention_cost": res["intervention_cost"],
                "healing_psi": res["healing_psi"]
            })

    df = pd.DataFrame(records)
    out_path = os.path.join(RESULTS_DIR, "exp4_gamma_sensitivity.csv")
    df.to_csv(out_path, index=False)
    print(f"Campaign 4 completed. Saved {len(df)} records to {out_path}")
    return df

if __name__ == "__main__":
    t_start = time.time()
    run_failure_severity_campaign(topologies=["abilene", "geant"], num_runs=50, k_values=[0, 1, 2, 3, 4])
    run_stress_sweep_campaign(topology_name="abilene", num_runs=50, stress_levels=[0.1, 0.3, 0.5, 0.7, 0.9])
    run_telemetry_noise_campaign(num_runs=50, noise_levels=[0.0, 0.05, 0.10, 0.20, 0.30])
    run_parameter_sensitivity_campaign(num_runs=40, gamma_values=[0.0, 0.5, 1.0, 2.0, 4.0, 8.0])
    print(f"\nAll experimental campaigns executed in {time.time() - t_start:.2f} seconds.")
