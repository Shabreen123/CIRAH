"""
CIRAH: Publication Figure Generator
Generates high-resolution, vector/PNG figures (300 DPI) for the journal manuscript.
Adheres to Elsevier / IEEE publication style with standard color palettes,
distinct markers, clear legends, labeled units, and error bars / 95% CIs.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
FIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'figures'))
os.makedirs(FIG_DIR, exist_ok=True)

# Publication styling
plt.rcParams.update({
    "font.size": 11,
    "font.family": "serif",
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2.0,
    "lines.markersize": 7,
    "grid.alpha": 0.35,
    "grid.linestyle": "--"
})

PALETTE = {
    "CIRAH": "#1b9e77",           # Emerald Green
    "CIRAH-noCausal": "#d95f02",  # Rust Orange
    "CIRAH-noRisk": "#7570b3",    # Purple
    "CIRAH-noInterv": "#e7298a",  # Pink
    "Dynamic-SP": "#386cb0",      # Classic Blue
    "Static-SP": "#e41a1c",       # Crimson Red
    "Backup-Path": "#ff7f00",     # Deep Amber
    "Risk-Aware": "#984ea3",      # Violet
    "MinChange-SP": "#4daf4a"     # Leaf Green
}

MARKERS = {
    "CIRAH": "o",
    "CIRAH-noCausal": "s",
    "CIRAH-noRisk": "^",
    "CIRAH-noInterv": "D",
    "Dynamic-SP": "v",
    "Static-SP": "X",
    "Backup-Path": "P",
    "Risk-Aware": "*",
    "MinChange-SP": "h"
}

def plot_fig5_success_rate():
    """Figure 5: Recovery Success Rate across multi-failure severity (k=0..4) with 95% CIs."""
    csv_path = os.path.join(RESULTS_DIR, "exp1_failure_severity.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)
    df_ab = df[df["topology"] == "abilene"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    methods = ["CIRAH", "Dynamic-SP", "Backup-Path", "Risk-Aware", "MinChange-SP", "Static-SP"]

    for m in methods:
        sub = df_ab[df_ab["method"] == m]
        agg = sub.groupby("k_failures")["success"].agg(["mean", "sem"]).reset_index()
        ax.errorbar(
            agg["k_failures"], agg["mean"] * 100.0,
            yerr=agg["sem"] * 1.96 * 100.0,
            label=m,
            color=PALETTE.get(m, "#333333"),
            marker=MARKERS.get(m, "o"),
            capsize=4,
            capthick=1.2
        )

    ax.set_xlabel("Number of Simultaneous Link Failures ($k$)")
    ax.set_ylabel("Recovery Success Rate (%)")
    ax.set_title("Recovery Success Rate vs. Failure Severity (Abilene Topology)")
    ax.set_ylim(-5, 105)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.grid(True)
    ax.legend(frameon=True, loc="lower left")
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig5_success_vs_severity.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig6_latency_and_loss():
    """Figure 6: Dual-panel plot of End-to-End Latency and Packet Loss under Stress Sweep."""
    csv_path = os.path.join(RESULTS_DIR, "exp2_stress_sweep.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    methods = ["CIRAH", "CIRAH-noInterv", "Dynamic-SP", "Risk-Aware", "Static-SP"]

    for m in methods:
        sub = df[df["method"] == m]
        agg = sub.groupby("stress_rho").agg(
            lat_mean=("latency_ms", "mean"),
            lat_sem=("latency_ms", "sem"),
            loss_mean=("loss_pct", "mean"),
            loss_sem=("loss_pct", "sem")
        ).reset_index()

        ax1.errorbar(
            agg["stress_rho"], agg["lat_mean"],
            yerr=agg["lat_sem"] * 1.96,
            label=m,
            color=PALETTE.get(m, "#333333"),
            marker=MARKERS.get(m, "o"),
            capsize=3
        )

        ax2.errorbar(
            agg["stress_rho"], agg["loss_mean"],
            yerr=agg["loss_sem"] * 1.96,
            label=m,
            color=PALETTE.get(m, "#333333"),
            marker=MARKERS.get(m, "o"),
            capsize=3
        )

    ax1.set_xlabel("Traffic & Link Stress Level ($\\rho$)")
    ax1.set_ylabel("End-to-End Latency (ms)")
    ax1.set_title("(a) Latency vs. Network Stress")
    ax1.set_ylim(0, 120)
    ax1.grid(True)
    ax1.legend(frameon=True, loc="upper left")

    ax2.set_xlabel("Traffic & Link Stress Level ($\\rho$)")
    ax2.set_ylabel("Packet Loss Rate (%)")
    ax2.set_title("(b) Packet Loss vs. Network Stress")
    ax2.set_ylim(-0.5, 25.0)
    ax2.grid(True)
    ax2.legend(frameon=True, loc="upper left")

    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig6_latency_loss_stress.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig7_intervention_footprint():
    """Figure 7: Control-Plane Footprint (Switches Modified and Flow-Mod Rules)."""
    csv_path = os.path.join(RESULTS_DIR, "exp1_failure_severity.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)
    df_k12 = df[(df["topology"] == "abilene") & (df["k_failures"].isin([1, 2, 3]))]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    methods = ["CIRAH", "Dynamic-SP", "Risk-Aware", "Backup-Path", "MinChange-SP"]
    
    # Filter methods and compute mean and sem
    sub = df_k12[df_k12["method"].isin(methods)]
    agg = sub.groupby(["k_failures", "method"])["switches_modified"].mean().unstack()

    x = np.arange(len(agg.index))
    width = 0.16
    for i, m in enumerate(methods):
        ax.bar(x + (i - 2) * width, agg[m], width, label=m, color=PALETTE.get(m, "#666666"), edgecolor="black", linewidth=0.8)

    ax.set_xlabel("Simultaneous Link Failures ($k$)")
    ax.set_ylabel("Switches Modified (Churn Count)")
    ax.set_title("Control-Plane Reconfiguration Footprint Across Recovery Methods")
    ax.set_xticks(x)
    ax.set_xticklabels([f"$k = {k}$" for k in agg.index])
    ax.grid(True, axis="y")
    ax.legend(frameon=True, loc="upper left")
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig7_switches_modified_footprint.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig8_residual_risk():
    """Figure 8: Residual Risk R_post across failure severity."""
    csv_path = os.path.join(RESULTS_DIR, "exp1_failure_severity.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)
    df_ab = df[df["topology"] == "abilene"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    methods = ["CIRAH", "CIRAH-noRisk", "Dynamic-SP", "MinChange-SP"]

    for m in methods:
        sub = df_ab[df_ab["method"] == m]
        agg = sub.groupby("k_failures")["risk_post"].agg(["mean", "sem"]).reset_index()
        ax.errorbar(
            agg["k_failures"], agg["mean"],
            yerr=agg["sem"] * 1.96,
            label=m,
            color=PALETTE.get(m, "#333333"),
            marker=MARKERS.get(m, "o"),
            capsize=4
        )

    # Draw R_max risk ceiling line
    ax.axhline(y=35.0, color="red", linestyle=":", linewidth=2.0, label="Risk Ceiling $R_{\\max} = 35.0$")

    ax.set_xlabel("Number of Simultaneous Link Failures ($k$)")
    ax.set_ylabel("Residual Post-Recovery Risk $R_{\\text{post}}(a)$")
    ax.set_title("Post-Recovery Network Risk vs. Constraint Bound ($R_{\\max}$)")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.grid(True)
    ax.legend(frameon=True, loc="upper left")
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig8_residual_risk_bound.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig9_ablation_radar():
    """Figure 9: Rebuilt 6-Way Component Ablation Bar Chart (Faculty Correction 2)."""
    csv_path = os.path.join(RESULTS_DIR, "exp4_rebuilt_ablations.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)

    ablation_methods = ["CIRAH-full", "CIRAH-noCausal", "CIRAH-noCF", "CIRAH-noCIHF", "CIRAH-noRisk", "CIRAH-noInterv"]
    metrics = ["success", "risk_post", "switches_modified", "intervention_cost"]
    
    agg = df.groupby("variant")[metrics].mean().reindex(ablation_methods)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
    
    bar_colors = ["#1b9e77", "#d95f02", "#e6ab02", "#66a61e", "#7570b3", "#e7298a"]
    labels = ["Full", "noCausal", "noCF", "noCIHF", "noRisk", "noInterv"]

    # 1. Success rate
    ax1.bar(labels, agg["success"] * 100.0, color=bar_colors, edgecolor="black")
    ax1.set_ylabel("Recovery Success Rate (%)")
    ax1.set_title("(a) Recovery Success Rate")
    ax1.set_ylim(0, 105)
    ax1.grid(True, axis="y")

    # 2. Risk post
    ax2.bar(labels, agg["risk_post"], color=bar_colors, edgecolor="black")
    ax2.set_ylabel("Residual Post Risk ($R_{\\text{post}}$)")
    ax2.set_title("(b) Post-Intervention Residual Risk")
    ax2.grid(True, axis="y")

    # 3. Switches modified
    ax3.bar(labels, agg["switches_modified"], color=bar_colors, edgecolor="black")
    ax3.set_ylabel("Switches Modified (Churn)")
    ax3.set_title("(c) Control-Plane Switch Churn")
    ax3.grid(True, axis="y")

    # 4. Intervention cost
    ax4.bar(labels, agg["intervention_cost"], color=bar_colors, edgecolor="black")
    ax4.set_ylabel("Intervention Cost $C_I(a)$")
    ax4.set_title("(d) Control Plane Reconfiguration Cost")
    ax4.grid(True, axis="y")

    plt.suptitle("Component-Level 6-Way Ablation Analysis (N=60 Paired Scenarios)", fontsize=13)
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig9_component_ablations.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig10_telemetry_noise():
    """Figure 10: Telemetry Noise Robustness (Causal Bayesian SCM vs Brittle Rule)."""
    csv_path = os.path.join(RESULTS_DIR, "exp3_telemetry_noise.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    methods = ["CIRAH (Causal SCM)", "CIRAH-noCausal (Rule-Based)", "Dynamic-SP"]

    for m in methods:
        sub = df[df["method"] == m]
        agg = sub.groupby("noise_sigma")["success"].agg(["mean", "sem"]).reset_index()
        col = PALETTE.get("CIRAH" if "Causal SCM" in m else ("CIRAH-noCausal" if "Rule-Based" in m else "Dynamic-SP"))
        ax.errorbar(
            agg["noise_sigma"], agg["mean"] * 100.0,
            yerr=agg["sem"] * 1.96 * 100.0,
            label=m,
            color=col,
            marker="o" if "Causal" in m else "s",
            capsize=4
        )

    ax.set_xlabel("Telemetry Measurement Noise ($\\sigma_{\\text{noise}}$)")
    ax.set_ylabel("Recovery Success Rate (%)")
    ax.set_title("Resilience to Telemetry Uncertainty & Noise")
    ax.set_ylim(0, 105)
    ax.grid(True)
    ax.legend(frameon=True, loc="lower left")
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig10_telemetry_noise_resilience.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

def plot_fig7_gamma_sweep():
    """Figure 7b: Gamma Sensitivity Sweep on switch modifications and healing gain."""
    csv_path = os.path.join(RESULTS_DIR, "exp4_gamma_sensitivity.csv")
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)

    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    agg = df.groupby("gamma").agg(
        sw_mean=("switches_modified", "mean"),
        sw_sem=("switches_modified", "sem"),
        cost_mean=("intervention_cost", "mean"),
        psi_mean=("healing_psi", "mean")
    ).reset_index()

    color1 = "#1b9e77"
    ax1.errorbar(agg["gamma"], agg["sw_mean"], yerr=agg["sw_sem"]*1.96, color=color1, marker="o", label="Switches Modified")
    ax1.set_xlabel("Healing-Field Weight Parameter ($\\gamma$)")
    ax1.set_ylabel("Switches Modified", color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = "#7570b3"
    ax2.plot(agg["gamma"], agg["psi_mean"], color=color2, marker="s", linestyle="--", label="Aggregate Healing $\\Psi(a)$")
    ax2.set_ylabel("Aggregate Healing Gain $\\Psi(a)$", color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

    ax1.set_title("Hyperparameter Sensitivity: Impact of Weight $\\gamma$")
    ax1.grid(True)
    plt.tight_layout()
    out_file = os.path.join(FIG_DIR, "fig11_gamma_sensitivity.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

if __name__ == "__main__":
    plot_fig5_success_rate()
    plot_fig6_latency_and_loss()
    plot_fig7_intervention_footprint()
    plot_fig8_residual_risk()
    plot_fig9_ablation_radar()
    plot_fig10_telemetry_noise()
    plot_fig7_gamma_sweep()
    print("All publication figures successfully generated in figures/ directory!")
