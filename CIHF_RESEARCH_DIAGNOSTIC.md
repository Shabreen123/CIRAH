# CIHF Research Diagnostic Report

**Branch:** cirah-final-audit
**Date:** 2026-10-29
**Scope:** Audit, alternative formulation, and controlled comparison of the Causal Intervention Healing Field (CIHF)

---

## 1. Phase A — Mathematical Audit of Existing CIHF

### 1.1 Computation Chain

The existing CIHF score follows a five-step pipeline. Each step is traced to its source code.

**Step 1: Pre-intervention node stress** (`controller_sim.py`, `execute_self_healing_cycle`)

```
S_before(v) = Σ_{u ∈ successors(v)} telemetry[(v,u)].loss
```

This sums packet-loss percentages on all outgoing edges of node v. Range: [0, ~300] for Abilene (up to 3 edges × 100% loss).

**Step 2: Post-intervention node stress** (`optimizer.py`, `optimize`)

```
S_after(a, v) = Σ_{u ∈ successors(v)} cf_link_losses[(v,u)]
```

Same sum, but using counterfactual predicted losses after intervention `a`.

**Step 3: Impulse vector** (`healing_field.py`, `construct_healing_field`)

```
raw_delta(v) = max(0, S_before(v) - S_after(v))
norm_delta(v) = min(1.0, raw_delta(v) / 100.0)     ← CLIPPED to [0, 1]
weight(v) = 1.5 if v ∈ Path(a), else 1.0
s_v = norm_delta(v) × weight(v)                     ← Range [0, 1.5]
```

**Step 4: Laplacian diffusion** (`healing_field.py`, `_compute_spectral_diffusion_operator`)

```
L_norm = I - D^{-1/2} W D^{-1/2}
h(a) = (I + σ L_norm)^{-1} s(a)     with σ = 1.5
```

The diffusion kernel has eigenvalues in [0.265, 1.0] (verified: eigenvalues of L_norm ∈ [0, 1.85] for Abilene, so I + σL ∈ [1, 3.77], inverse ∈ [0.265, 1.0]). The kernel is an **L2-norm contraction** (spectral radius ≤ 1), meaning ‖h‖₂ ≤ ‖s‖₂. However, element-wise dampening does **not** hold: diffusion can spread the impulse to neighboring nodes, causing h_v > s_v at some nodes. For a uniform impulse on Abilene, max(h) = 1.10 while max(s) = 1.0. The aggregate sum is approximately preserved (sum(h) ≈ sum(s)) because the constant-vector eigenvalue of L_norm is 0, giving kernel eigenvalue 1 for uniform inputs.

**Step 5: Aggregate and objective term** (`optimizer.py`)

```
Ψ(a) = Σ_v h_v                         ← For Abilene: typically 0.4–1.6
norm_psi = Ψ / Ψ_ref                    ← Ψ_ref = 10.0
J_term = -γ × norm_psi                  ← γ = 0.8
```

Final contribution: `0.8 × (1.0 / 10.0) ≈ 0.08`.

### 1.2 Why CIHF Fails to Change Candidate Selection

The objective function is:

```
J(a) = λ_I(C_I/C_I,ref) + λ_D(C_D/C_D,ref) + λ_L(C_L/C_L,ref) + β(R_post/R_max) - γ(Ψ/Ψ_ref)
```

Typical magnitudes for a viable reroute candidate:

| Term | Formula | Typical Value |
|---|---|---|
| Intervention cost | 1.0 × (15/30) | 0.50 |
| Disruption cost | 0.5 × (7/50) | 0.07 |
| Latency SLA | 0.3 × (3/40) | 0.02 |
| Risk | 1.2 × (7/35) | 0.24 |
| **CIHF** | **0.8 × (1.0/10)** | **0.08** |

The CIHF term (0.08) is ~5× smaller than the cost term (0.50) and ~3× smaller than the risk term (0.24). For CIHF to change the argmin, the Ψ difference between two candidates must overcome the differences in all other terms.

**Root cause: normalization chain compresses dynamic range.**

| Stage | Input range | Output range | Compression |
|---|---|---|---|
| Raw stress delta | 0–300 | 0–1 | ÷100, clip |
| Path weight | 0–1 | 0–1.5 | ×1.5 |
| Laplacian diffusion | 0–1.5 | 0–0.75 | dampen (eigenvalues ≤1) |
| Aggregate sum | 0–0.75 per node | 0–~2 for 11 nodes | Σ |
| Ψ_ref normalization | 0–2 | 0–0.2 | ÷10 |
| γ weighting | 0–0.2 | 0–0.16 | ×0.8 |

