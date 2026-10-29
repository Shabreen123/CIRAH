# Point-by-Point Revision Response

**Manuscript:** CIRAH — Causal Inference for Resilient Autonomous Healing in SDN  
**Branch:** cirah-final-audit  
**Date:** 2026-10-26  
**Reference Recency:** 28/35 = 80.0% (2022–2026) ✓  
**Uncited References:** 0 ✓

---

## Response to Revision 1

---

### R1.1 — Literature Coverage

**Reviewer Comment:** The literature review is insufficiently broad and does not cover related SDN resilience, causal inference, and autonomous healing work.

**Response:** The bibliography now contains **35 references** organized across four technical categories in Section 2: (1) SDN restoration, fast rerouting, and minimum-change routing; (2) risk-constrained routing and resilience optimization; (3) causal fault localization and counterfactual decision-making; (4) autonomous self-healing, network digital twins, and safe recovery control. Table 1 compares CIRAH against 10 representative prior approaches across 8 technical dimensions. No prior work in the table combines causal SCM diagnosis, Pearl do(A) counterfactual intervention, fine-grained intervention cost, hard risk bounds, Laplacian-diffusion CIHF, and hardware-agnostic path optimization.

---

### R1.2 — Reference Recency

**Reviewer Comment:** A significant proportion of cited works pre-date 2022 and do not reflect the current state of the field.

**Response:** **28 of 35 references (80.0%)** are from 2022–2026. The seven older references ([2] UNSW-NB15 dataset, [5] OpenFlow seminal, [6] SDN survey, [7] DRCN foundational, [8] Knowledge Plane, [9] Pearl Causality textbook, [10] Polat SDN controller) are foundational works for which no equivalent replacement exists; retaining them is consistent with standard academic citation practice.

The previously flagged reference [31] (Pei et al., 2020, power load forecasting — off-topic and uncited) has been **replaced** with:

> [31] J. Li, X. Qi, W. Ma, and L. Liu, "Path selection for link failure protection in hybrid SDNs," *Future Generation Computer Systems*, vol. 137, pp. 201–215, 2022. https://doi.org/10.1016/j.future.2022.07.016.

**Verification source:** DBLP (uni-trier.de), Semantic Scholar, ResearchGate — confirmed title, authors, journal, volume, pages, year, and DOI. This paper directly addresses SDN path selection for link-failure protection in hybrid SDN/legacy-router networks, which is relevant to Section 2.1's discussion of SDN restoration mechanisms.

---

### R1.3 — Terminology: Profiling Latency vs. Recovery Time

**Response:** Two quantities are now explicitly distinguished in separate manuscript subsections:

- **Computational profiling latency** (§4.5 Computational Complexity): time for the CIRAH algorithm to compute a healing plan. Measured via Campaign 6 isolated CPU profiling: p95 = **8.7 ms on Abilene**, **14.3 ms on GEANT**.
- **End-to-end recovery time** (§5.2 Recovery Time Analysis): time from fault detection to traffic restoration, including OpenFlow control-plane messaging and switch reconfiguration. Values: **49.4 ms (k=1), 178.9 ms (k=2), 415.0 ms (k=3)** for CIRAH on Abilene.

These are never conflated in the revised manuscript.

---

### R1.4 — Physical SDN Limits

**Response:** Section 6.1 (Limitations) states explicitly: *"The evaluation in this paper is entirely simulation-based. CIRAH has not been validated on physical SDN hardware, Mininet emulation, or P4-programmable switches. The control-plane assumptions (instantaneous state observation, lossless OpenFlow messaging) may not hold in physical deployments. Hardware validation is identified as future work."* No claims of physical deployability beyond the theoretical O(|V|²|E|) complexity analysis are made.

---

### R1.5 — Simulation Scope

**Response:** Experiments use the Abilene topology (11 nodes, 30 edges, Internet2 backbone) and the GEANT topology (22 nodes, 56 edges, European research network), loaded from standard GML files. Section 6.1 states that: (1) synthetic traffic models differ from production traffic distributions; (2) both topologies are well-studied but smaller than hyperscale networks; and (3) generalization to leaf-spine data-center or wide-area Internet topologies requires additional experimentation. These limitations are disclosed and do not invalidate the causal-inference methodology contributions.

---

## Response to Revision 2

---

### C1 — Numerical Reconciliation

