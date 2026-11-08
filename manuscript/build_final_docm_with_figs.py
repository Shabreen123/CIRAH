"""
Build CIRAH_FINAL_Springer.docm with figures embedded as real Word images.
Uses the official splnproc2510.docm template's styles and structure.
Images are embedded via Office Open XML inline drawing references.
"""

import zipfile, os, re, base64
from lxml import etree
from PIL import Image as PILImage
import io

TEMPLATE = r"C:\Users\LENOVO\Downloads\splnproc2510.docm"
FIG_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "figures"))
OUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "CIRAH_Springer_WithFigs.docm"))

# Namespace constants
W   = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP  = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R14 = "http://schemas.microsoft.com/office/2010/relationships/image"

def w(t):  return f"{{{W}}}{t}"
def r_(t): return f"{{{R}}}{t}"
def wp(t): return f"{{{WP}}}{t}"
def a_(t): return f"{{{A}}}{t}"
def p_(t): return f"{{{PIC}}}{t}"

def E(tag, **kw):
    el = etree.Element(tag)
    for k,v in kw.items():
        el.set(k, v)
    return el

# ── Image helper ──────────────────────────────────────────────────────────

def get_image_emu(path, max_width_cm=13.0):
    """Return (width_emu, height_emu) scaled to max_width_cm."""
    with PILImage.open(path) as im:
        w_px, h_px = im.size
        dpi = im.info.get('dpi', (96, 96))
        dpi_x = dpi[0] if dpi[0] > 0 else 96
        # Convert to EMU (1 inch = 914400 EMU)
        w_emu = int(w_px / dpi_x * 914400)
        h_emu = int(h_px / (dpi[1] if dpi[1] > 0 else 96) * 914400)
    max_emu = int(max_width_cm / 2.54 * 914400)
    if w_emu > max_emu:
        ratio = max_emu / w_emu
        w_emu = max_emu
        h_emu = int(h_emu * ratio)
    return w_emu, h_emu

def make_inline_image(rId, desc, w_emu, h_emu, draw_id):
    """Build <w:drawing> element for an inline image."""
    drawing = E(w("drawing"))
    inline  = E(wp("inline"),
                distT="0", distB="0", distL="0", distR="0",
                simplePos="0", relativeHeight="0",
                behindDoc="0", locked="0",
                layoutInCell="1", allowOverlap="0")
    # simple position
    sp = E(wp("simplePos"), x="0", y="0")
    inline.append(sp)
    # relative horizontal
    relH = E(wp("positionH"), relativeFrom="column")
    relH.append(E(wp("posOffset")))
    relH[0].text = "0"
    inline.append(relH)
    relV = E(wp("positionV"), relativeFrom="paragraph")
    relV.append(E(wp("posOffset")))
    relV[0].text = "0"
    inline.append(relV)
    # extent
    ext = E(wp("extent"), cx=str(w_emu), cy=str(h_emu))
    inline.append(ext)
    # effect extent
    efExt = E(wp("effectExtent"), l="0", t="0", r="0", b="0")
    inline.append(efExt)
    # doc properties
    docPr = E(wp("docPr"), id=str(draw_id), name=desc, descr=desc)
    inline.append(docPr)
    # cNvGraphicFramePr
    cNv = E(wp("cNvGraphicFramePr"))
    gfLocks = etree.SubElement(cNv,
        "{http://schemas.openxmlformats.org/drawingml/2006/main}graphicFrameLocks",
        noChangeAspect="1")
    inline.append(cNv)
    # graphic
    graphic = E(a_("graphic"))
    graphicData = E(a_("graphicData"),
        uri="http://schemas.openxmlformats.org/drawingml/2006/picture")
    pic_el = E(p_("pic"))
    nvPicPr = E(p_("nvPicPr"))
    cNvPr  = E(p_("cNvPr"), id=str(draw_id), name=desc)
    cNvIPr = E(p_("cNvPicPr"))
    nvPicPr.append(cNvPr); nvPicPr.append(cNvIPr)
    pic_el.append(nvPicPr)
    blipFill = E(p_("blipFill"))
    blip = E(a_("blip"))
    blip.set(r_("embed"), rId)
    blipFill.append(blip)
    stretch = E(a_("stretch"))
    fillRect = E(a_("fillRect"))
    stretch.append(fillRect)
    blipFill.append(stretch)
    pic_el.append(blipFill)
    spPr = E(p_("spPr"))
    xfrm = E(a_("xfrm"))
    off  = E(a_("off"), x="0", y="0")
    extEl= E(a_("ext"), cx=str(w_emu), cy=str(h_emu))
    xfrm.append(off); xfrm.append(extEl)
    spPr.append(xfrm)
    prstGeom = E(a_("prstGeom"), prst="rect")
    prstGeom.append(E(a_("avLst")))
    spPr.append(prstGeom)
    pic_el.append(spPr)
    graphicData.append(pic_el)
    graphic.append(graphicData)
    inline.append(graphic)
    drawing.append(inline)
    return drawing

def figure_paragraph(rId, desc, w_emu, h_emu, draw_id):
    """Full <w:p> containing a centered inline image."""
    p = E(w("p"))
    pPr = E(w("pPr"))
    pStyle = E(w("pStyle")); pStyle.set(w("val"), "Normal"); pPr.append(pStyle)
    jc = E(w("jc")); jc.set(w("val"), "center"); pPr.append(jc)
    sp = E(w("spacing")); sp.set(w("before"), "120"); sp.set(w("after"), "60")
    pPr.append(sp); p.append(pPr)
    run = E(w("r"))
    rPr = E(w("rPr")); run.append(rPr)
    drawing = make_inline_image(rId, desc, w_emu, h_emu, draw_id)
    run.append(drawing)
    p.append(run)
    return p

# ── XML para helpers ──────────────────────────────────────────────────────

def para(style_id, *runs, sb=None, sa=None, jc=None, ind_left=None, ind_hanging=None):
    p = E(w("p"))
    pPr = E(w("pPr"))
    pStyle = E(w("pStyle")); pStyle.set(w("val"), style_id); pPr.append(pStyle)
    if jc:
        j = E(w("jc")); j.set(w("val"), jc); pPr.append(j)
    sp_attr = {}
    if sb is not None: sp_attr["before"] = str(sb)
    if sa is not None: sp_attr["after"]  = str(sa)
    if sp_attr:
        sp = E(w("spacing"), **{w(k): v for k,v in sp_attr.items()}); pPr.append(sp)
    if ind_left is not None or ind_hanging is not None:
        ind = E(w("ind"))
        if ind_left:    ind.set(w("left"),    str(ind_left))
        if ind_hanging: ind.set(w("hanging"), str(ind_hanging))
        pPr.append(ind)
    p.append(pPr)
    for rd in runs:
        if rd is None: continue
        if isinstance(rd, str):
            text, bold, italic = rd, False, False
        else:
            text   = rd.get("t", "")
            bold   = rd.get("b", False)
            italic = rd.get("i", False)
        if not text: continue
        rn = E(w("r")); rPr = E(w("rPr"))
        if bold:   rPr.append(E(w("b")));  rPr.append(E(w("bCs")))
        if italic: rPr.append(E(w("i")));  rPr.append(E(w("iCs")))
        if rPr.getchildren(): rn.append(rPr)
        t_el = E(w("t")); t_el.text = text
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        rn.append(t_el); p.append(rn)
    return p

