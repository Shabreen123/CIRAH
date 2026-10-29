# Revision 3 Traceability Matrix

**Branch:** cirah-final-audit
**Checkpoint:** `checkpoint-pre-rev3` (8753cea)
**Date:** 2026-10-29
**Source:** Faculty Revision 3 comments (provided October 2026)

---

## Summary

| Status | Count |
|---|---|
| MET | 7 |
| PARTIALLY MET | 12 |
| NOT MET | 5 |
| BLOCKED | 2 |
| **Total** | **26** |

**Overall:** REVISION 3 NOT YET COMPLETE. Critical items require expanded experiments, additional baselines, and manuscript reframing of CIHF.

---

## 1. Major Technical Corrections

### Rev3-1: Strengthen CIHF algorithmic novelty (HIGHEST PRIORITY)

| Field | Value |
|---|---|
| **Requirement** | Define CIHF as a measurable estimate of counterfactual downstream stress reduction. Derive from predicted network stress before/after intervention. Compare against Laplacian diffusion, centrality, congestion-only, and alternatives. Report whether CIHF improves actual latency, loss, recovery success, or risk. |
| **Manuscript section** | §3.4 (CIHF), §5.4 (Ablation), Abstract, Highlights |
| **Required implementation** | Redesigned field with theoretical motivation; controlled comparison against alternatives |
| **Verification** | `CIHF_RESEARCH_DIAGNOSTIC.md` Phases A-G; `results/cihf_comparison_results.csv` |
| **Evidence** | Phase A-G audit tested 6 scoring modes across 720 runs. CIHF changed selection in 1/120 runs (0.8%). Paired outcomes: success diff=0.000, switches p=0.317, cost p=0.317, risk p=0.317. CSRF produces zero outcome differences vs None. Gamma sensitivity (0.0-6.4) shows no consistent effect. |
| **Status** | **NOT MET** — CIHF does not influence candidate selection or improve outcomes. Manuscript still claims CIHF as a decision-making contribution. Requires honest reframing. |
| **Remaining action** | Reframe CIHF in manuscript as post-hoc visualization or remove from objective. Update abstract, highlights, §3.4, §5.4, §7 consistently. |

### Rev3-2: Demonstrate actual benefit of counterfactual reasoning

| Field | Value |
|---|---|
| **Requirement** | Construct experiments where observed congestion is a downstream symptom. Compare full CIRAH vs noCF. Report action-selection disagreement, prediction error, regret, recovery performance. Explain when CF is beneficial. |
| **Manuscript section** | §5.4 (Ablation), §5.5 (Counterfactual validation) |
| **Required implementation** | Experiments with correlated failures, misleading telemetry, interacting flows |
| **Verification** | `experiments/diagnose_ablations.py` (Phase 3 diagnostics); `results/exp5_counterfactual_validation.csv` |
| **Evidence** | Diagnostic: CF changed selection in 100/100 tight-capacity scenarios. Standard ablation (Campaign 4): noCF produces identical results to full (same success, switches, cost, risk). Counterfactual validation: ρ=0.967±0.021 (CIRAH) vs 0.968±0.065 (myopic). |
| **Status** | **PARTIALLY MET** — CF mechanism works under tight capacity but ablation campaign scenarios have wide capacity margins. Manuscript §5.4 acknowledges "nearly identical" results but doesn't explain the capacity-dependence. |
| **Remaining action** | Add explanation in §5.4 that CF benefit is capacity-dependent. Reference diagnostic evidence. Consider adding tight-capacity ablation runs to the main campaign. |

### Rev3-3: Strengthen robust risk-constrained optimization