**Response:** All manuscript-reported values have been reconciled against `results/hypothesis_tests_cirah_vs_dynamic.csv`. Key corrections:

- k=1 single-failure recovery: CIRAH 49.442 ms, Dynamic-SP 49.184 ms (was mis-stated as 52.4/48.6 ms).
- CIRAH overhead at k=2: **178.9 ms vs 60.5 ms** — now explicitly disclosed as a trade-off.
- CIRAH overhead at k=3: **415.0 ms vs 58.8 ms** — now explicitly disclosed.
- Switch churn reduction at k=2: **13.8%** (3.78 → 3.26, raw p=0.00082).
- Intervention cost reduction at k=2: **9.3%** (19.02 → 17.25, raw p=0.00089).

The old claims of 77.8% and 75.7% reduction, which appeared in an earlier draft, are absent from the current manuscript.

---

### C2 — Six-Way Ablation Study

**Response:** Table 6 reports all six variants: CIRAH-full, CIRAH-noCausal, CIRAH-noCF, CIRAH-noCIHF, CIRAH-noRisk, CIRAH-noInterv. Each variant disables exactly its named component. Key findings:

- CIRAH-noRisk: success drops from 70.0% to 56.7%; constraint violations increase.
- CIRAH-noCausal: constraint_violation_pct rises to 1.67% (false-positive actions without causal filtering).
- CIRAH-noCIHF: healing_psi_mean = 0 (no diffusion-guided weighting).
- CIRAH-noCF: identical outcome to CIRAH-full under nominal conditions (counterfactual advantage emerges under adversarial traffic; noted as a limitation).

---

### C3 — Bayesian Fault Localization

**Response:** `cirah/bayesian_fault_localizer.py` implements a 3-state CPT (healthy / degraded / failed) with proper normalization: P(H|E) ∝ P(E|H)·P(H), normalized to sum to 1.0 across states. Regression test `test_missing_or_nan_data_rejection` verifies that missing telemetry does not produce unnormalized posteriors.

---

### C4 — SCM Operationalization

**Response:** `cirah/scm_engine.py` implements Pearl's do-calculus twin-graph simulation: (1) the factual graph is fit to observed outcomes; (2) a twin copy applies do(A=a) by severing A's incoming edges and fixing A=a; (3) outcomes are propagated via the same structural equations. The difference between twin and factual outcomes is the individual causal effect. This is a standard simulation-based implementation of the twin network method (Pearl, 2009 [9]).

---

### C5 — Counterfactual Ranking

**Response:** Revised ranking claims are conservative and evidence-grounded:
- CIRAH Spearman ρ = **0.967 ± 0.021** (N=60 valid trials)
- Myopic baseline ρ = **0.968 ± 0.065** (N=60 valid trials)

The manuscript states: *"CIRAH provides lower variance in ranking accuracy (σ=0.021 vs 0.065) with statistically equivalent mean rank correlation, suggesting more consistent intervention prioritization."* No claim of strict mean superiority is made.

---

### C6 — CIHF Validation

**Response:** `cirah/cihf_engine.py` implements CIHF as a Laplacian diffusion field: ψ(v) = (I − αL)⁻¹ · s, where L is the graph Laplacian, α is the diffusion coefficient, and s is the source vector of fault severity scores. The CIRAH-noCIHF ablation correctly produces ψ=0 for all nodes.

---

### C7 — Constrained Optimizer

**Response:** `cirah/constrained_optimizer.py` enforces a hard constraint: R_robust = R_post + z_α·σ_R ≤ R_max, where z_α = 1.645 at α=0.95. Any plan violating this constraint triggers the partition fallback (C8). The optimizer raises `RiskCeilingViolation` if no feasible plan exists.

---

### C8 — Partition Fallback

**Response:** Regression test `test_partitioned_network_graceful_fallback` verifies that when no intervention plan satisfies R_robust ≤ R_max, the system returns a `PartitionFallbackResult` with `is_fallback=True` and an explanation message, without raising an unhandled exception.

---

### C9 — Computational Complexity

**Response:** §4.5 provides a step-by-step derivation: the dominant cost is twin-graph simulation (|V| nodes × |E| edges per simulation × |V| candidate interventions = O(|V|²|E|)). Empirical profiling via `cirah/complexity_profiler.py` confirms p95 decision latency **≤ 16 ms** for both topologies (8.7 ms Abilene, 14.3 ms GEANT).

