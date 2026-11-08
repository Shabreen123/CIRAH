"""
Build CIRAH_FINAL_Springer.docm by injecting content into the official
splnproc2510.docm Springer LNCS template using its exact style names.

Strategy:
1. Open the .docm as a ZIP archive (it is just a ZIP).
2. Replace word/document.xml with our content using the template's style IDs.
3. Write the result as CIRAH_FINAL_Springer.docm — ready to open in Word.

This preserves ALL template features: macros, toolbar buttons, headers,
footers, numbering definitions, font tables, and Springer VBA toolbar.
"""

import zipfile, shutil, os, re
from lxml import etree

TEMPLATE = r"C:\Users\LENOVO\Downloads\splnproc2510.docm"
OUT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "CIRAH_FINAL_Springer.docm")

# ── XML namespace helpers ───────────────────────────────────────────────────

W  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A  = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC= "http://schemas.openxmlformats.org/drawingml/2006/picture"

def w(tag):  return f"{{{W}}}{tag}"
def r_(tag): return f"{{{R}}}{tag}"

def E(tag, **attrib):
    """Create a w: element."""
    return etree.Element(w(tag), attrib)

def para(style_id, *runs, jc=None, sb=None, sa=None, ind_left=None, ind_hanging=None):
    """Build a <w:p> element with the given style and run tuples."""
    p = E("p")
    pPr = E("pPr")
    pStyle = E("pStyle"); pStyle.set(w("val"), style_id)
    pPr.append(pStyle)
    if jc:
        j = E("jc"); j.set(w("val"), jc); pPr.append(j)
    spacing = {}
    if sb is not None: spacing["before"] = str(sb)
    if sa is not None: spacing["after"]  = str(sa)
    if spacing:
        sp = E("spacing")
        for k,v in spacing.items(): sp.set(w(k), v)
        pPr.append(sp)
    if ind_left is not None or ind_hanging is not None:
        ind = E("ind")
        if ind_left    is not None: ind.set(w("left"),    str(ind_left))
        if ind_hanging is not None: ind.set(w("hanging"), str(ind_hanging))
        pPr.append(ind)
    p.append(pPr)
    for run_data in runs:
        if run_data is None:
            continue
        if isinstance(run_data, str):
            text, bold, italic = run_data, False, False
        else:
            text = run_data.get("t", "")
            bold   = run_data.get("b", False)
            italic = run_data.get("i", False)
        if not text:
            continue
        rn = E("r")
        rPr = E("rPr")
        if bold:
            rPr.append(E("b")); rPr.append(E("bCs"))
        if italic:
            rPr.append(E("i")); rPr.append(E("iCs"))
        if rPr.getchildren():
            rn.append(rPr)
        t_el = E("t"); t_el.text = text
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        rn.append(t_el)
        p.append(rn)
    return p

def bold(t): return {"t": t, "b": True}
def ital(t): return {"t": t, "i": True}
def bi(t):   return {"t": t, "b": True, "i": True}

def para_body(text, style="Normal"):
    return para(style, text)

def heading1(num, title):
    return para("heading1", f"{num}  {title}")

def heading2(num, title):
    return para("heading2", f"{num}  {title}")

def heading3(title):
    return para("heading3", f"{title}.")

def make_table_xml(headers, rows, col_widths_pct=None):
    """Build a <w:tbl> element with Springer three-line style."""
    tbl = etree.Element(w("tbl"))

    tblPr = E("tblPr")
    tblStyle = E("tblStyle"); tblStyle.set(w("val"), "Normal Table"); tblPr.append(tblStyle)
    tblW = E("tblW"); tblW.set(w("type"), "pct"); tblW.set(w("w"), "5000"); tblPr.append(tblW)
    tblBorders = E("tblBorders")
    for side in ("top", "bottom"):
        b = E(side); b.set(w("val"),"single"); b.set(w("sz"),"12")
        b.set(w("space"),"0"); b.set(w("color"),"000000"); tblBorders.append(b)
    for side in ("left","right","insideH","insideV"):
        b = E(side); b.set(w("val"),"none"); tblBorders.append(b)
    tblPr.append(tblBorders)
    tbl.append(tblPr)

    def make_row(cells, is_header=False):
        tr = E("tr")
        for i, cell_text in enumerate(cells):
            tc = E("tc")
            tcPr = E("tcPr")
            tcW = E("tcW"); tcW.set(w("type"),"auto"); tcW.set(w("w"),"0"); tcPr.append(tcW)
            if is_header:
                bd = E("tcBorders")
                bb = E("bottom"); bb.set(w("val"),"single"); bb.set(w("sz"),"6")
                bb.set(w("space"),"0"); bb.set(w("color"),"000000"); bd.append(bb)
                tcPr.append(bd)
            tc.append(tcPr)
            p = E("p")
            pPr = E("pPr")
            pStyle = E("pStyle"); pStyle.set(w("val"), "Normal"); pPr.append(pStyle)
            sp = E("spacing"); sp.set(w("before"),"20"); sp.set(w("after"),"20"); pPr.append(sp)
            p.append(pPr)
            rn = E("r")
            rPr = E("rPr")
            sz = E("sz"); sz.set(w("val"),"16")  # 8pt = 16 half-points
            szCs= E("szCs"); szCs.set(w("val"),"16"); rPr.append(sz); rPr.append(szCs)
            if is_header:
                rPr.append(E("b")); rPr.append(E("bCs"))
            rn.append(rPr)
            t_el = E("t"); t_el.text = cell_text
            t_el.set("{http://www.w3.org/XML/1998/namespace}space","preserve")
            rn.append(t_el); p.append(rn); tc.append(p); tr.append(tc)
        return tr

    tbl.append(make_row(headers, is_header=True))
    for row in rows:
        tbl.append(make_row(row))
    return tbl

def code_block(text):
    """Monospace code block using programcode style."""
    lines = text.strip().split("\n")
    elems = []
    for line in lines:
        p = para("programcode", line)
        elems.append(p)
    return elems

# ── Build body paragraphs ───────────────────────────────────────────────────

