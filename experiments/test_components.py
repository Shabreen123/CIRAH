"""
Quick unit verification of CIRAH components.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.topologies import get_topology, generate_traffic_demands
from src.fault_generator import FaultGenerator
from src.causal_engine import StructuralCausalModel
from src.healing_field import HealingFieldPropagator
from src.cost_model import InterventionCostModel
from src.risk_assessment import RiskAssessmentModule
from src.optimizer import RiskConstrainedOptimizer
from src.baselines import StaticSP, DynamicSP, BackupPathRecovery, RiskAwareRouting, MinChangeHeuristic
from src.controller_sim import CIRAHController

def test_pipeline():
    print("Testing Abilene topology...")
    G = get_topology("abilene")
    print(f"Abilene nodes: {len(G.nodes())}, edges: {len(G.edges())}")

    flows = generate_traffic_demands(G, num_flows=6, rng_seed=42)
    # Set initial shortest paths
    import networkx as nx
    for f in flows:
        f["current_path"] = nx.shortest_path(G, f["src"], f["dst"], weight="latency")

    fg = FaultGenerator(rng_seed=123)
    # Inject single link failure
    target_link = ("NYCM", "CHIN")
    G_fault, meta = fg.inject_single_link_failure(G, target_edge=target_link)
    telemetry = fg.generate_noisy_telemetry(G_fault, noise_std=0.03)

    target_flow = flows[0]
    print(f"Target flow: {target_flow['flow_id']}, src: {target_flow['src']}, dst: {target_flow['dst']}")
    print(f"Original path: {target_flow['current_path']}")

    # Test Baselines
    static_sp = StaticSP()
    dyn_sp = DynamicSP()
    backup_sp = BackupPathRecovery(G)
    risk_sp = RiskAwareRouting()
    minchange_sp = MinChangeHeuristic()

    print("\n--- Testing Baselines ---")
    res_static = static_sp.compute_recovery_action(G_fault, flows, telemetry, target_flow)
    print(f"Static-SP Action: {res_static['action_id']}, Path: {res_static['path']}")

    res_dyn = dyn_sp.compute_recovery_action(G_fault, flows, telemetry, target_flow)
    print(f"Dynamic-SP Action: {res_dyn['action_id']}, Path: {res_dyn['path']}")

    res_backup = backup_sp.compute_recovery_action(G_fault, flows, telemetry, target_flow)
    print(f"Backup-Path Action: {res_backup['action_id']}, Path: {res_backup['path']}")

    # Test CIRAH
    print("\n--- Testing CIRAH Controller ---")
    cirah = CIRAHController(G, mode="full", lambda_I=1.0, beta=1.2, r_max=35.0)
    res_cirah = cirah.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
    print(f"CIRAH Result: Success={res_cirah['success']}, Action={res_cirah['action_id']}, Path={res_cirah['path']}")
    print(f"Cost: C_I={res_cirah['intervention_cost']}, Switches Mod={res_cirah['switches_modified']}, Links Changed={res_cirah['links_changed']}")
    print(f"Risk Post: {res_cirah['risk_post']} (Feasible={res_cirah['is_risk_feasible']}), Recovery Time: {res_cirah['recovery_time_ms']:.2f} ms")

    # Test Ablation
    cirah_no_causal = CIRAHController(G, mode="no_causal")
    res_no_causal = cirah_no_causal.execute_self_healing_cycle(G_fault, flows, telemetry, target_flow)
    print(f"CIRAH-noCausal Result: Success={res_no_causal['success']}, Risk Post={res_no_causal['risk_post']}")

    print("\nAll component tests PASSED successfully!")

if __name__ == "__main__":
    test_pipeline()
