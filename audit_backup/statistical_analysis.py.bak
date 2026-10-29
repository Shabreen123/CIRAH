"""
CIRAH: Statistical Inferential Analysis Engine (Revision 2 Rebuilt)
Calculates:
1. Paired Differences: D_i = X_{CIRAH, i} - X_{DynamicSP, i}
2. Within-Pair Paired Cohen's d_z = mean(D) / std(D)
3. Paired Wilcoxon Signed-Rank Test and Paired Student's t-test p-values
4. Two-Sided 95% Confidence Intervals for means and paired differences
5. Component-Level 6-Way Ablation Statistics
6. Counterfactual Prediction Errors (MAE) and Action Ranking Spearman rho
7. Scalability and Decision Latency Percentiles (p50, p95, Max)
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Dict

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))

def compute_paired_cohens_dz(d: np.ndarray) -> float:
    """Computes within-pair Cohen's d_z = mean(D) / std(D)."""
    s_d = np.std(d, ddof=1)
    if s_d < 1e-9:
        return 0.0
    return float(np.mean(d) / s_d)

def compute_ci(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes two-sided 95% confidence interval for the mean."""
    n = len(data)
    mean = np.mean(data)
    sem = stats.sem(data)
    if sem < 1e-9 or n < 2:
        return mean, mean
    h = sem * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return float(mean - h), float(mean + h)

def analyze_severity_campaign():
    """Analyzes exp1_failure_severity.csv across topologies, k values, and methods."""
    csv_path = os.path.join(RESULTS_DIR, "exp1_failure_severity.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print("\n" + "="*80)
    print("CAMPAIGN 1: FAILURE SEVERITY STATISTICAL ANALYSIS")
    print("="*80)

    # Summary table
    metrics = ["success", "latency_ms", "loss_pct", "risk_post", "switches_modified", "intervention_cost", "recovery_time_ms"]
    summary = df.groupby(["topology", "k_failures", "method"])[metrics].agg(["mean", "std"]).reset_index()
    summary_path = os.path.join(RESULTS_DIR, "summary_failure_severity.csv")
    summary.to_csv(summary_path, index=False)

    # Inferential Paired Tests: CIRAH vs Dynamic-SP
    test_records = []
    for topo in ["abilene", "geant"]:
        for k in [1, 2, 3]:
            df_k = df[(df["topology"] == topo) & (df["k_failures"] == k)]
            cirah_runs = df_k[df_k["method"] == "CIRAH"].sort_values("run_id")
            dyn_runs = df_k[df_k["method"] == "Dynamic-SP"].sort_values("run_id")

            for m in ["switches_modified", "intervention_cost", "recovery_time_ms", "risk_post", "success"]:
                v_cirah = cirah_runs[m].values
                v_dyn = dyn_runs[m].values
                diff = v_cirah - v_dyn

                mean_c = np.mean(v_cirah)
                mean_d = np.mean(v_dyn)
                mean_diff = np.mean(diff)
                pct_reduction = ((mean_d - mean_c) / mean_d * 100.0) if mean_d > 1e-6 else 0.0

                ci_diff = compute_ci(diff)
                d_z = compute_paired_cohens_dz(diff)

                try:
                    stat_w, p_w = stats.wilcoxon(v_cirah, v_dyn)
                except ValueError:
                    stat_w, p_w = 0.0, 1.0

                stat_t, p_t = stats.ttest_rel(v_cirah, v_dyn)

                test_records.append({
                    "topology": topo,
                    "k_failures": k,
                    "metric": m,
                    "CIRAH_mean": mean_c,
                    "DynamicSP_mean": mean_d,
                    "Pct_Reduction": pct_reduction,
                    "Mean_Diff": mean_diff,
                    "Diff_95CI": f"[{ci_diff[0]:.2f}, {ci_diff[1]:.2f}]",
                    "Paired_Cohens_dz": d_z,
                    "Wilcoxon_p": p_w,
                    "TTest_p": p_t,
                    "Significant_p05": bool(p_w < 0.05 or p_t < 0.05)
                })

    test_df = pd.DataFrame(test_records)
    test_out = os.path.join(RESULTS_DIR, "hypothesis_tests_cirah_vs_dynamic.csv")
    test_df.to_csv(test_out, index=False)
    print(test_df[test_df["topology"]=="abilene"][["k_failures", "metric", "CIRAH_mean", "DynamicSP_mean", "Pct_Reduction", "Paired_Cohens_dz", "Wilcoxon_p", "Significant_p05"]].to_string())

def analyze_rebuilt_ablations():
    """Analyzes exp4_rebuilt_ablations.csv: 6-way ablation comparison."""
    csv_path = os.path.join(RESULTS_DIR, "exp4_rebuilt_ablations.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print("\n" + "="*80)
    print("CAMPAIGN 4: 6-WAY COMPONENT ABLATION ANALYSIS (N=60 Paired Runs)")
    print("="*80)

    agg = df.groupby("variant").agg(
        success_mean=("success", "mean"),
        sla_violation_rate=("sla_met", lambda x: (1.0 - np.mean(x)) * 100.0),
        constraint_violation_pct=("constraint_violation", lambda x: np.mean(x) * 100.0),
        switches_mean=("switches_modified", "mean"),
        cost_mean=("intervention_cost", "mean"),
        risk_mean=("risk_post", "mean"),
        healing_psi_mean=("healing_psi", "mean")
    ).reset_index()

    order = ["CIRAH-full", "CIRAH-noCausal", "CIRAH-noCF", "CIRAH-noCIHF", "CIRAH-noRisk", "CIRAH-noInterv"]
    agg["sort_key"] = agg["variant"].apply(lambda v: order.index(v) if v in order else 99)
    agg = agg.sort_values("sort_key").drop(columns=["sort_key"])

    agg_out = os.path.join(RESULTS_DIR, "summary_ablation_metrics.csv")
    agg.to_csv(agg_out, index=False)
    print(agg.to_string(index=False))

def analyze_counterfactual_validation():
    """Analyzes exp5_counterfactual_validation.csv."""
    csv_path = os.path.join(RESULTS_DIR, "exp5_counterfactual_validation.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print("\n" + "="*80)
    print("CAMPAIGN 5: COUNTERFACTUAL PREDICTION VALIDATION (N=60)")
    print("="*80)
    print(f"Latency MAE: {df['latency_mae_ms'].mean():.2f} +/- {df['latency_mae_ms'].std():.2f} ms")
    print(f"Packet Loss MAE: {df['loss_mae_pct'].mean():.2f} +/- {df['loss_mae_pct'].std():.2f} %")
    print(f"Spearman Action Ranking Correlation: {df['spearman_rank_correlation'].mean():.3f} +/- {df['spearman_rank_correlation'].std():.3f}")

def analyze_computational_scalability():
    """Analyzes exp6_computational_scalability.csv."""
    csv_path = os.path.join(RESULTS_DIR, "exp6_computational_scalability.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print("\n" + "="*80)
    print("CAMPAIGN 6: COMPUTATIONAL SCALABILITY & LATENCY PROFILING")
    print("="*80)
    print(df.to_string(index=False))

if __name__ == "__main__":
    analyze_severity_campaign()
    analyze_rebuilt_ablations()
    analyze_counterfactual_validation()
    analyze_computational_scalability()
