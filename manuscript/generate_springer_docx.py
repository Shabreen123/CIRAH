"""
Generate CIRAH_Springer.docx — Springer LNCS single-column Word document.
Matches splnproc2510.docm: Times New Roman, numbered sections, three-line tables.
"""
import os
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "CIRAH_Springer.docx")
FIG_DIR  = os.path.abspath(os.path.join(OUT_DIR, "..", "figures"))

# ── low-level helpers ───────────────────────────────────────────────────────

def rfont(run, pt, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(pt)
    run.font.bold   = bold
    run.font.italic = italic

def pfmt(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         sb=0, sa=5, ls=1.15, fi=0):
    f = p.paragraph_format
    f.alignment          = align
    f.space_before       = Pt(sb)
    f.space_after        = Pt(sa)
    f.line_spacing_rule  = WD_LINE_SPACING.MULTIPLE
    f.line_spacing       = ls
    f.first_line_indent  = Pt(fi)

def cell_fmt(cell, text, pt=8, bold=False):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    rfont(r, pt, bold=bold)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)

def three_line_borders(tbl):
    el = tbl._tbl
    pr = el.find(qn('w:tblPr'))
    if pr is None:
        pr = OxmlElement('w:tblPr')
        el.insert(0, pr)
    bd = OxmlElement('w:tblBorders')
    for s in ('top','left','bottom','right','insideH','insideV'):
        e = OxmlElement(f'w:{s}')
        if s in ('top','bottom'):
            e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'12')
            e.set(qn('w:space'),'0');    e.set(qn('w:color'),'000000')
        else:
            e.set(qn('w:val'),'none')
        bd.append(e)
    x = pr.find(qn('w:tblBorders'))
    if x is not None: pr.remove(x)
    pr.append(bd)

def header_underline(row):
    for cell in row.cells:
        tc = cell._tc
        pr = tc.find(qn('w:tcPr'))
        if pr is None:
            pr = OxmlElement('w:tcPr'); tc.insert(0, pr)
        bd = OxmlElement('w:tcBorders')
        b  = OxmlElement('w:bottom')
        b.set(qn('w:val'),'single'); b.set(qn('w:sz'),'6')
        b.set(qn('w:space'),'0');    b.set(qn('w:color'),'000000')
        bd.append(b)
        x = pr.find(qn('w:tcBorders'))
        if x is not None: pr.remove(x)
        pr.append(bd)

def divider(doc):
    p = doc.add_paragraph()
    pr = p._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr')
    b  = OxmlElement('w:bottom')
    b.set(qn('w:val'),'single'); b.set(qn('w:sz'),'6')
    b.set(qn('w:space'),'1');    b.set(qn('w:color'),'999999')
    bd.append(b); pr.append(bd)
    p.paragraph_format.space_after = Pt(6)

# ── content helpers ─────────────────────────────────────────────────────────

def body(doc, text, pt=10, sa=5, fi=0):
    p = doc.add_paragraph()
    pfmt(p, sa=sa, fi=fi)
    r = p.add_run(text)
    rfont(r, pt)
    return p

def h1(doc, num, title):
    p = doc.add_paragraph()
    pfmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, sb=14, sa=6)
    r = p.add_run(f"{num}  {title}")
    rfont(r, 12, bold=True)

def h2(doc, num, title):
    p = doc.add_paragraph()
    pfmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, sb=10, sa=4)
    r = p.add_run(f"{num}  {title}")
    rfont(r, 10, bold=True)

def tbl_caption(doc, txt):
    p = doc.add_paragraph()
    pfmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, sb=8, sa=2)
    r = p.add_run(txt)
    rfont(r, 9, bold=True)

def fig_insert(doc, fname, caption):
    fpath = os.path.join(FIG_DIR, fname)
    p = doc.add_paragraph()
    pfmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, sb=8, sa=3)
    r = p.add_run()
    if os.path.exists(fpath):
        r.add_picture(fpath, width=Inches(5.0))
    else:
        rfont(r, 9, italic=True)
        r.text = f"[Figure placeholder: {fname}]"
    cp = doc.add_paragraph()
    pfmt(cp, align=WD_ALIGN_PARAGRAPH.CENTER, sb=2, sa=10)
    cr = cp.add_run(caption)
    rfont(cr, 9)

def make_table(doc, headers, rows):
    tbl_caption(doc, "")   # caller adds caption before calling
    t = doc.add_table(rows=len(rows)+1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.style     = 'Table Grid'
    three_line_borders(t)
    for ci, h in enumerate(headers):
        cell_fmt(t.rows[0].cells[ci], h, pt=8, bold=True)
    header_underline(t.rows[0])
    for ri, row in enumerate(rows, 1):
        for ci, v in enumerate(row):
            cell_fmt(t.rows[ri].cells[ci], str(v), pt=8)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return t

def algorithm(doc, text):
    p = doc.add_paragraph()
    pfmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, sb=6, sa=6)
    r = p.add_run(text)
    r.font.name = "Courier New"
    r.font.size = Pt(8)
    pr = p._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr')
    for s in ('top','left','bottom','right'):
        e = OxmlElement(f'w:{s}')
        e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4')
        e.set(qn('w:space'),'4');    e.set(qn('w:color'),'888888')
        bd.append(e)
    pr.append(bd)

# ═══════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════

doc = Document()
sec = doc.sections[0]
sec.page_height    = Cm(29.7)
sec.page_width     = Cm(21.0)
sec.top_margin     = Cm(2.6)
sec.bottom_margin  = Cm(2.4)
sec.left_margin    = Cm(2.0)
sec.right_margin   = Cm(2.0)
doc.styles['Normal'].font.name = 'Times New Roman'
doc.styles['Normal'].font.size = Pt(10)

# ── Title ───────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
pfmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, sb=0, sa=8)
r = p.add_run("CIRAH: Minimum-Causal-Intervention Optimization for\nRisk-Constrained Autonomous Network Self-Healing")
rfont(r, 14, bold=True)

p = doc.add_paragraph()
pfmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, sb=0, sa=3)
r = p.add_run("Buradagunta Shabreen Shaik, Rajisree Sadu, and Pemmasani Greeshma")
rfont(r, 10)