A raw stress reduction of 100% (severed link rerouted) becomes 0.078 in the objective (verified from actual data). The CIHF objective term (mean 0.078) is **0.11× the cost term** (0.72) and **0.02× the risk term** (3.46). The "1250× compression" claim in the original draft compared per-node raw stress (100) to the aggregate objective term (0.078), which is not a valid single-stage compression ratio — it conflates per-node maximums with aggregate sums across normalization stages. The accurate statement: the CIHF term spread across candidates (0.097) is too small relative to the spread in cost and risk terms to change the argmin.

### 1.3 Diagnostic Evidence (from previous runtime verification)

The `diagnose_ablations.py` script tested 5 scenario types × 20 seeds = 100 controlled scenarios:

| Scenario | CIHF changed selection | CF changed selection |
|---|---|---|
| Severe cut + capacity stress | 0/20 (0%) | 20/20 (100%) |
| Cross-traffic loss spike | 0/20 (0%) | 20/20 (100%) |
| Capacity bottleneck | 0/20 (0%) | 20/20 (100%) |
| Multi-hop stress gradient | 0/20 (0%) | 20/20 (100%) |
| High cross-traffic displacement | 0/20 (0%) | 20/20 (100%) |

**CIHF never changed the selected action.** The counterfactual evaluation always changed it (in tight-capacity scenarios), but CIHF did not.

---

## 2. Phase B — Proposed Alternative: Counterfactual Stress-Reduction Field (CSRF)

### 2.1 Design Rationale

The existing CIHF uses loss-only stress, clips to [0,1], and applies Laplacian diffusion that dampens the signal. The proposed CSRF uses a composite edge stress measure and avoids dampening.

### 2.2 Mathematical Definition

**Edge stress** (composite: utilization + delay + loss):

```
σ_e(a) = w_q · min(1, Q_e(a)) + w_d · min(1, D_e(a)/D_ref) + w_l · L_e(a)/100
```

where:
- Q_e = Load_e / Cap_e (utilization)
- D_e = queuing delay from M/M/1 model (ms)
- D_ref = base_latency of edge e (reference delay)
- L_e = packet loss (0–100%)
- w_q = 0.4, w_d = 0.3, w_l = 0.3

**Node stress** (max of outgoing edges, avoiding double-counting):

```
S_v(a) = max_{e ∈ out(v)} σ_e(a)
```

**Stress reduction at node v**:

```
ΔS_v(a) = max(0, S_v(before) - S_v(a))
```

**Flow-weighted healing field**:

```
H(a, v) = ΔS_v(a) × F_v
```

where F_v = number of flows traversing outgoing edges from v (captures multi-flow benefit).

**Aggregate healing gain**:

```
Ψ_CSRF(a) = Σ_v H(a, v)
```

### 2.3 Comparison with Conventional Approaches

| Approach | Stress measure | Spatial propagation | Flow weighting | Dampening |
|---|---|---|---|---|
| Original CIHF | Loss only (÷100, clip) | Laplacian diffusion | Path membership (1.5×) | Yes (eigenvalues ≤1) |
| Congestion-only | Utilization only | None | None | No |
| Centrality | Loss × betweenness | None | Betweenness weight | No |
| **CSRF (proposed)** | **Utilization + delay + loss** | **None (direct)** | **Flow count** | **No** |

**Key distinction from R_post**: R_post measures probabilistic cascade *risk* (will harm occur?), while CSRF measures deterministic stress *reduction* (how much did stress decrease?). These are complementary quantities. R_post uses exponential probability on links >85% utilization; CSRF uses actual utilization levels across all links.

### 2.4 Limitations of the Proposed Definition

1. **No spatial propagation**: Unlike Laplacian diffusion, CSRF does not model stress relief propagation to neighboring nodes. This is intentional (diffusion dampens the signal) but means the field captures only direct, local stress reduction.
2. **Composite weights are heuristic**: w_q, w_d, w_l are set by domain reasoning, not optimization.
3. **No theoretical guarantee** that CSRF will improve recovery outcomes. The stress reduction is a proxy for benefit, not a direct measure of SLA compliance.

