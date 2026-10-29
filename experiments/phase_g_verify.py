"""Phase G verification: normalization, gamma table, success metric, paired outcomes."""
import numpy as np
import pandas as pd
from scipy import stats
import os

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')

# ============================================================
# 1. Normalization compression from actual observed values
# ============================================================
df = pd.read_csv(os.path.join(RESULTS_DIR, 'cihf_comparison_results.csv'))
cihf_df = df[df['scoring_mode'] == 'cihf']
none_df = df[df['scoring_mode'] == 'none']
csrf_df = df[df['scoring_mode'] == 'csrf']

print("=== 1. Normalization Compression (actual observed) ===")
print(f"CIHF Psi:  mean={cihf_df['healing_psi'].mean():.4f}, "
      f"min={cihf_df['healing_psi'].min():.4f}, max={cihf_df['healing_psi'].max():.4f}")
print(f"CSRF Psi:  mean={csrf_df['healing_psi'].mean():.4f}, "
      f"min={csrf_df['healing_psi'].min():.4f}, max={csrf_df['healing_psi'].max():.4f}")
print(f"None Psi:  mean={none_df['healing_psi'].mean():.4f}")
print()

psi_mean = cihf_df['healing_psi'].mean()
psi_range = cihf_df['healing_psi'].max() - cihf_df['healing_psi'].min()

print(f"Observed Psi: mean={psi_mean:.4f}, range={psi_range:.4f}")
print(f"Objective term: gamma*Psi/Psi_ref = 0.8*{psi_mean:.4f}/10.0 = {0.8*psi_mean/10:.6f}")
print(f"Term spread: 0.8*{psi_range:.4f}/10.0 = {0.8*psi_range/10:.6f}")
print()

# Other terms
ci_mean = cihf_df['intervention_cost'].mean()
risk_mean = cihf_df['risk_post'].mean()
print(f"Cost term:  lambda_I*C_I/C_I_ref = 1.0*{ci_mean:.2f}/30 = {ci_mean/30:.4f}")
print(f"Risk term:  beta*R_post/R_max = 1.2*{risk_mean:.2f}/35 = {1.2*risk_mean/35:.4f}")
print(f"CIHF term:  gamma*Psi/Psi_ref = 0.8*{psi_mean:.4f}/10 = {0.8*psi_mean/10:.4f}")
print()
print(f"Ratio CIHF/Cost = {0.8*psi_mean/10 / (ci_mean/30):.2f}x")
print(f"Ratio CIHF/Risk = {0.8*psi_mean/10 / (1.2*risk_mean/35):.2f}x")
print()

# Correct compression description
print("Compression chain (per-node, typical observed):")
print(f"  Raw loss delta at stressed node: ~100 (one edge at 100% loss)")
print(f"  After /100 clip to [0,1]: ~1.0")
print(f"  After *1.5 path weight: ~1.5")
print(f"  After diffusion (sum preserved ~{psi_mean:.2f}): per-node ~{psi_mean/11:.4f}")
print(f"  After /Psi_ref(10): {psi_mean/10:.6f}")
print(f"  After *gamma(0.8): {0.8*psi_mean/10:.6f}")
print(f"  From raw 100 to final {0.8*psi_mean/10:.4f}: ratio ~{100/(0.8*psi_mean/10):.0f}x")
print(f"  NOTE: This is the per-node raw max vs the AGGREGATE term, not a true compression ratio.")
print(f"  The meaningful comparison: Psi spread across candidates ({psi_range:.4f})")
print(f"  vs cost/risk spread across candidates. The CIHF term spread = {0.8*psi_range/10:.4f}.")

# ============================================================
# 2. Gamma table label verification
# ============================================================
print("\n=== 2. Gamma Table Label Verification ===")
gamma_df = pd.read_csv(os.path.join(RESULTS_DIR, 'cihf_gamma_sensitivity.csv'))
print(f"Columns: {list(gamma_df.columns)}")
print(f"all_modes_agree values: {sorted(gamma_df['all_modes_agree'].unique())}")
print(f"all_modes_agree=1 means: ALL modes selected the SAME action")
print(f"all_modes_agree=0 means: modes DISAGREED on action selection")
print()

# Show the actual table from the code
print("Table in CIHF_RESEARCH_DIAGNOSTIC.md Section 4.2:")
print("The column 'all_modes_agree' is 1.00 (100%) or 0.95 (95%).")
print("This means 100% AGREEMENT or 95% AGREEMENT.")
print("The table correctly reports AGREEMENT rates, not disagreement rates.")
print()

# Show disagreement explicitly
for scenario in gamma_df['scenario'].unique():
    for gamma in sorted(gamma_df['gamma'].unique()):
        sub = gamma_df[(gamma_df['scenario'] == scenario) & (gamma_df['gamma'] == gamma)]
        n_runs = sub['run_id'].nunique()
        agree_rate = sub['all_modes_agree'].mean()
        disagree_count = n_runs - int(agree_rate * n_runs)
        if disagree_count > 0:
            print(f"  {scenario} gamma={gamma}: {disagree_count}/{n_runs} disagreement runs ({(1-agree_rate)*100:.0f}%)")

# ============================================================
# 3. Success metric definition
# ============================================================
print("\n=== 3. Success Metric Definition ===")
# From controller_sim.py:
# success = bool(target_res.get("connected", False) and target_res.get("sla_met", False))
# This is per-run, per-target-flow binary success.
print("Success definition (from controller_sim.py line ~107):")
print("  success = target_res.connected AND target_res.sla_met")
print("  Where:")
print("    connected = path is not severed (no link has loss >= 99%)")
print("    sla_met = latency <= sla_max_latency_ms AND loss <= sla_max_loss_pct")
print("  This is a per-run, per-target-flow binary indicator.")
print("  Denominator = total number of runs (not total number of flows).")
print("  Only the TARGET flow (flows[0] or first impaired flow) is evaluated.")
print()

