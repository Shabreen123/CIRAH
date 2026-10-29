# CIRAH Submission Readiness Assessment

**Branch:** cirah-final-audit  
**Date:** 2026-10-26  
**Assessed by:** Automated audit pipeline (verified by execution)

---

## Overall Assessment

| Gate | Status |
|---|---|
| **Ready for faculty revision review** | **✅ YES — SUBMIT** |
| **Ready for SCI Q1 journal submission** | **⚠️ NOT YET** — simulation-only; hardware validation required |

---

## Faculty Review: SUBMIT ✅

All previously identified blockers are resolved:

| Former Blocker | Status |
|---|---|
| B1 — Reference [31] (Pei et al. 2020, off-topic, uncited, pre-2022) reduced recency to 77.1% | **RESOLVED** — replaced with Li et al. 2022 (hybrid SDN path selection, DOI verified) → 28/35 = **80.0%** |
| B2 — 16 uncited bibliography entries | **RESOLVED** — all 35 references now cited (§2.1, §2.2, §2.4 expanded) |

### Passing Criteria (24/25 PASS, 1 PARTIAL)

- ✅ 13/13 regression tests pass (`test_audited_defects`)
- ✅ All component tests pass (`test_components.py`)
- ✅ Statistical analysis: 0 warnings; CSV regenerated
- ✅ `git diff --check`: 0 whitespace issues
- ✅ HTML regenerated: `manuscript/CIRAH_Journal_Paper.html`
- ✅ Numerical reconciliation: all values match `hypothesis_tests_cirah_vs_dynamic.csv`
- ✅ Six-way ablation: all 6 variants implemented and reported
- ✅ Bayesian fault localization: 3-state CPT with normalization
- ✅ SCM: Pearl do(A) twin-graph counterfactual simulation
- ✅ Counterfactual ranking: conservative claim (lower variance, not higher mean ρ)
- ✅ CIHF: Laplacian diffusion implemented and validated
- ✅ Constrained optimizer: hard risk ceiling enforced
- ✅ Partition fallback: regression-tested
- ✅ Complexity: O(|V|²|E|); p95 ≤ 16 ms empirically validated
- ✅ Paired Wilcoxon + Holm/Bonferroni: N=6 primary, N=30 omnibus
- ✅ All-zero difference handling: NaN p-values, non-informative notes
- ✅ 415 ms recovery at k=3 explicitly disclosed
- ✅ CIRAH not claimed faster at k=2,3 on Abilene
- ✅ No false significance claims
- ✅ **35 references ≥ 30 threshold** ✓
- ✅ **28/35 = 80.0% from 2022–2026** ✓
- ✅ **0 uncited references** ✓
- ✅ Ghost citations in §2.2 removed; replaced with real citations [3, 4, 31, 32]
- ✅ No fabricated data
- ✅ audit_backup/ preserved
- ⚠️ **Simulation-only evaluation** (PARTIAL — disclosed limitation, not blocking)

---

## SCI Q1 Journal Submission: NOT YET ⚠️

The manuscript is scientifically honest and internally consistent, but the following gaps would limit competitive journal review:

### 1. Hardware Testbed Validation (R10 — PARTIAL)

**Issue:** All experimental results are simulation-based. SCI Q1 reviewers in the SDN/networking domain typically require:
- Mininet emulation on real hardware, OR
- P4-programmable switch experiments, OR
- OpenDaylight or ONOS controller integration test

**Recommended action:** Add a Mininet-based validation experiment (4–8 nodes) demonstrating that CIRAH's control-plane integration is functionally correct on actual SDN hardware.

### 2. Topology Expansion

**Issue:** Abilene (11 nodes) and GEANT (22 nodes) are small relative to production networks.

**Recommended action:** Add at least one leaf-spine or fat-tree data-center topology experiment.

### 3. Traffic Model Diversity

**Issue:** Synthetic uniform-random traffic does not capture bursty or diurnal production patterns.

**Recommended action:** Evaluate under gravity-model or trace-driven traffic (e.g., CAIDA anonymized traces) for at least one topology.

---

## Risk Summary

| Risk | Severity | Status |
|---|---|---|
| Reference recency < 80% | HIGH — was FAIL | **RESOLVED** (80.0%) |
| Uncited references | MEDIUM — was PARTIAL | **RESOLVED** (0 uncited) |
| Ghost citations in §2.2 | MEDIUM | **RESOLVED** |
| Simulation-only evaluation | HIGH for SCI Q1 | Disclosed; faculty submission acceptable |
| k=3 recovery overhead (415 ms) | LOW — disclosure required | **RESOLVED** (explicitly disclosed) |
| Counterfactual ranking parity with myopic | LOW | **RESOLVED** (conservative claim) |

---

## Final Decision

**SUBMIT to faculty for revision review.** The manuscript is scientifically sound, internally consistent with the experiment outputs, reproducible from the committed code, and meets both the reference count and recency requirements. No blocking issues remain for faculty review.

**Do NOT submit to a SCI Q1 journal** without first adding hardware testbed validation (at minimum a Mininet experiment) and expanding to at least one additional network topology.
