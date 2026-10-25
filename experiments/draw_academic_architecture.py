"""
CIRAH: Authentic Academic Architecture Diagram Generator
Draws a clean, publication-grade engineering architecture diagram in the style of
IEEE Transactions / ACM SIGCOMM / Elsevier computer networks papers.
Uses clean geometric boxes, clear architectural tiers, precise mathematical labels,
crisp vector arrows, and no AI-generated gradients or infographic fluff.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

FIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'figures'))
os.makedirs(FIG_DIR, exist_ok=True)

def draw_academic_architecture():
    png_path = os.path.join(FIG_DIR, "fig1_academic_architecture.png")
    
    # 300 DPI, crisp academic dimensions (13.5 x 8.8 inches)
    fig, ax = plt.subplots(figsize=(13.5, 8.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette: Classic Academic Engineering (Clean, high contrast, print-safe)
    BORDER_COL = "#1A2530"     # Dark Slate
    CONTAINER_BG = "#F8FAFC"   # Very Light Cool Gray
    BOX_BG = "#FFFFFF"         # Crisp White
    HIGHLIGHT_BLUE = "#EBF3FB" # Soft Academic Blue
    HIGHLIGHT_GREEN = "#EAF7EE"# Soft Green for Verification/Healing
    HIGHLIGHT_RED = "#FDF2F2"  # Soft Coral for Risk
    HIGHLIGHT_PURPLE = "#F5F3FF" # Soft Lavender for Causal Engine
    ARROW_COL = "#2C3E50"      # Professional Charcoal

    # =========================================================================
    # 1. OUTER SUB-CONTAINERS (TIERS)
    # =========================================================================

    # TIER 1: Top Container - Telemetry & Ingestion (y: 67 to 95)
    t1_box = patches.FancyBboxPatch((3, 67), 94, 28, boxstyle="round,pad=0.5,rounding_size=1.0",
                                   facecolor="#F1F5F9", edgecolor="#64748B", linewidth=1.2)
    ax.add_patch(t1_box)
    ax.text(5, 92.5, "TIER 1: TELEMETRY INGESTION & DATA-PLANE OBSERVATION", 
            fontsize=10.5, fontweight="bold", color="#1E293B", family="sans-serif")

    # TIER 2: Middle Container - CIRAH Autonomous Causal Reasoning & Optimization Core (y: 25 to 64)
    t2_box = patches.FancyBboxPatch((3, 25), 94, 39, boxstyle="round,pad=0.5,rounding_size=1.0",
                                   facecolor=CONTAINER_BG, edgecolor="#0284C7", linewidth=1.5)
    ax.add_patch(t2_box)
    ax.text(5, 61.5, "TIER 2: CIRAH COGNITIVE CAUSAL OPTIMIZATION SUBSTRATE", 
            fontsize=10.5, fontweight="bold", color="#0369A1", family="sans-serif")

    # TIER 3: Bottom Container - Digital Twin & Closed-Loop Feedback (y: 3 to 22)
    t3_box = patches.FancyBboxPatch((3, 3), 94, 19, boxstyle="round,pad=0.5,rounding_size=1.0",
                                   facecolor="#F8FAFC", edgecolor="#475569", linewidth=1.2, linestyle="--")
    ax.add_patch(t3_box)
    ax.text(5, 19.5, "TIER 3: NETWORK DIGITAL TWIN & CLOSED-LOOP ADAPTATION", 
            fontsize=10.5, fontweight="bold", color="#334155", family="sans-serif")

    # =========================================================================
    # 2. TIER 1 COMPONENTS (Data-Plane Inputs & Observation)
    # =========================================================================
    
    # Box 1A: Telemetry Sources
    b_telem = patches.FancyBboxPatch((5, 70), 20, 20, boxstyle="round,pad=0.4,rounding_size=0.8",
                                    facecolor=BOX_BG, edgecolor=BORDER_COL, linewidth=1.2)
    ax.add_patch(b_telem)
    ax.text(15, 87, "Network Telemetry\nData Plane Inputs", fontsize=9.5, fontweight="bold", ha="center", va="center")
    ax.plot([6, 24], [83.5, 83.5], color="#CBD5E1", linewidth=0.8)
    telem_text = "• Dynamic Topology (V, E)\n• Traffic Demand Matrix (F)\n• Link Latency & Packet Loss\n• Buffer / Queue Depths (Q)\n• Flow Table Counters"
    ax.text(6.5, 76.5, telem_text, fontsize=8, va="center", color="#334155", family="sans-serif")

    # Box 1B: Anomaly Localization
    b_obs = patches.FancyBboxPatch((30, 70), 22, 20, boxstyle="round,pad=0.4,rounding_size=0.8",
                                  facecolor=HIGHLIGHT_BLUE, edgecolor="#0284C7", linewidth=1.2)
    ax.add_patch(b_obs)
    ax.text(41, 87, "Stage 1: Failure\nObservation & Detection", fontsize=9.5, fontweight="bold", ha="center", va="center", color="#0369A1")
    ax.plot([31, 51], [83.5, 83.5], color="#BAE6FD", linewidth=0.8)
    obs_text = "• Threshold Anomaly Trigger\n• Multi-link Outage Identifier\n• SLA Degradation Isolation\n• Flow Impairment Mapping\nOutput: Observed Symptoms O"
    ax.text(31.5, 76.5, obs_text, fontsize=8, va="center", color="#0F172A", family="sans-serif")

    # Box 1C: Actuation & Verification
    b_act = patches.FancyBboxPatch((74, 70), 21, 20, boxstyle="round,pad=0.4,rounding_size=0.8",
                                  facecolor=HIGHLIGHT_GREEN, edgecolor="#16A34A", linewidth=1.4)
    ax.add_patch(b_act)
    ax.text(84.5, 87, "Stage 6: Control-Plane\nActuation & Verification", fontsize=9.5, fontweight="bold", ha="center", va="center", color="#15803D")
    ax.plot([75, 94], [83.5, 83.5], color="#BBF7D0", linewidth=0.8)
    act_text = "• OpenFlow FLOW_MOD Dispatch\n• Barrier Request / Sync\n• TCAM Flow Reconfiguration\n• Real-Time SLA Verification\n• Closed-Loop State Update"
    ax.text(75.5, 76.5, act_text, fontsize=8, va="center", color="#14532D", family="sans-serif")

    # Arrow 1A -> 1B
    ax.annotate("", xy=(30, 80), xytext=(25, 80),
                arrowprops=dict(arrowstyle="->", color=ARROW_COL, lw=1.8, mutation_scale=12))

    # =========================================================================
    # 3. TIER 2 COMPONENTS (Causal Model, Counterfactuals, Diffusion & Optimizer)
    # =========================================================================

    # Box 2A: Structural Causal Model (SCM) & Bayesian Traceback
    b_scm = patches.FancyBboxPatch((5, 29), 20, 29, boxstyle="round,pad=0.4,rounding_size=0.8",
                                  facecolor=HIGHLIGHT_PURPLE, edgecolor="#7C3AED", linewidth=1.2)
    ax.add_patch(b_scm)
    ax.text(15, 54.5, "Stage 2: Structural Causal\nModel (SCM) & Traceback", fontsize=9, fontweight="bold", ha="center", va="center", color="#6D28D9")
    ax.plot([6, 24], [51, 51], color="#DDD6FE", linewidth=0.8)
    scm_text = "• Causal Graph G = (V, E)\n• Endogenous Vars: F, L, Q, R, Y\n• Exogenous Noise: U_L, U_Q, U_Y\n• Bayesian Fault Posterior:\n  P(Fe = 1 | O, ActivePaths)\n• Eliminates spurious correlations\n• True root-cause localization"
    ax.text(6.5, 41, scm_text, fontsize=7.8, va="center", color="#3B0764", family="sans-serif")

    # Box 2B: Candidate Interventions & Counterfactual Evaluator
    b_cf = patches.FancyBboxPatch((28, 29), 21, 29, boxstyle="round,pad=0.4,rounding_size=0.8",
                                 facecolor=BOX_BG, edgecolor=BORDER_COL, linewidth=1.2)
    ax.add_patch(b_cf)
    ax.text(38.5, 54.5, "Stage 3: Pearl Counterfactual\nIntervention Engine", fontsize=9, fontweight="bold", ha="center", va="center")
    ax.plot([29, 48], [51, 51], color="#CBD5E1", linewidth=0.8)
    cf_text = "• Candidate Space A:\n  - Null action a0 (keep route)\n  - K-Shortest Loop-Free Detours\n  - Ingress Rate Pacing (0.8x)\n• 3-Step Counterfactual Logic:\n  1. Abduction: Infer U given O\n  2. Action: do(A = a) [sever arrow]\n  3. Prediction: Y(a) = f(do(a), U)\n• P(F_rec | do(a)) Estimation"
    ax.text(29.2, 41, cf_text, fontsize=7.6, va="center", color="#334155", family="sans-serif")

    # Box 2C: Healing-Field Propagator (CIHF)
    b_cihf = patches.FancyBboxPatch((52, 29), 20, 29, boxstyle="round,pad=0.4,rounding_size=0.8",
                                   facecolor=BOX_BG, edgecolor="#D97706", linewidth=1.2)
    ax.add_patch(b_cihf)
    ax.text(62, 54.5, "Stage 4: Causal Healing\nField Propagator (CIHF)", fontsize=9, fontweight="bold", ha="center", va="center", color="#B45309")
    ax.plot([53, 71], [51, 51], color="#FDE68A", linewidth=0.8)
    cihf_text = "• Normalized Graph Laplacian:\n  L_norm = I - D^(-1/2) W D^(-1/2)\n• Steady-State Heat Diffusion:\n  h(a) = (I + σ L_norm)^(-1) s(a)\n• s(a): Spatial Stress Relief\n• Aggregate Network Benefit:\n  Ψ(a) = Σ_v H(a, v)\n• Continuous equilibrium model"
    ax.text(53.2, 41, cihf_text, fontsize=7.6, va="center", color="#78350F", family="sans-serif")

    # Box 2D: Risk Assessment & Minimum-Intervention Optimizer
    b_opt = patches.FancyBboxPatch((75, 29), 20, 29, boxstyle="round,pad=0.4,rounding_size=0.8",
                                  facecolor=HIGHLIGHT_RED, edgecolor="#DC2626", linewidth=1.4)
    ax.add_patch(b_opt)
    ax.text(85, 54.5, "Stage 5: Risk-Constrained\nMinimum-Intervention Solver", fontsize=9, fontweight="bold", ha="center", va="center", color="#B91C1C")
    ax.plot([76, 94], [51, 51], color="#FECACA", linewidth=0.8)
    opt_text = "• Objective Function:\n  min [ λI C_I + λD C_D +\n        λL C_L + β R_post - γ Ψ ]\n• Constraints:\n  - R_post(a) ≤ R_max\n  - P(F_rec | do(a)) ≥ τ\n  - Connectivity(a) == 1\n• Multi-Tier Safe Fallback Engine\n• Action Selection a*"
    ax.text(76.2, 41, opt_text, fontsize=7.6, va="center", color="#7F1D1D", family="sans-serif")

    # Connectors across Tier 2
    ax.annotate("", xy=(28, 43.5), xytext=(25, 43.5),
                arrowprops=dict(arrowstyle="->", color=ARROW_COL, lw=1.6, mutation_scale=10))
    ax.annotate("", xy=(52, 43.5), xytext=(49, 43.5),
                arrowprops=dict(arrowstyle="->", color=ARROW_COL, lw=1.6, mutation_scale=10))
    ax.annotate("", xy=(75, 43.5), xytext=(72, 43.5),
                arrowprops=dict(arrowstyle="->", color=ARROW_COL, lw=1.6, mutation_scale=10))

    # Downward connector from Tier 1 Observation into Tier 2 SCM
    ax.annotate("", xy=(15, 58), xytext=(41, 70),
                arrowprops=dict(arrowstyle="->", color=ARROW_COL, lw=1.6, mutation_scale=10,
                                connectionstyle="arc3,rad=-0.15"))
    ax.text(26, 62, "Telemetry O", fontsize=7.8, fontweight="bold", color="#0284C7", backgroundcolor="#FFF")

    # Upward connector from Tier 2 Optimizer into Tier 1 Actuation
    ax.annotate("", xy=(84.5, 70), xytext=(85, 58),
                arrowprops=dict(arrowstyle="->", color="#16A34A", lw=2.0, mutation_scale=12))
    ax.text(85.5, 63.5, "Optimal Action a*", fontsize=8, fontweight="bold", color="#15803D", backgroundcolor="#FFF")

    # =========================================================================
    # 4. TIER 3 COMPONENTS (Digital Twin & Continuous Adaptation)
    # =========================================================================

    b_dt = patches.FancyBboxPatch((5, 6), 42, 11, boxstyle="round,pad=0.4,rounding_size=0.6",
                                 facecolor=BOX_BG, edgecolor="#475569", linewidth=1.2)
    ax.add_patch(b_dt)
    ax.text(26, 14, "Network Digital Twin (NDT) Simulation Sandbox", fontsize=9, fontweight="bold", ha="center", va="center", color="#1E293B")
    dt_text = "• Zero-risk shadow emulation of candidate do(A=a) actions\n• Synthetic validation of residual capacity & buffer overflows"
    ax.text(26, 9.5, dt_text, fontsize=7.8, ha="center", va="center", color="#475569")

    b_learn = patches.FancyBboxPatch((52, 6), 43, 11, boxstyle="round,pad=0.4,rounding_size=0.6",
                                    facecolor=BOX_BG, edgecolor="#0D9488", linewidth=1.2)
    ax.add_patch(b_learn)
    ax.text(73.5, 14, "Continuous Learning & Policy Adaptation", fontsize=9, fontweight="bold", ha="center", va="center", color="#0F766E")
    learn_text = "• Online Bayesian edge weight update based on post-repair telemetry\n• Dynamic tuning of risk parameter β and healing weight γ"
    ax.text(73.5, 9.5, learn_text, fontsize=7.8, ha="center", va="center", color="#134E4A")

    # Bi-directional arrows between Tier 2 and Tier 3
    ax.annotate("", xy=(26, 29), xytext=(26, 17),
                arrowprops=dict(arrowstyle="<->", color="#475569", lw=1.4, mutation_scale=10))
    ax.annotate("", xy=(73.5, 29), xytext=(73.5, 17),
                arrowprops=dict(arrowstyle="<->", color="#0D9488", lw=1.4, mutation_scale=10))

    # Long Closed-Loop Feedback Arrow (Actuation -> Continuous Learning -> Telemetry)
    ax.annotate("", xy=(15, 70), xytext=(84.5, 6),
                arrowprops=dict(arrowstyle="->", color="#0284C7", lw=1.8, linestyle="--",
                                connectionstyle="arc3,rad=0.35"))
    ax.text(48, 1, "Closed-Loop Self-Healing Feedback: Actuation Telemetry Update -> Observation", 
            fontsize=8.5, fontweight="bold", color="#0369A1", ha="center")

    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated clean academic architecture diagram: {png_path}")
    return png_path

if __name__ == "__main__":
    draw_academic_architecture()
