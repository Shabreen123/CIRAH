"""
CIRAH: CIHF & Counterfactual Ablation Diagnostic
Phase 3 — Determine whether CIHF and CF scores genuinely influence candidate rankings.

Measures per-candidate:
  - Individual objective terms (C_I, C_D, C_L, R_post, Psi)
  - Full objective J(a) under each ablation mode
  - Whether the argmin changes between modes
  - Whether candidate rankings differ

Also tests targeted stress scenarios designed to expose CIHF and CF contributions.
"""

import os
import sys
import numpy as np
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


def evaluate_candidate_terms(
    topology: nx.DiGraph,
    candidates: List[Dict[str, Any]],
    causal_engine: StructuralCausalModel,
    healing_propagator: HealingFieldPropagator,
    risk_module: RiskAssessmentModule,
    cost_model: InterventionCostModel,
    flows: List[Dict[str, Any]],
    telemetry: Dict[Tuple[str, str], Dict[str, float]],
    target_flow: Dict[str, Any],
    pre_node_stress: Dict[str, float],
    optimizer: RiskConstrainedOptimizer,
    is_myopic: bool = False,
    is_causal: bool = True,
    cihf_mode: str = "cihf",
) -> List[Dict[str, Any]]:
    """Evaluate all candidates and return per-candidate term breakdown."""
    records = []
    for cand in candidates:
        cf_res = causal_engine.evaluate_counterfactual(
            cand, flows, telemetry, is_myopic=is_myopic
        )
        risk_res = risk_module.evaluate_risk(topology, cand, cf_res, target_flow)
        cost_res = cost_model.compute_intervention_cost(
            old_path=target_flow.get("current_path"),
            new_path=cand.get("path"),
            flow_demand_mbps=target_flow["bandwidth_mbps"],
            is_reassigned=(cand["type"] != "no_change"),
        )

        post_node_stress = {}
        for n in topology.nodes():
            out_loss = sum(
                cf_res["cf_link_losses"].get((n, v), 0.0)
                for v in topology.successors(n)
            )
            post_node_stress[n] = float(out_loss)

        h_field = healing_propagator.construct_healing_field(
            cand, pre_node_stress, post_node_stress, scoring_mode=cihf_mode
        )
        psi = healing_propagator.compute_aggregate_healing_gain(h_field)

        t_out = cf_res["flow_outcomes"].get(target_flow["flow_id"], {})
        actual_lat = t_out.get("latency", 1e5)
        sla_lat = max(1.0, target_flow["sla_max_latency_ms"])
        norm_c_l = float((actual_lat / sla_lat) + (max(0.0, actual_lat - sla_lat) / optimizer.c_l_ref))

        sigma_r = 0.08 * risk_res["R_post"]
        r_robust = risk_res["R_post"] + (optimizer.z_alpha * sigma_r)

        norm_c_i = cost_res["C_I"] / optimizer.c_i_ref
        norm_c_d = cost_res["C_D"] / optimizer.c_d_ref

        if not is_causal:
            cand_p = cand.get("path", [])
            corr_penalty = 0.0
            if cand_p and len(cand_p) > 1:
                for i in range(len(cand_p) - 1):
                    e = (cand_p[i], cand_p[i + 1])
                    t_loss = telemetry.get(e, {}).get("loss", 0.0)
                    corr_penalty += t_loss * 2.5
            norm_r = (risk_res["R_post"] + corr_penalty) / optimizer.r_max
        else:
            norm_r = risk_res["R_post"] / optimizer.r_max
        norm_psi = psi / optimizer.psi_ref

        j_score = (
            optimizer.lambda_I * norm_c_i
            + optimizer.lambda_D * norm_c_d
            + optimizer.lambda_L * norm_c_l
            + optimizer.beta * norm_r
            - optimizer.gamma * norm_psi
        )

        # Also compute J with gamma=0 (noCIHF) to see the difference
        j_no_cihf = (
            optimizer.lambda_I * norm_c_i
            + optimizer.lambda_D * norm_c_d
            + optimizer.lambda_L * norm_c_l
            + optimizer.beta * norm_r
            # gamma * norm_psi term removed
        )

        records.append({
            "action_id": cand["action_id"],
            "type": cand["type"],
            "path_len": len(cand.get("path", [])),
            "throttle": cand.get("throttle_ratio", 1.0),
            "C_I": cost_res["C_I"],
            "C_D": cost_res["C_D"],
            "norm_c_i": norm_c_i,
            "norm_c_d": norm_c_d,
            "norm_c_l": norm_c_l,
            "R_post": risk_res["R_post"],
            "norm_r": norm_r,
            "Psi": psi,
            "norm_psi": norm_psi,
            "gamma_psi_term": optimizer.gamma * norm_psi,
            "J_full": j_score,
            "J_no_cihf": j_no_cihf,
            "connected": t_out.get("connected", False),
            "sla_met": t_out.get("sla_met", False),
            "cf_loads": cf_res["cf_link_loads"],
        })
    return records


