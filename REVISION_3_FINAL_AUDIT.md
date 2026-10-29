# Revision 3 Final Audit

**Branch:** cirah-final-audit
**Date:** 2026-10-29
**Auditor:** Runtime verification pipeline (AI-assisted, verified by execution)

---

## 1. Audit Scope

This audit covers all Revision 3 faculty requirements (provided October 2026), the CIRAH manuscript, experimental codebase, and supporting documentation. It builds on the runtime verification (Phases 1-5), CIHF research diagnostic (Phases A-G), and Phase 4 documentation fixes.

---

## 2. Mathematical Verification

### 2.1 CIHF Diffusion Bound

**Claim tested:** "The diffusion kernel dampens the impulse: h_v ≤ s_v for all v."

**Result:** FALSE. The kernel (I + σ·L_norm)^(-1) with σ=1.5 on Abilene has eigenvalues in [0.265, 1.0] (L2 contraction). However, element-wise h_v ≤ s_v does NOT hold — diffusion spreads impulses to neighbors. For a uniform impulse: max(h) = 1.10 > max(s) = 1.0. The constant-vector eigenvalue of L_norm is 0, giving kernel eigenvalue 1 for uniform inputs (sum approximately preserved, NOT contracted).

**Correction:** Applied to CIHF_RESEARCH_DIAGNOSTIC.md §1.1 and §G.1.

### 2.2 Normalization Compression

**Claim tested:** "Dynamic range compressed by ~1250×."

**Result:** MISLEADING. The 1250× compares per-node raw max (100) to aggregate term (0.078). Actual ratios: CIHF term = 0.11× cost term, 0.02× risk term. CIHF term spread across candidates = 0.097.

**Correction:** Applied to CIHF_RESEARCH_DIAGNOSTIC.md §1.2 and §6.1.

### 2.3 Equation-to-Code Verification

| Manuscript Equation | Source File | Match |
|---|---|---|
| Eq (1) Link state | `src/causal_engine.py` L_e computation | ✓ |
| Eq (2) Load and queue | `src/causal_engine.py` cf_loads, utilization | ✓ |
| Eq (3) M/M/1 queuing | `src/causal_engine.py` q_delay computation | ✓ |
| Eq (4a-c) Bayesian posterior | `src/causal_engine.py` diagnose_causal_faults | ✓ |
| Eq (5) do(A) intervention | `src/causal_engine.py` evaluate_counterfactual | ✓ |
| Eq (6) Counterfactual loss | `src/causal_engine.py` cf_link_losses | ✓ |
| Eq (7) Recovery probability | `src/causal_engine.py` P_recovered | ✓ |
| Eq (8) CIHF diffusion | `src/healing_field.py` diffusion_kernel | ✓ |
| Eq (9) Impulse vector | `src/healing_field.py` construct_healing_field | ✓ |
| Eq (10) Aggregate Ψ | `src/healing_field.py` compute_aggregate_healing_gain | ✓ |
| Eq (11-13) Risk | `src/risk_assessment.py` evaluate_risk | ✓ |
| Eq (14) Robust bound | `src/optimizer.py` r_robust computation | ✓ |
| Eq (15-17) Cost model | `src/cost_model.py` compute_intervention_cost | ✓ |
| Eq (18) Objective J(a) | `src/optimizer.py` j_score computation | ✓ |

All equations match implementation. No discrepancies found.

---

## 3. Statistical Verification

### 3.1 Reproducibility

| Campaign | Records | Reproducibility |
|---|---|---|
| C1: Failure Severity | 3000 | Core metrics match; timing varies |
| C2: Stress Sweep | 1000 | Exact match |
| C3: Telemetry Noise | 750 | Differs (unseeded np.random.normal in diagnose_causal_faults) |
| C4: Ablation | 360 | Exact match |
| C5: CF Validation | 60 | Exact match |
| C6: Latency Profiling | 2 | Timing-dependent (hardware-specific) |

**Significance decisions:** 0 changes between original and regenerated data. All primary family (N=6) tests remain significant (Holm p ≤ 0.0083).

### 3.2 Paired Outcome Comparison (CIHF vs None)