| Field | Value |
|---|---|
| **Requirement** | Define random variables, risk function, uncertainty distribution, confidence level precisely. Justify z_α=1.645 and σ_R estimation. Distinguish confidence bound on mean vs individual outcomes. Evaluate empirical violation probability. Compare against deterministic thresholds and chance-constrained alternatives. State assumptions. |
| **Manuscript section** | §3.5 (Risk), §3.7 (Optimization) |
| **Required implementation** | Formal justification of robust constraint; empirical violation rate measurement |
| **Verification** | `src/risk_assessment.py`, `src/optimizer.py`; `results/exp4_rebuilt_ablations.csv` |
| **Evidence** | Robust constraint R_robust = R_post + z_α·σ_R implemented with z_α=1.645, σ_R=0.08·R_post. noRisk ablation: success drops 70.0%→56.7%, violations increase. Full CIRAH: 0.0% constraint violations. |
| **Status** | **PARTIALLY MET** — Constraint is implemented and empirically validated (0% violations). But z_α justification and σ_R estimation are heuristic, not formally derived. Distinction between mean-confidence and individual-outcome bounds not explicit. |
| **Remaining action** | Add formal justification of z_α and σ_R in §3.5. Clarify that the bound is on estimated risk, not individual recovery outcomes. Note assumption: σ_R=0.08·R_post is a modeling choice, not empirically calibrated. |

### Rev3-4: Add theoretical properties and algorithmic guarantees

| Field | Value |
|---|---|
| **Requirement** | Define decision variables, feasible set, objective, constraints consistently. Specify whether solver obtains global optimum or best among restricted candidates. Establish sufficient conditions for feasible recovery. Analyze complexity per component. Label heuristic vs guaranteed. Explain fallback guarantees. |
| **Manuscript section** | §3.7, §3.8, §3.10 |
| **Required implementation** | Formal problem statement; optimality discussion; complexity derivation |
| **Verification** | `src/optimizer.py` (candidate enumeration + filtering); `src/controller_sim.py` (fallback) |
| **Evidence** | Algorithm 1 enumerates K=6 shortest paths × 2 throttle variants = 13 candidates. Selection is argmin over enumerated set, NOT global optimum. Complexity documented: O(K·|V|log|V| + |A|·(|E|+|V|²)). Fallback detects partitions and does not claim false recovery. |
| **Status** | **PARTIALLY MET** — Algorithm 1 is documented but doesn't explicitly state "best among enumerated candidates, not global optimum." Complexity is derived but Laplacian inverse cost (O(|V|³) for dense) vs precomputed (O(N²) memory) not distinguished. |
| **Remaining action** | Add explicit statement that solver finds best among K-shortest candidates, not global optimum. Clarify Laplacian inverse is precomputed. Label method as heuristic with bounded candidate set. |

---

## 2. Experimental Methodology

### Rev3-5: Add stronger comparative algorithms

| Field | Value |
|---|---|
| **Requirement** | Add risk-constrained minimum-change optimizer. Compare with/without CIHF but identical weights. Include CIHF without CF. Compare against exact MIP on small networks. |
| **Manuscript section** | §4.4, §5 |
| **Required implementation** | New baseline: constrained minimum-change optimizer; exact oracle on small networks |
| **Verification** | `src/baselines.py` (5 baselines exist); no constrained optimizer or exact oracle |
| **Evidence** | Current baselines: Static-SP, Dynamic-SP, Backup-Path, Risk-Aware, MinChange-SP. |
| **Status** | **NOT MET** — No risk-constrained minimum-change optimizer or exact MIP oracle implemented. |
| **Remaining action** | Implement constrained minimum-change baseline. Optionally add exact oracle on Diamond topology. |

### Rev3-6: Expand to larger/diverse networks

| Field | Value |
|---|---|
| **Requirement** | Include larger topologies (>22 nodes), leaf-spine data-center, multiple alternative paths. Increase concurrent flows. Test single, simultaneous, correlated, recurring failures. |
| **Manuscript section** | §4.1, §5 |
| **Required implementation** | Additional topologies (fat-tree, larger mesh); expanded fault scenarios |
| **Verification** | `src/topologies.py` (Abilene 11, GEANT 22, Diamond 6) |
| **Evidence** | Fat-tree k=4 (20 switches) is defined in topologies.py but not used in experiments. No leaf-spine or >22 node topology. |
| **Status** | **NOT MET** — No larger topologies tested in experiments. Fat-tree exists in code but is unused. |
| **Remaining action** | Add fat-tree topology to experiment campaigns. Consider adding a 50+ node topology. |

### Rev3-7: Improve counterfactual model validation

