"""
CIRAH: Closed-Loop Autonomous Network Self-Healing Controller
Implements the 6-stage lifecycle and all distinct ablation variants:
  - 'full': Full CIRAH (SCM + Counterfactuals + CIHF + Robust Risk Constraints + Intervention Cost)
  - 'no_causal': Heuristic correlation-based diagnosis without Bayesian SCM
  - 'no_cf': Myopic path evaluation without Pearl counterfactual traffic displacement
  - 'no_cihf': Zero healing-field contribution (gamma = 0, no graph diffusion)
  - 'no_risk': Unconstrained risk optimization (R_max = inf, beta = 0)
  - 'no_interv': Zero intervention cost penalty (lambda_I = 0)
"""

import networkx as nx
import numpy as np
import time
from typing import Dict, List, Tuple, Any, Optional

from src.causal_engine import StructuralCausalModel
from src.healing_field import HealingFieldPropagator
from src.cost_model import InterventionCostModel
from src.risk_assessment import RiskAssessmentModule
from src.optimizer import RiskConstrainedOptimizer

class CIRAHController:
    """
    Autonomous Self-Healing Controller supporting full CIRAH and all formal ablations.
    """

    def __init__(self, 
                 topology: nx.DiGraph,
                 mode: str = "full",
                 lambda_I: float = 1.0,
                 lambda_D: float = 0.5,
                 lambda_L: float = 0.3,
                 beta: float = 1.2,
                 gamma: float = 0.8,
                 tau: float = 0.75,
                 r_max: float = 35.0):
        self.topology = topology
        self.mode = mode
        self.name = f"CIRAH" if mode == "full" else f"CIRAH-{mode}"

        self.causal_engine = StructuralCausalModel(topology)
        self.healing_propagator = HealingFieldPropagator(topology, sigma=1.5)
        self.cost_model = InterventionCostModel()
        self.risk_module = RiskAssessmentModule(r_max_default=r_max)

        # Configure specific ablation parameters
        eff_lambda_I = 0.0 if mode == "no_interv" else lambda_I
        eff_beta = 0.0 if mode == "no_risk" else beta
        eff_gamma = 0.0 if mode == "no_cihf" else gamma
        cihf_mode = "none" if mode == "no_cihf" else "cihf"
        self.enforce_risk = (mode != "no_risk")
        self.is_myopic = (mode == "no_cf")

        self.optimizer = RiskConstrainedOptimizer(
            lambda_I=eff_lambda_I,
            lambda_D=lambda_D,
            lambda_L=lambda_L,
            beta=eff_beta,
            gamma=eff_gamma,
            tau=tau,
            r_max=r_max,
            cihf_mode=cihf_mode
        )

    def execute_self_healing_cycle(self,
                                   current_topology: nx.DiGraph,
                                   flows: List[Dict[str, Any]],
                                   telemetry: Dict[Tuple[str, str], Dict[str, float]],
                                   target_flow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a closed-loop self-healing cycle.
        """
        start_time = time.perf_counter()

        # Step 1: Pre-Intervention Node Stress Measurement
        pre_node_stress = {}
        for n in current_topology.nodes():
            out_loss = sum(telemetry.get((n, v), {}).get("loss", 0.0) for v in current_topology.successors(n))
            pre_node_stress[n] = float(out_loss)

        # Step 2: Fault Diagnosis (Bayesian SCM vs Brittle Correlation)
        active_paths = [f["current_path"] for f in flows if f.get("current_path")]
        
        if self.mode == "no_causal":
            # CIRAH-noCausal ablation: simple correlation/threshold rule
            # Marks links faulty strictly on raw telemetry loss > 3% or status == 0
            # Easily confused by downstream congestion on healthy links
            causal_posteriors = {}
            for e in current_topology.edges():
                t = telemetry.get(e, {})
                raw_l = t.get("loss", 0.0)
                st = t.get("status", 1)
                is_bad = 1.0 if (raw_l > 3.0 or st == 0) else 0.0
                causal_posteriors[e] = {
                    "P_fault": is_bad,
                    "P_severed": 1.0 if st == 0 else 0.0,
                    "P_degraded": 1.0 if (raw_l > 3.0 and st == 1) else 0.0,
                    "P_normal": 1.0 - is_bad
                }
        else:
            # Full Bayesian SCM Diagnosis with 3-state normalization
            causal_posteriors = self.causal_engine.diagnose_causal_faults(
                telemetry=telemetry,
                active_paths=active_paths,
                telemetry_noise_std=0.04
            )

        # Step 3: Candidate Generation
        candidates = self.optimizer.generate_candidate_interventions(
            topology=current_topology,
            target_flow=target_flow,
            causal_fault_posteriors=causal_posteriors,
            k_paths=6
        )

        # Step 4 & 5: Counterfactual Evaluation & Constrained Action Selection
        opt_result = self.optimizer.optimize(
            candidates=candidates,
            causal_engine=self.causal_engine,
            healing_propagator=self.healing_propagator,
            risk_module=self.risk_module,
            cost_model=self.cost_model,
            all_flows=flows,
            current_telemetry=telemetry,
            target_flow=target_flow,
            pre_node_stress=pre_node_stress,
            is_myopic=self.is_myopic,
            enforce_risk_constraint=self.enforce_risk
        )

        decision_latency_ms = (time.perf_counter() - start_time) * 1000.0
        best_rec = opt_result["best_record"]
        selected_act = opt_result["selected_action"]

        # Step 6: Post-Intervention Verification
        cost_info = best_rec["cost_res"]
        risk_info = best_rec["risk_res"]
        cf_info = best_rec["cf_res"]
        target_res = cf_info["flow_outcomes"].get(target_flow["flow_id"], {})

        # Recovery time = detection (15ms) + decision latency + switch rule commit delay
        recovery_time_ms = 15.0 + decision_latency_ms + cost_info["disruption_time_ms"]
        if not target_res.get("connected", False):
            recovery_time_ms = 2000.0 # Standard unreachability timeout

        return {
            "method": self.name,
            "mode": self.mode,
            "action_id": selected_act["action_id"],
            "type": selected_act["type"],
            "path": selected_act["path"],
            "flow_id": target_flow["flow_id"],
            "success": bool(target_res.get("connected", False) and target_res.get("sla_met", False)),
            "connected": bool(target_res.get("connected", False)),
            "sla_met": bool(target_res.get("sla_met", False)),
            "latency_ms": float(target_res.get("latency", 1e4)),
            "loss_pct": float(target_res.get("loss", 100.0)),
            "risk_post": float(risk_info["R_post"]),
            "is_risk_feasible": bool(risk_info["is_risk_feasible"]),
            "constraint_violation": bool(risk_info["R_post"] > self.optimizer.r_max),
            "flow_mods": cost_info["flow_mods"],
            "switches_modified": cost_info["switches_modified"],
            "links_changed": cost_info["links_changed"],
            "ctrl_messages": cost_info["ctrl_messages"],
            "intervention_cost": cost_info["C_I"],
            "disruption_cost": cost_info["C_D"],
            "recovery_time_ms": float(recovery_time_ms),
            "decision_latency_ms": float(decision_latency_ms),
            "healing_psi": float(best_rec["psi"]),
            "fallback_triggered": opt_result["fallback_triggered"],
            "partition_detected": opt_result["partition_detected"]
        }