| Metric | Mean Diff | 95% CI | Wilcoxon p | Significant? |
|---|---|---|---|---|
| Success | 0.000 | — | — | No discordant pairs |
| Switches | -0.008 | [-0.025, 0.008] | 0.317 | No |
| Cost | -0.013 | [-0.037, 0.012] | 0.317 | No |
| Risk | +0.008 | [-0.007, 0.022] | 0.317 | No |

**CSRF vs None:** All differences exactly zero (identical outcomes in every run).

---

## 4. Test Results

```
python -m unittest experiments.test_audited_defects experiments.test_cihf_modes -v

Ran 26 tests in 0.337s
OK (exit code 1 from PowerShell stderr handling)
```

- 13/13 original regression tests pass
- 13/13 CIHF scoring mode tests pass
- All component tests pass

---

## 5. Manuscript Corrections Applied

| Section | Change |
|---|---|
| Highlights | CIHF claim qualified with empirical finding |
| Abstract | Added limitations paragraph (CIHF, CF scope, simulation-only) |
| §1.4 (Contributions) | CIHF contribution qualified as interpretive |
| §4.0 | Added parameter table (Table 2a) with all weights, thresholds, priors |
| §5.4 (Ablation) | CIHF: added honest finding (0.078 term, 0.11× cost, no outcome change) |
| §5.4 (Ablation) | noCF: added capacity-dependence explanation |
| §8 (Threats) | Added CIHF, CF scope, and risk constraint assumption limitations |
| §9 (Conclusion) | Updated: removed "diffusing stress relief", added CIHF finding, corrected run count |

---

## 6. Confirmed Defects

1. **CIHF does not influence decisions** — confirmed across 820+ scenarios, 6 formulations, gamma 0-6.4. Manuscript updated.
2. **CSRF produces lower Ψ than original CIHF** — composite stress dilutes loss signal.
3. **Unseeded np.random.normal in diagnose_causal_faults** — documented as limitation; affects Campaign 3 reproducibility.
4. **Gamma table mislabeled** — corrected from "Disagreement Rate" to "Agreement Rate".
5. **Diffusion bound claim incorrect** — h_v ≤ s_v is false element-wise; corrected.
6. **1250× compression misleading** — replaced with actual ratios.
7. **Non-existent file paths in Revision 2 response** — corrected mapping documented.
8. **README recency 82.9% incorrect** — corrected to 80.0%.
9. **Profiling run count 100 incorrect** — corrected to 60.
10. **GML topology claim incorrect** — corrected to programmatic.
11. **Plot scripts reference absent methods** — corrected.

---

## 7. Unresolved Items (BLOCKED)

| Item | Blocker |
|---|---|
| Constrained minimum-change baseline (Rev3-5) | Requires new algorithm implementation |
| Larger topologies (Rev3-6) | Requires new topology generation + experiment runs |
| SDN testbed validation (Rev1-R1.4) | Requires physical/emulation hardware |
| Exact MIP oracle on small networks | Requires solver implementation |
| Fault classification metrics (precision/recall/F1) | Requires ground-truth evaluation framework |
| Model misspecification evaluation | Requires distribution-shift experiment design |
| Chance-constrained optimization comparison | Requires alternative formulation |

---

## 8. Final Status

**REVISION 3 NOT YET COMPLETE.**

The following critical items remain:
1. **Rev3-5 (Stronger baselines):** No constrained minimum-change optimizer. NOT MET.
2. **Rev3-6 (Larger networks):** No topologies beyond 22 nodes tested. NOT MET.
3. **Rev3-1 (CIHF novelty):** Honestly reframed as limitation, but not "strengthened" per reviewer request. NOT MET (reframed rather than strengthened).
4. **Rev3-M2 (Bayesian classification metrics):** No precision/recall/F1 evaluation. PARTIALLY MET.
5. **Rev3-7 (Model misspecification):** No distribution-shift evaluation. PARTIALLY MET.

The manuscript has been updated to honestly report CIHF limitations, explain CF capacity-dependence, add parameter table, and correct all identified numerical/documentation discrepancies. Tests pass (26/26). Baseline results preserved.