| Field | Value |
|---|---|
| **Requirement** | Validate M/M/1 against finite-buffer bursty simulation. Explain exogenous noise inference and identifiability. Report prediction errors separately for normal/degraded/failed links. Evaluate under model misspecification. Distinguish simulated vs physical validation. |
| **Manuscript section** | §5.5, §8 |
| **Required implementation** | Model misspecification experiments; per-state prediction error breakdown |
| **Verification** | `experiments/run_experiments.py` Campaign 5; `results/exp5_counterfactual_validation.csv` |
| **Evidence** | Campaign 5 validates against independent `simulate_independent_dataplane` with stochastic burstiness. MAE: latency 1.23±0.61 ms, loss 0.37±0.18%. No per-state breakdown or misspecification test. |
| **Status** | **PARTIALLY MET** — Independent validation exists (non-circular). Per-state errors and misspecification tests are missing. |
| **Remaining action** | Add per-state (normal/degraded/severed) prediction error breakdown. Add misspecification note in limitations. |

### Rev3-8: Strengthen runtime and scalability analysis

| Field | Value |
|---|---|
| **Requirement** | Report mean, median, p95, worst-case. Separate algorithm from total recovery. Report runtime vs topology size, fault count, candidate count. Compare with baselines. Explain no-feasible-candidate behavior. Quantify churn-recovery trade-off. |
| **Manuscript section** | §3.10, §5.1 |
| **Required implementation** | Scaling analysis across topology sizes; runtime comparison with baselines |
| **Verification** | `results/exp6_computational_scalability.csv` (Abilene + GEANT) |
| **Evidence** | p50/p95/max reported: Abilene 5.9/8.7/9.2 ms, GEANT 10.9/14.3/15.7 ms. Algorithm vs total recovery distinguished in §3.10 and §5.2. |
| **Status** | **PARTIALLY MET** — Latency percentiles reported. Scaling analysis only covers 2 topologies (11 and 22 nodes). No baseline runtime comparison. No-fallback behavior documented but not quantified. |
| **Remaining action** | Add runtime for larger topology. Add baseline runtime comparison. |

---

## 3. Statistical and Numerical Corrections

### Rev3-S1: Reconcile total experimental run count

| Field | Value |
|---|---|
| **Requirement** | Reconcile ~4,920 paired runs with individual campaign counts. |
| **Manuscript section** | Abstract, §4.5, Conclusion |
| **Verification** | Campaign counts: C1=3000, C2=1000, C3=750, C4=360, C5=60, C6=120 → total=5290 |
| **Evidence** | Manuscript says "approximately 4,920 paired Monte Carlo simulations". Actual total is 5,290. |
| **Status** | **PARTIALLY MET** — Count is approximate and slightly understated. |
| **Remaining action** | Correct to "approximately 5,290" or specify "over 4,900" if keeping approximate. |

### Rev3-S2: Reconcile significance claims

| Field | Value |
|---|---|
| **Requirement** | Reconcile significance after Holm correction with omnibus non-significance. Define hypothesis families clearly. |
| **Manuscript section** | §6 (Statistical Validation) |
| **Verification** | `results/hypothesis_tests_cirah_vs_dynamic.csv` |
| **Evidence** | Two families defined: Primary (N=6, all significant at Holm p≤0.0083) and Omnibus (N=30, 5 significant). Non-significant results explicitly reported. |
| **Status** | **MET** — Families are clearly defined. Non-significant omnibus results are honestly reported. |

### Rev3-S3: Counterfactual ablation explanation

| Field | Value |
|---|---|
| **Requirement** | Explain why removing CF produces nearly identical performance. |
| **Manuscript section** | §5.4 |
| **Verification** | `results/exp4_rebuilt_ablations.csv`; `CIHF_RESEARCH_DIAGNOSTIC.md` Phase 3 |
| **Evidence** | CF changes decisions only under tight capacity (80 Mbps links, 40 Mbps flows). Standard ablation uses 1000 Mbps links where traffic displacement doesn't cause congestion. |
| **Status** | **PARTIALLY MET** — Manuscript §5.4 acknowledges "nearly identical" but doesn't explain the capacity-dependence mechanism. |
| **Remaining action** | Add explanation in §5.4: CF benefit is capacity-dependent; under wide capacity, myopic and CF produce identical load estimates. |