def build_body():
    body_el = etree.Element(w("body"))

    def add(el):
        if isinstance(el, list):
            for e in el: body_el.append(e)
        else:
            body_el.append(el)

    # ── Title ──
    add(para("papertitle", "CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing"))
    add(para("author", "Buradagunta Shabreen Shaik, Rajisree Sadu, and Pemmasani Greeshma"))
    add(para("address", "School of Computer Science and Engineering, VIT-AP University, Amaravati, Andhra Pradesh 522237, India"))

    # ── Abstract ──
    add(para("abstract",
        bold("Abstract. "),
        "Modern software-defined communication networks face unpredictable link outages, performance degradation, "
        "and cascading congestion that jeopardize strict service-level agreements. Conventional self-healing "
        "techniques rely on reactive shortest-path recomputation or correlation-based heuristic rerouting; however, "
        "these approaches frequently trigger excessive switch reconfiguration churn, control-plane message storms, "
        "and secondary congestion cascades across un-intervened paths. This paper presents CIRAH "
        "(Causal-Intervention Risk-constrained Autonomous network self-Healing), an optimization framework for "
        "autonomous network restoration. CIRAH establishes an explicit Structural Causal Model (SCM) connecting "
        "physical faults, link degradation, dynamic M/M/1 queuing delays, routing topology, and end-to-end service "
        "outcomes. Leveraging Pearl's counterfactual do-calculus, CIRAH estimates the consequence of candidate "
        "interventions prior to execution. A constrained combinatorial optimizer selects the minimum-cost "
        "intervention satisfying robust post-recovery risk ceilings and SLA confidence thresholds. Across paired "
        "Monte Carlo runs on the Abilene topology under double-link failures, CIRAH reduces switch modifications by "
        "13.8% (p=0.00082, d_z=-0.56) and intervention cost by 9.3% (p=0.00089), with identical 72.0% success "
        "rate as Dynamic-SP. A 6-way ablation confirms the hard risk constraint as the dominant component: "
        "removing it drops success from 70.0% to 56.7%."))

    add(para("keywords",
        bold("Keywords: "),
        "Autonomous network self-healing, Structural Causal Models, Pearl's do-calculus, "
        "minimum-causal intervention, risk-constrained optimization, Software-Defined Networking."))

    # ── 1. Introduction ──
    add(heading1("1", "Introduction"))
    add(para("Normal",
        "Software-Defined Networking (SDN) centralizes control intelligence, granting network operators "
        "programmatic visibility and fine-grained forwarding control across distributed data-plane switches [1,2]. "
        "Despite these architectural advantages, wide-area and data-center networks operate under intense dynamic "
        "volatility, where physical fiber cuts, optical transponder brownouts, hardware failures, and bursty traffic "
        "surges trigger severe service degradation [3,4]. When outages occur, the network management system must "
        "autonomously detect the fault, diagnose the underlying cause, compute a remedial configuration, and verify "
        "service restoration with minimal downtime [5,6]."))

    add(heading2("1.1", "Limitations of Existing Approaches"))
    add(para("Normal",
        "While autonomous recovery has been widely explored, existing paradigms exhibit distinct operational "
        "limitations. Reactive Shortest-Path Rerouting restores connectivity but ignores control-plane churn, "
        "frequently modifying extensive switch sets and creating transient forwarding loops [7,10,11]. Precomputed "
        "Protection Paths offer sub-50 ms restoration [3,7] but exhaust switch TCAM resources and fail under "
        "concurrent multi-link failures. Risk-Aware Routing [4,6] does not penalize the operational cost of "
        "reconfiguration. Deep Reinforcement Learning policies [16,19,23] lack formal safety constraints and require "
        "immense offline training datasets [11]. Correlation-Based Diagnosis [10,14,27] fails to distinguish root "
        "causes from downstream symptoms. Existing systems cannot evaluate counterfactual queries — assessing what "
        "the post-recovery state would be if action a were executed [8,9]."))

    add(heading2("1.2", "Research Gap"))
    add(para("Normal",
        "Although prior network-recovery approaches address fault diagnosis, path restoration, and risk-aware "
        "routing, the extent to which causal uncertainty, intervention-induced congestion, and control-plane "
        "reconfiguration costs can be jointly incorporated into a risk-constrained recovery decision remains to be "
        "established. The central research question is: Can a network self-healing controller select a feasible "
        "recovery action that maintains service, satisfies an explicit post-recovery risk limit, and minimizes "
        "operational intervention cost while accounting for uncertainty in fault diagnosis and predicted recovery "
        "outcomes?"))

    add(heading2("1.3", "Hypotheses"))
    for h in [
        "H1 (Intervention Parsimony). CIRAH achieves a statistically significant reduction in switch modifications and control-plane intervention cost compared to reactive Dynamic-SP (p < 0.05).",
        "H2 (Risk Compliance). CIRAH maintains post-recovery risk strictly below R_max, whereas unconstrained variants exhibit elevated violations.",
        "H3 (Noise Resilience). Under telemetry observation uncertainty sigma_noise >= 0.20, Bayesian fault estimation maintains higher recovery success than heuristic rule-based diagnosis.",
        "H4 (Scalability). The parsimonious intervention advantage of CIRAH persists across Abilene (11 nodes), GEANT (22 nodes), and Fat-tree (20 nodes).",
    ]:
        add(para("Normal", h))

    add(heading2("1.4", "Contributions"))
    for txt in [
        "Causal fault-to-recovery formulation: A formally specified SCM connecting link faults, traffic conditions, M/M/1 queuing behavior, routing interventions, and end-to-end service outcomes, with explicit assumptions, identifiability limitations, and predictive accuracy evaluation.",
        "Intervention-aware recovery optimization: A constrained recovery formulation jointly accounting for control-plane reconfiguration cost, service disruption, residual network risk, and SLA feasibility, compared with established constrained routing methods.",
        "Network-wide intervention impact estimation: A graph-based stress-relief mechanism (CIHF) evaluated against 5 alternative scoring methods. Controlled experiments (720 paired runs) show CIHF does not change action selection in 99.2% of scenarios; it is retained as an interpretive visualization of spatial stress relief.",
        "Uncertainty-aware risk handling: A robust risk bound with empirical 0.0% constraint-violation rate at the default threshold (N=30 independent scenarios).",
        "Reproducible experimental validation: Approximately 5,300 paired Monte Carlo runs across three topologies, 6-way component ablations, paired statistical comparisons, and open-source implementation.",
    ]:
        add(para("numitem", txt))

    # ── 2. Literature Review ──
    add(heading1("2", "Literature Review"))

    add(heading2("2.1", "SDN Restoration and Minimum-Change Routing"))
    add(para("Normal",
        "SDN architectures decouple control and data planes via OpenFlow [5,6]. Sharma et al. [7] studied "
        "proactive protection versus reactive restoration, showing protection achieves sub-50 ms failover at the "
        "cost of rapid TCAM exhaustion. Qin et al. [3] introduced FAPR, balancing proactive backup selection with "
        "reactive restoration. Yusuf et al. [4] formulated adaptive path selection using flow classification and "
        "composite QoS metrics. Li et al. [31] examined path selection for link-failure protection in hybrid SDNs, "
        "showing selective SDN upgrade minimizes repair-path length and transient congestion. None of these works "
        "model the control-plane message cost incurred during large-scale reconfigurations."))

    add(heading2("2.2", "Risk-Constrained Routing and Resilience Optimization"))
    add(para("Normal",
        "Risk-aware routing avoids links vulnerable to failure or buffer overflows [4,6]. Risk-aware traffic "
        "engineering incorporates probabilistic link availability into path optimization for wide-area SDN "
        "deployments [3,4,31]. Machine-learning methods for short-term traffic-flow prediction [32] have been "
        "explored to trigger proactive restoration. However, these formulations do not enforce hard post-recovery "
        "risk ceilings, nor penalize the operational overhead of modifying forwarding entries in the control plane."))

    add(heading2("2.3", "Causal Fault Localization and Counterfactual Decision-Making"))
    add(para("Normal",
        "Causal inference, formalized by Pearl [9], distinguishes observational correlation P(Y|X) from "
        "interventional manipulation P(Y|do(X)). In networking, causal directed graphs have been applied to "
        "root-cause fault localization [8,9]. Existing causal approaches terminate at fault localization; they do "
        "not integrate counterfactual outcome prediction directly into an online intervention optimization algorithm "
        "that evaluates alternative recovery actions."))

    add(heading2("2.4", "Autonomous Self-Healing and Digital Twins"))
    add(para("Normal",
        "Clark et al.'s Knowledge Plane [8] originated autonomous network management. Recent Network Digital Twins "
        "(NDTs) [1,6] provide risk-free simulation environments. Sanz Rodrigo et al. [1] demonstrated zero-touch "
        "SLA preservation. Deep learning models have been applied to DDoS mitigation in SDNs, encompassing "
        "systematic reviews [11], DNN classifiers [15,21], optimised models [17,18], hybrid frameworks "
        "[12,13,20,22,24-26,33-35], attention methods [27,30], IoT extensions [19,29], and ensemble methods [14,23]. "
        "CIRAH bridges causal fault localization and risk-constrained intervention optimization."))

    add(heading2("2.5", "Comparison Table"))
    add(para("Normal", "Table 1 compares CIRAH against representative approaches across eight technical dimensions."))

    add(para("tablecaption", "Table 1. Technical comparison of network fault recovery and management approaches."))
    t1_headers = ["Approach","Causal Diag.","CF Pred.","Interv. Cost","Risk","Net-wide Effects","Uncertainty","Guarantees","Validation"]
    t1_rows = [
        ["FAPR [3]","No (Heartbeat)","No","Resource proxy","None","Local link only","Deterministic","None","Mininet"],
        ["Yusuf et al. [4]","No (Threshold)","No","None","None","Path-level","None","None","Simulation"],
        ["Polat & Polat [10]","No (Rules)","No","None","None","None","None","None","Mininet/POX"],
        ["Hnamte et al. [15]","No (DNN)","No","None","None","Local drop","Softmax prob.","None","Authentic traces"],
        ["Paidipati et al. [16]","No (DRL)","No","None","Soft penalty","Global reward","Replay","None","Cloud sim."],
        ["Leena et al. [28]","Correlation GNN","No","Path cost proxy","None","Neighbourhood GNN","Cluster density","None","Emulation"],
        ["Dynamic-SP [7]","Link-down alert","No","None","None","Local link status","None","None","Sim./Testbed"],
        ["Constrained-MinChange","Link-down alert","No","Switch diff count","Hard Bound","Local link status","None","Risk Feasibility","Simulation"],
        ["CIRAH (Proposed)","Bayesian SCM","Pearl do(A)","Fine-grained C_I,C_D","Hard Bound R_post<=R_max","Laplacian Diffusion (CIHF)","3-State Bayesian + Noise","Robust Risk Bound","Abilene, GEANT, Fat-tree"],
    ]
    add(make_table_xml(t1_headers, t1_rows))

    # ── 3. Methodology ──
    add(heading1("3", "The CIRAH Framework"))

    add(heading2("3.1", "End-to-End System Architecture"))
    add(para("Normal",
        "The CIRAH architecture comprises three functional tiers organized into a closed-loop control system. "
        "Tier 1 (Telemetry and Observation) performs continuous monitoring of link latency, loss, flow rates, and "
        "switch port statistics. Tier 2 (Cognitive Causal Optimization Substrate) executes SCM-based Bayesian fault "
        "traceback, Pearl counterfactual intervention evaluation, CIHF diffusion, and the risk-constrained "
        "minimum-intervention solver. Tier 3 (Network Digital Twin and Adaptation) provides virtual state emulation "
        "for risk-free what-if counterfactual validation and continuous Bayesian model adaptation. "
        "Figure 1 illustrates the three-tier architecture."))
    add(para("figurecaption", "Fig. 1. CIRAH three-tier architecture: Tier 1 (Telemetry & Observation), Tier 2 (Cognitive Causal Optimization Substrate), Tier 3 (Digital Twin & Closed-Loop Adaptation). [Insert figure here]"))

    add(heading2("3.2", "Formal Structural Causal Model (SCM)"))
    add(para("Normal",
        "We define the network state using a 6-tuple SCM M = <U, V, F, P(U)>, where exogenous variables "
        "U = {U_loss, U_lat} represent background physical noise and traffic jitter. Endogenous variables V comprise: "
        "fault state F_e in {0,1,2} (0: Normal, 1: Degraded, 2: Severed); link properties L_e = <lat_e, loss_e, "
        "cap_e>; queue utilization Q_e in [0,1]; routing matrix R; service outcomes Y_f = <lat_f, loss_f, conn_f>; "
        "and candidate intervention operator A. The causal DAG assumes F_e -> L_e, {L_e,R} -> Q_e, Q_e -> Y_f, "
        "A -> R, with no hidden common causes between independent link faults."))
    add(para("Normal",
        "Link state structural equation (Eq. 1): L_e equals <lat_0, 0, cap_0> + U for F_e=0 (Normal); "
        "<lat_0*(1+delta), loss_deg, cap_0*rho> + U for F_e=1 (Degraded); <infinity, 100%, 0> for F_e=2 (Severed). "
        "Queue utilization (Eq. 2): Q_e = Load_e / max(1.0, cap_e). M/M/1 queuing delay (Eq. 3): "
        "D_queue = Load/(cap-Load)*2.0 for Q<0.85; 15+35*((Q-0.85)/0.15)^1.5 for 0.85<=Q<=1.0; "
        "50+(Q-1)*80 for Q>1.0."))

    add(heading3("Validated Bayesian Causal Fault Localization"))
    add(para("Normal",
        "Given noisy telemetry observations O_e and the set of active paths traversing edge e, the unnormalized "
        "posterior score for state k in {0,1,2} is (Eq. 4a): s_k(e) = P(O_e|F_e=k) * P(F_e=k) * w_k(Paths). "
        "Priors: P(F_e=0)=0.95, P(F_e=1)=0.03, P(F_e=2)=0.02, reflecting ISP backbone base rates. "
        "Path-evidence multipliers (Eq. 4b): w_0 = 1/(1+3*rho_e), w_1 = 1+2.5*rho_e, w_2 = 1+4*rho_e, "
        "where rho_e = N_degraded(e)/max(1,N_traversing(e)). "
        "Normalized posterior (Eq. 4c): P(F_e=k|O_e,Paths) = s_k(e)/sum_j s_j(e), ensuring sum = 1.0."))
    add(para("Normal",
        "Empirical precision/recall/F1 evaluated across 3,000 edge assessments (N=100 fault scenarios): "
        "Normal state P/R/F1 = 1.000; Severed state P/R/F1 = 1.000; overall accuracy = 1.000. "
        "The Degraded state F1 = 0.000 because the fault generator injects only complete severances, leaving "
        "degraded-state classification unevaluated — this is acknowledged as a limitation."))

    add(heading2("3.3", "Counterfactual Intervention Evaluation Engine"))
    add(para("Normal",
        "CIRAH executes Pearl's three-step counterfactual algorithm. "
        "(1) Abduction: estimate latent exogenous noise U_lat,e = max(0, O_lat,e - base_lat_e) and "
        "U_loss,e = max(0, O_loss,e). "
        "(2) Action: modify the SCM by the do-operator, setting R_f* <- Path(a) and severing all incoming "
        "causal arrows into R_f* (Eq. 5). "
        "(3) Prediction: forward-propagate traffic demands with fixed U to compute counterfactual loads, "
        "queue delays, and service outcomes (Eq. 6). "
        "Recovery probability (Eq. 7): P(F_rec|do(A=a)) = E[I(lat_pred <= SLA_lat AND loss_pred <= SLA_loss) | O]."))
    add(para("Normal",
        "Counterfactual evaluation changes 72% of selected actions under tight capacity constraints (80 Mbps links, "
        "40 Mbps cross-traffic) but produces identical outcomes under the default wide-capacity (1,000 Mbps) "
        "ablation scenarios, because traffic displacement does not cause congestion at wide margins."))

    add(heading2("3.4", "Causal Intervention Healing Field (CIHF)"))
    add(para("Normal",
        "CIHF quantifies spatial stress relief via normalized graph Laplacian diffusion. The normalized Laplacian "
        "is L_norm = I - D^(-1/2) W D^(-1/2), where W_ij = 1/max(1, lat_ij). The steady-state diffusion kernel "
        "(Eq. 8): h(a) = (I + sigma*L_norm)^(-1) * s(a), where s(a) is the normalized stress impulse vector "
        "(Eq. 9) and sigma=1.5 defines the spatial decay radius. The aggregate healing gain (Eq. 10): "
        "Psi(a) = 1^T * h(a). The Laplacian inverse is precomputed at initialization in O(|V|^3) time; "
        "per-event cost is a matrix-vector multiply in O(|V|^2)."))
    add(para("Normal",
        "Controlled experiments across 720 paired runs comparing 6 scoring modes (Laplacian diffusion, no-field, "
        "local-only, betweenness-centrality, congestion-only, counterfactual stress-reduction field) show CIHF "
        "changed the selected action in only 1 of 120 runs (0.8%), with paired Wilcoxon p=0.317 for all outcome "
        "metrics (success, switches, cost, risk). CIHF is retained as an interpretive stress-relief visualization "
        "rather than a decision-making component."))

    add(heading2("3.5", "Risk Assessment Module and Robust Constraints"))
    add(para("Normal",
        "The residual risk decomposes as R_post(a) = R_op(a) + R_prop(a) (Eq. 11). "
        "Operational risk (Eq. 12): R_op = P_disconnect * 100 + P_SLA * 25 + P_flap * 15, covering immediate "
        "service disruption and reconfiguration hazards. "
        "Propagation risk (Eq. 13): R_prop = sum_{e in E} I(util_e > 0.85) * [1 - exp(-1.8*(util_e-0.85)/0.15)] * 40, "
        "capturing secondary cascading congestion risk. "
        "Robust risk constraint (Eq. 14): R_robust(a) = R_post(a) + z_alpha * sigma_R(a) <= R_max, where "
        "z_alpha = 1.645 (95% one-sided Gaussian quantile) and sigma_R = 0.08 * R_post (proportional estimation "
        "uncertainty). This bound applies to the estimated mean risk, not individual recovery outcomes. "
        "Empirical validation at R_max=35.0 confirms 0.0% observed violation rate (N=30 independent scenarios)."))

    add(heading2("3.6", "Multi-Dimensional Intervention Cost Model"))
    add(para("Normal",
        "Direct control-plane cost (Eq. 15): C_I(a) = w_rule * DeltaRules + w_sw * DeltaSwitches + "
        "w_msg * Msg_ctrl, with weights w_rule=1.0, w_sw=2.5, w_msg=0.5. "
        "Transient disruption cost (Eq. 16): C_D(a) = (DeltaSwitches * 12ms / 1000) * d_f * 5.0, where "
        "12ms is the per-switch TCAM rule commit delay. "
        "Latency SLA excess (Eq. 17): C_L(a) = max(0, lat_predicted - SLA_lat)."))

    add(heading2("3.7", "Normalized Combinatorial Optimization"))
    add(para("Normal",
        "The optimal intervention a* minimizes the normalized objective (Eq. 18): "
        "J(a) = lambda_I*(C_I/C_I,ref) + lambda_D*(C_D/C_D,ref) + lambda_L*(C_L/C_L,ref) + "
        "beta*(R_post/R_max) - gamma*(Psi/Psi_ref), "
        "subject to: R_robust(a) <= R_max (robust risk ceiling); P(F_rec|do(a)) >= tau (SLA recovery confidence); "
        "connectivity(a) = 1 (topological reachability)."))
    add(para("Normal",
        "The solver enumerates K=6 loop-free shortest candidate paths plus their throttled variants, yielding "
        "|A| <= 13 candidates. It selects the lowest-J(a) feasible candidate. This is a heuristic with a bounded "
        "candidate set, not a global optimum. Ties are broken by evaluation order (deterministic under fixed seeds). "
        "Reference normalizers: C_I,ref=30.0, C_D,ref=50.0, C_L,ref=40.0, Psi_ref=10.0. All parameter values "
        "are listed in Table 2a."))

    add(para("tablecaption", "Table 2a. CIRAH algorithm parameters."))
    params = [
        ("lambda_I","1.0","Intervention cost weight"),
        ("lambda_D","0.5","Disruption cost weight"),
        ("lambda_L","0.3","Latency SLA weight"),
        ("beta","1.2","Risk penalty weight"),
        ("gamma","0.8","Healing field weight"),
        ("tau","0.75","Minimum recovery confidence"),
        ("R_max","35.0","Hard post-recovery risk ceiling"),
        ("z_alpha","1.645","95% one-sided Gaussian quantile"),
        ("sigma_R","0.08 * R_post","Proportional risk estimation uncertainty"),
        ("sigma","1.5","CIHF Laplacian diffusion parameter"),
        ("K","6","Max. candidate paths per failure event"),
        ("C_I,ref / C_D,ref / C_L,ref","30.0 / 50.0 / 40.0","Cost normalization scales"),
        ("Psi_ref","10.0","Healing gain normalization scale"),
        ("Fallback throttle (partition)","0.50","Ingress rate when partition detected"),
        ("Fallback throttle (risk)","0.75","Ingress rate for risk-violating paths"),
        ("P(F_e=0/1/2)","0.95 / 0.03 / 0.02","Bayesian priors: Normal / Degraded / Severed"),
    ]
    add(make_table_xml(["Symbol / Parameter","Value","Description"], params))

    add(heading2("3.8", "Safe Fallback Mechanism"))
    add(para("Normal",
        "When A_feas is empty, CIRAH invokes a two-tier fallback. "
        "(1) Network Partition Check: partition detected via graph reachability on the active-link subgraph "
        "(nx.has_path on links with status=1). If no path exists, CIRAH applies 50% ingress rate throttling "
        "to prevent buffer overflows, reports partition_detected=True, and sets recovery_time_ms=2000 to signal "
        "service unavailability. CIRAH does not claim false recovery under physical partition. The 50% throttle "
        "halves offered load to limit buffer overflow on surviving links. "
        "(2) Paced Detour: if connected paths exist but all violate R_max, the lowest-risk connected candidate "
        "is selected with 75% ingress rate limiting. Fallback was triggered in 6.7% of runs at R_max=35.0 "
        "and in up to 30.0% at R_max=10.0. Throttling cannot restore connectivity across a true physical partition."))

    add(heading2("3.9", "Algorithm Specification"))
    alg_lines = [
        "Algorithm 1: CIRAH Counterfactual Risk-Constrained Intervention Selection",
        "Input:  G=(V,E), Telemetry O, Flows F, Impaired flow f*, R_max, tau",
        "Output: Optimal intervention a*",
        "",
        "1.  A <- {a_0 (null action)}",
        "2.  // Step 1: 3-State Bayesian Causal Traceback",
        "3.  For each edge e in E do:",
        "4.      Compute s_k(e) = P(O_e|F=k)*P(F=k)*w_k(Paths) for k in {0,1,2}",
        "5.      P(F_e=k|O_e,Paths) <- s_k(e) / sum_{j=0}^2 s_j(e)",
        "6.  End",
        "7.  // Step 2: Minimum-Causal Candidate Generation",
        "8.  H <- PenalizeGraphWeights(G, posteriors)",
        "9.  Paths_K <- K-shortest loop-free paths(H, f*.src, f*.dst, K=6)",
        "10. For each path p in Paths_K:",
        "11.     A <- A + {reroute(p, throttle=1.0), reroute_paced(p, throttle=0.85)}",
        "12. End",
        "13. // Step 3: Counterfactual Evaluation & Constrained Filtering",
        "14. A_feas <- empty",
        "15. For each candidate a in A:",
        "16.     Y_hat(a) <- EvaluateCounterfactual(M, do(A=a), O, Fixed_U)",
        "17.     R_post(a) <- EvaluateRisk(G, a, Y_hat(a))",
        "18.     R_robust <- R_post + z_alpha * sigma_R(a)",
        "19.     J(a) <- lambda_I*(C_I/ref)+...+beta*(R_post/R_max)-gamma*(Psi/Psi_ref)",
        "20.     If R_robust<=R_max AND P_rec>=tau AND connected: A_feas += {a}",
        "21. End",
        "22. // Step 4: Action Selection",
        "23. If A_feas != empty: a* <- argmin_{a in A_feas} J(a)",
        "24. Else:               a* <- ExecuteSafeFallback(A, G, f*)",
        "25. InstallFlowModRules(a*); Return a*",
    ]
    add(code_block("\n".join(alg_lines)))

    add(heading2("3.10", "Computational Complexity Analysis"))
    add(para("Normal",
        "Algorithmic complexity per failure event: Bayesian 3-state fault estimation O(|E|); "
        "K-shortest loop-free path generation O(K*|V|*(|E|+|V|*log|V|)); "
        "counterfactual evaluation per candidate O(|F|*|Path|+|E|); "
        "CIHF diffusion O(|V|^2) using precomputed inverted kernel (initialized in O(|V|^3), "
        "O(|V|^2) memory, O(|V|^2) per-event). "
        "Overall: O(K*|V|*log|V| + |A|*(|E|+|V|^2))."))
    add(para("Normal",
        "Measured controller algorithmic execution latency (60 profiling runs, Intel Core i5-8600K, 16 GB RAM): "
        "Abilene (11 nodes): Mean=6.28 ms, Median=5.92 ms, p95=8.70 ms, Worst-case=9.15 ms. "
        "GEANT (22 nodes): Mean=10.78 ms, Median=10.93 ms, p95=14.33 ms, Worst-case=15.70 ms. "
        "Fat-tree k=4 (20 nodes): mean total recovery 105.7 ms (algorithm-only execution <16 ms). "
        "This profiling measures isolated CPU computation only, excluding OpenFlow rule installation "
        "and data-plane propagation delay."))

    # ── 4. Experimental Setup ──
    add(heading1("4", "Experimental Setup"))

    add(heading2("4.1", "Topologies"))
    add(para("Normal",
        "Three network topologies are evaluated. "
        "(1) Abilene Internet2 Backbone: 11 nodes, 30 directed edges, 1,000 Mbps capacity, geographical delays 5-28 ms. "
        "(2) GEANT Pan-European Research Backbone: 22 nodes, 56 directed edges, 1,000 Mbps core links, 500 Mbps regional branches. "
        "(3) Fat-tree k=4: 20 nodes (4 core, 8 aggregation, 8 edge switches), 64 directed edges, 1,000/500 Mbps. "
        "All topologies are constructed programmatically; no external GML files are required."))

    add(heading2("4.2", "Traffic Flow Demands and SLA Profiles"))
    add(para("Normal",
        "Each experiment generates 8 concurrent traffic flows between randomly sampled source-destination pairs "
        "with demands between 10.0 and 45.0 Mbps. Flow SLAs specify maximum permissible latency "
        "(SLA_lat in [1.8, 2.5] * base delay) and maximum packet loss (SLA_loss in [1.0%, 3.0%])."))

    add(heading2("4.3", "Fault Generation and Telemetry Noise"))
    add(para("Normal",
        "Seven failure modes are evaluated: single-link failure (k=1); concurrent multi-link failures "
        "(k in {2,3,4}); 75% link capacity brownout; delay and loss spikes (+80 ms delay, +12% loss); "
        "bursty traffic congestion (3.5x demand surge); and telemetry measurement noise "
        "(sigma_noise in [0.0, 0.30])."))

    add(heading2("4.4", "Evaluated Baselines and Ablation Variants"))
    add(para("Normal",
        "Baselines: Static-SP [10] (non-adaptive), Dynamic-SP [7] (reactive Dijkstra), Backup-Path [3] "
        "(fast reroute), Risk-Aware [4] (multi-metric Dijkstra), MinChange-SP (edge-overlap minimization), "
        "and Constrained-MinChange (same candidate paths and R_max constraint as CIRAH, but myopic load "
        "estimation and minimum switch-diff selection). Ablations: CIRAH-noCausal, CIRAH-noCF, "
        "CIRAH-noCIHF, CIRAH-noRisk, CIRAH-noInterv."))

    add(heading2("4.5", "Experimental Protocol and Statistical Design"))
    add(para("Normal",
        "N=50 independent Monte Carlo runs per severity level with identical random seeds across all methods "
        "(paired seed policy). Success metric: a recovery attempt is classified as successful if and only if "
        "the target flow satisfies both (1) connectivity — no link in the selected path has predicted loss >= 99% "
        "— and (2) SLA compliance — predicted end-to-end latency <= SLA_lat and packet loss <= SLA_loss. "
        "Denominator = total runs; only the target flow is evaluated per run. "
        "Primary inferential test: two-sided paired Wilcoxon signed-rank test, alpha=0.05. "
        "Effect sizes: within-pair Cohen's d_z = D_bar / s_D. "
        "Multiplicity control: Primary Abilene family (N=6: switch churn and intervention cost at k=1,2,3) "
        "and Omnibus family (N=30: 2 topologies x 3 severity levels x 5 metrics)."))

    # ── 5. Results ──
    add(heading1("5", "Experimental Results and Discussion"))

    add(heading2("5.1", "Multi-Failure Severity Evaluation (RQ1, RQ3)"))
    add(para("figurecaption", "Fig. 2. Recovery success rate across k=0-4 simultaneous link failures on the Abilene topology (N=50 runs per condition, 95% CI). [Insert fig5_success_vs_severity.png]"))
    add(para("Normal",
        "Table 2 reports performance across failure severity levels on the Abilene topology. CIRAH matches "
        "Dynamic-SP in recovery success (90.0% at k=1; 72.0% at k=2; 68.0% at k=3) while consistently "
        "reducing switch churn and intervention cost. Under double-link failure (k=2), CIRAH reduces mean "
        "switch modifications from 3.78 to 3.26 — a 13.8% reduction (p=0.00082, d_z=-0.56) — and decreases "
        "mean intervention cost from 19.02 to 17.25 — a 9.3% reduction (p=0.00089). At k=1, CIRAH achieves "
        "recovery time of 49.4 ms comparable to Dynamic-SP (49.2 ms). At k=3, recovery time rises to "
        "415.0 ms vs. 58.8 ms for Dynamic-SP, reflecting the combinatorial depth of counterfactual path "
        "search. Backup-Path restores fewer scenarios successfully because pre-computed disjoint paths fail "
        "under concurrent multi-link failures."))

    add(para("tablecaption", "Table 2. Multi-link failure severity results (Abilene topology, N=50 paired runs per condition)."))
    t2h = ["Severity","Method","Success (%)","Latency (ms)","Loss (%)","Risk (R_post)","Switches Mod.","Cost (C_I)","Recovery (ms)"]
    t2r = [
        ["k=1","Dynamic-SP","90.0","43.0 +/- 2.3","0.19 +/- 0.03","2.91 +/- 0.74","2.84 +/- 0.32","14.34 +/- 1.55","49.2 +/- 3.9"],
        ["k=1","CIRAH","90.0","44.6 +/- 2.4","0.19 +/- 0.03","2.93 +/- 0.74","2.28 +/- 0.24","12.30 +/- 1.22","49.4 +/- 2.9"],
        ["k=2","Dynamic-SP","72.0","49.3 +/- 2.8","0.22 +/- 0.03","11.39 +/- 3.43","3.78 +/- 0.25","19.02 +/- 1.20","60.5 +/- 3.0"],
        ["k=2","CIRAH","72.0","52.4 +/- 3.0","0.24 +/- 0.03","11.46 +/- 3.42","3.26 +/- 0.21","17.25 +/- 1.06","178.9 +/- 65.8"],
        ["k=3","Dynamic-SP","68.0","53.1 +/- 2.8","0.21 +/- 0.03","21.57 +/- 5.40","3.64 +/- 0.35","18.27 +/- 1.65","58.8 +/- 4.2"],
        ["k=3","CIRAH","68.0","57.8 +/- 3.5","0.22 +/- 0.03","21.64 +/- 5.39","3.24 +/- 0.30","16.95 +/- 1.47","415.0 +/- 106.1"],
    ]
    add(make_table_xml(t2h, t2r))

    add(heading2("5.2", "Control-Plane Churn and Intervention Footprint (RQ2)"))
    add(para("Normal",
        "Under double-link failure conditions (k=2) on the Abilene topology, CIRAH reduces the mean number of "
        "modified switches from 3.78 to 3.26 (13.8% reduction, p=0.00082, Cohen's d_z=-0.56) and decreases mean "
        "control-plane intervention cost from 19.02 to 17.25 (9.3% reduction, p=0.00089). Both CIRAH and "
        "Dynamic-SP achieve an identical recovery success rate of 72.0%. Under single-link failures (k=1), "
        "CIRAH reduces switch churn from 2.84 to 2.28 (19.7% reduction, p=0.00206, d_z=-0.47) and intervention "
        "cost from 14.34 to 12.30 (14.2% reduction, p=0.00209). CIRAH's mean recovery time at k=1 is 49.4 ms "
        "compared to 49.2 ms for Dynamic-SP — comparable single-failure recovery speed while avoiding "
        "rewriting forwarding rules on intermediate switches."))

    add(heading2("5.3", "Telemetry Noise Robustness (RQ3)"))
    add(para("figurecaption", "Fig. 3. Recovery success under telemetry measurement noise (sigma_noise = 0.0-0.30) comparing Bayesian SCM against rule-based diagnosis (N=50 runs per noise level). [Insert fig10_telemetry_noise_resilience.png]"))
    add(para("Normal",
        "Under severe telemetry distortion (sigma=0.30), Dynamic-SP success rate degrades to 44.0%, while CIRAH "
        "sustains 54.0% (+22.7% relative advantage) with significantly lower residual risk (8.53 vs. 10.01). "
        "This confirms Hypothesis H3: Bayesian SCM traceback effectively filters out measurement noise that "
        "causes brittle shortest-path algorithms to route flows into congested bottlenecks."))

    add(heading2("5.4", "Rebuilt 6-Way Component Ablation Study (RQ4)"))
    add(para("figurecaption", "Fig. 4. Six-way ablation results (N=60 paired runs): (a) recovery success, (b) residual risk, (c) switch churn, (d) intervention cost. [Insert fig9_component_ablations.png]"))

    add(para("tablecaption", "Table 3. Rebuilt 6-way component ablation results (Abilene topology, N=60 paired runs)."))
    t3h = ["Variant","What Was Removed","Success (%)","SLA Viol. (%)","Constr. Viol. (%)","Switches","Cost (C_I)","Risk (R_post)","Healing (Psi)"]
    t3r = [
        ["CIRAH-full","None (Reference)","70.0","30.0","0.0","3.60","18.90","7.06","0.974"],
        ["CIRAH-noCausal","SCM Bayesian traceback","70.0","30.0","1.7","3.55","18.63","8.29","0.960"],
        ["CIRAH-noCF","Counterfactual do(A) (Myopic)","70.0","30.0","0.0","3.60","18.90","7.04","0.974"],
        ["CIRAH-noCIHF","Healing field (gamma=0)","70.0","30.0","0.0","3.60","18.90","7.06","0.000"],
        ["CIRAH-noRisk","Hard risk bound (R_max=inf, beta=0)","56.7","43.3","0.0","3.25","17.68","8.57","0.998"],
        ["CIRAH-noInterv","Intervention cost penalty (lambda_I=0)","70.0","30.0","0.0","3.78","19.53","7.04","0.958"],
    ]
    add(make_table_xml(t3h, t3r))

    add(para("Normal",
        "Removing the hard risk constraint (CIRAH-noRisk) drops recovery success from 70.0% to 56.7% and surges "
        "SLA violations from 30.0% to 43.3%, while increasing residual risk to 8.57. Without risk gating, "
        "unconstrained optimization greedily routes traffic through heavily loaded bottlenecks that trigger "
        "secondary buffer drops. Removing the intervention cost penalty (CIRAH-noInterv) increases switch "
        "modifications from 3.60 to 3.78 and elevates intervention cost to 19.53. Removing the CIHF healing "
        "field (CIRAH-noCIHF) collapses the spectral healing gain to Psi=0.000, but produces no measurable "
        "change in success, switches, cost, or risk — consistent with the finding that CIHF does not change "
        "action selection under tested conditions. Removing causal traceback (CIRAH-noCausal) increases "
        "post-repair risk from 7.06 to 8.29 and introduces constraint violations (1.7%) due to false-positive "
        "fault localization under cross-traffic noise."))

    add(heading2("5.5", "Counterfactual Prediction Accuracy and Physical Validation"))
    add(para("Normal",
        "Campaign 5 evaluates counterfactual predictions against an independent stochastic finite-buffer "
        "data-plane simulator (simulate_independent_dataplane) that models physical queue dynamics, traffic "
        "burstiness, and buffer overflow tail drops across N=60 trials. "
        "Results: Latency MAE = 1.23 +/- 0.61 ms (CIRAH) vs. 1.11 +/- 0.54 ms (myopic baseline). "
        "Packet Loss MAE = 0.37 +/- 0.18%. "
        "Spearman action ranking correlation: CIRAH rho = 0.967 +/- 0.021; myopic rho = 0.968 +/- 0.065 "
        "(N=60 valid paired trials). Both methods achieve high rank concordance with ground-truth data-plane "
        "action rankings. CIRAH displays narrower ranking variance (+/-0.021 vs. +/-0.065)."))

    add(heading2("5.6", "Constrained Baseline, Fat-Tree Scalability, and Risk Sensitivity"))
    add(para("tablecaption", "Table 4. CIRAH vs. Constrained-MinChange baseline (Abilene, avg. k=1,2,3, N=150 total)."))
    t4h = ["Method","Success (%)","Switches Modified","Intervention Cost","Residual Risk"]
    t4r = [
        ["Static-SP","12.0","0.00","0.00","89.08"],
        ["Dynamic-SP","76.7","3.42","17.21","11.96"],
        ["MinChange-SP","74.7","2.90","15.40","12.30"],
        ["Constrained-MinChange","74.7","2.91","15.45","12.30"],
        ["CIRAH","76.7","2.93","15.51","12.01"],
    ]
    add(make_table_xml(t4h, t4r))
    add(para("Normal",
        "CIRAH achieves the same success rate as Dynamic-SP (76.7%) with similar switch count to "
        "Constrained-MinChange (2.93 vs. 2.91). The marginal risk advantage (12.01 vs. 12.30) reflects "
        "CIRAH's use of causal posteriors to avoid fault-probable links. On the Fat-tree topology (20 nodes, "
        "64 directed edges), all methods achieve 90% success; CIRAH reduces switch modifications from 3.46 "
        "(Dynamic-SP) to 2.29 — a 33.8% reduction — demonstrating scalability beyond Abilene and GEANT."))

    add(para("tablecaption", "Table 5. Risk threshold sensitivity at k=2, Abilene (N=30 runs per R_max)."))
    t5h = ["R_max","Success (%)","Violation (%)","Fallback (%)","Mean R_post","Mean Switches"]
    t5r = [
        ["10.0","80.0","20.0","20.0","4.98","3.13"],
        ["20.0","70.0","13.3","30.0","14.44","2.73"],
        ["35.0 (default)","93.3","0.0","6.7","2.91","2.90"],
        ["50.0","70.0","6.7","30.0","12.06","2.60"],
        ["100.0","73.3","3.3","26.7","8.91","3.17"],
    ]
    add(make_table_xml(t5h, t5r))
    add(para("Normal",
        "R_max=35.0 achieves the highest success rate (93.3%) with 0.0% violations and only 6.7% fallback, "
        "confirming it as a well-calibrated default for the Abilene topology under the evaluated traffic model."))

    # ── 6. Statistical Validation ──
    add(heading1("6", "Inferential Statistical Validation"))

    add(para("tablecaption", "Table 6. Paired inferential hypothesis tests: CIRAH vs. Dynamic-SP (Abilene topology, N=50)."))
    t6h = ["k","Metric","CIRAH Mean","Dyn-SP Mean","% Reduction","Mean Diff","95% CI","Cohen's d_z","Wilcoxon p","Holm p","Sig. (N=6)?"]
    t6r = [
        ["1","Switches Modified","2.28","2.84","-19.7%","-0.56","[-0.90, -0.22]","-0.47","0.00206","0.0083","Yes"],
        ["1","Intervention Cost","12.30","14.34","-14.2%","-2.04","[-3.30, -0.78]","-0.46","0.00209","0.0083","Yes"],
        ["2","Switches Modified","3.26","3.78","-13.8%","-0.52","[-0.78, -0.26]","-0.56","0.00082","0.0049","Yes"],
        ["2","Intervention Cost","17.25","19.02","-9.3%","-1.77","[-2.69, -0.85]","-0.55","0.00089","0.0049","Yes"],
        ["3","Switches Modified","3.24","3.64","-11.0%","-0.40","[-0.66, -0.14]","-0.44","0.00280","0.0083","Yes"],
        ["3","Intervention Cost","16.95","18.27","-7.2%","-1.32","[-2.23, -0.41]","-0.41","0.00304","0.0083","Yes"],
    ]
    add(make_table_xml(t6h, t6r))
    add(para("Normal",
        "All six Primary Abilene family hypotheses are significant after Holm-Bonferroni step-down adjustment "
        "(p_adj <= 0.0083 < 0.05), confirming Hypothesis H1 with high statistical confidence. The paired "
        "difference 95% confidence interval for switch churn at k=2 strictly excludes zero ([-0.78, -0.26]). "
        "Recovery time, residual risk, and success rate do not achieve omnibus significance under the N=30 "
        "omnibus family; these are reported as non-significant."))

    # ── 7. Discussion ──
    add(heading1("7", "Discussion and System Trade-offs"))
    add(para("Normal",
        "Trade-off between churn and path latency. CIRAH occasionally accepts a path with 2 to 3 ms higher "
        "propagation latency if that path avoids reconfiguring multiple core switches. In carrier and datacenter "
        "environments, this trade-off is highly desirable: saving multiple switch TCAM updates avoids transient "
        "packet reordering and flow table lockups."))
    add(para("Normal",
        "CIHF as interpretive visualization. The CIHF field correctly computes spatial stress relief across the "
        "network graph but does not change action selection in 99.2% of tested scenarios. Its objective term "
        "contribution (mean 0.078) is 0.11x the cost term (0.720) and 0.02x the risk term (3.455). Increasing "
        "the healing field weight gamma up to 6.4 (8x default) does not consistently change selection. "
        "CIHF is retained as an interpretive visualization of spatial stress relief."))
    add(para("Normal",
        "Counterfactual value under capacity constraints. The counterfactual do(A) mechanism changes 72% of "
        "selected actions under tight capacity constraints (80 Mbps links, 40 Mbps cross-traffic). Under "
        "default wide-capacity conditions (1,000 Mbps), it produces identical outcomes to myopic evaluation "
        "because traffic displacement does not cause congestion. CF has measurable value in "
        "capacity-constrained environments at the cost of higher computation."))
    add(para("Normal",
        "Recovery time overhead and scaling. CIRAH's SCM-based diagnosis and combinatorial candidate evaluation "
        "introduce measurable decision latency that increases with failure severity. Recovery time at k=1 is "
        "on par with reactive shortest path (49.4 ms vs. 49.2 ms); it increases to 178.9 ms at k=2 and "
        "reaches 415.0 ms at k=3, compared with 58.8 ms for Dynamic-SP. CIRAH trades computational decision "
        "latency for substantial reductions in switch modification churn and lower risk of secondary congestion."))

    # ── 8. Threats ──
    add(heading1("8", "Threats to Validity and Limitations"))
    add(para("Normal",
        "Construct Validity. Intervention cost is modeled using OpenFlow message weights and switch reconfiguration "
        "delay proxies (Delta_t_commit = 12 ms). Hardware-specific commit latencies may vary."))
    add(para("Normal",
        "CIHF Limitation. Controlled experiments across 720 paired runs confirm the Causal Intervention Healing "
        "Field does not change the selected recovery action in 99.2% of tested scenarios and produces no "
        "measurable difference in success, switches, cost, or risk. CIHF is retained as an interpretive "
        "stress-relief visualization."))
    add(para("Normal",
        "Counterfactual Evaluation Scope. The counterfactual do(A) mechanism changes action selection under "
        "tight capacity constraints but produces identical outcomes to myopic evaluation under the default "
        "wide-capacity conditions used in the ablation campaign. The model is calibrated against the simulator's "
        "own structural equations; accurate predictions reflect internal consistency, not external validity "
        "against a physical testbed."))
    add(para("Normal",
        "Risk Constraint Assumptions. The robust risk bound R_robust = R_post + z_alpha * sigma_R uses a "
        "heuristic uncertainty estimate sigma_R = 0.08 * R_post, not an empirically calibrated variance. "
        "The bound applies to the estimated mean risk under Gaussian noise, not to individual recovery outcomes."))
    add(para("Normal",
        "Bayesian Degraded-State Limitation. The degraded-state classifier has not been evaluated against true "
        "degraded links because the fault generator injects only complete severances, leaving no degraded "
        "ground-truth cases in the evaluation dataset."))
    add(para("Normal",
        "External Validity. All results are from simulation on Abilene, GEANT, and Fat-tree topologies "
        "without physical SDN hardware (Mininet, P4 switches) validation. Results may not generalize to "
        "production SDN deployments, data-center topologies, or real traffic distributions."))

    # ── 9. Conclusion ──
    add(heading1("9", "Conclusion and Future Scope"))
    add(para("Normal",
        "This paper presented CIRAH, a causal-intervention optimization framework for autonomous network "
        "self-healing under risk constraints. By formalizing network dynamics as an SCM, computing Pearl's "
        "counterfactual interventional outcomes do(A=a), and enforcing robust post-recovery risk limits, "
        "CIRAH systematically discovers the minimum-cost recovery action that satisfies post-repair risk "
        "constraints. Across approximately 5,300 paired Monte Carlo simulation runs on Abilene, GEANT, and "
        "Fat-tree topologies, CIRAH demonstrated a statistically verified reduction in switch churn (13.8% "
        "to 19.7%, p < 0.01) over reactive shortest-path rerouting while maintaining 0.0% risk constraint "
        "violations at R_max=35.0. The 6-way ablation study established that the hard risk constraint is "
        "the most impactful component (success drops from 70.0% to 56.7% when removed), followed by the "
        "intervention cost penalty. The Causal Intervention Healing Field was found to not influence candidate "
        "selection under tested conditions and is retained as an interpretive visualization. Future work "
        "targets deployment on physical P4-programmable SDN testbeds for sub-millisecond line-rate "
        "counterfactual inference."))

    add(para("acknowlegments",
        "Conflict of Interest. The authors declare no competing financial interests or personal relationships "
        "that could have appeared to influence the work reported in this paper."))
    add(para("acknowlegments",
        "Data Availability. The complete source code, topology graphs, Monte Carlo experiment runners, raw CSV "
        "datasets, and figure generation scripts are openly available at https://github.com/Shabreen123/CIRAH"))

    # ── References ──
    add(heading1("", "References"))
    refs = [
        "1. Sanz Rodrigo, M. et al.: Network Digital Twin-Generated Dataset for ML-based Zero-Touch SLA Preservation. Zenodo (2025). https://doi.org/10.5281/zenodo.17255327",
        "2. Moustafa, N., Slay, J.: UNSW-NB15: A Comprehensive Dataset for Network Intrusion Detection. Proc. IEEE MilCIS, pp. 1-6 (2015)",
        "3. Qin, H. et al.: FAPR: An Adaptive Approach to Link Failure Recovery in SDN with High Speed and Low Interruption Rate. Applied Sciences 14(11), 4719 (2024)",
        "4. Yusuf, M.N. et al.: Adaptive Path Selection Algorithm with Flow Classification for Software-Defined Networks. Mathematics 11(6), 1404 (2023)",
        "5. McKeown, N. et al.: OpenFlow: Enabling Innovation in Campus Networks. ACM SIGCOMM CCR 38(2), 69-74 (2008)",
        "6. Kreutz, D. et al.: Software-Defined Networking: A Comprehensive Survey. Proc. IEEE 103(1), 14-76 (2015)",
        "7. Sharma, S. et al.: Enabling Fast Failure Recovery in OpenFlow Networks. Proc. DRCN, pp. 164-171 (2011)",
        "8. Clark, D.D. et al.: A Knowledge Plane for the Internet. Proc. ACM SIGCOMM, pp. 3-10 (2003)",
        "9. Pearl, J.: Causality: Models, Reasoning, and Inference, 2nd edn. Cambridge Univ. Press (2009)",
        "10. Polat, O., Polat, H.: An Intelligent SDN Controller to Detect and Mitigate DoS Attacks. J. ICT 20(1), 1-24 (2021)",
        "11. Polat, O. et al.: Supervised and Deep Learning for DDoS Detection in SDN: Systematic Review. Eng. Sci. Technol. 75, 102290 (2026)",
        "12. Kachavimath, A.V., Narayan, D.G.: Hybrid DL with Consensus Feature Selection for DDoS in SDN. Procedia Comput. Sci. 252, 643-652 (2025)",
        "13. Mehmood, S. et al.: DDoS Detection in SDN Using Optimiser-equipped CNN-MLP. PLoS ONE 20(1), e0312425 (2025)",
        "14. Gayantha, N. et al.: Advanced DDoS Detection and Mitigation in SDN. Proc. IEEE SCSE (2025)",
        "15. Hnamte, V. et al.: DDoS Attack Detection Using DNN in SDN. Comput. Secur. 138, 103661 (2024)",
        "16. Paidipati, K.K. et al.: Ensemble of DRL for DDoS Detection in Cloud-Based SDN. Multimedia Tools Appl. 83(11), 32367-32385 (2024)",
        "17. Al-Dunainawi, Y. et al.: Optimised AI Model for DDoS Detection in SDN. IEEE Access 11, 106733-106748 (2023)",
        "18. Setitra, M.A. et al.: Optimised MLP-CNN for DDoS Detection in SDN. Network 3(4), 538-562 (2023)",
        "19. Aslam, M. et al.: Adaptive ML-Based DDoS Mitigation for SDN-Enabled IoT. Sensors 22(7), 2697 (2022)",
        "20. Swileh, M.N., Zhang, S.: Unseen Attack Detection in SDN Using BERT-Based LLM. AI 6(7), 154 (2025)",
        "21. Gadallah, W.G. et al.: Deep Learning Technique to Detect DDoS in SDN. Comput. Secur. 137, 103588 (2024)",
        "22. Wang, H. et al.: DDoS Detection Using Stacked Autoencoder and GRU for SDN. Comput. J. bxaf021 (2025)",
        "23. Abid, Y.A. et al.: Multilevel DNN for DDoS Detection in SDN-IoT. IEEE IoT J. 11(14), 24715-24725 (2024)",
        "24. Veeresh, G.B. et al.: Swish-Optimized Trident Fusion Network for Attack Classification in SDN. Knowl.-Based Syst. 114860 (2025)",
        "25. Chattopadhyay, S. et al.: Enhanced DDoS Detection in SDN Using Ensemble Learning. SN Comput. Sci. 5(5), 580 (2024)",
        "26. Zaidoun, A.S., Lachiri, Z.: Hybrid DL for Multi-class DDoS Detection in SDN. Ann. Telecommun. (2025)",
        "27. Nithya, R., Vinoth Kumar, K.: Attention Driven Hybrid DL for IDS in SDN. Results Eng. 26, 113552 (2026)",
        "28. Leena, R. et al.: Attack Detection Using Hierarchical Dual GNN. Comput. Electr. Eng. 124, 110315 (2025)",
        "29. Rbah, Y. et al.: Hybrid Deep-Learning SDN-Based IDS for IoMT. IRECAP 14(1) (2024)",
        "30. Alabrah, A.: Improved CCF Detector with IQR Outlier Normalisation. Sensors 23(9), 4406 (2023)",
        "31. Li, J. et al.: Path Selection for Link Failure Protection in Hybrid SDNs. Future Gener. Comput. Syst. 137, 201-215 (2022)",
        "32. Liu, S. et al.: CNN-BiGRU-Attention for Short-Term Traffic Flow Prediction. Sustainability 16(5), 1986 (2024)",
        "33. Arun Prasad, P.B. et al.: Hybrid Metaheuristics with DL for Cyberattack Prevention in SDN. Tech. Gaz. 31(1) (2024)",
        "34. Kavitha, S. et al.: Intelligent IDS Using Enhanced AOA with DL. Tech. Gaz. 30(4) (2023)",
        "35. Naeen, H.M. et al.: Enhancing SDN Security with DL for DDoS Detection. Sci. Rep. 15(1), 33419 (2025)",
    ]
    for ref in refs:
        add(para("referenceitem", ref))

    # End of document section properties
    sectPr = E("sectPr")
    pgSz = E("pgSz")
    pgSz.set(w("w"), "11906")   # A4 width in twentieths of a point
    pgSz.set(w("h"), "16838")   # A4 height
    sectPr.append(pgSz)
    pgMar = E("pgMar")
    pgMar.set(w("top"),    "1474")   # 26mm
    pgMar.set(w("bottom"), "1360")   # 24mm
    pgMar.set(w("left"),   "1134")   # 20mm
    pgMar.set(w("right"),  "1134")   # 20mm
    pgMar.set(w("header"), "709")
    pgMar.set(w("footer"), "709")
    sectPr.append(pgMar)
    body_el.append(sectPr)

    return body_el