def run_diagnostic_scenario(
    topo_name: str = "abilene",
    seed: int = 5000,
    scenario_desc: str = "",
    inject_fn=None,
):
    """Run a single diagnostic scenario and compare ablation modes."""
    print(f"\n{'='*70}")
    print(f"DIAGNOSTIC SCENARIO: {scenario_desc}")
    print(f"Topology: {topo_name}, Seed: {seed}")
    print(f"{'='*70}")

    G = get_topology(topo_name)
    fg = FaultGenerator(rng_seed=seed)
    flows = generate_traffic_demands(G, num_flows=8, rng_seed=seed)
    for f in flows:
        f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")

    target_flow = flows[0]

    G_fault = G.copy()
    if inject_fn:
        G_fault = inject_fn(G_fault, fg, flows, target_flow)

    telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.04)

    pre_node_stress = {}
    for n in G_fault.nodes():
        out_loss = sum(telemetry.get((n, v), {}).get("loss", 0.0) for v in G_fault.successors(n))
        pre_node_stress[n] = float(out_loss)

    # Set up components
    causal_engine = StructuralCausalModel(G_fault)
    healing_propagator = HealingFieldPropagator(G_fault, sigma=1.5)
    risk_module = RiskAssessmentModule(r_max_default=35.0)
    cost_model = InterventionCostModel()
    optimizer = RiskConstrainedOptimizer(
        lambda_I=1.0, lambda_D=0.5, lambda_L=0.3, beta=1.2, gamma=0.8, r_max=35.0
    )

    # Diagnose causal faults
    active_paths = [f["current_path"] for f in flows if f.get("current_path")]
    posteriors = causal_engine.diagnose_causal_faults(telemetry, active_paths)

    # Generate candidates
    candidates = optimizer.generate_candidate_interventions(
        G_fault, target_flow, posteriors, k_paths=6
    )

    print(f"\nGenerated {len(candidates)} candidates:")
    for c in candidates:
        print(f"  {c['action_id']:20s} type={c['type']:15s} path_len={len(c.get('path',[]))} throttle={c.get('throttle_ratio',1.0)}")

    # Evaluate under full CIRAH (CF + CIHF)
    full_records = evaluate_candidate_terms(
        G_fault, candidates, causal_engine, healing_propagator, risk_module,
        cost_model, flows, telemetry, target_flow, pre_node_stress, optimizer,
        is_myopic=False, is_causal=True, cihf_mode="cihf"
    )

    # Evaluate under noCIHF (CF + no healing field)
    no_cihf_records = evaluate_candidate_terms(
        G_fault, candidates, causal_engine, healing_propagator, risk_module,
        cost_model, flows, telemetry, target_flow, pre_node_stress, optimizer,
        is_myopic=False, is_causal=True, cihf_mode="none"
    )

    # Evaluate under noCF (myopic + CIHF)
    no_cf_records = evaluate_candidate_terms(
        G_fault, candidates, causal_engine, healing_propagator, risk_module,
        cost_model, flows, telemetry, target_flow, pre_node_stress, optimizer,
        is_myopic=True, is_causal=True, cihf_mode="cihf"
    )

    # Print per-candidate comparison
    print(f"\n{'Candidate':22s} | {'C_I':>6s} {'C_D':>6s} {'C_L':>6s} | {'R_post':>7s} {'Psi':>6s} | "
          f"{'γΨ term':>7s} | {'J_full':>7s} {'J_noCIHF':>8s} {'J_noCF':>7s} | {'Conn':>4s} {'SLA':>4s}")
    print("-" * 110)
    for i, (fr, nr_cf, nr_nc) in enumerate(zip(full_records, no_cf_records, no_cihf_records)):
        print(f"{fr['action_id']:22s} | {fr['C_I']:6.2f} {fr['C_D']:6.2f} {fr['norm_c_l']:6.3f} | "
              f"{fr['R_post']:7.2f} {fr['Psi']:6.3f} | {fr['gamma_psi_term']:7.4f} | "
              f"{fr['J_full']:7.4f} {nr_nc['J_full']:8.4f} {nr_cf['J_full']:7.4f} | "
              f"{'Y' if fr['connected'] else 'N':>4s} {'Y' if fr['sla_met'] else 'N':>4s}")

    # Check if rankings change
    full_rank = sorted(range(len(full_records)), key=lambda i: full_records[i]["J_full"])
    no_cihf_rank = sorted(range(len(no_cihf_records)), key=lambda i: no_cihf_records[i]["J_full"])
    no_cf_rank = sorted(range(len(no_cf_records)), key=lambda i: no_cf_records[i]["J_full"])

    print(f"\nRanking (by J, lowest first):")
    print(f"  Full CIRAH:     {[full_records[i]['action_id'] for i in full_rank[:5]]}")
    print(f"  noCIHF (γ=0):   {[no_cihf_records[i]['action_id'] for i in no_cihf_rank[:5]]}")
    print(f"  noCF (myopic):  {[no_cf_records[i]['action_id'] for i in no_cf_rank[:5]]}")

    # Check if top candidate changes
    full_best = full_rank[0]
    no_cihf_best = no_cihf_rank[0]
    no_cf_best = no_cf_rank[0]

    print(f"\n  Best candidate (full):     {full_records[full_best]['action_id']} (J={full_records[full_best]['J_full']:.6f})")
    print(f"  Best candidate (noCIHF):   {no_cihf_records[no_cihf_best]['action_id']} (J={no_cihf_records[no_cihf_best]['J_full']:.6f})")
    print(f"  Best candidate (noCF):     {no_cf_records[no_cf_best]['action_id']} (J={no_cf_records[no_cf_best]['J_full']:.6f})")

    if full_best == no_cihf_best:
        print(f"  >> CIHF does NOT change the selected action (same best: {full_records[full_best]['action_id']})")
    else:
        print(f"  >> CIHF CHANGES the selected action ({full_records[full_best]['action_id']} -> {no_cihf_records[no_cihf_best]['action_id']})")

    if full_best == no_cf_best:
        print(f"  >> CF does NOT change the selected action (same best: {full_records[full_best]['action_id']})")
    else:
        print(f"  >> CF CHANGES the selected action ({full_records[full_best]['action_id']} -> {no_cf_records[no_cf_best]['action_id']})")

    # Measure the spread of Psi across candidates
    psi_values = [r["Psi"] for r in full_records]
    psi_range = max(psi_values) - min(psi_values) if psi_values else 0
    psi_std = np.std(psi_values) if psi_values else 0
    print(f"\n  Psi spread across candidates: min={min(psi_values):.4f} max={max(psi_values):.4f} "
          f"range={psi_range:.4f} std={psi_std:.4f}")

    # Measure CF vs myopic load differences
    print(f"\n  CF vs Myopic counterfactual load comparison (top 3 candidates):")
    for i in full_rank[:3]:
        cf_loads = full_records[i]["cf_loads"]
        myopic_loads = no_cf_records[i]["cf_loads"]
        max_diff = max(abs(cf_loads.get(e, 0) - myopic_loads.get(e, 0)) for e in cf_loads)
        print(f"    {full_records[i]['action_id']:22s}: max_load_diff={max_diff:.2f} Mbps")

    return full_records, no_cihf_records, no_cf_records