def bold(t): return {"t": t, "b": True}
def ital(t): return {"t": t, "i": True}

def h1(num, title): return para("heading1", f"{num}  {title}")
def h2(num, title): return para("heading2", f"{num}  {title}")
def h3(title):      return para("heading3", f"{title}.")
def body(text):     return para("Normal", text)
def figcap(text):   return para("figurecaption", text)
def tblcap(text):   return para("tablecaption", text, sa=40)
def numitem(text):  return para("numitem", text)

def make_table(headers, rows):
    tbl = E(w("tbl"))
    tblPr = E(w("tblPr"))
    tblStyle = E(w("tblStyle")); tblStyle.set(w("val"), "Normal Table"); tblPr.append(tblStyle)
    tblW = E(w("tblW")); tblW.set(w("type"), "pct"); tblW.set(w("w"), "5000"); tblPr.append(tblW)
    bd = E(w("tblBorders"))
    for s in ("top","bottom"):
        b = E(w(s)); b.set(w("val"),"single"); b.set(w("sz"),"12")
        b.set(w("space"),"0"); b.set(w("color"),"000000"); bd.append(b)
    for s in ("left","right","insideH","insideV"):
        b = E(w(s)); b.set(w("val"),"none"); bd.append(b)
    tblPr.append(bd); tbl.append(tblPr)

    def row_el(cells, hdr=False):
        tr = E(w("tr"))
        for val in cells:
            tc = E(w("tc")); tcPr = E(w("tcPr"))
            tcW = E(w("tcW")); tcW.set(w("type"),"auto"); tcW.set(w("w"),"0"); tcPr.append(tcW)
            if hdr:
                bds = E(w("tcBorders")); bb = E(w("bottom"))
                bb.set(w("val"),"single"); bb.set(w("sz"),"6")
                bb.set(w("space"),"0"); bb.set(w("color"),"000000")
                bds.append(bb); tcPr.append(bds)
            tc.append(tcPr)
            p = E(w("p")); pPr = E(w("pPr"))
            pStyle = E(w("pStyle")); pStyle.set(w("val"),"Normal"); pPr.append(pStyle)
            sp = E(w("spacing")); sp.set(w("before"),"20"); sp.set(w("after"),"20"); pPr.append(sp)
            p.append(pPr)
            rn = E(w("r")); rPr = E(w("rPr"))
            sz = E(w("sz")); sz.set(w("val"),"16"); rPr.append(sz)
            szCs = E(w("szCs")); szCs.set(w("val"),"16"); rPr.append(szCs)
            if hdr: rPr.append(E(w("b"))); rPr.append(E(w("bCs")))
            rn.append(rPr)
            t_el = E(w("t")); t_el.text = val
            t_el.set("{http://www.w3.org/XML/1998/namespace}space","preserve")
            rn.append(t_el); p.append(rn); tc.append(p); tr.append(tc)
        return tr

    tbl.append(row_el(headers, hdr=True))
    for row in rows:
        tbl.append(row_el(row))
    return tbl

def code_paras(text):
    return [para("programcode", line if line else " ") for line in text.split("\n")]

# ── Image registry ────────────────────────────────────────────────────────

class ImageReg:
    """Tracks images added to the document and assigns relationship IDs."""
    def __init__(self):
        self.images = []   # list of (rId, filename, ext, data_bytes)
        self._counter = 1
        self._draw_id = 100

    def add(self, filename):
        path = os.path.join(FIG_DIR, filename)
        if not os.path.exists(path):
            return None, 0, 0
        # Convert to PNG if needed
        with PILImage.open(path) as im:
            im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = buf.getvalue()
        w_emu, h_emu = get_image_emu(path, max_width_cm=12.5)
        rId = f"rImgId{self._counter}"
        self._counter += 1
        did = self._draw_id
        self._draw_id += 1
        self.images.append((rId, os.path.splitext(filename)[0] + ".png", "png", data))
        return rId, w_emu, h_emu, did

    def fig_para(self, filename):
        """Return a <w:p> with the image embedded, or a placeholder if missing."""
        result = self.add(filename)
        if result[0] is None:
            return para("Normal", ital(f"[Figure: {filename} not found]"))
        rId, w_emu, h_emu, did = result
        return figure_paragraph(rId, filename, w_emu, h_emu, did)


img = ImageReg()

# ── Build document body ───────────────────────────────────────────────────

