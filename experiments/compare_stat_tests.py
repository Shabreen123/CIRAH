"""Compare original vs regenerated hypothesis test results."""
import pandas as pd
import numpy as np

orig = pd.read_csv("results_original_backup/hypothesis_tests_cirah_vs_dynamic.csv")
regen = pd.read_csv("results/hypothesis_tests_cirah_vs_dynamic.csv")

# Merge on topology, k_failures, metric
merged = pd.merge(orig, regen, on=["topology", "k_failures", "metric"], suffixes=("_orig", "_regen"))

print("KEY METRIC COMPARISON: Regenerated vs Original hypothesis tests")
print("=" * 80)
for _, row in merged.iterrows():
    p_orig = row.get("Wilcoxon_p_raw_orig", float("nan"))
    p_regen = row.get("Wilcoxon_p_raw_regen", float("nan"))
    cm_orig = row.get("CIRAH_mean_orig", float("nan"))
    cm_regen = row.get("CIRAH_mean_regen", float("nan"))
    dm_orig = row.get("DynamicSP_mean_orig", float("nan"))
    dm_regen = row.get("DynamicSP_mean_regen", float("nan"))
    dz_orig = row.get("Paired_Cohens_dz_orig", float("nan"))
    dz_regen = row.get("Paired_Cohens_dz_regen", float("nan"))

    sig_primary_orig = row.get("Sig_Primary_Abilene_Holm_p05_orig", False)
    sig_primary_regen = row.get("Sig_Primary_Abilene_Holm_p05_regen", False)
    sig_omnibus_orig = row.get("Sig_Omnibus_Holm_p05_orig", False)
    sig_omnibus_regen = row.get("Sig_Omnibus_Holm_p05_regen", False)

    # Check p-value match (within 10% relative tolerance for non-NaN)
    if pd.isna(p_orig) and pd.isna(p_regen):
        p_match = "NaN=NaN"
    elif pd.isna(p_orig) != pd.isna(p_regen):
        p_match = "NaN MISMATCH"
    else:
        rel_diff = abs(p_orig - p_regen) / max(abs(p_orig), 1e-10)
        p_match = f"MATCH({rel_diff:.3f})" if rel_diff < 0.05 else f"DIFFER({rel_diff:.3f})"

    sig_match = ""
    if not pd.isna(p_orig):
        if sig_primary_orig != sig_primary_regen:
            sig_match = " SIGNIFICANCE_CHANGED"
        if sig_omnibus_orig != sig_omnibus_regen:
            sig_match += " OMNIBUS_CHANGED"

    topo = row["topology"]
    k = row["k_failures"]
    metric = row["metric"]
    print(f"  {topo:7s} k={k} {metric:20s}: CIRAH={cm_orig:.3f}/{cm_regen:.3f} "
          f"Dyn={dm_orig:.3f}/{dm_regen:.3f} dz={dz_orig:.3f}/{dz_regen:.3f} "
          f"p={p_orig:.5f}/{p_regen:.5f} [{p_match}]{sig_match}")

# Summary
print()
print("SIGNIFICANCE CHANGES:")
sig_changes = merged[
    (merged["Sig_Primary_Abilene_Holm_p05_orig"] != merged["Sig_Primary_Abilene_Holm_p05_regen"]) |
    (merged["Sig_Omnibus_Holm_p05_orig"] != merged["Sig_Omnibus_Holm_p05_regen"])
]
if len(sig_changes) == 0:
    print("  No significance decisions changed between original and regenerated.")
else:
    print(f"  {len(sig_changes)} row(s) changed significance!")
    print(sig_changes[["topology","k_failures","metric",
                        "Sig_Primary_Abilene_Holm_p05_orig","Sig_Primary_Abilene_Holm_p05_regen",
                        "Sig_Omnibus_Holm_p05_orig","Sig_Omnibus_Holm_p05_regen"]].to_string())