def scenario_severe_cut_with_capacity_stress(G, fg, flows, target_flow):
    """Scenario A: Severe link cut + capacity reduction on alternative paths."""
    curr_p = target_flow["current_path"]
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G[e[0]][e[1]]["status"] = 0
        G[e[0]][e[1]]["loss"] = 100.0
        if G.has_edge(e[1], e[0]):
            G[e[1]][e[0]]["status"] = 0
            G[e[1]][e[0]]["loss"] = 100.0
    # Reduce capacity on alternative paths to stress routing
    for u, v in G.edges():
        if fg.rng.random() < 0.25:
            G[u][v]["capacity"] = 30.0
    return G


def scenario_cross_traffic_loss_spike(G, fg, flows, target_flow):
    """Scenario B: Link cut + cross-traffic loss on a healthy detour link."""
    curr_p = target_flow["current_path"]
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G[e[0]][e[1]]["status"] = 0
        G[e[0]][e[1]]["loss"] = 100.0
        if G.has_edge(e[1], e[0]):
            G[e[1]][e[0]]["status"] = 0
            G[e[1]][e[0]]["loss"] = 100.0
    # Induce loss on a healthy alternative link
    for e in G.edges():
        if G[e[0]][e[1]].get("status", 1) == 1 and e not in [tuple(curr_p[i:i+2]) for i in range(len(curr_p)-1)]:
            G[e[0]][e[1]]["loss"] = 3.8
            break
    return G