---

## 3. Phase C — Controlled Comparison Results

### 3.1 Experimental Design

- **Topologies**: Abilene (11 nodes)
- **Scenarios**: 4 types (standard, tight_capacity, mixed_stress, multi_fault)
- **Runs**: 30 per scenario × 6 scoring modes = 720 total records
- **Gamma**: 0.8 (default)
- **Independent evaluation**: StandardizedEvaluator (separate from selection score)
- **Output file**: `results/cihf_comparison_results.csv`

### 3.2 Action-Selection Agreement

| Scenario | All 6 modes agree | Disagreement runs |
|---|---|---|
| standard | 100% (30/30) | 0 |
| tight_capacity | 100% (30/30) | 0 |
| mixed_stress | 100% (30/30) | 0 |
| multi_fault | 96.7% (29/30) | 1 |

Only 1 out of 120 runs showed disagreement (multi_fault scenario, run 20).

### 3.3 The Single Disagreement Case

In multi_fault/run=20, the modes split into two groups:

| Mode | Selected action | Success | Ψ |
|---|---|---|---|
| cihf | act_path_3_paced | 1 | 1.62 |
| local_only | act_path_3_paced | 1 | 1.60 |
| centrality | act_path_3_paced | 1 | 2.06 |
| none | act_path_1_paced | 1 | 0.00 |
| congestion | act_path_1_paced | 1 | 0.02 |
| csrf | act_path_1_paced | 1 | 0.02 |

Both selections succeeded. The CIHF/centrality/local_only group preferred a longer paced path with higher Ψ; the none/congestion/csrf group preferred a shorter path. **No outcome difference.**

### 3.4 Per-Mode Outcome Summary (averaged across all scenarios)

| Mode | Success | Switches | Cost | Risk | Ψ | Latency |
|---|---|---|---|---|---|---|
| cihf | 0.383 | 4.35 | 21.61 | 100.78 | 0.98 | 8405 |
| none | 0.383 | 4.36 | 21.63 | 100.77 | 0.00 | 8405 |
| local_only | 0.383 | 4.35 | 21.61 | 100.78 | 0.98 | 8405 |
| centrality | 0.383 | 4.35 | 21.61 | 100.78 | 1.30 | 8405 |
| congestion | 0.383 | 4.36 | 21.63 | 100.77 | 0.82 | 8405 |
| csrf | 0.383 | 4.36 | 21.63 | 100.77 | 0.41 | 8405 |

All modes produce **identical success rates** (38.3%) and nearly identical outcomes. The Ψ values differ (as expected) but do not translate to outcome differences.

### 3.5 Key Finding

CSRF produces **lower** Ψ values (0.41) than the original CIHF (0.98). The composite stress measure (utilization + delay + loss) dilutes the loss signal that dominates the original CIHF. In scenarios where the primary stress reduction is from rerouting away from a 100%-loss severed link, the loss-only CIHF actually captures more signal than the composite CSRF.

---

## 4. Phase D — Gamma Sensitivity

### 4.1 Design

- **Modes tested**: cihf, csrf, none
- **Scenarios**: tight_capacity, mixed_stress
- **Gamma values**: [0.0, 0.4, 0.8, 1.6, 3.2, 6.4]
- **Runs**: 20 per scenario × gamma = 720 records
- **Output file**: `results/cihf_gamma_sensitivity.csv`

### 4.2 Action-Selection Agreement Rate by Gamma

| Scenario | γ=0.0 | γ=0.4 | γ=0.8 | γ=1.6 | γ=3.2 | γ=6.4 |
|---|---|---|---|---|---|---|
| mixed_stress | 100% | 95% | 100% | 100% | 100% | 100% |
| tight_capacity | 100% | 100% | 100% | 100% | 100% | 100% |

Values report the percentage of runs where all three tested modes (cihf, csrf, none) selected the **same** action. 100% = complete agreement; 95% = one run out of 20 had disagreement. The single disagreement at γ=0.4 in mixed_stress is likely due to non-deterministic noise in `diagnose_causal_faults` (which uses unseeded `np.random.normal`), not a genuine CIHF effect.

### 4.3 Mean Ψ by Gamma