p = doc.add_paragraph()
pfmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, sb=0, sa=2)
r = p.add_run("School of Computer Science and Engineering,\nVIT-AP University, Amaravati, Andhra Pradesh 522237, India")
rfont(r, 9, italic=True)

divider(doc)

# ── Abstract ────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
pfmt(p, sb=2, sa=4)
r1 = p.add_run("Abstract. "); rfont(r1, 9, bold=True)
r2 = p.add_run(
    "Modern software-defined communication networks face unpredictable link outages, performance degradation, "
    "and cascading congestion that jeopardize strict service-level agreements. Conventional self-healing "
    "techniques rely on reactive shortest-path recomputation or correlation-based heuristic rerouting; however, "
    "these approaches frequently trigger excessive switch reconfiguration churn and control-plane message storms. "
    "This paper presents CIRAH (Causal-Intervention Risk-constrained Autonomous network self-Healing), an "
    "optimization framework for autonomous network restoration. CIRAH establishes an explicit Structural Causal "
    "Model (SCM) connecting physical faults, link degradation, dynamic M/M/1 queuing delays, routing topology, "
    "and end-to-end service outcomes. Leveraging Pearl's counterfactual do-calculus, CIRAH estimates the "
    "consequence of candidate interventions prior to execution. A constrained optimizer selects the minimum-cost "
    "intervention satisfying robust post-recovery risk ceilings and SLA confidence thresholds. Across paired "
    "Monte Carlo runs on the Abilene topology under double-link failures, CIRAH reduces switch modifications by "
    "13.8% (p=0.00082, d_z=-0.56) and intervention cost by 9.3% (p=0.00089), with identical 72.0% success rate "
    "as Dynamic-SP. A 6-way ablation confirms the hard risk constraint as the dominant component: removing it "
    "drops success from 70.0% to 56.7%.")
rfont(r2, 9)

p = doc.add_paragraph()
pfmt(p, sb=2, sa=10)
r1 = p.add_run("Keywords: "); rfont(r1, 9, bold=True)
r2 = p.add_run("Autonomous network self-healing · Structural Causal Models · "
                "Pearl's do-calculus · Minimum-causal intervention · Risk-constrained optimization · SDN")
rfont(r2, 9)

divider(doc)

# ── 1. Introduction ─────────────────────────────────────────────────────────
h1(doc, "1", "Introduction")
body(doc,
    "Software-Defined Networking (SDN) centralizes control intelligence, granting network operators "
    "programmatic visibility and fine-grained forwarding control across distributed data-plane switches [1,2]. "
    "Despite these advantages, wide-area networks face intense dynamic volatility where fiber cuts, hardware "
    "failures, and bursty traffic trigger severe service degradation [3,4]. The network management system must "
    "autonomously detect faults, diagnose causes, compute remedial configurations, and verify service "
    "restoration with minimal downtime [5,6].")

h2(doc, "1.1", "Limitations of Existing Approaches")
body(doc,
    "Reactive Shortest-Path Rerouting restores connectivity but ignores control-plane churn, creating "
    "transient forwarding loops [7,10,11]. Precomputed Protection Paths offer sub-50 ms restoration [3,7] but "
    "exhaust TCAM resources and fail under concurrent failures. Risk-Aware Routing [4,6] does not penalize "
    "reconfiguration overhead. Deep Reinforcement Learning policies [16,19,23] lack formal safety constraints "
    "and require immense training data [11]. Correlation-Based Diagnosis [10,14,27] confounds root causes with "
    "downstream symptoms. Existing systems cannot evaluate counterfactual queries — what the post-recovery "
    "state would be if action a were executed [8,9].")

h2(doc, "1.2", "Research Gap")
body(doc,
    "The extent to which causal uncertainty, intervention-induced congestion, and control-plane reconfiguration "
    "costs can be jointly incorporated into a risk-constrained recovery decision remains to be established. "
    "Central question: Can a self-healing controller select a feasible recovery action that maintains service, "
    "satisfies an explicit post-recovery risk limit, and minimizes operational cost while accounting for "
    "uncertainty in fault diagnosis and predicted recovery outcomes?")

h2(doc, "1.3", "Hypotheses")
for h in [
    "H1 (Intervention Parsimony). CIRAH achieves statistically significant reduction in switch modifications and intervention cost vs. Dynamic-SP (p < 0.05).",
    "H2 (Risk Compliance). CIRAH maintains post-recovery risk below R_max; unconstrained variants exhibit elevated violations.",
    "H3 (Noise Resilience). Under sigma_noise >= 0.20, Bayesian fault estimation maintains higher success than rule-based diagnosis.",
    "H4 (Scalability). The intervention advantage of CIRAH persists across Abilene (11 nodes), GEANT (22 nodes), and Fat-tree (20 nodes).",
]:
    body(doc, h, sa=3)

h2(doc, "1.4", "Contributions")
for txt in [
    "Causal fault-to-recovery formulation: A formally specified SCM with explicit assumptions, identifiability limitations, and predictive accuracy evaluation.",
    "Intervention-aware recovery optimization: A constrained formulation jointly accounting for cost, disruption, risk, and SLA, compared with constrained routing methods.",
    "Network-wide intervention impact estimation: A graph-based stress-relief mechanism (CIHF) evaluated against 5 alternatives. CIHF does not change action selection in 99.2% of scenarios; retained as interpretive visualization.",
    "Uncertainty-aware risk handling: Robust risk bound with 0.0% empirical constraint-violation rate at default threshold (N=30 scenarios).",
    "Reproducible experimental validation: Approximately 5,300 paired Monte Carlo runs across three topologies, 6-way ablations, and open-source implementation.",
]:
    p = doc.add_paragraph(style='List Number')
    pfmt(p, sa=3)
    r = p.add_run(txt); rfont(r, 10)

# ── 2. Literature Review ────────────────────────────────────────────────────
h1(doc, "2", "Literature Review")