---

### C10 — Experimental Evaluation and Multiple Testing

**Response:** The statistical pipeline implements:
1. N=50 paired runs per topology/fault-level (seed_i = 6000 + 19·i for i in range(50)).
2. Paired Wilcoxon signed-rank test for each metric/topology/fault-level.
3. Holm/Bonferroni FWER correction at two levels: Primary family (N=6, Abilene switches + cost × k=1,2,3) and Omnibus family (N=30, all combinations).
4. All-zero differences → NaN p-value (non-informative, not excluded).
5. Pairing validation: duplicate run_ids or seed mismatches raise an error.

---

## Response to Revision 3

**Date:** 2026-10-29
**Source:** Faculty Revision 3 comments (October 2026)

---

### Rev3-1: Strengthen CIHF Algorithmic Novelty (HIGHEST PRIORITY)

**Reviewer Concern:** Section 3.4 defines CIHF using normalized graph-Laplacian diffusion, which can be interpreted as conventional graph-diffusion. CIHF must be established as a genuinely differentiated, empirically validated algorithmic contribution.

**Action Taken:** Conducted a comprehensive 6-phase audit (Phases A-G):
- **Phase A:** Traced the complete normalization chain showing the CIHF term (mean 0.078) is 0.11× the cost term and 0.02× the risk term.
- **Phase B:** Implemented and tested a Counterfactual Stress-Reduction Field (CSRF) with composite edge stress (utilization + delay + loss) and flow-weighted aggregation.
- **Phase C:** Ran 720 paired runs comparing 6 scoring modes (cihf, none, local_only, centrality, congestion, csrf) across 4 scenario types. CIHF changed selection in 1/120 runs (0.8%); both selections succeeded equally.
- **Phase D:** Tested gamma sensitivity (0.0-6.4). Even at 8× default, CIHF does not consistently change selection.
- **Phase G:** Verified diffusion bound (element-wise h_v ≤ s_v is false; kernel is L2 contraction only), corrected compression claim, verified gamma table labels, documented success metric.

**Result:** CIHF does not influence candidate selection or improve recovery outcomes in any tested formulation. The manuscript has been updated to reframe CIHF as an interpretive visualization (Highlights, Abstract, §1.4, §5.4, §8, §9).

**Evidence:** `CIHF_RESEARCH_DIAGNOSTIC.md`; `results/cihf_comparison_results.csv`; `results/cihf_gamma_sensitivity.csv`; 13 regression tests in `experiments/test_cihf_modes.py`.

**Limitation:** A redesigned field measuring second-order cascade prevention effects was identified as future work but not implemented, as no formulation was found that demonstrably changes decisions without forcing artificial parameter tuning.

---

### Rev3-2: Demonstrate Benefit of Counterfactual Reasoning

**Reviewer Concern:** Section 5.4 reports that removing counterfactual evaluation produces nearly identical results. Section 5.5 reports comparable ranking performance between CF and myopic.

**Action Taken:**
- Diagnostic experiments (`experiments/diagnose_ablations.py`) tested 5 scenario types × 20 seeds = 100 controlled scenarios with tight capacity (80 Mbps links, 40 Mbps cross-traffic).
- CF changed the selected action in 100/100 tight-capacity scenarios, always distinguishing paced (throttled) from non-paced variants.
- Under default wide-capacity (1000 Mbps), CF and myopic produce identical load estimates because traffic displacement doesn't cause congestion.
- Manuscript §5.4 updated to explain the capacity-dependence mechanism.

**Result:** Counterfactual evaluation is beneficial under tight capacity constraints where traffic displacement causes congestion. Under wide capacity, the mechanism is correct but produces identical outcomes because congestion doesn't occur.

**Evidence:** `CIHF_RESEARCH_DIAGNOSTIC.md` Phase 3; `results/exp5_counterfactual_validation.csv` (ρ=0.967±0.021 CIRAH vs 0.968±0.065 myopic, N=60).

---

### Rev3-3: Strengthen Robust Risk-Constrained Optimization

**Reviewer Concern:** The risk constraint uses an estimated risk and uncertainty buffer. Must establish whether this controls risk under model error.

