# CIRAH Reproducibility Guide

**Branch:** cirah-final-audit  
**HEAD commit:** a8d234da9049fcfbf203565675374fb0779f3ea4  
**Working-tree modification:** manuscript/CIRAH_Journal_Paper.md (4 ins / 4 del, not committed)  
**Date:** 2026-10-26

---

## 1. Environment

| Item | Value |
|---|---|
| Python version | 3.12 |
| Operating system | Windows 11 (development); Linux-compatible |
| Working directory | `C:\Users\LENOVO\OneDrive\Desktop\cirah_verified` |
| Branch | `cirah-final-audit` |

### 1.1 Python Dependencies

| Package | Purpose |
|---|---|
| `scipy` | Wilcoxon signed-rank test, Spearman correlation |
| `networkx` | Graph operations, Abilene/GEANT topology construction |
| `numpy` | Numerical arrays, Laplacian computation |
| `pandas` | CSV I/O for hypothesis test results |
| `matplotlib` | Publication figure generation |
| `seaborn` | Statistical plot styling |

Install:
```bash
pip install -r requirements.txt
```

Pinned versions are specified in `requirements.txt`. No compiled extension or build step required.

---

## 2. Repository Setup

```bash
git clone <repo-url> cirah_verified
cd cirah_verified
git checkout cirah-final-audit
git log --oneline -1
# Expected: a8d234d ...
```

---

## 3. Topologies

| Topology | Nodes | Edges | Source |
|---|---|---|---|
| Abilene | 11 | 30 | Programmatic (Internet2 backbone) |
| GEANT | 22 | 56 | Programmatic (European research network) |
| Diamond-Extended | 6 | 16 | Programmatic (controlled testbed) |

Topologies are constructed programmatically in `src/topologies.py` via `get_topology(name)`. No external GML files are required. All experiments run fully offline.

---

## 4. Random Seeds

Each campaign uses a deterministic seed formula. Seeds are not shared across campaigns.

| Campaign | Seed Formula | Runs per Condition |
|---|---|---|
| 1 — Failure Severity | `seed = 1000 + run_idx * 17 + k * 101` | 50 per topology × k-level |
| 2 — Stress Sweep | `seed = 2000 + run_idx * 13 + int(rho * 100)` | 50 per stress level |
| 3 — Telemetry Noise | `seed = 3000 + run_idx * 23 + int(sigma_n * 100)` | 50 per noise level |
| 4 — Ablation | `seed = 5000 + run_idx * 31` | 60 paired runs |
| 5 — Counterfactual Validation | `seed = 6000 + idx * 19` | 60 evaluations |
| 6 — Latency Profiling | `i` in `range(60)` (no explicit seed) | 60 per topology |

**Note:** Campaign 6 measures wall-clock execution time, which is inherently hardware-dependent. The profiling values in the manuscript were recorded on Intel Core i5-8600K, 16 GB RAM and will vary on different hardware.

---

## 5. Reproduction Commands

Run all commands from `C:\Users\LENOVO\OneDrive\Desktop\cirah_verified`.

### 5.1 Regression Tests (Audited Defects)

```bash
python -m unittest experiments.test_audited_defects -v
```

Expected: **13 tests, all OK**. Runtime: < 60 s.

### 5.2 Component Tests

```bash
python experiments/test_components.py
```

Expected: `All component tests PASSED`

### 5.3 Statistical Analysis

```bash
python experiments/statistical_analysis.py
```

Expected: Hypothesis test tables printed; 0 warnings. Output: `results/hypothesis_tests_cirah_vs_dynamic.csv`.

### 5.4 HTML Manuscript Rendering

```bash
python manuscript/convert_to_html.py
```

Expected: `manuscript/CIRAH_Journal_Paper.html` created/updated.

### 5.5 Whitespace Check

```bash
git diff --check
```

Expected: no output (0 issues).

---

## 6. Output Files

| File | Description |
|---|---|
| `results/hypothesis_tests_cirah_vs_dynamic.csv` | Primary statistical output: per-condition Wilcoxon + Holm/Bonferroni results |
| `manuscript/CIRAH_Journal_Paper.html` | Rendered HTML manuscript |
| `audit_backup/` | Pre-audit backup files (preserved; do not delete) |
| `FINAL_AUDIT_REPORT.md` | Requirement-by-requirement audit status |
| `REVISION_RESPONSE.md` | Point-by-point response to Revision 1 and Revision 2 |
| `SUBMISSION_READINESS.md` | Faculty/journal readiness assessment |

---

## 7. Reference Audit Reproducibility

The reference audit was verified programmatically:
- Parses all `[N] ...` entries from the `## References` section
- Scans all `[N]` bracket patterns in the manuscript body
- Reports uncited entries and 2022–2026 recency percentage

Final verified state: **35 references, 28/35 (80.0%) from 2022–2026, 0 uncited**.

Replacement reference [31] (Li et al. 2022) verified via:
- DBLP (uni-trier.de): title, authors, journal, volume, pages confirmed
- Semantic Scholar: title, year, DOI confirmed
- ResearchGate: abstract and bibliographic metadata confirmed
- DOI: https://doi.org/10.1016/j.future.2022.07.016

---

## 8. Known Restrictions and Limitations

1. **Simulation only.** All results are from simulation with synthetic traffic on programmatically constructed topologies. No physical SDN hardware (Mininet, P4 switches) was used.
2. **External validity not established.** Results may not generalize to production SDN deployments, data-center topologies, or real traffic distributions.
3. **Windows path separators.** On Linux/macOS, replace backslashes with forward slashes.
4. **No network access required.** All experiments run fully offline using in-memory simulation.
5. **Partial non-determinism in fault diagnosis.** `src/causal_engine.py`'s `diagnose_causal_faults` method adds measurement noise via `np.random.normal()` using the global NumPy random state, which is never explicitly seeded. This introduces small non-deterministic perturbations to Bayesian fault posteriors. Campaigns 2, 4, and 5 are fully deterministic (seeded `FaultGenerator` RNG drives all outcomes), but Campaigns 1 and 3 may exhibit minor cross-run variation in timing-sensitive metrics (recovery_time_ms, latency_ms). Core metrics (success rate, switches_modified, intervention_cost, risk_post) and all statistical significance decisions are stable across reruns.
6. **Timing-dependent metrics.** Campaign 6 measures wall-clock execution time, which varies with hardware and system load. The sub-16 ms claim is specific to the benchmark hardware (Intel Core i5-8600K, 16 GB RAM).

---

## 9. Verification Checklist

- [x] `python -m unittest experiments.test_audited_defects -v` → 13/13 OK
- [x] `python experiments/test_components.py` → All PASSED
- [x] `python experiments/statistical_analysis.py` → 0 warnings
- [x] `git diff --check` → 0 issues
- [x] `python manuscript/convert_to_html.py` → HTML generated
- [x] Reference [31] replaced with verified Li et al. 2022 → 28/35 = 80.0%
- [x] All 35 bibliography entries cited in manuscript body → 0 uncited
