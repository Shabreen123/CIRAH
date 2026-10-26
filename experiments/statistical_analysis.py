"""
CIRAH: Statistical Inferential Analysis Engine (Audited and Rigorous)
Calculates:
1. Paired Differences: D_i = X_{CIRAH, i} - X_{DynamicSP, i} with explicit run_id and seed pairing validation
2. Within-Pair Paired Cohen's d_z = mean(D) / std(D)
3. Paired Wilcoxon Signed-Rank Test (prespecified primary inferential test)
4. Paired Student's t-test (reported transparently for normality contrast)
5. Multiplicity corrections across all planned comparisons:
   - Family 1 (Planned Omnibus Family, N=30): 2 topologies x 3 failure levels x 5 metrics
     Reported with Holm step-down and Bonferroni adjusted p-values preserving the full declared family size of 30
   - Family 2 (Primary Abilene Hypothesis Family, N=6): switch churn and intervention cost across k=1, 2, 3
6. Safe, warning-free handling of all-zero paired differences (reported as non-informative)
7. Two-Sided 95% Confidence Intervals for means and paired differences
8. Component-Level 6-Way Ablation Statistics
9. Counterfactual Prediction Errors (MAE) and Action Ranking Spearman rho
10. Scalability and Decision Latency Percentiles (p50, p95, Max)
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Dict, Optional

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))

def compute_paired_cohens_dz(d: np.ndarray) -> float:
    """Computes within-pair Cohen's d_z = mean(D) / std(D)."""
    s_d = np.std(d, ddof=1)
    if s_d < 1e-9:
        return 0.0
    return float(np.mean(d) / s_d)