def build_body():
    BD = []   # list of XML elements

    def add(x):
        if isinstance(x, list):
            BD.extend(x)
        else:
            BD.append(x)

    # Title block
    add(para("papertitle",
        "CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing"))
    add(para("author",
        "Buradagunta Shabreen Shaik, Rajisree Sadu, and Pemmasani Greeshma"))
    add(para("address",
        "School of Computer Science and Engineering, VIT-AP University, Amaravati, Andhra Pradesh 522237, India"))

    # Abstract
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
        "13.8% (p=0.00082, Cohen's d_z=-0.56) and intervention cost by 9.3% (p=0.00089), with identical 72.0% "
        "success rate as Dynamic-SP. A 6-way ablation confirms the hard risk constraint as the dominant "
        "component: removing it drops success from 70.0% to 56.7%."))
    add(para("keywords",
        bold("Keywords: "),
        "Autonomous network self-healing, Structural Causal Models, Pearl's do-calculus, minimum-causal "
        "intervention, risk-constrained optimization, Software-Defined Networking."))

    # ─ 1 Introduction ─
    add(h1("1", "Introduction"))
    add(body(
        "Software-Defined Networking (SDN) centralizes control intelligence, granting network operators "
        "programmatic visibility and fine-grained forwarding control across distributed data-plane switches [1,2]. "
        "Despite these architectural advantages, wide-area and data-center networks operate under intense dynamic "
        "volatility, where physical fiber cuts, optical transponder brownouts, hardware failures, and bursty traffic "
        "surges trigger severe service degradation [3,4]. When outages occur, the network management system must "
        "autonomously detect the fault, diagnose the underlying cause, compute a remedial configuration, and verify "
        "service restoration with minimal downtime [5,6]."))

    add(h2("1.1", "Limitations of Existing Approaches"))
    add(body(
        "While autonomous recovery has been widely explored, existing paradigms exhibit distinct operational "
        "limitations. Reactive Shortest-Path Rerouting restores connectivity but ignores control-plane churn, "
        "frequently modifying extensive switch sets and creating transient forwarding loops [7,10,11]. Precomputed "
        "Protection Paths offer sub-50 ms restoration [3,7] but exhaust switch TCAM resources and fail under "
        "concurrent multi-link failures. Risk-Aware Routing [4,6] does not penalize the operational cost of "
        "reconfiguration. Deep Reinforcement Learning policies [16,19,23] lack formal safety constraints and "
        "require immense offline training datasets [11]. Correlation-Based Diagnosis [10,14,27] fails to "
        "distinguish root causes from downstream symptoms. Existing systems cannot evaluate counterfactual "
        "queries — assessing what the post-recovery state would be if action a were executed [8,9]."))

    add(h2("1.2", "Research Gap"))
    add(body(
        "Although prior network-recovery approaches address fault diagnosis, path restoration, and risk-aware "
        "routing, the extent to which causal uncertainty, intervention-induced congestion, and control-plane "
        "reconfiguration costs can be jointly incorporated into a risk-constrained recovery decision remains to "
        "be established. The central research question is: Can a network self-healing controller select a "
        "feasible recovery action that maintains service, satisfies an explicit post-recovery risk limit, and "
        "minimizes operational intervention cost while accounting for uncertainty in fault diagnosis and "
        "predicted recovery outcomes?"))

    add(h2("1.3", "Hypotheses"))
    for h in [
        "H1 (Intervention Parsimony). CIRAH achieves a statistically significant reduction in switch modifications and intervention cost compared to reactive Dynamic-SP (p < 0.05).",
        "H2 (Risk Compliance). CIRAH maintains post-recovery risk strictly below R_max, whereas unconstrained variants exhibit elevated violations.",
        "H3 (Noise Resilience). Under telemetry observation uncertainty sigma_noise >= 0.20, Bayesian fault estimation maintains higher recovery success than heuristic rule-based diagnosis.",
        "H4 (Scalability). The parsimonious intervention advantage of CIRAH persists across Abilene (11 nodes), GEANT (22 nodes), and Fat-tree k=4 (20 nodes).",
    ]:
        add(body(h))

    add(h2("1.4", "Contributions"))
    for txt in [
        "Causal fault-to-recovery formulation: A formally specified SCM connecting link faults, traffic conditions, M/M/1 queuing behavior, routing interventions, and end-to-end service outcomes, with explicit assumptions, identifiability limitations, and predictive accuracy evaluation.",
        "Intervention-aware recovery optimization: A constrained formulation jointly accounting for control-plane reconfiguration cost, service disruption, residual network risk, and SLA feasibility, compared with constrained routing methods.",
        "Network-wide intervention impact estimation: A graph-based stress-relief mechanism (CIHF) evaluated against 5 alternative scoring methods. Controlled experiments (720 paired runs) show CIHF does not change action selection in 99.2% of scenarios; retained as interpretive stress-relief visualization.",
        "Uncertainty-aware risk handling: A robust risk bound with empirical 0.0% constraint-violation rate at the default threshold (N=30 independent scenarios).",
        "Reproducible experimental validation: Approximately 5,300 paired Monte Carlo runs across three topologies, 6-way component ablations, paired statistical comparisons, and open-source implementation at https://github.com/Shabreen123/CIRAH",
    ]:
        add(numitem(txt))

    # ─ 2 Literature Review ─
    add(h1("2", "Literature Review"))

    add(h2("2.1", "SDN Restoration and Minimum-Change Routing"))
    add(body(
        "SDN architectures decouple control and data planes via OpenFlow [5,6]. Sharma et al. [7] studied "
        "proactive protection versus reactive restoration, showing protection achieves sub-50 ms failover at "
        "the cost of rapid TCAM exhaustion. Qin et al. [3] introduced FAPR, balancing proactive backup "
        "selection with reactive restoration. Yusuf et al. [4] formulated adaptive path selection using flow "
        "classification and composite QoS metrics. Li et al. [31] examined path selection for link-failure "
        "protection in hybrid SDNs. None of these works model the control-plane message cost incurred during "
        "large-scale reconfigurations."))

    add(h2("2.2", "Risk-Constrained Routing and Resilience Optimization"))
    add(body(
        "Risk-aware routing avoids links vulnerable to failure or buffer overflows [4,6]. Risk-aware traffic "
        "engineering incorporates probabilistic link availability into path optimization [3,4,31]. "
        "Machine-learning methods for traffic-flow prediction [32] trigger proactive restoration. However, "
        "these formulations do not enforce hard post-recovery risk ceilings, nor penalize the operational "
        "overhead of modifying forwarding entries in the control plane."))

    add(h2("2.3", "Causal Fault Localization and Counterfactual Decision-Making"))
    add(body(
        "Causal inference, formalized by Pearl [9], distinguishes observational correlation P(Y|X) from "
        "interventional manipulation P(Y|do(X)). In networking, causal directed graphs have been applied to "
        "root-cause fault localization [8,9]. Existing causal approaches terminate at fault localization; they "
        "do not integrate counterfactual outcome prediction directly into an online intervention optimization "
        "algorithm that evaluates alternative recovery actions."))

    add(h2("2.4", "Autonomous Self-Healing and Digital Twins"))
    add(body(
        "Clark et al.'s Knowledge Plane [8] originated autonomous network management. Recent Network Digital "
        "Twins (NDTs) [1,6] provide risk-free simulation environments. Deep learning models have been applied "
        "to DDoS mitigation in SDNs encompassing systematic reviews [11], DNN classifiers [15,21], optimised "
        "models [17,18], hybrid frameworks [12,13,20,22,24-26,33-35], attention methods [27,30], IoT "
        "extensions [19,29], and ensemble methods [14,23]. CIRAH bridges causal fault localization and "
        "risk-constrained intervention optimization by integrating causal diagnosis, counterfactual evaluation, "
        "and risk-constrained action selection in a unified closed-loop framework."))

    add(h2("2.5", "Comparison Table"))
    add(body("Table 1 compares CIRAH against representative approaches across eight technical dimensions."))
    add(tblcap("Table 1. Technical comparison of network fault recovery and management approaches."))
    add(make_table(
        ["Approach","Causal Diag.","CF Pred.","Interv. Cost","Risk","Net-wide","Uncertainty","Guarantees","Validation"],
        [
            ["FAPR [3]","No (Heartbeat)","No","Resource proxy","None","Local link","Deterministic","None","Mininet"],
            ["Yusuf et al. [4]","No (Threshold)","No","None","None","Path-level","None","None","Simulation"],
            ["Polat & Polat [10]","No (Rules)","No","None","None","None","None","None","Mininet/POX"],
            ["Hnamte et al. [15]","No (DNN)","No","None","None","Local drop","Softmax","None","Traces"],
            ["Paidipati et al. [16]","No (DRL)","No","None","Soft penalty","Global reward","Replay","None","Cloud sim."],
            ["Leena et al. [28]","Correlation GNN","No","Path cost","None","Neighbourhood GNN","Cluster","None","Emulation"],
            ["Dynamic-SP [7]","Link-down alert","No","None","None","Local status","None","None","Sim./Testbed"],
            ["Constrained-MinChange","Link-down alert","No","Switch diff","Hard Bound","Local status","None","Risk Feasib.","Simulation"],
            ["CIRAH (Proposed)","Bayesian SCM","Pearl do(A)","Fine-grained C_I,C_D","Hard Bound R_post<=R_max","Laplacian CIHF","3-State+Noise","Robust Bound","Abilene,GEANT,Fat-tree"],
        ]
    ))

    # ─ 3 Methodology ─
    add(h1("3", "The CIRAH Framework"))

    add(h2("3.1", "End-to-End System Architecture"))
    # FIGURE 1
    add(img.fig_para("fig1_academic_architecture.png"))
    add(figcap(
        "Fig. 1. CIRAH three-tier architecture. Tier 1: Telemetry and Observation. "
        "Tier 2: Cognitive Causal Optimization Substrate (SCM, counterfactual evaluation, CIHF, optimizer). "
        "Tier 3: Network Digital Twin and closed-loop adaptation."))
    add(body(
        "The CIRAH architecture comprises three functional tiers (Fig. 1). Tier 1 (Telemetry and Observation) "
        "performs continuous monitoring of link latency, loss, flow rates, and switch port statistics. "
        "Tier 2 (Cognitive Causal Optimization Substrate) executes SCM-based Bayesian fault traceback, Pearl "
        "counterfactual intervention evaluation, CIHF diffusion, and the risk-constrained minimum-intervention "
        "solver. Tier 3 (Network Digital Twin and Adaptation) provides virtual state emulation for risk-free "
        "what-if validation and continuous Bayesian model adaptation."))

    add(h2("3.2", "Structural Causal Model (SCM)"))
    add(body(
        "We define the network state using a 6-tuple SCM M = <U, V, F, P(U)> with exogenous variables "
        "U = {U_loss, U_lat} and endogenous variables: fault state F_e in {0,1,2} (Normal, Degraded, "
        "Severed); link properties L_e = <lat_e, loss_e, cap_e>; queue utilization Q_e in [0,1]; routing "
        "matrix R; service outcomes Y_f = <lat_f, loss_f, conn_f>; and intervention A. "
        "The causal DAG assumes F_e -> L_e, {L_e,R} -> Q_e, Q_e -> Y_f, A -> R, with no hidden common "
        "causes between independent link faults."))
    add(body(
        "Link state structural equations (Eq. 1): L_e = <lat_0,0,cap_0>+U for F_e=0 (Normal); "
        "<lat_0*(1+delta),loss_deg,cap_0*rho>+U for F_e=1 (Degraded); <inf,100%,0> for F_e=2 (Severed). "
        "Queue utilization (Eq. 2): Q_e = Load_e / max(1.0, cap_e). "
        "M/M/1 queuing delay (Eq. 3): D = Load/(cap-Load)*2 for Q<0.85; "
        "15+35*((Q-0.85)/0.15)^1.5 for 0.85<=Q<=1; 50+(Q-1)*80 for Q>1."))

    add(h3("Validated Bayesian Causal Fault Localization"))
    add(body(
        "Given noisy telemetry O_e and the set of active paths traversing edge e, the unnormalized posterior "
        "score for state k in {0,1,2} is (Eq. 4a): s_k(e) = P(O_e|F_e=k) * P(F_e=k) * w_k(Paths). "
        "Priors: P(F_e=0)=0.95, P(F_e=1)=0.03, P(F_e=2)=0.02 (ISP backbone base rates). "
        "Path-evidence multipliers (Eq. 4b): w_0=1/(1+3*rho_e), w_1=1+2.5*rho_e, w_2=1+4*rho_e. "
        "Normalized posterior (Eq. 4c): P(F_e=k|O_e,Paths) = s_k(e) / sum_j s_j(e), ensuring sum = 1.0. "
        "Empirical evaluation (3,000 edge assessments, N=100 fault scenarios): "
        "Normal P/R/F1=1.000; Severed P/R/F1=1.000; overall accuracy=1.000. "
        "Degraded F1=0.000 (fault generator injects only complete severances — acknowledged limitation)."))

    add(h2("3.3", "Counterfactual Intervention Evaluation"))
    add(body(
        "CIRAH executes Pearl's three-step counterfactual procedure. "
        "(1) Abduction: U_lat,e = max(0, O_lat,e - base_lat_e). "
        "(2) Action: do(A=a) — set R_f* = Path(a), sever causal arrows into R_f* (Eq. 5). "
        "(3) Prediction: forward-propagate with fixed U to obtain counterfactual loads, queue delays, and "
        "service outcomes (Eq. 6). Recovery probability (Eq. 7): "
        "P(F_rec|do(A=a)) = E[I(lat<=SLA_lat AND loss<=SLA_loss) | O]. "
        "Counterfactual evaluation changes 72% of selected actions under tight capacity (80 Mbps links, "
        "40 Mbps cross-traffic) but produces identical outcomes under default wide-capacity (1,000 Mbps) "
        "ablation scenarios, because traffic displacement does not cause congestion at wide margins."))

    add(h2("3.4", "Causal Intervention Healing Field (CIHF)"))
    add(body(
        "CIHF quantifies spatial stress relief via normalized graph Laplacian diffusion (Eq. 8): "
        "h(a) = (I + sigma*L_norm)^(-1) * s(a), Psi(a) = 1^T * h(a) (Eq. 10). "
        "The Laplacian inverse is precomputed at initialization in O(|V|^3); per-event cost is O(|V|^2). "
        "Controlled experiments across 720 paired runs (6 scoring modes) show CIHF changed the selected "
        "action in only 1 of 120 runs (0.8%), Wilcoxon p=0.317 for all outcome metrics. "
        "CIHF is retained as an interpretive stress-relief visualization rather than a decision-making component."))

    add(h2("3.5", "Risk Assessment and Robust Constraint"))
    add(body(
        "Residual risk (Eq. 11): R_post(a) = R_op(a) + R_prop(a). "
        "Operational risk (Eq. 12): R_op = P_disc*100 + P_SLA*25 + P_flap*15. "
        "Propagation risk (Eq. 13): R_prop = sum_e [util_e>0.85] * [1-exp(-1.8*(util_e-0.85)/0.15)] * 40. "
        "Robust constraint (Eq. 14): R_robust = R_post + z_alpha*sigma_R <= R_max, "
        "z_alpha=1.645 (95% one-sided Gaussian quantile), sigma_R=0.08*R_post (proportional estimation "
        "uncertainty). The bound applies to estimated mean risk, not individual outcomes. "
        "Empirical validation at R_max=35.0: 0.0% observed violations (N=30 independent scenarios)."))

    add(h2("3.6", "Intervention Cost Model"))
    add(body(
        "Direct control-plane cost (Eq. 15): C_I = w_rule*DeltaRules + w_sw*DeltaSwitches + w_msg*Msg_ctrl, "
        "with w_rule=1.0, w_sw=2.5, w_msg=0.5. "
        "Transient disruption cost (Eq. 16): C_D = (DeltaSwitches*12ms/1000)*d_f*5.0. "
        "Latency SLA excess (Eq. 17): C_L = max(0, lat_predicted - SLA_lat)."))

    add(h2("3.7", "Normalized Combinatorial Optimization"))
    add(body(
        "Objective (Eq. 18): J(a) = lambda_I*(C_I/C_I,ref) + lambda_D*(C_D/C_D,ref) + "
        "lambda_L*(C_L/C_L,ref) + beta*(R_post/R_max) - gamma*(Psi/Psi_ref), "
        "subject to: R_robust(a) <= R_max; P(F_rec|do(a)) >= tau; connectivity(a)=1. "
        "Solver enumerates K=6 loop-free shortest paths plus throttled variants, yielding |A|<=13 candidates. "
        "Selects lowest-J feasible candidate (heuristic with bounded set, not global optimum). "
        "All parameters are listed in Table 2a."))

    add(tblcap("Table 2a. CIRAH algorithm parameters."))
    add(make_table(
        ["Symbol / Parameter","Value","Description"],
        [
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
            ("Fallback throttle: partition / risk","0.50 / 0.75","Ingress rate limits in fallback"),
            ("P(F_e=0/1/2)","0.95 / 0.03 / 0.02","Bayesian priors: Normal/Degraded/Severed"),
        ]
    ))

    add(h2("3.8", "Safe Fallback Mechanism"))
    add(body(
        "When A_feas is empty, CIRAH invokes a two-tier fallback. "
        "(1) Partition detection via graph reachability on the active-link subgraph. If no path exists, "
        "CIRAH applies 50% ingress throttling, reports service unavailability, and does not claim false "
        "recovery. The 50% rate halves offered load to limit buffer overflow on surviving links. "
        "(2) Paced detour: if connected paths exist but violate R_max, the lowest-risk candidate is "
        "selected with 75% ingress rate limiting. Fallback triggered in 6.7% of runs at R_max=35.0 and "
        "up to 30.0% at R_max=10.0. Throttling cannot restore connectivity across a true physical partition."))

    add(h2("3.9", "Algorithm Specification"))
    add(code_paras(
        "Algorithm 1: CIRAH Counterfactual Risk-Constrained Intervention Selection\n"
        "Input:  G=(V,E), Telemetry O, Flows F, Impaired flow f*, R_max, tau\n"
        "Output: Optimal intervention a*\n\n"
        "1.  A <- {a_0 (null action)}\n"
        "2.  For each e in E:\n"
        "3.      s_k(e) = P(O_e|F=k)*P(F=k)*w_k(Paths)  for k in {0,1,2}\n"
        "4.      P(F_e=k|O_e,Paths) <- s_k / sum_j s_j\n"
        "5.  H <- PenalizeGraphWeights(G, posteriors)\n"
        "6.  For each of K shortest loop-free paths p:\n"
        "7.      A <- A + {reroute(p,1.0), reroute_paced(p,0.85)}\n"
        "8.  A_feas <- empty\n"
        "9.  For each a in A:\n"
        "10.     Y_hat <- EvaluateCounterfactual(M, do(A=a), O, U_hat)\n"
        "11.     R_post <- EvaluateRisk(G, a, Y_hat)\n"
        "12.     R_robust <- R_post + z_alpha * sigma_R\n"
        "13.     J(a) = lambda_I*C_I/C_ref + ... - gamma*Psi/Psi_ref\n"
        "14.     If R_robust<=R_max AND P_rec>=tau AND connected: A_feas += {a}\n"
        "15. If A_feas != empty : a* <- argmin_{a in A_feas} J(a)\n"
        "16. Else               : a* <- SafeFallback(A, G, f*)\n"
        "17. InstallFlowRules(a*); Return a*"
    ))

    add(h2("3.10", "Computational Complexity"))
    add(body(
        "Per failure event: Bayesian diagnosis O(|E|); K-shortest paths O(K|V|(|E|+|V|log|V|)); "
        "counterfactual evaluation per candidate O(|F|*|Path|+|E|); CIHF O(|V|^2) (precomputed inverse, "
        "O(|V|^3) one-time init). Overall: O(K|V|log|V| + |A|(|E|+|V|^2)). "
        "Measured mean algorithmic latency (60 profiling runs): "
        "Abilene 6.28 ms (p95=8.70 ms); GEANT 10.78 ms (p95=14.33 ms); "
        "Fat-tree 20-node total recovery 105.7 ms (algorithm-only <16 ms)."))

    # ─ 4 Experimental Setup ─
    add(h1("4", "Experimental Setup"))

    add(h2("4.1", "Topologies"))
    add(body(
        "Three network topologies are evaluated. "
        "(1) Abilene Internet2 Backbone: 11 nodes, 30 directed edges, 1,000 Mbps capacity, delays 5-28 ms. "
        "(2) GEANT Pan-European Research Backbone: 22 nodes, 56 directed edges, 1,000/500 Mbps. "
        "(3) Fat-tree k=4: 20 nodes (4 core, 8 aggregation, 8 edge), 64 directed edges, 1,000/500 Mbps. "
        "All topologies constructed programmatically; no external files required."))

    add(h2("4.2", "Traffic, Faults, and Telemetry Noise"))
    add(body(
        "Each run generates 8 concurrent flows, demands 10-45 Mbps, SLAs: latency in [1.8,2.5]*base, "
        "loss in [1%,3%]. Seven failure modes: single-link (k=1); concurrent multi-link (k=2,3,4); "
        "75% capacity brownout; bufferbloat (+80 ms,+12% loss); bursty traffic (3.5x demand); "
        "telemetry noise (sigma_noise in [0,0.30])."))

    add(h2("4.3", "Baselines, Ablations, and Statistical Protocol"))
    add(body(
        "Baselines: Static-SP [10], Dynamic-SP [7], Backup-Path [3], Risk-Aware [4], MinChange-SP, "
        "Constrained-MinChange (same R_max constraint as CIRAH, myopic load estimation). "
        "Ablations: CIRAH-noCausal, CIRAH-noCF, CIRAH-noCIHF, CIRAH-noRisk, CIRAH-noInterv. "
        "N=50 paired runs per condition with matched seeds. "
        "Two-sided paired Wilcoxon signed-rank test, alpha=0.05. Effect sizes: Cohen's d_z = D_bar/s_D. "
        "Multiplicity control: Primary Abilene family (N=6) and Omnibus family (N=30). "
        "Success: no path link has loss>=99% AND latency and loss meet SLA bounds."))

    # ─ 5 Results ─
    add(h1("5", "Experimental Results and Discussion"))

    add(h2("5.1", "Multi-Failure Severity (Abilene)"))
    # FIGURE 2
    add(img.fig_para("fig5_success_vs_severity.png"))
    add(figcap(
        "Fig. 2. Recovery success rate across k=0-4 simultaneous link failures on the Abilene topology "
        "(N=50 paired runs per condition, 95% CI shown)."))
    add(body(
        "Table 2 reports Abilene topology results. CIRAH matches Dynamic-SP success (90.0% at k=1, "
        "72.0% at k=2, 68.0% at k=3) while consistently reducing switch churn and intervention cost. "
        "Under k=2, CIRAH reduces switches from 3.78 to 3.26 (13.8%, p=0.00082, d_z=-0.56) and "
        "cost from 19.02 to 17.25 (9.3%, p=0.00089). Recovery time at k=1 is comparable (49.4 vs. "
        "49.2 ms); at k=3 it rises to 415.0 ms vs. 58.8 ms, reflecting combinatorial search depth."))
    add(tblcap("Table 2. Multi-link failure severity results (Abilene topology, N=50 paired runs per level)."))
    add(make_table(
        ["Severity","Method","Success (%)","Latency (ms)","Loss (%)","Risk","Switches","Cost","Recovery (ms)"],
        [
            ["k=1","Dynamic-SP","90.0","43.0+/-2.3","0.19+/-0.03","2.91+/-0.74","2.84+/-0.32","14.34+/-1.55","49.2+/-3.9"],
            ["k=1","CIRAH","90.0","44.6+/-2.4","0.19+/-0.03","2.93+/-0.74","2.28+/-0.24","12.30+/-1.22","49.4+/-2.9"],
            ["k=2","Dynamic-SP","72.0","49.3+/-2.8","0.22+/-0.03","11.39+/-3.43","3.78+/-0.25","19.02+/-1.20","60.5+/-3.0"],
            ["k=2","CIRAH","72.0","52.4+/-3.0","0.24+/-0.03","11.46+/-3.42","3.26+/-0.21","17.25+/-1.06","178.9+/-65.8"],
            ["k=3","Dynamic-SP","68.0","53.1+/-2.8","0.21+/-0.03","21.57+/-5.40","3.64+/-0.35","18.27+/-1.65","58.8+/-4.2"],
            ["k=3","CIRAH","68.0","57.8+/-3.5","0.22+/-0.03","21.64+/-5.39","3.24+/-0.30","16.95+/-1.47","415.0+/-106.1"],
        ]
    ))

    add(h2("5.2", "Telemetry Noise Resilience"))
    # FIGURE 3
    add(img.fig_para("fig10_telemetry_noise_resilience.png"))
    add(figcap(
        "Fig. 3. Recovery success under telemetry measurement noise (sigma_noise = 0.0-0.30) "
        "comparing Bayesian SCM against rule-based diagnosis (N=50 runs per noise level)."))
    add(body(
        "Under sigma=0.30, Dynamic-SP degrades to 44.0% success while CIRAH sustains 54.0% "
        "(+22.7% relative advantage) with lower residual risk (8.53 vs. 10.01), confirming H3."))

    add(h2("5.3", "6-Way Component Ablation"))
    # FIGURE 4
    add(img.fig_para("fig9_component_ablations.png"))
    add(figcap(
        "Fig. 4. Six-way ablation results (N=60 paired runs, Abilene): "
        "(a) recovery success rate, (b) residual risk, (c) switch churn, (d) intervention cost."))
    add(tblcap("Table 3. Six-way component ablation results (Abilene topology, N=60 paired runs)."))
    add(make_table(
        ["Variant","Removed","Success (%)","SLA Viol. (%)","Constr. Viol. (%)","Switches","Cost","Risk","Psi"],
        [
            ["CIRAH-full","None (Reference)","70.0","30.0","0.0","3.60","18.90","7.06","0.974"],
            ["CIRAH-noCausal","SCM Bayesian traceback","70.0","30.0","1.7","3.55","18.63","8.29","0.960"],
            ["CIRAH-noCF","Counterfactual do(A)","70.0","30.0","0.0","3.60","18.90","7.04","0.974"],
            ["CIRAH-noCIHF","Healing field (gamma=0)","70.0","30.0","0.0","3.60","18.90","7.06","0.000"],
            ["CIRAH-noRisk","Hard risk bound","56.7","43.3","0.0","3.25","17.68","8.57","0.998"],
            ["CIRAH-noInterv","Cost penalty (lambda_I=0)","70.0","30.0","0.0","3.78","19.53","7.04","0.958"],
        ]
    ))
    add(body(
        "Removing the hard risk constraint (CIRAH-noRisk) drops success from 70.0% to 56.7% and raises "
        "SLA violations from 30.0% to 43.3% — the strongest component effect. Removing the intervention "
        "cost penalty (CIRAH-noInterv) increases switch churn from 3.60 to 3.78. Removing CIHF collapses "
        "Psi to 0.000 but produces no measurable change in success, switches, cost, or risk, consistent "
        "with the finding that CIHF does not change action selection under tested conditions."))

    # FIGURE 5 (switches footprint)
    add(h2("5.4", "Statistical Validation"))
    add(img.fig_para("fig7_switches_modified_footprint.png"))
    add(figcap(
        "Fig. 5. Mean switch modifications per recovery across all compared methods at k=1,2,3 failures."))
    add(tblcap("Table 4. Paired hypothesis tests: CIRAH vs. Dynamic-SP (Abilene, N=50)."))
    add(make_table(
        ["k","Metric","CIRAH","Dyn-SP","Delta%","95% CI","d_z","p (Wilcoxon)","Holm p","Sig.?"],
        [
            ["1","Switches","2.28","2.84","-19.7%","[-0.90,-0.22]","-0.47","0.00206","0.0083","Yes"],
            ["1","Cost","12.30","14.34","-14.2%","[-3.30,-0.78]","-0.46","0.00209","0.0083","Yes"],
            ["2","Switches","3.26","3.78","-13.8%","[-0.78,-0.26]","-0.56","0.00082","0.0049","Yes"],
            ["2","Cost","17.25","19.02","-9.3%","[-2.69,-0.85]","-0.55","0.00089","0.0049","Yes"],
            ["3","Switches","3.24","3.64","-11.0%","[-0.66,-0.14]","-0.44","0.00280","0.0083","Yes"],
            ["3","Cost","16.95","18.27","-7.2%","[-2.23,-0.41]","-0.41","0.00304","0.0083","Yes"],
        ]
    ))
    add(body(
        "All six Primary Abilene family hypotheses are significant after Holm adjustment "
        "(p_adj <= 0.0083 < 0.05), confirming H1. Recovery time, residual risk, and success rate "
        "do not achieve omnibus significance (N=30 family); reported as non-significant."))

    add(h2("5.5", "Constrained Baseline and Fat-Tree Scalability"))
    add(tblcap("Table 5. CIRAH vs. Constrained-MinChange baseline (Abilene avg. k=1,2,3, N=150)."))
    add(make_table(
        ["Method","Success (%)","Switches","Cost","Risk"],
        [
            ["Static-SP","12.0","0.00","0.00","89.08"],
            ["Dynamic-SP","76.7","3.42","17.21","11.96"],
            ["MinChange-SP","74.7","2.90","15.40","12.30"],
            ["Constrained-MinChange","74.7","2.91","15.45","12.30"],
            ["CIRAH","76.7","2.93","15.51","12.01"],
        ]
    ))
    add(body(
        "CIRAH matches Dynamic-SP success (76.7%) with switch count similar to Constrained-MinChange. "
        "The marginal risk advantage (12.01 vs. 12.30) reflects causal posterior weighting. "
        "On Fat-tree (20 nodes), all methods achieve 90% success; CIRAH reduces switches from 3.46 "
        "(Dynamic-SP) to 2.29 — a 33.8% reduction — demonstrating scalability beyond Abilene and GEANT."))

    add(h2("5.6", "Risk Threshold Sensitivity"))
    add(tblcap("Table 6. Risk threshold sensitivity at k=2, Abilene (N=30 runs per R_max)."))
    add(make_table(
        ["R_max","Success (%)","Violation (%)","Fallback (%)","Mean Risk","Switches"],
        [
            ["10.0","80.0","20.0","20.0","4.98","3.13"],
            ["20.0","70.0","13.3","30.0","14.44","2.73"],
            ["35.0 (default)","93.3","0.0","6.7","2.91","2.90"],
            ["50.0","70.0","6.7","30.0","12.06","2.60"],
            ["100.0","73.3","3.3","26.7","8.91","3.17"],
        ]
    ))
    add(body("R_max=35.0 achieves the highest success (93.3%) with 0.0% violations and 6.7% fallback."))

    # ─ 6 Discussion ─
    add(h1("6", "Discussion"))
    add(body(
        "Churn-latency trade-off. CIRAH occasionally accepts a path with 2-3 ms higher propagation latency "
        "to avoid reconfiguring additional core switches. In carrier networks, saving multiple TCAM updates "
        "avoids transient packet reordering and flow table lockups — a highly desirable trade-off."))
    add(body(
        "CIHF as interpretive visualization. The CIHF field correctly computes spatial stress relief but does "
        "not change action selection in 99.2% of scenarios. Its objective term (mean 0.078) is 0.11x the cost "
        "term and 0.02x the risk term. Increasing gamma up to 6.4 (8x default) does not consistently change "
        "selection. CIHF is retained as a post-hoc interpretive visualization of network-wide stress relief."))
    add(body(
        "Counterfactual value. The do(A) mechanism changes 72% of selected actions under tight capacity "
        "(80 Mbps links). Under wide-capacity (1,000 Mbps) conditions, it produces identical outcomes to "
        "myopic evaluation. CF has measurable decision impact in capacity-constrained environments."))
    add(body(
        "Recovery time overhead. Decision latency scales with failure severity: 49.4 ms at k=1 (comparable "
        "to Dynamic-SP), 178.9 ms at k=2, and 415.0 ms at k=3. CIRAH trades computation time for "
        "substantial reductions in switch modification churn. For sub-100 ms requirements, "
        "hardware-accelerated SCM solvers represent a promising future extension."))

    # ─ 7 Threats ─
    add(h1("7", "Threats to Validity and Limitations"))
    add(body(
        "Construct Validity. Intervention cost uses OpenFlow message weights and switch delay proxies "
        "(Delta_t_commit=12 ms); hardware-specific latencies may vary."))
    add(body(
        "CIHF Limitation. Controlled experiments (720 paired runs) confirm CIHF does not change action "
        "selection or improve any outcome metric under tested conditions. The CIHF objective term (mean 0.078) "
        "is 0.11x the cost term and 0.02x the risk term. Retained as interpretive visualization only."))
    add(body(
        "Counterfactual Scope. The do(A) mechanism changes decisions under tight capacity but produces "
        "identical outcomes under default wide-capacity ablation scenarios. Model is calibrated against "
        "simulator equations — accurate predictions reflect internal consistency, not external validity."))
    add(body(
        "Risk Constraint Assumptions. Robust bound uses heuristic sigma_R=0.08*R_post, not empirically "
        "calibrated variance. Bound applies to estimated mean risk, not individual recovery outcomes."))
    add(body(
        "Bayesian Degraded-State Limitation. Degraded-state classifier unevaluated against true degraded "
        "links (fault generator injects only complete severances)."))
    add(body(
        "Simulation Only. All results are from simulation without Mininet/P4 physical testbed validation. "
        "Results may not generalize to production SDN deployments or real traffic distributions."))

    # ─ 8 Conclusion ─
    add(h1("8", "Conclusion and Future Scope"))
    add(body(
        "This paper presented CIRAH, a causal-intervention optimization framework for autonomous network "
        "self-healing under risk constraints. By formalizing network dynamics as an SCM, computing Pearl's "
        "counterfactual outcomes do(A=a), and enforcing robust post-recovery risk limits, CIRAH discovers "
        "the minimum-cost recovery action satisfying post-repair risk constraints. Across approximately 5,300 "
        "paired Monte Carlo simulation runs on Abilene, GEANT, and Fat-tree topologies, CIRAH demonstrated "
        "statistically verified switch churn reductions of 13.8%-19.7% (p<0.01) over reactive shortest-path "
        "rerouting, with 0.0% risk constraint violations at R_max=35.0. The 6-way ablation established the "
        "hard risk constraint as the most impactful component. CIHF does not influence action selection under "
        "tested conditions and is retained as an interpretive visualization. Future work targets deployment "
        "on physical P4-programmable SDN testbeds for sub-millisecond counterfactual inference."))

    add(para("acknowlegments",
        bold("Conflict of Interest. "),
        "The authors declare no competing financial interests."))
    add(para("acknowlegments",
        bold("Data Availability. "),
        "Source code, topology graphs, experiment runners, raw CSV datasets, and figure generation scripts "
        "are openly available at https://github.com/Shabreen123/CIRAH"))

    # ─ References ─
    add(h1("", "References"))
    refs = [
        "1. Sanz Rodrigo, M. et al.: Network Digital Twin-Generated Dataset for Zero-Touch SLA Preservation. Zenodo (2025). https://doi.org/10.5281/zenodo.17255327",
        "2. Moustafa, N., Slay, J.: UNSW-NB15: A Dataset for Network Intrusion Detection. Proc. IEEE MilCIS, pp. 1-6 (2015)",
        "3. Qin, H. et al.: FAPR: An Adaptive Approach to Link Failure Recovery in SDN. Applied Sciences 14(11), 4719 (2024)",
        "4. Yusuf, M.N. et al.: Adaptive Path Selection with Flow Classification for SDNs. Mathematics 11(6), 1404 (2023)",
        "5. McKeown, N. et al.: OpenFlow: Enabling Innovation in Campus Networks. ACM SIGCOMM CCR 38(2), 69-74 (2008)",
        "6. Kreutz, D. et al.: Software-Defined Networking: A Comprehensive Survey. Proc. IEEE 103(1), 14-76 (2015)",
        "7. Sharma, S. et al.: Enabling Fast Failure Recovery in OpenFlow Networks. Proc. DRCN, pp. 164-171 (2011)",
        "8. Clark, D.D. et al.: A Knowledge Plane for the Internet. Proc. ACM SIGCOMM, pp. 3-10 (2003)",
        "9. Pearl, J.: Causality: Models, Reasoning, and Inference, 2nd edn. Cambridge Univ. Press (2009)",
        "10. Polat, O., Polat, H.: An Intelligent SDN Controller to Detect and Mitigate DoS Attacks. J. ICT 20(1), 1-24 (2021)",
        "11. Polat, O. et al.: DL Techniques for DDoS Detection in SDN: Systematic Review. Eng. Sci. Technol. 75, 102290 (2026)",
        "12. Kachavimath, A.V., Narayan, D.G.: Hybrid DL with Consensus Feature Selection for DDoS in SDN. Procedia Comput. Sci. 252, 643-652 (2025)",
        "13. Mehmood, S. et al.: DDoS Detection in SDN Using CNN-MLP. PLoS ONE 20(1), e0312425 (2025)",
        "14. Gayantha, N. et al.: Advanced DDoS Detection and Mitigation in SDN. Proc. IEEE SCSE (2025)",
        "15. Hnamte, V. et al.: DDoS Detection Using DNN in SDN. Comput. Secur. 138, 103661 (2024)",
        "16. Paidipati, K.K. et al.: DRL Ensemble for DDoS Detection in Cloud-Based SDN. Multimedia Tools Appl. 83(11), 32367-32385 (2024)",
        "17. Al-Dunainawi, Y. et al.: Optimised AI Model for DDoS Detection in SDN. IEEE Access 11, 106733-106748 (2023)",
        "18. Setitra, M.A. et al.: Optimised MLP-CNN for DDoS Detection in SDN. Network 3(4), 538-562 (2023)",
        "19. Aslam, M. et al.: Adaptive ML-Based DDoS Mitigation for SDN-IoT. Sensors 22(7), 2697 (2022)",
        "20. Swileh, M.N., Zhang, S.: Unseen Attack Detection in SDN Using BERT. AI 6(7), 154 (2025)",
        "21. Gadallah, W.G. et al.: DL Technique to Detect DDoS in SDN. Comput. Secur. 137, 103588 (2024)",
        "22. Wang, H. et al.: DDoS Detection Using Autoencoder and GRU for SDN. Comput. J. bxaf021 (2025)",
        "23. Abid, Y.A. et al.: Multilevel DNN for DDoS Detection in SDN-IoT. IEEE IoT J. 11(14), 24715-24725 (2024)",
        "24. Veeresh, G.B. et al.: Swish-Optimized Trident Fusion Network for SDN. Knowl.-Based Syst. 114860 (2025)",
        "25. Chattopadhyay, S. et al.: Enhanced DDoS Detection in SDN Using Ensemble Learning. SN Comput. Sci. 5(5), 580 (2024)",
        "26. Zaidoun, A.S., Lachiri, Z.: Hybrid DL for Multi-class DDoS in SDN. Ann. Telecommun. (2025)",
        "27. Nithya, R., Vinoth Kumar, K.: Attention Driven Hybrid DL for IDS in SDN. Results Eng. 26, 113552 (2026)",
        "28. Leena, R. et al.: Attack Detection Using Hierarchical Dual GNN. Comput. Electr. Eng. 124, 110315 (2025)",
        "29. Rbah, Y. et al.: Hybrid DL SDN-Based IDS for IoMT. IRECAP 14(1) (2024)",
        "30. Alabrah, A.: Improved CCF Detector with IQR Normalisation. Sensors 23(9), 4406 (2023)",
        "31. Li, J. et al.: Path Selection for Link Failure Protection in Hybrid SDNs. Future Gener. Comput. Syst. 137, 201-215 (2022)",
        "32. Liu, S. et al.: CNN-BiGRU-Attention for Traffic Flow Prediction. Sustainability 16(5), 1986 (2024)",
        "33. Arun Prasad, P.B. et al.: Hybrid Metaheuristics with DL for SDN Cyberattack Prevention. Tech. Gaz. 31(1) (2024)",
        "34. Kavitha, S. et al.: Intelligent IDS Using Enhanced AOA with DL. Tech. Gaz. 30(4) (2023)",
        "35. Naeen, H.M. et al.: Enhancing SDN Security with DL for DDoS Detection. Sci. Rep. 15(1), 33419 (2025)",
    ]
    for ref in refs:
        add(para("referenceitem", ref, ind_left=200, ind_hanging=200))

    # Section properties
    sectPr = E(w("sectPr"))
    pgSz = E(w("pgSz"))
    pgSz.set(w("w"), "11906"); pgSz.set(w("h"), "16838")
    sectPr.append(pgSz)
    pgMar = E(w("pgMar"))
    pgMar.set(w("top"),    "1474"); pgMar.set(w("bottom"), "1360")
    pgMar.set(w("left"),  "1134"); pgMar.set(w("right"),  "1134")
    pgMar.set(w("header"),"709");  pgMar.set(w("footer"), "709")
    sectPr.append(pgMar)
    BD.append(sectPr)

    return BD