# ── Assemble the docm ───────────────────────────────────────────────────────

def build_docm():
    print("Reading template...")
    with zipfile.ZipFile(TEMPLATE, 'r') as zt:
        template_files = {name: zt.read(name) for name in zt.namelist()}

    # Parse template document.xml to get namespaces and root structure
    orig_doc_xml = template_files['word/document.xml']
    orig_tree = etree.fromstring(orig_doc_xml)
    nsmap = orig_tree.nsmap

    # Build our new body
    print("Building document body...")
    new_body = build_body()

    # Reconstruct document element with template namespaces
    doc_el = etree.Element(
        f"{{{W}}}document",
        nsmap={
            'wpc': 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas',
            'cx': 'http://schemas.microsoft.com/office/drawing/2014/chartex',
            'cx1': 'http://schemas.microsoft.com/office/drawing/2015/9/8/chartex',
            'cx2': 'http://schemas.microsoft.com/office/drawing/2015/10/21/chartex',
            'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
            'aink': 'http://schemas.microsoft.com/office/drawing/2016/ink',
            'am3d': 'http://schemas.microsoft.com/office/drawing/2017/model3d',
            'o': 'urn:schemas-microsoft-com:office:office',
            'oel': 'http://schemas.microsoft.com/office/2019/extlst',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
            'v': 'urn:schemas-microsoft-com:vml',
            'wp14': 'http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing',
            'wp': WP,
            'w10': 'urn:schemas-microsoft-com:office:word',
            'w': W,
            'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
            'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
            'w16se': 'http://schemas.microsoft.com/office/word/2015/wordml/symex',
            'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
            'wpi': 'http://schemas.microsoft.com/office/word/2010/wordprocessingInk',
            'wne': 'http://schemas.microsoft.com/office/word/2006/wordml',
            'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
        }
    )
    doc_el.append(new_body)

    new_doc_xml = etree.tostring(doc_el, xml_declaration=True, encoding='UTF-8', standalone=True)

    # Write output docm (keep all template parts except document.xml)
    print(f"Writing {OUT_PATH}...")
    with zipfile.ZipFile(OUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for name, data in template_files.items():
            if name == 'word/document.xml':
                zo.writestr(name, new_doc_xml)
            else:
                zo.writestr(name, data)

    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"Done: {OUT_PATH} ({size_kb} KB)")

if __name__ == '__main__':
    build_docm()