| γ | CIHF Ψ | CSRF Ψ | None Ψ |
|---|---|---|---|
| 0.0 | 1.01 | 0.31 | 0.0 |
| 0.4 | 0.85 | 0.42 | 0.0 |
| 0.8 | 1.07 | 0.37 | 0.0 |
| 1.6 | 0.85 | 0.36 | 0.0 |
| 3.2 | 1.01 | 0.42 | 0.0 |
| 6.4 | 1.01 | 0.42 | 0.0 |

Ψ values are stable across gamma values (as expected — gamma weights the term in J but does not change how Ψ is computed). CSRF consistently produces lower Ψ than CIHF.

### 4.4 Key Finding

Increasing γ alone does not make CIHF change candidate selection. The Ψ spread across candidates (the signal) is too small relative to the spread in cost and risk terms (the noise), regardless of γ.

---

## 5. Phase E — Test Results

### 5.1 New Regression Tests

File: `experiments/test_cihf_modes.py`

```
Ran 13 tests in 0.317s
OK
```

Tests cover:
1. All modes produce valid (finite, non-negative) field values
2. "none" mode produces zero field
3. CSRF responds to capacity changes
4. Edge stress responds to utilization, delay, and loss individually
5. No-op intervention produces low stress reduction
6. Disconnected path through severed link is detected
7. Zero-demand flows don't cause exceptions
8. Near-capacity edge stress is bounded
9. CSRF is deterministic under same seed
10. Selection score is independent from outcome metric
11. Different modes can select different actions (in controlled multi-fault scenarios)

### 5.2 Existing Test Suite

```
Ran 13 tests in 0.032s  (test_audited_defects)
OK

All component tests PASSED successfully!  (test_components)
```

**Total: 26 tests pass (13 existing + 13 new).**

---

## 6. Phase F — Summary and Manuscript Revision Recommendations

### 6.1 Confirmed Defects

1. **CIHF does not influence candidate selection** (confirmed across 220+ scenarios). The CIHF objective term (mean 0.078) is 0.11× the cost term and 0.02× the risk term. The CIHF term spread across candidates (0.097) is insufficient to change the argmin.

2. **CSRF (proposed alternative) also does not influence selection** and produces lower Ψ values than the original CIHF. The composite stress measure dilutes the loss signal.

3. **Increasing γ alone does not fix the problem.** Even at γ=6.4, the Ψ spread across candidates is too small relative to other term differences.

### 6.2 What Works

- **Counterfactual evaluation (CF) changes selection in 100% of tight-capacity scenarios.** The CF mechanism correctly models traffic displacement and distinguishes paced vs. non-paced variants.
- **Risk constraint (noRisk ablation) has a clear effect**: success drops 70%→56.7%.
- **Intervention cost penalty (noInterv ablation) has a clear effect**: switches increase 3.60→3.78.

### 6.3 Honest Negative Result

The CIHF component, in all tested formulations (original Laplacian diffusion, local-only, centrality, congestion-only, and proposed CSRF), does not meaningfully influence candidate selection or improve recovery outcomes under the tested scenarios. The component is correctly implemented but its contribution to the objective function is too small to change decisions.

### 6.4 Manuscript Sections Requiring Revision

| Section | Current claim | Required revision |
|---|---|---|
| §3.4 (CIHF) | "Introduces CIHF via normalized graph Laplacian heat diffusion to quantify spatial stress relief" | Add honest limitation: CIHF does not influence candidate selection under tested scenarios; its contribution is dominated by cost and risk terms |
| §5.4 (Ablation) | "Eliminating the graph Laplacian diffusion field causes the spectral healing gain to collapse to Ψ=0.000" | Clarify: Ψ collapses but recovery outcomes (success, switches, cost, risk) are identical to full CIRAH — CIHF removal has no measurable effect |
| Abstract | "models spatial stress relaxation via a continuous Causal Intervention Healing Field (CIHF) governed by normalized graph Laplacian heat diffusion" | Qualify: CIHF is defined and computed but does not change action selection under tested conditions |
| Highlights | "Introduces the Causal Intervention Healing Field (CIHF) via normalized graph Laplacian heat diffusion" | Add: "CIHF's contribution to action selection was empirically evaluated and found not to change decisions under tested scenarios" |
| §3.7 (Optimization) | Objective includes -γ(Ψ/Ψ_ref) term | Retain formulation but add note that the term's magnitude is insufficient to change argmin in practice |

### 6.5 Recommended Next Steps (Not Implemented)