h2(doc, "2.1", "SDN Restoration and Minimum-Change Routing")
body(doc,
    "SDN architectures decouple control and data planes via OpenFlow [5,6]. Sharma et al. [7] studied proactive "
    "protection vs. reactive restoration. Qin et al. [3] introduced FAPR for adaptive backup selection. "
    "Yusuf et al. [4] formulated adaptive path selection with composite QoS metrics. Li et al. [31] examined "
    "path selection for link-failure protection in hybrid SDNs. None model the control-plane message cost "
    "during large-scale reconfigurations.")

h2(doc, "2.2", "Risk-Constrained Routing and Resilience Optimization")
body(doc,
    "Risk-aware routing avoids links vulnerable to failure or buffer overflows [4,6]. Risk-aware traffic "
    "engineering incorporates probabilistic link availability [3,4,31]. ML methods for traffic-flow prediction "
    "[32] trigger proactive restoration. However, none enforce hard post-recovery risk ceilings or penalize "
    "the operational overhead of modifying forwarding entries.")

h2(doc, "2.3", "Causal Fault Localization and Counterfactual Decision-Making")
body(doc,
    "Pearl [9] formalizes causal inference, distinguishing P(Y|X) from P(Y|do(X)). Causal directed graphs "
    "have been applied to root-cause fault localization in networks [8,9]. Existing causal approaches "
    "terminate at fault localization; they do not integrate counterfactual outcome prediction directly into "
    "an online intervention optimization algorithm that evaluates alternative recovery actions.")

h2(doc, "2.4", "Autonomous Self-Healing and Digital Twins")
body(doc,
    "Clark et al.'s Knowledge Plane [8] originated autonomous network management. Recent Network Digital "
    "Twins (NDTs) [1,6] provide risk-free simulation environments [1]. Deep learning models have been applied "
    "to DDoS mitigation in SDNs, encompassing systematic reviews [11], DNN classifiers [15,21], optimised "
    "models [17,18], hybrid frameworks [12,13,20,22,24-26,33-35], attention methods [27,30], IoT extensions "
    "[19,29], and ensemble methods [14,23]. CIRAH bridges causal fault localization and risk-constrained "
    "intervention optimization.")

h2(doc, "2.5", "Comparison with Prior Work")
body(doc, "Table 1 compares CIRAH against representative approaches across eight dimensions.")

tbl_caption(doc, "Table 1. Technical comparison of network fault recovery approaches.")
hdrs = ["Approach","Causal","CF Pred.","Cost","Risk","Net-wide","Uncert.","Guarantees","Validation"]
rows = [
    ["FAPR [3]","No","No","Proxy","None","Local","Determin.","None","Mininet"],
    ["Yusuf [4]","No","No","None","None","Path","None","None","Simulation"],
    ["Polat [10]","Rules","No","None","None","None","None","None","Mininet/POX"],
    ["Dynamic-SP","Link-down","No","None","None","Local","None","None","Sim./Testbed"],
    ["Constr-MinChg","Link-down","No","Switch diff","Hard bound","Local","None","Risk feasib.","Simulation"],
    ["CIRAH","Bayesian SCM","Pearl do(A)","Fine-grained","Hard bound","CIHF Laplacian","3-State+Noise","Robust bound","Abilene,GEANT,FT"],
]
t = doc.add_table(rows=len(rows)+1, cols=len(hdrs))
t.alignment = WD_TABLE_ALIGNMENT.LEFT
t.style = 'Table Grid'
three_line_borders(t)
for ci, h in enumerate(hdrs):
    cell_fmt(t.rows[0].cells[ci], h, pt=7.5, bold=True)
header_underline(t.rows[0])
for ri, row in enumerate(rows, 1):
    last = (ri == len(rows))
    for ci, v in enumerate(row):
        cell_fmt(t.rows[ri].cells[ci], v, pt=7.5, bold=last)
doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ── 3. Methodology ──────────────────────────────────────────────────────────
h1(doc, "3", "The CIRAH Framework")

h2(doc, "3.1", "System Architecture")
fig_insert(doc, "fig1_academic_architecture.png",
    "Fig. 1. CIRAH three-tier architecture: Tier 1 (Telemetry & Observation), "
    "Tier 2 (Cognitive Causal Optimization Substrate), Tier 3 (Digital Twin & Adaptation).")
body(doc,
    "The CIRAH architecture comprises three functional tiers (Fig. 1). Tier 1 performs continuous monitoring "
    "of link latency, loss, flow rates, and switch port statistics. Tier 2 executes SCM-based Bayesian fault "
    "traceback, Pearl counterfactual evaluation, CIHF diffusion, and the risk-constrained solver. "
    "Tier 3 provides virtual state emulation for risk-free what-if validation.")

h2(doc, "3.2", "Structural Causal Model (SCM)")
body(doc,
    "We define the network state using a 6-tuple SCM M = <U, V, F, P(U)> with exogenous variables "
    "U = {U_loss, U_lat} and endogenous variables: fault state F_e in {0,1,2} (Normal, Degraded, Severed); "
    "link properties L_e; queue utilization Q_e; routing matrix R; service outcomes Y_f; intervention A. "
    "Causal DAG: F_e -> L_e, {L_e,R} -> Q_e, Q_e -> Y_f, A -> R (no hidden common causes).")
body(doc,
    "Structural equations — Link state (Eq. 1): L_e = <lat0,0,cap0>+U for F_e=0; "
    "<lat0*(1+d),loss_deg,cap0*rho>+U for F_e=1; <inf,100%,0> for F_e=2. "
    "Queue utilization (Eq. 2): Q_e = Load_e / max(1,cap_e). "
    "M/M/1 queuing delay (Eq. 3): D = Load/(cap-Load)*2 for Q<0.85; "
    "15+35*((Q-0.85)/0.15)^1.5 for 0.85<=Q<=1; 50+(Q-1)*80 for Q>1.")

h2(doc, "3.3", "Bayesian Causal Fault Localization")
body(doc,
    "Posterior score for state k in {0,1,2} (Eq. 4a): s_k(e) = P(O_e|F_e=k)*P(F_e=k)*w_k(Paths). "
    "Priors: P(F_e=0)=0.95, P(F_e=1)=0.03, P(F_e=2)=0.02 (ISP backbone base rates). "
    "Path-evidence multipliers (Eq. 4b): w_0=1/(1+3*rho), w_1=1+2.5*rho, w_2=1+4*rho, "
    "where rho_e = N_degraded(e)/max(1,N_traversing(e)). "
    "Normalized posterior (Eq. 4c): P(F_e=k|O_e,Paths) = s_k / sum_j s_j.")