# ── Build relationships XML ───────────────────────────────────────────────

def build_rels_xml(original_rels_xml, images):
    """Inject image relationships into word/_rels/document.xml.rels"""
    tree = etree.fromstring(original_rels_xml)
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    img_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    for rId, fname, ext, _ in images:
        rel = etree.SubElement(tree, f"{{{ns}}}Relationship")
        rel.set("Id", rId)
        rel.set("Type", img_type)
        rel.set("Target", f"media/{fname}")
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

# ── Assemble final docm ───────────────────────────────────────────────────

def build():
    print("Reading template...")
    with zipfile.ZipFile(TEMPLATE, 'r') as zt:
        tfiles = {name: zt.read(name) for name in zt.namelist()}

    print("Building body elements...")
    body_elements = build_body()

    # Build document.xml
    W_NS = {"w": W, "r": R, "wp": WP, "a": A, "pic": PIC,
            "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
            "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
            "o": "urn:schemas-microsoft-com:office:office",
            "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
            "v": "urn:schemas-microsoft-com:vml",
            "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
            "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
            "wne": "http://schemas.microsoft.com/office/word/2006/wordml"}

    doc_el = etree.Element(w("document"), nsmap=W_NS)
    body_el = etree.SubElement(doc_el, w("body"))
    for el in body_elements:
        body_el.append(el)

    new_doc_xml = etree.tostring(doc_el, xml_declaration=True,
                                  encoding="UTF-8", standalone=True)

    # Build updated relationships
    orig_rels = tfiles.get('word/_rels/document.xml.rels', b'')
    new_rels = build_rels_xml(orig_rels, img.images)

    print(f"Writing {OUT_PATH}...")
    with zipfile.ZipFile(OUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for name, data in tfiles.items():
            if name == 'word/document.xml':
                zo.writestr(name, new_doc_xml)
            elif name == 'word/_rels/document.xml.rels':
                zo.writestr(name, new_rels)
            else:
                zo.writestr(name, data)
        # Write embedded images
        for rId, fname, ext, data in img.images:
            zo.writestr(f"word/media/{fname}", data)

    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"Done: {OUT_PATH} ({size_kb} KB)")
    print(f"Images embedded: {len(img.images)}")
    for rId, fname, ext, data in img.images:
        print(f"  {rId}: {fname} ({len(data)//1024} KB)")

if __name__ == '__main__':
    build()