def compute_ci(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes two-sided 95% confidence interval for paired difference or mean."""
    n = len(data)
    mean = float(np.mean(data))
    sem = stats.sem(data)
    if sem < 1e-9 or n < 2:
        return mean, mean
    h = sem * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return float(mean - h), float(mean + h)

def holm_bonferroni_adjust(p_values: List[float], family_size: Optional[int] = None) -> List[float]:
    """
    Applies Holm-Bonferroni step-down adjustment to a list of p-values for a declared family size.
    Preserves NaN positions for non-applicable / non-informative tests while counting all
    hypotheses in the family against the family-wise error rate (FWER).
    """
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    n_family = len(valid_indices) if family_size is None else family_size
    sorted_pairs = sorted([(i, p_values[i]) for i in valid_indices], key=lambda x: x[1])

    adj = {i: np.nan for i in range(len(p_values))}
    cum_max = 0.0
    for rank, (orig_idx, p) in enumerate(sorted_pairs):
        multiplier = n_family - rank
        raw_adj = min(1.0, p * multiplier)
        cum_max = max(cum_max, raw_adj)
        adj[orig_idx] = float(cum_max)
    return [adj[i] for i in range(len(p_values))]

def bonferroni_adjust(p_values: List[float], family_size: Optional[int] = None) -> List[float]:
    """
    Applies Bonferroni single-step adjustment using the declared family size.
    Preserves NaN positions for non-applicable / non-informative tests.
    """
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    n_family = len(valid_indices) if family_size is None else family_size
    return [float(min(1.0, p * n_family)) if not np.isnan(p) else np.nan for p in p_values]

def validate_and_pair_runs(df_k: pd.DataFrame, topology: str, k: int) -> pd.DataFrame:
    """
    Explicitly validates that CIRAH and Dynamic-SP runs are paired by run_id and seed.
    Raises ValueError on duplicates, missing pairs, or mismatched seeds.
    """
    cirah = df_k[df_k['method'] == 'CIRAH'].copy()
    dyn = df_k[df_k['method'] == 'Dynamic-SP'].copy()

    # Check for duplicate run IDs within each method
    if cirah['run_id'].duplicated().any():
        dups = cirah[cirah['run_id'].duplicated()]['run_id'].tolist()
        raise ValueError(f'Duplicate run_id detected in CIRAH runs for {topology} k={k}: {dups}')
    if dyn['run_id'].duplicated().any():
        dups = dyn[dyn['run_id'].duplicated()]['run_id'].tolist()
        raise ValueError(f'Duplicate run_id detected in Dynamic-SP runs for {topology} k={k}: {dups}')

    # Inner merge on run_id and seed
    merged = pd.merge(cirah, dyn, on=['run_id', 'seed'], suffixes=('_cirah', '_dyn'))

    # Strict check: all runs must be successfully paired
    if len(merged) != len(cirah) or len(merged) != len(dyn):
        missing_c = set(cirah['run_id']) - set(dyn['run_id'])
        missing_d = set(dyn['run_id']) - set(cirah['run_id'])
        raise ValueError(
            f'Pairing mismatch for {topology} k={k}: '
            f'CIRAH count={len(cirah)}, Dynamic-SP count={len(dyn)}, matched={len(merged)}. '
            f'Unmatched CIRAH runs: {missing_c}, Unmatched Dynamic-SP runs: {missing_d}'
        )
    return merged

def analyze_severity_campaign():
    """Analyzes exp1_failure_severity.csv across topologies, k values, and methods."""
    csv_path = os.path.join(RESULTS_DIR, 'exp1_failure_severity.csv')
    if not os.path.exists(csv_path):
        print(f'Warning: {csv_path} not found.')
        return

    df = pd.read_csv(csv_path)
    print('\n' + '='*80)
    print('CAMPAIGN 1: FAILURE SEVERITY STATISTICAL ANALYSIS')
    print('='*80)

    # 1. Summary table across all methods and failure severities
    metrics = ['success', 'latency_ms', 'loss_pct', 'risk_post', 'switches_modified', 'intervention_cost', 'recovery_time_ms']
    summary = df.groupby(['topology', 'k_failures', 'method'])[metrics].agg(['mean', 'std']).reset_index()
    summary_path = os.path.join(RESULTS_DIR, 'summary_failure_severity.csv')
    summary.to_csv(summary_path, index=False)

    # 2. Planned Inferential Comparisons: CIRAH vs Dynamic-SP
    topologies = ['abilene', 'geant']
    k_values = [1, 2, 3]
    eval_metrics = ['switches_modified', 'intervention_cost', 'recovery_time_ms', 'risk_post', 'success']

    test_records = []

    for topo in topologies:
        for k in k_values:
            df_k = df[(df['topology'] == topo) & (df['k_failures'] == k)]
            merged = validate_and_pair_runs(df_k, topo, k)

            for m in eval_metrics:
                v_c = merged[m + '_cirah'].values.astype(float)
                v_d = merged[m + '_dyn'].values.astype(float)

                # Check for NaN / Infinite observations
                if np.isnan(v_c).any() or np.isnan(v_d).any() or np.isinf(v_c).any() or np.isinf(v_d).any():
                    raise ValueError(f'NaN or infinite value encountered in {topo} k={k} metric {m}')

                diff = v_c - v_d
                n_pairs = len(diff)
                mean_c = float(np.mean(v_c))
                mean_d = float(np.mean(v_d))
                mean_diff = float(np.mean(diff))
                pct_reduction = float((mean_d - mean_c) / mean_d * 100.0) if abs(mean_d) > 1e-6 else 0.0

                ci_diff = compute_ci(diff)
                d_z = compute_paired_cohens_dz(diff)

                # Safe handling of all-zero paired differences (e.g. success rate when both methods succeed identically)
                all_zero = bool(np.all(np.abs(diff) < 1e-9))
                if all_zero:
                    p_w = np.nan
                    p_t = np.nan
                    test_valid = False
                    test_note = 'Zero difference across all pairs (non-informative test)'
                else:
                    res_w = stats.wilcoxon(v_c, v_d)
                    p_w = float(res_w.pvalue)
                    res_t = stats.ttest_rel(v_c, v_d)
                    p_t = float(res_t.pvalue)
                    test_valid = True
                    test_note = 'Valid paired test'

                test_records.append({
                    'topology': topo,
                    'k_failures': k,
                    'metric': m,
                    'n_pairs': n_pairs,
                    'CIRAH_mean': mean_c,
                    'DynamicSP_mean': mean_d,
                    'Pct_Reduction': pct_reduction,
                    'Mean_Diff': mean_diff,
                    'Diff_95CI': f'[{ci_diff[0]:.2f}, {ci_diff[1]:.2f}]',
                    'Paired_Cohens_dz': d_z,
                    'Wilcoxon_p_raw': p_w,
                    'TTest_p_raw': p_t,
                    'test_valid': test_valid,
                    'test_note': test_note
                })

    test_df = pd.DataFrame(test_records)

    # 3. Multiplicity corrections across the omnibus family (declared N=30 comparisons)
    raw_p_list = test_df['Wilcoxon_p_raw'].tolist()
    test_df['Omnibus_Holm_p'] = holm_bonferroni_adjust(raw_p_list, family_size=30)
    test_df['Omnibus_Bonferroni_p'] = bonferroni_adjust(raw_p_list, family_size=30)

    # 4. Primary Prespecified Abilene Family (prespecified N=6 comparisons: switch modifications and intervention cost at k=1,2,3)
    abilene_primary_mask = (test_df['topology'] == 'abilene') & (test_df['metric'].isin(['switches_modified', 'intervention_cost']))
    prim_p = [row['Wilcoxon_p_raw'] if abilene_primary_mask.iloc[idx] else np.nan for idx, row in test_df.iterrows()]
    prim_valid = [p for p in prim_p if not np.isnan(p)]
    test_df['Primary_Abilene_Holm_p'] = np.nan
    test_df['Primary_Abilene_Bonferroni_p'] = np.nan
    if len(prim_valid) == 6:
        adj_h = holm_bonferroni_adjust(prim_valid, family_size=6)
        adj_b = bonferroni_adjust(prim_valid, family_size=6)
        prim_indices = test_df[abilene_primary_mask].index
        for idx_pos, df_idx in enumerate(prim_indices):
            test_df.loc[df_idx, 'Primary_Abilene_Holm_p'] = adj_h[idx_pos]
            test_df.loc[df_idx, 'Primary_Abilene_Bonferroni_p'] = adj_b[idx_pos]

    # Explicit significance decisions (Wilcoxon signed-rank test with FWER alpha=0.05)
    test_df['Sig_Raw_Wilcoxon_p05'] = test_df['Wilcoxon_p_raw'].apply(lambda p: bool(p < 0.05) if not np.isnan(p) else False)
    test_df['Sig_Omnibus_Holm_p05'] = test_df['Omnibus_Holm_p'].apply(lambda p: bool(p < 0.05) if not np.isnan(p) else False)
    test_df['Sig_Omnibus_Bonferroni_p05'] = test_df['Omnibus_Bonferroni_p'].apply(lambda p: bool(p < 0.05) if not np.isnan(p) else False)
    test_df['Sig_Primary_Abilene_Holm_p05'] = test_df['Primary_Abilene_Holm_p'].apply(lambda p: bool(p < 0.05) if not np.isnan(p) else False)

    test_out = os.path.join(RESULTS_DIR, 'hypothesis_tests_cirah_vs_dynamic.csv')
    test_df.to_csv(test_out, index=False)
    print(f'Hypothesis tests saved to {test_out}')

    print('\n--- Abilene Failure Severity Statistical Results ---')
    disp_cols = ['k_failures', 'metric', 'CIRAH_mean', 'DynamicSP_mean', 'Pct_Reduction', 'Paired_Cohens_dz', 'Wilcoxon_p_raw', 'Omnibus_Holm_p', 'Sig_Omnibus_Holm_p05', 'Primary_Abilene_Holm_p', 'Sig_Primary_Abilene_Holm_p05']
    print(test_df[test_df['topology'] == 'abilene'][disp_cols].to_string(index=False))

    print('\n--- GEANT Failure Severity Statistical Results ---')
    disp_cols_g = ['k_failures', 'metric', 'CIRAH_mean', 'DynamicSP_mean', 'Pct_Reduction', 'Paired_Cohens_dz', 'Wilcoxon_p_raw', 'Omnibus_Holm_p', 'Sig_Omnibus_Holm_p05']
    print(test_df[test_df['topology'] == 'geant'][disp_cols_g].to_string(index=False))

def analyze_rebuilt_ablations():
    """Analyzes exp4_rebuilt_ablations.csv: 6-way ablation comparison."""
    csv_path = os.path.join(RESULTS_DIR, 'exp4_rebuilt_ablations.csv')
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print('\n' + '='*80)
    print('CAMPAIGN 4: 6-WAY COMPONENT ABLATION ANALYSIS (N=60 Paired Runs)')
    print('='*80)

    agg = df.groupby('variant').agg(
        success_mean=('success', 'mean'),
        sla_violation_rate=('sla_met', lambda x: float((1.0 - np.mean(x)) * 100.0)),
        constraint_violation_pct=('constraint_violation', lambda x: float(np.mean(x) * 100.0)),
        switches_mean=('switches_modified', 'mean'),
        cost_mean=('intervention_cost', 'mean'),
        risk_mean=('risk_post', 'mean'),
        healing_psi_mean=('healing_psi', 'mean')
    ).reset_index()

    order = ['CIRAH-full', 'CIRAH-noCausal', 'CIRAH-noCF', 'CIRAH-noCIHF', 'CIRAH-noRisk', 'CIRAH-noInterv']
    agg['sort_key'] = agg['variant'].apply(lambda v: order.index(v) if v in order else 99)
    agg = agg.sort_values('sort_key').drop(columns=['sort_key'])

    agg_out = os.path.join(RESULTS_DIR, 'summary_ablation_metrics.csv')
    agg.to_csv(agg_out, index=False)
    print(agg.to_string(index=False))

def analyze_counterfactual_validation():
    """Analyzes exp5_counterfactual_validation.csv."""
    csv_path = os.path.join(RESULTS_DIR, 'exp5_counterfactual_validation.csv')
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print('\n' + '='*80)
    print('CAMPAIGN 5: COUNTERFACTUAL PREDICTION VALIDATION (N=60)')
    print('='*80)
    print(f'Latency MAE: {df["latency_mae_ms"].mean():.2f} +/- {df["latency_mae_ms"].std():.2f} ms')
    print(f'Packet Loss MAE: {df["loss_mae_pct"].mean():.2f} +/- {df["loss_mae_pct"].std():.2f} %')

    # Safe ranking correlation reporting with dropna()
    rho_valid = df['spearman_rank_correlation'].dropna()
    print(f'Spearman Action Ranking Correlation: {rho_valid.mean():.3f} +/- {rho_valid.std():.3f} (N={len(rho_valid)} valid trials)')

    if 'myopic_spearman_rank_correlation' in df.columns:
        myo_valid = df['myopic_spearman_rank_correlation'].dropna()
        print(f'Myopic Baseline Ranking Correlation: {myo_valid.mean():.3f} +/- {myo_valid.std():.3f} (N={len(myo_valid)} valid trials)')

def analyze_computational_scalability():
    """Analyzes exp6_computational_scalability.csv."""
    csv_path = os.path.join(RESULTS_DIR, 'exp6_computational_scalability.csv')
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    print('\n' + '='*80)
    print('CAMPAIGN 6: COMPUTATIONAL SCALABILITY & LATENCY PROFILING')
    print('='*80)
    print(df.to_string(index=False))

if __name__ == '__main__':
    analyze_severity_campaign()
    analyze_rebuilt_ablations()
    analyze_counterfactual_validation()
    analyze_computational_scalability()