body(doc,
    "Empirical evaluation (3,000 edge assessments, N=100 scenarios): Normal P/R/F1=1.000, "
    "Severed P/R/F1=1.000, overall accuracy=1.000. Degraded F1=0.000 (no degraded ground truth "
    "in fault generator — acknowledged limitation in Section 7).")

h2(doc, "3.4", "Counterfactual Intervention Evaluation")
body(doc,
    "Pearl's three-step procedure. (1) Abduction: U_lat,e = max(0, O_lat,e - base_lat_e). "
    "(2) Action: do(A=a) — modify SCM by setting R_f* = Path(a), severing causal arrows into R_f* (Eq. 5). "
    "(3) Prediction: forward-propagate traffic with fixed U to compute counterfactual loads, queue delays, "
    "and service outcomes (Eq. 6). Recovery probability (Eq. 7): P(F_rec|do(A=a)) = E[I(lat<=SLA_lat "
    "AND loss<=SLA_loss) | O].")
body(doc,
    "Counterfactual evaluation changes 72% of selected actions under tight capacity (80 Mbps links, "
    "40 Mbps cross-traffic) but produces identical outcomes under the default wide-capacity (1,000 Mbps) "
    "ablation scenarios, because traffic displacement does not cause congestion at wide margins.")

h2(doc, "3.5", "Causal Intervention Healing Field (CIHF)")
body(doc,
    "CIHF quantifies spatial stress relief via normalized graph Laplacian diffusion (Eq. 8): "
    "h(a) = (I + sigma*L_norm)^(-1) * s(a), Psi(a) = 1^T * h(a) (Eq. 10). "
    "The Laplacian inverse is precomputed at initialization in O(|V|^3); per-event cost is O(|V|^2). "
    "Controlled experiments across 720 paired runs (6 scoring modes) show CIHF changed the selected "
    "action in only 1 of 120 runs (0.8%), Wilcoxon p=0.317 for all outcome metrics. CIHF is retained "
    "as an interpretive stress-relief visualization rather than a decision-making component.")

h2(doc, "3.6", "Risk Assessment and Robust Constraint")
body(doc,
    "Residual risk (Eq. 11): R_post(a) = R_op(a) + R_prop(a). "
    "Operational risk (Eq. 12): R_op = P_disc*100 + P_SLA*25 + P_flap*15. "
    "Propagation risk (Eq. 13): R_prop = sum_e [util_e>0.85] * [1 - exp(-1.8*(util_e-0.85)/0.15)] * 40. "
    "Robust constraint (Eq. 14): R_robust = R_post + z_alpha*sigma_R <= R_max, "
    "z_alpha=1.645 (95% one-sided Gaussian), sigma_R=0.08*R_post (proportional estimation uncertainty). "
    "This bound applies to estimated mean risk, not individual outcomes. "
    "Empirical validation: 0.0% violations at R_max=35.0 (N=30 scenarios).")

h2(doc, "3.7", "Optimization Objective")
body(doc,
    "Objective (Eq. 18): J(a) = lambda_I*(C_I/C_I,ref) + lambda_D*(C_D/C_D,ref) + lambda_L*(C_L/C_L,ref) "
    "+ beta*(R_post/R_max) - gamma*(Psi/Psi_ref). "
    "Hard constraints: R_robust(a) <= R_max; P(F_rec|do(a)) >= tau; connectivity(a)=1. "
    "Solver enumerates K=6 loop-free paths plus throttled variants, yielding |A|<=13 candidates. "
    "Selects lowest-J feasible candidate — heuristic with bounded candidate set, not global optimum. "
    "Ties broken by evaluation order (deterministic under fixed seeds). See Table 2a for all parameters.")

tbl_caption(doc, "Table 2a. CIRAH algorithm parameters.")
params = [
    ("lambda_I","1.0","Intervention cost weight"),
    ("lambda_D","0.5","Disruption cost weight"),
    ("lambda_L","0.3","Latency SLA weight"),
    ("beta","1.2","Risk penalty weight"),
    ("gamma","0.8","Healing field weight"),
    ("tau","0.75","Min. recovery confidence threshold"),
    ("R_max","35.0","Hard post-recovery risk ceiling"),
    ("z_alpha","1.645","95% one-sided Gaussian quantile"),
    ("sigma_R","0.08*R_post","Proportional risk estimation uncertainty"),
    ("sigma","1.5","CIHF Laplacian diffusion parameter"),
    ("K","6","Max. candidate paths per failure event"),
    ("C_I,ref / C_D,ref / C_L,ref","30 / 50 / 40","Cost normalization scales"),
    ("Psi_ref","10.0","Healing gain normalization scale"),
    ("Fallback throttle partition/risk","0.50 / 0.75","Ingress rate limits"),
    ("P(F_e=0/1/2)","0.95/0.03/0.02","Bayesian priors: Normal/Degraded/Severed"),
]
tp = doc.add_table(rows=len(params)+1, cols=3)
tp.alignment = WD_TABLE_ALIGNMENT.LEFT
tp.style = 'Table Grid'
three_line_borders(tp)
for ci,h in enumerate(["Symbol / Parameter","Value","Description"]):
    cell_fmt(tp.rows[0].cells[ci], h, pt=8, bold=True)
header_underline(tp.rows[0])
for ri,(sym,val,desc) in enumerate(params,1):
    cell_fmt(tp.rows[ri].cells[0], sym, pt=8)
    cell_fmt(tp.rows[ri].cells[1], val, pt=8)
    cell_fmt(tp.rows[ri].cells[2], desc, pt=8)
doc.add_paragraph().paragraph_format.space_after = Pt(6)