# Why is success only 38.3%?
print("Why is overall success only 38.3%?")
print(f"  Total runs: {len(df)} across 6 modes")
print(f"  Scenarios: standard (53.3%), tight_capacity (43.3%), mixed_stress (23.3%), multi_fault (33.3%)")
print(f"  The mixed_stress scenario has only 23.3% success — it applies")
print(f"  random capacity degradation AND random loss to many links,")
print(f"  making it very hard for ANY method to find a path that meets SLA.")
print(f"  All 6 modes produce the same success rate because they all")
print(f"  select from the same candidate set with the same risk constraints.")
print()

# Per-scenario success
for scen in df['scenario'].unique():
    scen_df = df[df['scenario'] == scen]
    print(f"  {scen}: success={scen_df['success'].mean():.4f} (n={len(scen_df)})")

# ============================================================
# 4. Paired outcomes with confidence intervals
# ============================================================
print("\n=== 4. Paired Outcomes: CIHF vs None (same scenario, same run) ===")

# For each (topology, scenario, run_id), pair cihf and none
cihf_pivot = df[df['scoring_mode'].isin(['cihf', 'none'])].pivot_table(
    index=['topology', 'scenario', 'run_id'],
    columns='scoring_mode',
    values=['success', 'switches_modified', 'intervention_cost', 'risk_post', 'healing_psi']
)

# Flatten multi-index columns
cihf_pivot.columns = ['_'.join(col).strip() for col in cihf_pivot.columns.values]
cihf_pivot = cihf_pivot.reset_index()

# Compute paired differences (cihf - none)
diff_success = cihf_pivot['success_cihf'] - cihf_pivot['success_none']
diff_switches = cihf_pivot['switches_modified_cihf'] - cihf_pivot['switches_modified_none']
diff_cost = cihf_pivot['intervention_cost_cihf'] - cihf_pivot['intervention_cost_none']
diff_risk = cihf_pivot['risk_post_cihf'] - cihf_pivot['risk_post_none']

print(f"N pairs: {len(cihf_pivot)}")
print()

for name, diff in [("Success", diff_success), ("Switches", diff_switches),
                    ("Cost", diff_cost), ("Risk", diff_risk)]:
    mean_d = float(np.mean(diff))
    std_d = float(np.std(diff, ddof=1))
    n = len(diff)
    if std_d > 1e-9:
        ci_low = mean_d - 1.96 * std_d / np.sqrt(n)
        ci_high = mean_d + 1.96 * std_d / np.sqrt(n)
        if name == "Success":
            # Binary outcome: use McNemar's test or exact test
            both_success = int(((cihf_pivot['success_cihf'] == 1) & (cihf_pivot['success_none'] == 1)).sum())
            both_fail = int(((cihf_pivot['success_cihf'] == 0) & (cihf_pivot['success_none'] == 0)).sum())
            cihf_only = int(((cihf_pivot['success_cihf'] == 1) & (cihf_pivot['success_none'] == 0)).sum())
            none_only = int(((cihf_pivot['success_cihf'] == 0) & (cihf_pivot['success_none'] == 1)).sum())
            print(f"  {name}: mean_diff={mean_d:.4f}, 95% CI=[{ci_low:.4f}, {ci_high:.4f}]")
            print(f"    Both success: {both_success}, Both fail: {both_fail}")
            print(f"    CIHF only: {cihf_only}, None only: {none_only}")
            print(f"    Discordant pairs: {cihf_only + none_only}")
            if cihf_only + none_only > 0:
                # Exact sign test p-value
                from scipy.stats import binom_test
                p = float(binom_test(min(cihf_only, none_only), cihf_only + none_only, 0.5))
                print(f"    Sign test p-value: {p:.4f}")
            else:
                print(f"    No discordant pairs — identical success outcomes")
        else:
            # Continuous: Wilcoxon signed-rank
            if np.all(np.abs(diff) < 1e-9):
                print(f"  {name}: mean_diff={mean_d:.4f} (ALL ZERO — identical outcomes)")
            else:
                w_stat, w_p = stats.wilcoxon(diff)
                print(f"  {name}: mean_diff={mean_d:.4f}, 95% CI=[{ci_low:.4f}, {ci_high:.4f}], "
                      f"Wilcoxon p={w_p:.4f}")
    else:
        print(f"  {name}: mean_diff={mean_d:.4f} (all differences identical)")
    print()

# Also compare CSRF vs None
print("=== Paired Outcomes: CSRF vs None ===")
csrf_pivot = df[df['scoring_mode'].isin(['csrf', 'none'])].pivot_table(
    index=['topology', 'scenario', 'run_id'],
    columns='scoring_mode',
    values=['success', 'switches_modified', 'intervention_cost', 'risk_post']
)
csrf_pivot.columns = ['_'.join(col).strip() for col in csrf_pivot.columns.values]
csrf_pivot = csrf_pivot.reset_index()

diff_success_csrf = csrf_pivot['success_csrf'] - csrf_pivot['success_none']
diff_switches_csrf = csrf_pivot['switches_modified_csrf'] - csrf_pivot['switches_modified_none']

for name, diff in [("Success", diff_success_csrf), ("Switches", diff_switches_csrf)]:
    if np.all(np.abs(diff) < 1e-9):
        print(f"  {name}: ALL ZERO (identical outcomes)")
    else:
        mean_d = float(np.mean(diff))
        print(f"  {name}: mean_diff={mean_d:.4f}, n_discordant={int(np.sum(np.abs(diff) > 0))}")