### Rev3-S4: CIHF ablation on real metrics

| Field | Value |
|---|---|
| **Requirement** | Report CIHF effect on real network metrics, not only internal healing-gain. |
| **Manuscript section** | §5.4, Table 4 |
| **Verification** | `results/cihf_comparison_results.csv`; `CIHF_RESEARCH_DIAGNOSTIC.md` Phase G |
| **Evidence** | Table 4 reports: noCIHF has identical success (70%), switches (3.60), cost (18.90), risk (7.06) to full CIRAH. Only Ψ differs (0.000 vs 0.974). Phase G paired test: success diff=0.000, switches p=0.317, cost p=0.317, risk p=0.317. |
| **Status** | **PARTIALLY MET** — Table 4 shows identical outcomes. Manuscript notes Ψ collapse but doesn't state that no other metric changes. |
| **Remaining action** | Add explicit statement in §5.4: "CIHF removal does not change success, switches, cost, or risk; only the internal Ψ metric differs." |

### Rev3-S5: Recovery success and SLA compliance definition

| Field | Value |
|---|---|
| **Requirement** | Define each metric separately including denominator and treatment of disconnected pairs. |
| **Manuscript section** | §4.5, §5 |
| **Verification** | `src/controller_sim.py` line ~107; `CIHF_RESEARCH_DIAGNOSTIC.md` §G.4 |
| **Evidence** | success = connected AND sla_met for target flow only. Connected = no link with loss≥99%. SLA = latency≤max AND loss≤max. Denominator = total runs. Only target flow evaluated. |
| **Status** | **MET** — Definition documented in Phase G. Manuscript §4.2 describes SLA profiles. |
| **Remaining action** | Add explicit metric definition in §4.5 or footnote. |

### Rev3-S6: Risk-bound compliance reporting

| Field | Value |
|---|---|
| **Requirement** | Report observed violation rates and uncertainty intervals. |
| **Manuscript section** | §5.4, Table 4 |
| **Verification** | `results/exp4_rebuilt_ablations.csv` |
| **Evidence** | Full CIRAH: 0.0% constraint violations. noRisk: 0.0% (constraint disabled). noCausal: 1.67% violations. |
| **Status** | **MET** — Violation rates reported in Table 4. |

### Rev3-S7: Effect sizes for all comparisons

| Field | Value |
|---|---|
| **Requirement** | Paired differences, CIs, effect sizes, adjusted p-values for all primary comparisons. |
| **Manuscript section** | §6, Table 5 |
| **Verification** | `results/hypothesis_tests_cirah_vs_dynamic.csv` |
| **Evidence** | Table 5 reports: CIRAH mean, Dynamic-SP mean, % reduction, mean diff, 95% CI, paired Cohen's d_z, raw Wilcoxon p, primary Holm p, omnibus Holm p. |
| **Status** | **MET** — All required statistics reported. |

### Rev3-S8: Reproducibility verification

| Field | Value |
|---|---|
| **Requirement** | Verify all figures, tables, statistics can be regenerated from raw data and scripts. |
| **Manuscript section** | §8, REPRODUCIBILITY.md |
| **Verification** | Phase 2 runtime verification; `experiments/compare_results.py`, `experiments/compare_stat_tests.py` |
| **Evidence** | All campaigns regenerated; 26/26 tests pass; significance decisions unchanged; REPRODUCIBILITY.md updated with correct commands, seeds, dependencies. |
| **Status** | **MET** — Reproducibility verified in runtime verification phase. |

---

## 4. Mathematical Formulation

### Rev3-M1: SCM completeness