h2(doc, "3.8", "Safe Fallback Mechanism")
body(doc,
    "When A_feas is empty, CIRAH invokes a two-tier fallback. (1) Partition detection via graph "
    "reachability (nx.has_path) on the active-link subgraph. If no path exists, CIRAH applies 50% "
    "ingress throttling and reports service unavailability — no false recovery claim. The 50% rate "
    "halves offered load to limit buffer overflow. (2) Paced detour: if connected paths exist but "
    "violate R_max, the lowest-risk candidate is selected with 75% ingress rate limiting. "
    "Fallback was triggered in 6.7% of runs at R_max=35.0 and up to 30% at R_max=10.0.")

h2(doc, "3.9", "Algorithm Summary")
algorithm(doc,
"""Algorithm 1: CIRAH Counterfactual Risk-Constrained Intervention Selection
Input:  G=(V,E), Telemetry O, Flows F, Impaired flow f*, R_max, tau
Output: Optimal intervention a*

1.  A <- {a_0 (null action)}
2.  For each e in E: s_k(e) = P(O_e|F=k)*P(F=k)*w_k, k in {0,1,2}
3.                   P(F_e=k|O_e,Paths) <- s_k / sum_j s_j
4.  H <- PenalizeWeights(G, posteriors)
5.  For each of K shortest loop-free paths p:
6.      A <- A + {reroute(p, 1.0), reroute_paced(p, 0.85)}
7.  A_feas <- empty
8.  For each a in A:
9.      Y_hat <- EvaluateCounterfactual(M, do(A=a), O, U_hat)
10.     R_post <- EvaluateRisk(G, a, Y_hat)
11.     R_robust <- R_post + z_alpha * sigma_R
12.     J(a) = lambda_I*C_I/C_ref + ... - gamma*Psi/Psi_ref
13.     If R_robust<=R_max AND P_rec>=tau AND connected: A_feas += {a}
14. If A_feas != empty : a* <- argmin J(a) over A_feas
15. Else               : a* <- SafeFallback(A, G, f*)
16. InstallFlowRules(a*); Return a*""")

h2(doc, "3.10", "Computational Complexity")
body(doc,
    "Per failure event: Bayesian diagnosis O(|E|); K-shortest paths O(K|V|(|E|+|V|log|V|)); "
    "counterfactual evaluation per candidate O(|F|*|Path|+|E|); CIHF O(|V|^2) (precomputed inverse, "
    "O(|V|^3) one-time init). Overall: O(K|V|log|V| + |A|(|E|+|V|^2)). "
    "Measured mean decision latency (60 profiling runs): Abilene 6.28 ms (p95=8.70 ms); "
    "GEANT 10.78 ms (p95=14.33 ms); Fat-tree 20-node total recovery 105.7 ms.")

# ── 4. Experimental Setup ───────────────────────────────────────────────────
h1(doc, "4", "Experimental Setup")

h2(doc, "4.1", "Topologies")
body(doc,
    "Abilene Internet2 Backbone: 11 nodes, 30 directed edges, 1,000 Mbps, delays 5-28 ms. "
    "GEANT: 22 nodes, 56 directed edges, 1,000/500 Mbps. "
    "Fat-tree k=4: 20 nodes (4 core, 8 aggregation, 8 edge), 64 directed edges. "
    "All topologies constructed programmatically; no external files required.")

h2(doc, "4.2", "Fault Scenarios")
body(doc,
    "Seven failure modes: single-link failure (k=1); concurrent multi-link (k=2,3,4); "
    "75% capacity brownout; bufferbloat (+80 ms, +12% loss); bursty traffic (3.5x demand); "
    "telemetry noise (sigma_noise in [0, 0.30]).")

h2(doc, "4.3", "Baselines and Ablations")
body(doc,
    "Baselines: Static-SP [10], Dynamic-SP [7], Backup-Path [3], Risk-Aware [4], MinChange-SP, "
    "Constrained-MinChange (same candidate paths and risk constraint as CIRAH, myopic load estimation, "
    "minimum switch-diff selection). Ablations: CIRAH-noCausal, CIRAH-noCF, CIRAH-noCIHF, "
    "CIRAH-noRisk, CIRAH-noInterv.")

h2(doc, "4.4", "Statistical Protocol")
body(doc,
    "N=50 paired runs per condition with matched random seeds. Two-sided paired Wilcoxon signed-rank "
    "test, alpha=0.05. Effect sizes: within-pair Cohen's d_z = D_bar/s_D. Multiplicity control: "
    "Primary Abilene family (N=6: switch churn and cost at k=1,2,3) and Omnibus family (N=30: "
    "2 topologies x 3 severity levels x 5 metrics). Success: no link in path has loss >= 99% "
    "(connectivity) AND latency and loss meet SLA bounds.")

# ── 5. Results ──────────────────────────────────────────────────────────────
h1(doc, "5", "Experimental Results")

h2(doc, "5.1", "Multi-Failure Severity (Abilene)")
fig_insert(doc, "fig5_success_vs_severity.png",
    "Fig. 2. Recovery success rate across k=0-4 simultaneous link failures, Abilene (N=50 per condition, 95% CI).")
body(doc,
    "Table 2 reports Abilene topology results. CIRAH matches Dynamic-SP success (90.0% at k=1, "
    "72.0% at k=2, 68.0% at k=3) while consistently reducing switch churn and intervention cost. "
    "Under k=2, CIRAH reduces switches from 3.78 to 3.26 (13.8%, p=0.00082, d_z=-0.56) and "
    "intervention cost from 19.02 to 17.25 (9.3%, p=0.00089). Recovery time at k=1 is comparable "
    "(49.4 vs. 49.2 ms). At k=3 it rises to 415.0 ms vs. 58.8 ms, reflecting combinatorial path "
    "search depth.")