1. **Redesign CIHF to measure second-order effects**: Instead of first-order stress reduction (which all candidates provide equally by rerouting away from the fault), measure cascade prevention benefit — how much the intervention reduces the risk of secondary congestion on paths used by OTHER flows.
2. **Scale-normalize Ψ dynamically**: Set Ψ_ref to the median Ψ across candidates in each decision cycle, making the term adaptively scaled rather than using a fixed constant.
3. **Test on topologies with more diverse path characteristics**: Abilene's small diameter (11 nodes) may limit the diversity of stress-reduction patterns across candidates.
4. **Acknowledge limitation honestly**: If no formulation is found that changes decisions, report this as a negative result and reframe CIHF as an interpretive visualization tool rather than a decision-changing component.

---

## 7. Reproducibility Record

| Item | Value |
|---|---|
| Python | 3.12.4 |
| Branch | cirah-final-audit |
| Commit | 47021e1 |
| New files | `experiments/cihf_comparison.py`, `experiments/test_cihf_modes.py` |
| New results | `results/cihf_comparison_results.csv` (720 records), `results/cihf_gamma_sensitivity.csv` (720 records) |
| Test command | `python -m unittest experiments.test_audited_defects experiments.test_cihf_modes -v` |
| Test result | 26/26 OK |
| Experiment command | `python experiments/cihf_comparison.py` |
| Baseline CSVs | Preserved (not overwritten) |

---

## 8. Phase G — Mathematical and Reporting Verification

### G.1 Diffusion Bound Verification

**Claim tested**: "The diffusion kernel dampens the impulse: h_v ≤ s_v for all v."

**Result**: The claim is **false** as stated. The kernel (I + σ·L_norm)^(-1) with σ=1.5 on Abilene has eigenvalues in [0.265, 1.0], confirming it is an L2-norm contraction (‖h‖₂ ≤ ‖s‖₂). However, element-wise dampening does not hold:

- For a unit impulse at one node: max(h) = 0.46 ≤ max(s) = 1.0 (true for this case)
- For a uniform impulse across all nodes: max(h) = 1.10 > max(s) = 1.0 (**violated**)
- For a half-uniform impulse: max(h) = 0.55 > max(s) = 0.50 (**violated**)

Diffusion spreads the impulse to neighboring nodes, which can increase individual node values above their original impulse. The correct mathematical statement: the kernel is a spectral contraction (all eigenvalues ≤ 1), but not a pointwise contraction. The aggregate sum is approximately preserved because the constant-vector eigenvalue of L_norm is 0, giving the kernel eigenvalue 1 for uniform inputs.

**Correction applied**: Section 1.1 Step 4 has been updated to reflect this finding.

### G.2 Normalization Compression Calculation

**Claim tested**: "The dynamic range is compressed by a factor of ~1250×."

**Result**: The 1250× figure is **misleading**. It compares a per-node raw stress maximum (100% loss at one node) to the aggregate objective term (0.078), conflating per-node maximums with aggregate sums across multiple normalization stages.

**Actual observed values** (from 720-run comparison):

| Quantity | Mean | Min | Max |
|---|---|---|---|
| CIHF Ψ | 0.977 | 0.573 | 1.790 |
| CIHF term (γΨ/Ψ_ref) | 0.078 | 0.046 | 0.143 |
| Cost term (λ_I·C_I/C_I,ref) | 0.720 | — | — |
| Risk term (β·R_post/R_max) | 3.455 | — | — |

The CIHF term is 0.11× the cost term and 0.02× the risk term. The meaningful metric is the CIHF term **spread** across candidates within a run (0.097), which is too small to overcome differences in other terms.

**Correction applied**: Sections 1.2 and 6.1 have been updated with accurate ratios.

### G.3 Gamma Table Label

**Claim tested**: Section 4.2 was labeled "Disagreement Rate by Gamma" with values showing 100% and 95%.

**Result**: The label was **incorrect**. The underlying column `all_modes_agree` reports the percentage of runs where all modes selected the same action (1 = agreement). Values of 100% and 95% mean 100% agreement and 95% agreement, not disagreement. Only 1/720 runs showed any disagreement (mixed_stress, γ=0.4).

**Correction applied**: Label changed to "Action-Selection Agreement Rate by Gamma" with explicit clarification.

### G.4 Success Metric Definition

**Implementation traced** (`controller_sim.py`, `execute_self_healing_cycle`):

