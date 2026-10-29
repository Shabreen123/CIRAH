"""Compare original vs regenerated experiment results."""
import pandas as pd
import numpy as np
import os

ORIG = "results_original_backup"
REGEN = "results"

files_and_skip = {
    "exp1_failure_severity.csv": ["recovery_time_ms", "decision_latency_ms"],
    "exp2_stress_sweep.csv": ["recovery_time_ms"],
    "exp3_telemetry_noise.csv": [],
    "exp4_rebuilt_ablations.csv": ["recovery_time_ms"],
    "exp5_counterfactual_validation.csv": [],
}

for f, skip_cols in files_and_skip.items():
    orig = pd.read_csv(os.path.join(ORIG, f))
    regen = pd.read_csv(os.path.join(REGEN, f))

    compare_cols = [c for c in orig.columns
                    if c not in skip_cols
                    and orig[c].dtype in ["float64", "int64"]
                    and c in regen.columns]

    max_diff = 0
    max_col = ""
    for col in compare_cols:
        diff = np.abs(orig[col].values - regen[col].values)
        md = np.nanmax(diff) if len(diff) > 0 else 0
        if md > max_diff:
            max_diff = md
            max_col = col

    # Count rows with any difference in core metrics (excluding latency/loss which have noise)
    core_cols = [c for c in compare_cols if c not in ["latency_ms", "loss_pct"]]
    diffs = 0
    for col in core_cols:
        diffs += int((orig[col].values != regen[col].values).sum())

    print(f"\n{f}:")
    print(f"  Compared {len(compare_cols)} cols (skipping {skip_cols})")
    print(f"  Max diff: {max_diff:.6f} in {max_col}")
    print(f"  Core metric value mismatches (excl latency/loss): {diffs}")

    # Show summary stats for key metrics
    for key_col in ["success", "switches_modified", "intervention_cost", "risk_post"]:
        if key_col in compare_cols:
            om = orig[key_col].mean()
            rm = regen[key_col].mean()
            match_str = "MATCH" if abs(om - rm) < 1e-6 else "DIFFERS"
            print(f"  {key_col}: orig_mean={om:.4f} regen_mean={rm:.4f} [{match_str}]")

    # For latency_ms (which has non-deterministic noise from np.random.normal)
    if "latency_ms" in compare_cols:
        om = orig["latency_ms"].mean()
        rm = regen["latency_ms"].mean()
        print(f"  latency_ms: orig_mean={om:.4f} regen_mean={rm:.4f} (non-deterministic noise expected)")

    # Check for structural differences (rows, columns, unique methods)
    if "method" in orig.columns:
        orig_methods = set(orig["method"].unique())
        regen_methods = set(regen["method"].unique())
        if orig_methods != regen_methods:
            print(f"  METHOD MISMATCH: orig={orig_methods} regen={regen_methods}")
        else:
            print(f"  Methods match: {sorted(orig_methods)}")

    if "topology" in orig.columns:
        orig_topo = set(orig["topology"].unique())
        regen_topo = set(regen["topology"].unique())
        print(f"  Topologies match: {orig_topo == regen_topo}")

    if "variant" in orig.columns:
        orig_var = set(orig["variant"].unique())
        regen_var = set(regen["variant"].unique())
        print(f"  Variants match: {orig_var == regen_var}")