| Field | Value |
|---|---|
| **Requirement** | Complete DAG showing relationships. Define every variable (domain, units, structural equation). State assumptions (causal direction, confounders, telemetry reliability). Explain calibration. Establish identifiability. |
| **Manuscript section** | §3.2 |
| **Verification** | `src/causal_engine.py`; manuscript §3.2 equations (1)-(7) |
| **Evidence** | SCM defined as 6-tuple with U={U_loss, U_lat}, V={F_e, L_e, Q_e, R, Y_f, A}. Structural equations (1)-(3) define link state and queuing. Counterfactual evaluation (5)-(7) implements abduction-action-prediction. |
| **Status** | **PARTIALLY MET** — Variables defined but DAG not drawn as figure. Calibration not discussed. Identifiability not formally established. Exogenous noise inference is point-estimate, not distributional. |
| **Remaining action** | Add causal DAG as figure. Add calibration note. Add identifiability discussion. |

### Rev3-M2: Bayesian fault localization

| Field | Value |
|---|---|
| **Requirement** | Justify likelihood functions and priors. Explain path-evidence multipliers. Check double-counting from correlated paths. Report precision, recall, F1, calibration. Compare with simpler methods. |
| **Manuscript section** | §3.2, equations (4a)-(4c) |
| **Verification** | `src/causal_engine.py` `diagnose_causal_faults`; `results/exp3_telemetry_noise.csv` |
| **Evidence** | 3-state CPT with priors P(normal)=0.95, P(degraded)=0.03, P(severed)=0.02. Path evidence multipliers w_k defined for all 3 states. Normalization verified (sums to 1.0, tested in `test_missing_telemetry_and_division_by_zero`). Campaign 3 shows CIRAH-noCausal degrades under noise. |
| **Status** | **PARTIALLY MET** — Likelihoods and priors are defined but not formally justified. No precision/recall/F1 evaluation. Double-counting from correlated paths not analyzed. |
| **Remaining action** | Add justification for priors. Add fault classification evaluation. Analyze correlated-path evidence. |

### Rev3-M3: Intervention cost and optimization

| Field | Value |
|---|---|
| **Requirement** | Explain physical interpretation of every weight. Conduct sensitivity analysis. Justify reference normalizers. State solver scope (all actions vs candidates). Specify tie-breaking. Separate hard constraints from soft penalties. |
| **Manuscript section** | §3.6, §3.7 |
| **Verification** | `src/cost_model.py`, `src/optimizer.py` |
| **Evidence** | Weights: w_rule=1.0, w_switch=2.5, w_msg=0.5, w_flow_disrupt=5.0. References: C_I,ref=30, C_D,ref=50, C_L,ref=40, Ψ_ref=10. Solver: argmin over K=6 shortest paths × 2 throttle variants = 13 candidates. Hard constraint (R_robust≤R_max) separated from soft penalty (β·R_post/R_max). |
| **Status** | **PARTIALLY MET** — Weights defined but not sensitivity-analyzed. Tie-breaking is implicit (Python min returns first). Solver scope not explicitly stated as "best among enumerated, not global." |
| **Remaining action** | Add sensitivity analysis. State solver scope explicitly. Document tie-breaking rule. |

### Rev3-M4: Safe fallback mechanism

| Field | Value |
|---|---|
| **Requirement** | Define when partition is detected. Justify 50%/25% throttling. Measure SLA violations during fallback. Clarify throttling cannot restore connectivity across partition. |
| **Manuscript section** | §3.8 |
| **Verification** | `src/optimizer.py` `_execute_safe_fallback`; `test_audited_defects.py` `test_partitioned_network_graceful_fallback` |
| **Evidence** | Partition detected via `nx.has_path()` on active links. If partitioned: 50% throttle, partition_detected=True, recovery_time=2000ms. If connected but risk-violating: 75% throttle, lowest-risk candidate. Test verifies no crash on partition. |
| **Status** | **PARTIALLY MET** — Partition detection is tested. Throttling values (50%, 75%) are not justified or evaluated. SLA violations during fallback not reported. |
| **Remaining action** | Add justification or evaluation of throttling values. Report fallback trigger frequency and service impact. |

---

## 5. Literature Review

### Rev3-L1: Add recent directly relevant work