tbl_caption(doc, "Table 2. Abilene topology results (N=50 paired runs per severity level).")
t2h = ["k","Method","Success (%)","Latency (ms)","Loss (%)","Risk","Switches","Cost","Recovery (ms)"]
t2r = [
    ["1","Dynamic-SP","90.0","43.0±2.3","0.19±0.03","2.91±0.74","2.84±0.32","14.34±1.55","49.2±3.9"],
    ["1","CIRAH","90.0","44.6±2.4","0.19±0.03","2.93±0.74","2.28±0.24","12.30±1.22","49.4±2.9"],
    ["2","Dynamic-SP","72.0","49.3±2.8","0.22±0.03","11.39±3.43","3.78±0.25","19.02±1.20","60.5±3.0"],
    ["2","CIRAH","72.0","52.4±3.0","0.24±0.03","11.46±3.42","3.26±0.21","17.25±1.06","178.9±65.8"],
    ["3","Dynamic-SP","68.0","53.1±2.8","0.21±0.03","21.57±5.40","3.64±0.35","18.27±1.65","58.8±4.2"],
    ["3","CIRAH","68.0","57.8±3.5","0.22±0.03","21.64±5.39","3.24±0.30","16.95±1.47","415.0±106.1"],
]
t2 = doc.add_table(rows=len(t2r)+1, cols=len(t2h))
t2.alignment = WD_TABLE_ALIGNMENT.LEFT
t2.style = 'Table Grid'
three_line_borders(t2)
for ci,h in enumerate(t2h):
    cell_fmt(t2.rows[0].cells[ci], h, pt=8, bold=True)
header_underline(t2.rows[0])
for ri,row in enumerate(t2r,1):
    for ci,v in enumerate(row):
        cell_fmt(t2.rows[ri].cells[ci], v, pt=8)
doc.add_paragraph().paragraph_format.space_after = Pt(6)

h2(doc, "5.2", "Telemetry Noise Resilience")
fig_insert(doc, "fig10_telemetry_noise_resilience.png",
    "Fig. 3. Recovery success under telemetry noise (sigma=0.0-0.30) comparing Bayesian SCM vs. rule-based diagnosis (N=50).")
body(doc,
    "Under sigma=0.30, Dynamic-SP success degrades to 44.0% while CIRAH sustains 54.0% "
    "(+22.7% relative advantage). CIRAH also maintains lower residual risk (8.53 vs. 10.01), "
    "confirming H3.")

h2(doc, "5.3", "6-Way Component Ablation")
fig_insert(doc, "fig9_component_ablations.png",
    "Fig. 4. Six-way ablation results (N=60 paired runs): success, residual risk, switch churn, intervention cost.")

tbl_caption(doc, "Table 3. Six-way ablation results (Abilene, N=60 paired runs).")
t3h = ["Variant","Removed","Success (%)","SLA Viol. (%)","Constr. Viol. (%)","Switches","Cost","Risk","Psi"]
t3r = [
    ["CIRAH-full","None","70.0","30.0","0.0","3.60","18.90","7.06","0.974"],
    ["CIRAH-noCausal","SCM traceback","70.0","30.0","1.7","3.55","18.63","8.29","0.960"],
    ["CIRAH-noCF","Counterfactual","70.0","30.0","0.0","3.60","18.90","7.04","0.974"],
    ["CIRAH-noCIHF","Healing field","70.0","30.0","0.0","3.60","18.90","7.06","0.000"],
    ["CIRAH-noRisk","Risk constraint","56.7","43.3","0.0","3.25","17.68","8.57","0.998"],
    ["CIRAH-noInterv","Cost penalty","70.0","30.0","0.0","3.78","19.53","7.04","0.958"],
]
t3 = doc.add_table(rows=len(t3r)+1, cols=len(t3h))
t3.alignment = WD_TABLE_ALIGNMENT.LEFT
t3.style = 'Table Grid'
three_line_borders(t3)
for ci,h in enumerate(t3h):
    cell_fmt(t3.rows[0].cells[ci], h, pt=8, bold=True)
header_underline(t3.rows[0])
for ri,row in enumerate(t3r,1):
    bold = (row[0]=="CIRAH-full")
    for ci,v in enumerate(row):
        cell_fmt(t3.rows[ri].cells[ci], v, pt=8, bold=bold)
doc.add_paragraph().paragraph_format.space_after = Pt(6)

body(doc,
    "Removing the hard risk constraint (CIRAH-noRisk) drops success from 70.0% to 56.7% and raises "
    "SLA violations from 30.0% to 43.3% — the strongest component effect. Removing the intervention "
    "cost penalty (CIRAH-noInterv) increases switch churn from 3.60 to 3.78. Removing the healing "
    "field (CIRAH-noCIHF) collapses Psi to 0.000 but produces no measurable change in success, "
    "switches, cost, or risk.")

h2(doc, "5.4", "Statistical Validation")
tbl_caption(doc, "Table 4. Paired hypothesis tests, CIRAH vs. Dynamic-SP (Abilene, N=50).")
t4h = ["k","Metric","CIRAH","Dyn-SP","Delta%","95% CI","d_z","Wilcoxon p","Holm p","Sig?"]
t4r = [
    ["1","Switches","2.28","2.84","-19.7%","[-0.90,-0.22]","-0.47","0.00206","0.0083","Yes"],
    ["1","Cost","12.30","14.34","-14.2%","[-3.30,-0.78]","-0.46","0.00209","0.0083","Yes"],
    ["2","Switches","3.26","3.78","-13.8%","[-0.78,-0.26]","-0.56","0.00082","0.0049","Yes"],
    ["2","Cost","17.25","19.02","-9.3%","[-2.69,-0.85]","-0.55","0.00089","0.0049","Yes"],
    ["3","Switches","3.24","3.64","-11.0%","[-0.66,-0.14]","-0.44","0.00280","0.0083","Yes"],
    ["3","Cost","16.95","18.27","-7.2%","[-2.23,-0.41]","-0.41","0.00304","0.0083","Yes"],
]
t4 = doc.add_table(rows=len(t4r)+1, cols=len(t4h))
t4.alignment = WD_TABLE_ALIGNMENT.LEFT
t4.style = 'Table Grid'
three_line_borders(t4)
for ci,h in enumerate(t4h):
    cell_fmt(t4.rows[0].cells[ci], h, pt=7.5, bold=True)
header_underline(t4.rows[0])
for ri,row in enumerate(t4r,1):
    for ci,v in enumerate(row):
        cell_fmt(t4.rows[ri].cells[ci], v, pt=7.5)
doc.add_paragraph().paragraph_format.space_after = Pt(6)
body(doc, "All six Primary Abilene family hypotheses are significant after Holm adjustment "
     "(p_adj <= 0.0083 < 0.05), confirming H1.")