def scenario_capacity_bottleneck(G, fg, flows, target_flow):
    """Scenario C: Link cut + capacity bottleneck on shortest alternative."""
    curr_p = target_flow["current_path"]
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G[e[0]][e[1]]["status"] = 0
        G[e[0]][e[1]]["loss"] = 100.0
        if G.has_edge(e[1], e[0]):
            G[e[1]][e[0]]["status"] = 0
            G[e[1]][e[0]]["loss"] = 100.0
    target_demand = target_flow["bandwidth_mbps"]
    for u, v in G.edges():
        if u == curr_p[0] and v != curr_p[1]:
            G[u][v]["capacity"] = max(10.0, target_demand * 0.70)
    return G


def scenario_multi_hop_stress_gradient(G, fg, flows, target_flow):
    """Scenario D: Multi-hop stress gradient designed to expose CIHF spatial diffusion.

    Creates a stress gradient across the topology by inducing varying loss levels
    on links at different distances from the failure point. This should make the
    Laplacian diffusion term differentiate candidates based on spatial stress relief.
    """
    curr_p = target_flow["current_path"]
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G[e[0]][e[1]]["status"] = 0
        G[e[0]][e[1]]["loss"] = 100.0
        if G.has_edge(e[1], e[0]):
            G[e[1]][e[0]]["status"] = 0
            G[e[1]][e[0]]["loss"] = 100.0

    # Create a stress gradient: links near the failure have higher loss
    failed_node = curr_p[0]
    for u, v in G.edges():
        if G[u][v].get("status", 1) == 1:
            # Distance from failure point
            try:
                dist_u = nx.shortest_path_length(G.to_undirected(), failed_node, u)
            except nx.NetworkXNoPath:
                dist_u = 10
            loss_level = max(0.0, 8.0 - dist_u * 1.5)  # Decreasing loss with distance
            if loss_level > 0:
                G[u][v]["loss"] = max(G[u][v].get("loss", 0.0), loss_level)
    return G