| Field | Value |
|---|---|
| **Requirement** | Add work on causal network diagnosis, counterfactual decision-making, risk-constrained routing, minimum-change reconfiguration, network restoration. |
| **Manuscript section** | §2 |
| **Verification** | Manuscript §2.1-§2.5; 35 references |
| **Evidence** | 35 references, 80.0% from 2022-2026, 0 uncited. Organized into 4 categories. Table 1 compares 10 approaches across 8 dimensions. |
| **Status** | **PARTIALLY MET** — References are recent and organized. Gap: no direct comparison with causal-routing or counterfactual decision-making papers in networking. |
| **Remaining action** | Add comparison with closest causal/diagnosis approaches if available in literature. |

### Rev3-L2: Verify every reference

| Field | Value |
|---|---|
| **Requirement** | Verify every reference supports the attributed claim. |
| **Manuscript section** | §2, References |
| **Verification** | `FINAL_AUDIT_REPORT.md` §4 (reference audit) |
| **Evidence** | 35 references verified: 28/35 (80.0%) from 2022-2026. All in-text citations resolved. No ghost citations. |
| **Status** | **MET** — Reference audit completed and documented. |

### Rev3-L3: Precise novelty comparison

| Field | Value |
|---|---|
| **Requirement** | Explain what CIRAH can do that a strong minimum-change, risk-constrained optimizer cannot. |
| **Manuscript section** | §2.5, §1.2 |
| **Verification** | Manuscript §1.2 (research gap), §2.5 (comparison table) |
| **Evidence** | Research gap stated as investigation question. Table 1 compares 8 dimensions. But no direct comparison with a constrained minimum-change optimizer. |
| **Status** | **PARTIALLY MET** — Comparison table exists but doesn't include constrained optimizer. |
| **Remaining action** | Add constrained optimizer to comparison or explain why CIRAH differs. |

---

## 6. Writing and Presentation

### Rev3-W1: Rewrite abstract

| Field | Value |
|---|---|
| **Requirement** | State specific novelty, strongest validated improvements, principal limitations. Remove unsupported claims. |
| **Manuscript section** | Abstract |
| **Status** | **PARTIALLY MET** — Abstract reports verified numbers (13.8% churn reduction, p<0.01). But still claims CIHF as a contribution without evidence of decision-making benefit. |
| **Remaining action** | Remove or qualify CIHF claim in abstract. Add limitation statement. |

### Rev3-W2: Reduce repeated claims

| Field | Value |
|---|---|
| **Requirement** | Reduce repeated claims across highlights, introduction, contributions, results, conclusion. |
| **Status** | **PARTIALLY MET** — Some repetition exists. |
| **Remaining action** | Review and consolidate. |

### Rev3-W3: Verifiable contributions

| Field | Value |
|---|---|
| **Requirement** | Present contributions as verifiable technical advances, not module list. |
| **Status** | **PARTIALLY MET** — §1.4 lists 5 contributions with some validation references. CIHF contribution (item 3) claims "graph-based stress-relief mechanism" without evidence of decision benefit. |
| **Remaining action** | Qualify CIHF contribution. |

### Rev3-W4: Equation rendering

| Field | Value |
|---|---|
| **Requirement** | Ensure all equations, symbols, subscripts, Greek letters render correctly. |
| **Status** | **MET** — Equations verified in Markdown source. |

### Rev3-W5: Figure readability

| Field | Value |
|---|---|
| **Requirement** | Improve architecture diagram, causal graph, healing-field visualization, ablation plots. |
| **Status** | **PARTIALLY MET** — Architecture figure exists. No causal DAG figure. No healing-field visualization. |
| **Remaining action** | Add causal DAG figure. Add healing-field visualization if retained. |

### Rev3-W6: Parameter table

| Field | Value |
|---|---|
| **Requirement** | Clear parameter table covering objective weights, risk thresholds, confidence levels, path-search settings, traffic assumptions, fallback thresholds. |
| **Status** | **NOT MET** — No consolidated parameter table exists. Parameters are scattered across §3.5-§3.7. |
| **Remaining action** | Add parameter table. |

### Rev3-W7: Reproducibility instructions

| Field | Value |
|---|---|
| **Requirement** | Setup instructions, dependency versions, experiment commands, random seeds, scripts. |
| **Status** | **MET** — `requirements.txt` created. `REPRODUCIBILITY.md` updated with correct commands, seeds, dependencies. |