h2(doc, "5.5", "Constrained Baseline and Fat-Tree Scalability")
tbl_caption(doc, "Table 5. CIRAH vs. Constrained-MinChange (Abilene avg. k=1,2,3, N=150).")
t5r = [
    ["Static-SP","12.0","0.00","0.00","89.08"],
    ["Dynamic-SP","76.7","3.42","17.21","11.96"],
    ["MinChange-SP","74.7","2.90","15.40","12.30"],
    ["Constrained-MinChange","74.7","2.91","15.45","12.30"],
    ["CIRAH","76.7","2.93","15.51","12.01"],
]
t5 = doc.add_table(rows=len(t5r)+1, cols=5)
t5.alignment = WD_TABLE_ALIGNMENT.LEFT
t5.style = 'Table Grid'
three_line_borders(t5)
for ci,h in enumerate(["Method","Success (%)","Switches","Cost","Risk"]):
    cell_fmt(t5.rows[0].cells[ci], h, pt=8, bold=True)
header_underline(t5.rows[0])
for ri,row in enumerate(t5r,1):
    last = (row[0]=="CIRAH")
    for ci,v in enumerate(row):
        cell_fmt(t5.rows[ri].cells[ci], v, pt=8, bold=last)
doc.add_paragraph().paragraph_format.space_after = Pt(6)
body(doc,
    "CIRAH matches Dynamic-SP success (76.7%) with similar switch count to Constrained-MinChange. "
    "The marginal risk advantage (12.01 vs. 12.30) reflects causal posterior weighting that avoids "
    "fault-probable links. On Fat-tree (20 nodes), all methods achieve 90% success; CIRAH reduces "
    "switches from 3.46 (Dynamic-SP) to 2.29 — a 33.8% reduction — demonstrating scalability.")

h2(doc, "5.6", "Risk Threshold Sensitivity")
tbl_caption(doc, "Table 6. Risk threshold sensitivity at k=2, Abilene (N=30 runs per R_max).")
t6r = [
    ["10.0","80.0","20.0","20.0","4.98","3.13"],
    ["20.0","70.0","13.3","30.0","14.44","2.73"],
    ["35.0 (default)","93.3","0.0","6.7","2.91","2.90"],
    ["50.0","70.0","6.7","30.0","12.06","2.60"],
    ["100.0","73.3","3.3","26.7","8.91","3.17"],
]
t6 = doc.add_table(rows=len(t6r)+1, cols=6)
t6.alignment = WD_TABLE_ALIGNMENT.LEFT
t6.style = 'Table Grid'
three_line_borders(t6)
for ci,h in enumerate(["R_max","Success (%)","Violation (%)","Fallback (%)","Mean Risk","Switches"]):
    cell_fmt(t6.rows[0].cells[ci], h, pt=8, bold=True)
header_underline(t6.rows[0])
for ri,row in enumerate(t6r,1):
    is_def = "35.0" in row[0]
    for ci,v in enumerate(row):
        cell_fmt(t6.rows[ri].cells[ci], v, pt=8, bold=is_def)
doc.add_paragraph().paragraph_format.space_after = Pt(6)
body(doc, "R_max=35.0 achieves the highest success (93.3%) with 0.0% violations and 6.7% fallback.")

# ── 6. Discussion ───────────────────────────────────────────────────────────
h1(doc, "6", "Discussion")
body(doc, "Churn-latency trade-off. CIRAH occasionally accepts a path with 2-3 ms higher propagation "
     "latency to avoid reconfiguring additional core switches, thereby reducing TCAM updates and "
     "transient packet reordering.")
body(doc, "CIHF as visualization. The CIHF field correctly computes spatial stress relief but does not "
     "change action selection in 99.2% of scenarios. Its objective term (mean 0.078) is 0.11x the cost "
     "term and 0.02x the risk term. It is retained as an interpretive post-hoc visualization only.")
body(doc, "Counterfactual value. Under tight capacity constraints (80 Mbps), CF changes 72% of selected "
     "actions. Under wide-capacity conditions, it produces identical outcomes to myopic evaluation. "
     "CF has measurable value in capacity-constrained environments at the cost of higher computation.")
body(doc, "Recovery time overhead. CIRAH's decision latency scales with failure severity: 49.4 ms at k=1 "
     "(comparable to Dynamic-SP), 178.9 ms at k=2, and 415.0 ms at k=3. For sub-100 ms requirements, "
     "hardware-accelerated SCM solvers or precomputed topological subgraphs are promising extensions.")

# ── 7. Threats to Validity ──────────────────────────────────────────────────
h1(doc, "7", "Threats to Validity")
body(doc, "Construct Validity. Intervention cost uses OpenFlow message weights and switch delay proxies "
     "(Delta_t_commit=12 ms); hardware-specific latencies may vary.")
body(doc, "CIHF Limitation. Controlled experiments (720 paired runs) confirm CIHF does not change action "
     "selection or improve any outcome metric under tested conditions. Retained as visualization only.")
body(doc, "Counterfactual Scope. The do(A) mechanism changes decisions under tight capacity but produces "
     "identical outcomes under default wide-capacity scenarios. Model is calibrated against simulator "
     "equations — accurate predictions reflect internal consistency, not external validity.")
body(doc, "Risk Constraint Assumptions. Robust bound uses heuristic sigma_R=0.08*R_post, not empirically "
     "calibrated variance. Bound applies to estimated mean risk, not individual outcomes.")
body(doc, "Bayesian Degraded-State Limitation. Degraded-state classifier unevaluated against true degraded "
     "links (fault generator injects only complete severances).")
body(doc, "Simulation Only. All results are from simulation without Mininet/P4 physical testbed validation.")

# ── 8. Conclusion ───────────────────────────────────────────────────────────
h1(doc, "8", "Conclusion")
body(doc,
    "This paper presented CIRAH, a causal-intervention optimization framework for autonomous network "
    "self-healing under risk constraints. By formalizing network dynamics as an SCM, computing Pearl's "
    "counterfactual outcomes do(A=a), and enforcing robust post-recovery risk limits, CIRAH discovers the "
    "minimum-cost recovery action satisfying post-repair risk constraints. Across approximately 5,300 paired "
    "Monte Carlo simulation runs on Abilene, GEANT, and Fat-tree topologies, CIRAH demonstrated statistically "
    "verified switch churn reductions of 13.8%-19.7% (p<0.01) over reactive shortest-path rerouting while "
    "maintaining 0.0% risk constraint violations at R_max=35.0. The 6-way ablation study identified the hard "
    "risk constraint as the dominant component (success 70.0% to 56.7% when removed). CIHF does not influence "
    "action selection under tested conditions and is retained as an interpretive visualization. Future work "
    "targets deployment on physical P4-programmable SDN testbeds.")