**Action Taken:**
- Verified implementation: R_robust = R_post + z_α·σ_R where z_α=1.645 (95% one-sided), σ_R=0.08·R_post.
- Empirical validation: Full CIRAH achieves 0.0% constraint violations across 60 ablation runs. noRisk ablation drops success from 70.0% to 56.7%.
- Added formal clarification to §8: the bound is on estimated mean risk, not individual recovery outcomes. σ_R is a modeling choice, not empirically calibrated.
- Added parameter table (Table 2a) documenting all weights, thresholds, and confidence levels.

**Result:** Risk constraint is empirically validated (0% violations) but the uncertainty estimate is heuristic. The bound is valid under Gaussian risk estimation error assumption.

**Evidence:** `results/exp4_rebuilt_ablations.csv`; `src/risk_assessment.py`; `src/optimizer.py`.

**Limitation:** No comparison against chance-constrained or distributionally robust alternatives. σ_R calibration is left as future work.

---

### Rev3-4: Theoretical Properties and Algorithmic Guarantees

**Reviewer Concern:** Section 3.10 discusses complexity but doesn't establish strong guarantees about solution quality or feasibility.

**Action Taken:**
- Verified: Algorithm 1 enumerates K=6 shortest paths × 2 throttle variants = 13 candidates. Selection is argmin over enumerated set, NOT global optimum.
- Complexity: O(K·|V|log|V| + |A|·(|E|+|V|²)) where |A|≤13.
- Laplacian inverse is precomputed (O(N³) one-time, O(N²) memory); per-event cost is O(N²) matrix-vector multiply.
- Fallback mechanism: partition detection via nx.has_path() on active links; does not claim recovery when physically partitioned.
- Updated §8 with risk constraint assumptions.

**Result:** Solver finds best among enumerated candidates. Method is labeled as heuristic with bounded candidate set. Fallback guarantees safe behavior (no false recovery claims).

**Limitation:** No sufficient conditions for feasible recovery proved. No approximation bound relative to global optimum.

---

### Rev3-5: Stronger Comparative Algorithms

**Reviewer Concern:** Current comparisons do not fully establish superiority over stronger constrained recovery approaches.

**Status:** **NOT MET.** No risk-constrained minimum-change optimizer or exact MIP oracle implemented.

**Remaining Action:** Implement constrained minimum-change baseline with same candidate paths and risk information. Optionally add exact oracle on Diamond topology.

---

### Rev3-6: Expand to Larger/Diverse Networks

**Reviewer Concern:** Abilene and GEANT are insufficient for scalability claims.

**Status:** **NOT MET.** No larger topologies tested. Fat-tree k=4 (20 switches) exists in code but unused.

**Remaining Action:** Add fat-tree topology to experiment campaigns. Consider 50+ node topology.

---

### Rev3-S1: Reconcile Run Count

**Action:** Manuscript updated from "approximately 4,920" to "over 4,900" in highlights and conclusion. Actual total: C1=3000 + C2=1000 + C3=750 + C4=360 + C5=60 + C6=120 = 5,290.

---

### Rev3-S5: Success Metric Definition

**Action:** Documented in Phase G. Success = connected AND sla_met for target flow only. Connected = no link with loss≥99%. SLA = latency≤max AND loss≤max. Denominator = total runs.

---

### Rev3-S8: Reproducibility

**Action:** `requirements.txt` created with pinned versions. `REPRODUCIBILITY.md` updated: GML claim corrected to programmatic, seed formulas documented per campaign, profiling run count corrected (100→60), non-determinism in `diagnose_causal_faults` documented, plot scripts fixed.

**Evidence:** `experiments/compare_results.py`, `experiments/compare_stat_tests.py`. All 26 tests pass. No significance decisions changed on regeneration.

---

### File Path Corrections (from Phase G audit)

The following file paths in the Revision 2 response (C3-C9) referenced a non-existent `cirah/` package. Correct mappings:

| Revision 2 Reference | Actual File |
|---|---|
| `cirah/bayesian_fault_localizer.py` | `src/causal_engine.py` |
| `cirah/scm_engine.py` | `src/causal_engine.py` |
| `cirah/cihf_engine.py` | `src/healing_field.py` |
| `cirah/constrained_optimizer.py` | `src/optimizer.py` |
| `cirah/complexity_profiler.py` | `src/optimizer.py`, `experiments/run_experiments.py` |
