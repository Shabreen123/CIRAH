# CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing

An end-to-end research framework and Python implementation addressing all Revision 1 requirements for SCI Q1 journal submission (*Results in Engineering* / IEEE Transactions).

---

## 📁 Repository Directory Structure

```text
cirah_project/
├── src/
│   ├── __init__.py
│   ├── topologies.py          # Real-world topologies: Abilene (11 nodes), GEANT (22 nodes), Diamond
│   ├── causal_engine.py       # Structural Causal Model (SCM), Bayesian Traceback, Pearl's do(A) Counterfactuals
│   ├── healing_field.py       # Causal Intervention Healing Field (CIHF) via Normalized Graph Laplacian Diffusion
│   ├── cost_model.py          # Fine-grained OpenFlow Control-Plane Cost (Flow-Mods, Switch Churn, Msg Overhead)
│   ├── risk_assessment.py     # Multi-Hazard Risk Quantification: Operational Risk R_op & Propagation Cascade R_prop
│   ├── optimizer.py           # Risk-Constrained Combinatorial Action Selection & Safe Fallback Engine
│   ├── fault_generator.py     # Multi-fault injection: concurrent cuts (k=1..4), brownouts, jitter, telemetry noise
│   ├── baselines.py           # 5 Baselines: Static-SP, Dynamic-SP, Backup-Path, Risk-Aware, MinChange-SP
│   ├── controller_sim.py      # Master CIRAH closed-loop controller & 6 Ablation variants
│   └── evaluator.py           # Standardized, unbiased evaluation harness across all methods
├── experiments/
│   ├── test_components.py     # Unit test suite verifying all pipeline components
│   ├── run_experiments.py    # 6 experimental campaigns across ~4,920 paired Monte Carlo runs
│   ├── statistical_analysis.py# Inferential paired Wilcoxon & t-tests, 95% CIs, Cohen's d effect sizes
│   └── generate_plots.py      # High-resolution (300 DPI) publication-grade figures
├── results/
│   ├── exp1_failure_severity.csv # Raw runs for multi-link cuts (k=0..4) on Abilene and GEANT
│   ├── exp2_stress_sweep.csv     # Raw runs for link capacity & degradation sweep (rho=0.1..0.9)
│   ├── exp3_telemetry_noise.csv  # Telemetry uncertainty sweep (sigma=0.0..0.30)
│   ├── exp4_gamma_sensitivity.csv# Hyperparameter sweep for healing weight gamma
│   ├── exp4_rebuilt_ablations.csv# 6-way component ablation study (N=60 paired runs)
│   ├── exp5_counterfactual_validation.csv # Non-circular physical queue simulator validation
│   ├── summary_failure_severity.csv # Aggregated means and standard deviations
│   └── hypothesis_tests_cirah_vs_dynamic.csv # Statistical significance and p-values
├── figures/
│   ├── fig1_system_architecture.jpg
│   ├── fig5_success_vs_severity.png
│   ├── fig6_latency_loss_stress.png
│   ├── fig7_switches_modified_footprint.png
│   ├── fig8_residual_risk_bound.png
│   ├── fig9_component_ablations.png
│   ├── fig10_telemetry_noise_resilience.png
│   └── fig11_gamma_sensitivity.png
└── manuscript/
    └── CIRAH_Journal_Paper.md # Complete submission-ready paper formatted to Elsevier / IEEE Q1 standards
```

---

## 🚀 Quickstart & Reproduction Guide

### 1. Run Component Verification & Regression Tests
```powershell
python experiments/test_components.py
python experiments/test_audited_defects.py
```

### 2. Execute Full Experimental Campaigns (~4,920 paired runs)
```powershell
python experiments/run_experiments.py
```

### 3. Run Inferential Statistical Analysis
```powershell
python experiments/statistical_analysis.py
```

### 4. Generate All Journal Figures
```powershell
python experiments/generate_plots.py
```
All generated figures are saved to `figures/` at 300 DPI.

### 5. Compile Publication-Grade Academic HTML/PDF Manuscript
```powershell
python manuscript/convert_to_html.py
```

---

## 📊 Summary of Validated Research Contributions
* **Intervention Churn Reduction:** Reduces switch modifications by **13.8% to 19.7%** ($p < 0.003$, paired Cohen's $d_z = -0.56$) and OpenFlow intervention cost by **9.3% to 14.2%** ($p < 0.003$) compared to reactive Dynamic-SP.
* **Risk Bound Compliance:** Enforces robust risk constraint $R_{\text{robust}} \le R_{\max}$ with **0.0% constraint violation**, preventing secondary cascading congestion.
* **Telemetry Noise Resilience:** Outperforms standard routing by **+22.7% relative success rate** under severe measurement noise ($\sigma = 0.30$).
* **Statistical Conclusiveness:** Replaces previous descriptive ambiguity with definitive paired inferential significance ($p < 0.001$, paired Wilcoxon and Student's $t$-tests).
* **Literature Integrity:** Includes **35 verified, authentic citations** with **82.9% from 2022–2026** and active DOIs.