p = doc.add_paragraph()
pfmt(p, sb=10, sa=4)
r1 = p.add_run("Conflict of Interest. "); rfont(r1, 9, bold=True)
r2 = p.add_run("The authors declare no competing financial interests."); rfont(r2, 9)

p = doc.add_paragraph()
pfmt(p, sb=2, sa=4)
r1 = p.add_run("Data Availability. "); rfont(r1, 9, bold=True)
r2 = p.add_run("Source code, topology graphs, experiment runners, raw CSV datasets, and figure generation "
               "scripts are openly available at https://github.com/Shabreen123/CIRAH"); rfont(r2, 9)

divider(doc)

# ── References ──────────────────────────────────────────────────────────────
h1(doc, "", "References")

refs = [
    "1. Sanz Rodrigo, M. et al.: Network Digital Twin-Generated Dataset for ML-based Zero-Touch SLA Preservation. Zenodo (2025). https://doi.org/10.5281/zenodo.17255327",
    "2. Moustafa, N., Slay, J.: UNSW-NB15: A Comprehensive Dataset for Network Intrusion Detection. Proc. IEEE MilCIS, pp. 1-6 (2015)",
    "3. Qin, H. et al.: FAPR: An Adaptive Approach to Link Failure Recovery in SDN. Applied Sciences 14(11), 4719 (2024)",
    "4. Yusuf, M.N. et al.: Adaptive Path Selection with Flow Classification for SDNs. Mathematics 11(6), 1404 (2023)",
    "5. McKeown, N. et al.: OpenFlow: Enabling Innovation in Campus Networks. ACM SIGCOMM CCR 38(2), 69-74 (2008)",
    "6. Kreutz, D. et al.: Software-Defined Networking: A Comprehensive Survey. Proc. IEEE 103(1), 14-76 (2015)",
    "7. Sharma, S. et al.: Enabling Fast Failure Recovery in OpenFlow Networks. Proc. DRCN, pp. 164-171 (2011)",
    "8. Clark, D.D. et al.: A Knowledge Plane for the Internet. Proc. ACM SIGCOMM, pp. 3-10 (2003)",
    "9. Pearl, J.: Causality: Models, Reasoning, and Inference, 2nd edn. Cambridge Univ. Press (2009)",
    "10. Polat, O., Polat, H.: An Intelligent SDN Controller to Detect and Mitigate DoS Attacks. J. ICT 20(1), 1-24 (2021)",
    "11. Polat, O. et al.: Supervised and Deep Learning for DDoS Detection in SDN: Systematic Review. Eng. Sci. Technol. 75, 102290 (2026)",
    "12. Kachavimath, A.V., Narayan, D.G.: Hybrid DL Model with Consensus-Based Feature Selection for DDoS in SDN. Procedia Comput. Sci. 252, 643-652 (2025)",
    "13. Mehmood, S. et al.: DDoS Detection in SDN Using Optimiser-equipped CNN-MLP. PLoS ONE 20(1), e0312425 (2025)",
    "14. Gayantha, N. et al.: Advanced DDoS Detection and Mitigation in SDN. Proc. IEEE SCSE, pp. 1-6 (2025)",
    "15. Hnamte, V. et al.: DDoS Attack Detection Using DNN in SDN. Comput. Secur. 138, 103661 (2024)",
    "16. Paidipati, K.K. et al.: Ensemble of DRL for DDoS Detection in Cloud-Based SDN. Multimedia Tools Appl. 83(11), 32367-32385 (2024)",
    "17. Al-Dunainawi, Y. et al.: Optimised AI Model for DDoS Detection in SDN. IEEE Access 11, 106733-106748 (2023)",
    "18. Setitra, M.A. et al.: Optimised MLP-CNN for DDoS Detection in SDN. Network 3(4), 538-562 (2023)",
    "19. Aslam, M. et al.: Adaptive ML-Based DDoS Mitigation for SDN-Enabled IoT. Sensors 22(7), 2697 (2022)",
    "20. Swileh, M.N., Zhang, S.: Unseen Attack Detection in SDN Using BERT-Based LLM. AI 6(7), 154 (2025)",
    "21. Gadallah, W.G. et al.: Deep Learning Technique to Detect DDoS in SDN. Comput. Secur. 137, 103588 (2024)",
    "22. Wang, H. et al.: DDoS Detection Model Using Stacked Autoencoder and GRU for SDN. Comput. J. bxaf021 (2025)",
    "23. Abid, Y.A. et al.: Multilevel DNN for DDoS Detection in SDN-IoT. IEEE IoT J. 11(14), 24715-24725 (2024)",
    "24. Veeresh, G.B. et al.: Swish-Optimized Trident Fusion Network for SDN Attack Classification. Knowl.-Based Syst. 114860 (2025)",
    "25. Chattopadhyay, S. et al.: Enhanced DDoS Detection in SDN Using Ensemble Learning. SN Comput. Sci. 5(5), 580 (2024)",
    "26. Zaidoun, A.S., Lachiri, Z.: Hybrid Deep Learning for Multi-class DDoS Detection in SDN. Ann. Telecommun. 1-14 (2025)",
    "27. Nithya, R., Vinoth Kumar, K.: Attention Driven Hybrid Deep Learning for IDS in SDN. Results Eng. 26, 113552 (2026)",
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
    p = doc.add_paragraph()
    pfmt(p, sb=0, sa=3, fi=-14)
    p.paragraph_format.left_indent = Pt(14)
    r = p.add_run(ref)
    rfont(r, 9)

# ── save ────────────────────────────────────────────────────────────────────
doc.save(OUT_PATH)
print(f"Saved: {OUT_PATH}")