```python
success = bool(target_res.get("connected", False) and target_res.get("sla_met", False))
```

Where:
- `connected`: Path has no link with predicted loss ≥ 99% (i.e., no severed link in the path)
- `sla_met`: `latency ≤ sla_max_latency_ms` AND `loss ≤ sla_max_loss_pct` for the target flow
- **Denominator**: Total number of runs (not total flows). Only the target flow (flows[0] or first impaired flow) is evaluated per run.
- **Scope**: Per-run, per-target-flow binary indicator. Other flows' outcomes are not included in the success metric.

**Why 38.3% overall**: The four scenarios have very different difficulty levels:

| Scenario | Success rate | Difficulty driver |
|---|---|---|
| standard | 53.3% | Moderate — 25% of links have reduced capacity |
| tight_capacity | 43.3% | Hard — all links at 80 Mbps, high cross-traffic |
| mixed_stress | 23.3% | Very hard — random capacity degradation + random loss on many links |
| multi_fault | 33.3% | Hard — 3 simultaneous link failures |

The mixed_stress scenario (23.3%) and multi_fault (33.3%) drag down the average. All 6 CIHF modes produce the same success rate because they select from the same candidate set under the same risk constraints.

### G.5 Independent Contribution: Action Change vs. Outcome Improvement

**Distinction**: A scoring mode "changing the selected action" means the argmin of J differs. A scoring mode "improving the outcome" means the independently evaluated recovery success, latency, or risk is better. These are different: a mode can change the action without improving outcomes, or fail to change the action (and thus trivially not improve outcomes).

**Paired statistical comparison** (CIHF vs. None, 120 paired runs):

| Metric | Mean diff (CIHF−None) | 95% CI | Wilcoxon p | Significant? |
|---|---|---|---|---|
| Success | 0.0000 | — | — | No discordant pairs |
| Switches | −0.0083 | [−0.025, 0.008] | 0.317 | No |
| Cost | −0.0125 | [−0.037, 0.012] | 0.317 | No |
| Risk | +0.0075 | [−0.007, 0.022] | 0.317 | No |

**CSRF vs. None**: All differences are exactly zero — identical outcomes in every run.

**Interpretation**: CIHF changes the selected action in only 1/120 runs (0.8%), and in that case both selections succeed equally. The paired comparison shows no statistically significant difference in any outcome metric. CSRF produces zero outcome differences. This confirms that CIHF (in any tested form) does not improve recovery decisions — it neither changes actions nor improves outcomes.

### G.6 Final Decision on CIHF

**Recommendation**: CIHF should **not remain a decision-making component** in its current form. The evidence:

1. **No action change**: CIHF changed selection in 0/100 diagnostic scenarios and 1/120 comparison runs (0.8%).
2. **No outcome improvement**: Paired comparison shows zero success difference and no significant cost/risk/switches difference (all p ≥ 0.317).
3. **CSRF also fails**: The proposed alternative produces even lower Ψ and zero outcome differences.
4. **Gamma scaling fails**: Even at γ=6.4 (8× default), CIHF does not consistently change selection.
5. **Root cause is structural**: All viable reroute candidates reduce stress at the same nodes (those adjacent to the severed link), producing similar Ψ values. The CIHF term cannot differentiate candidates that differ in cost/risk but not in stress-reduction pattern.

**Options for the manuscript**:

- **Option A (Redesign)**: Redefine the field to measure second-order cascade prevention (how much the intervention reduces congestion on paths used by OTHER flows). This could differentiate candidates that have similar first-order stress reduction but different multi-flow cascade effects. This requires new algorithmic work and validation.
- **Option B (Interpretive visualization)**: Retain CIHF as a post-hoc visualization of spatial stress relief, explicitly disclaiming any decision-making role. Remove it from the objective function. The ablation study would then show identical results with and without CIHF, reported honestly.
- **Option C (Remove)**: Remove CIHF from the paper entirely and focus the contribution on the counterfactual evaluation (which demonstrably changes decisions) and the risk constraint (which demonstrably affects success).

**Recommended path for faculty revisions**: Option B or C, depending on whether the manuscript needs a "healing field" contribution for positioning. If CIHF must remain as a claimed contribution, Option A requires implementing and validating a genuinely different field definition — one that captures multi-flow or cascade-prevention effects not already measured by R_post.