def scenario_high_cross_traffic_displacement(G, fg, flows, target_flow):
    """Scenario E: Link cut + high cross-traffic that should be displaced by rerouting.

    Sets high bandwidth on multiple flows whose paths share links with candidate
    reroute paths. This should make counterfactual load computation differ from myopic.
    """
    curr_p = target_flow["current_path"]
    if len(curr_p) > 1:
        e = (curr_p[0], curr_p[1])
        G[e[0]][e[1]]["status"] = 0
        G[e[0]][e[1]]["loss"] = 100.0
        if G.has_edge(e[1], e[0]):
            G[e[1]][e[0]]["status"] = 0
            G[e[1]][e[0]]["loss"] = 100.0

    # Increase bandwidth on other flows to create capacity pressure
    for f in flows:
        if f["flow_id"] != target_flow["flow_id"]:
            f["bandwidth_mbps"] = 40.0  # High demand

    # Reduce capacity on shared links to amplify displacement effects
    for u, v in G.edges():
        if G[u][v].get("status", 1) == 1:
            G[u][v]["capacity"] = 80.0  # Tight capacity

    return G


def run_multi_seed_analysis(num_seeds=20):
    """Run multiple seeds and count how often CIHF/CF changes the selected action."""
    print(f"\n{'#'*70}")
    print(f"MULTI-SEED ANALYSIS: {num_seeds} seeds per scenario")
    print(f"{'#'*70}")

    scenarios = [
        ("Severe cut + capacity stress", scenario_severe_cut_with_capacity_stress),
        ("Cross-traffic loss spike", scenario_cross_traffic_loss_spike),
        ("Capacity bottleneck on alternative", scenario_capacity_bottleneck),
        ("Multi-hop stress gradient", scenario_multi_hop_stress_gradient),
        ("High cross-traffic displacement", scenario_high_cross_traffic_displacement),
    ]

    for scenario_name, inject_fn in scenarios:
        cihf_changed = 0
        cf_changed = 0
        total_valid = 0
        psi_spreads = []

        for seed in range(5000, 5000 + num_seeds):
            try:
                full_recs, no_cihf_recs, no_cf_recs = run_diagnostic_scenario(
                    "abilene", seed, scenario_name, inject_fn
                )
                total_valid += 1

                full_rank = sorted(range(len(full_recs)), key=lambda i: full_recs[i]["J_full"])
                no_cihf_rank = sorted(range(len(no_cihf_recs)), key=lambda i: no_cihf_recs[i]["J_full"])
                no_cf_rank = sorted(range(len(no_cf_recs)), key=lambda i: no_cf_recs[i]["J_full"])

                if full_rank[0] != no_cihf_rank[0]:
                    cihf_changed += 1
                if full_rank[0] != no_cf_rank[0]:
                    cf_changed += 1

                psi_vals = [r["Psi"] for r in full_recs]
                psi_spreads.append(max(psi_vals) - min(psi_vals))
            except Exception as e:
                print(f"  Seed {seed} failed: {e}")

        print(f"\n  [{scenario_name}]")
        print(f"    Valid scenarios: {total_valid}/{num_seeds}")
        print(f"    CIHF changed selection: {cihf_changed}/{total_valid} ({100*cihf_changed/max(1,total_valid):.1f}%)")
        print(f"    CF changed selection:   {cf_changed}/{total_valid} ({100*cf_changed/max(1,total_valid):.1f}%)")
        print(f"    Mean Psi spread: {np.mean(psi_spreads) if psi_spreads else 0:.4f}")
        print(f"    Max Psi spread:  {max(psi_spreads) if psi_spreads else 0:.4f}")


if __name__ == "__main__":
    # Single detailed scenario first
    run_diagnostic_scenario("abilene", 5000, "Severe cut + capacity stress",
                            scenario_severe_cut_with_capacity_stress)

    run_diagnostic_scenario("abilene", 5000, "Multi-hop stress gradient (CIHF-targeted)",
                            scenario_multi_hop_stress_gradient)

    run_diagnostic_scenario("abilene", 5000, "High cross-traffic displacement (CF-targeted)",
                            scenario_high_cross_traffic_displacement)

    # Multi-seed analysis across all scenarios
    run_multi_seed_analysis(num_seeds=20)
