"""
CIRAH: Architecture Diagram Generator
Generates:
1. figures/cirah_architecture.drawio (Native Draw.io / diagrams.net XML, 100% editable)
2. figures/fig1_architecture.svg (Vector publication SVG)
3. figures/fig1_clean_architecture.png (Publication-grade 300 DPI vector graphic)
"""

import os
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

FIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'figures'))
os.makedirs(FIG_DIR, exist_ok=True)

def generate_drawio_xml():
    """Generates a complete, fully editable Draw.io / diagrams.net XML file."""
    drawio_path = os.path.join(FIG_DIR, "cirah_architecture.drawio")

    xml_content = """<mxfile host="app.diagrams.net" modified="2026-10-25T16:30:00.000Z" agent="CIRAH" version="21.0.0" type="device">
  <diagram id="cirah-arch" name="CIRAH System Architecture">
    <mxGraphModel dx="1400" dy="850" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" math="1" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- Header Banner -->
        <mxCell id="title" value="&lt;b&gt;&lt;font style=&quot;font-size: 18px;&quot; color=&quot;#ffffff&quot;&gt;CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing&lt;/font&gt;&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#003366;strokeColor=#002244;arcSize=10;" vertex="1" parent="1">
          <mxGeometry x="50" y="20" width="1100" height="50" as="geometry" />
        </mxCell>

        <!-- Stage 0: Network Input -->
        <mxCell id="input_box" value="&lt;b&gt;Network Input&lt;/b&gt;&lt;hr&gt;&bull; Topology Information&lt;br&gt;&bull; Traffic Patterns&lt;br&gt;&bull; Logs &amp; Alerts&lt;br&gt;&bull; Performance Metrics" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f0fe;strokeColor=#4285f4;align=left;spacingLeft=10;" vertex="1" parent="1">
          <mxGeometry x="50" y="90" width="130" height="230" as="geometry" />
        </mxCell>

        <!-- Stage 1: Failure Observation -->
        <mxCell id="s1_box" value="&lt;b&gt;1. Failure Observation&lt;br&gt;&amp; Detection&lt;/b&gt;&lt;hr&gt;&bull; Anomaly detection&lt;br&gt;&bull; Failure localization&lt;br&gt;&bull; Affected services identification&lt;br&gt;&lt;br&gt;&lt;b&gt;[Observed Failures]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1976d2;align=center;" vertex="1" parent="1">
          <mxGeometry x="200" y="90" width="150" height="230" as="geometry" />
        </mxCell>

        <!-- Stage 2: Causal Failure Graph -->
        <mxCell id="s2_box" value="&lt;b&gt;2. Causal Failure Graph&lt;br&gt;Construction&lt;/b&gt;&lt;hr&gt;&bull; Causal discovery&lt;br&gt;&bull; Bayesian influence estimation&lt;br&gt;&bull; Failure propagation modeling&lt;br&gt;&lt;br&gt;&lt;b&gt;[Causal Graph G]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#388e3c;align=center;" vertex="1" parent="1">
          <mxGeometry x="370" y="90" width="150" height="230" as="geometry" />
        </mxCell>

        <!-- Stage 3: Intervention Search -->
        <mxCell id="s3_box" value="&lt;b&gt;3. Intervention Search&lt;br&gt;(Minimum-Causal)&lt;/b&gt;&lt;hr&gt;Candidate Interventions:&lt;br&gt;$$do(f_i = 0), do(a_j)$$&lt;br&gt;&bull; Causal impact analysis&lt;br&gt;&bull; Minimum set selection&lt;br&gt;&lt;br&gt;&lt;b&gt;[Intervention Set A*]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#7b1fa2;align=center;" vertex="1" parent="1">
          <mxGeometry x="540" y="90" width="150" height="230" as="geometry" />
        </mxCell>

        <!-- Stage 4: Healing-Field Propagation -->
        <mxCell id="s4_box" value="&lt;b&gt;4. Healing-Field&lt;br&gt;Propagation&lt;/b&gt;&lt;hr&gt;&bull; Laplacian heat diffusion&lt;br&gt;&bull; Propagate healing field&lt;br&gt;&bull; Estimate post-intervention state&lt;br&gt;&lt;br&gt;&lt;b&gt;[Healing Field H(a)]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff8e1;strokeColor=#ffa000;align=center;" vertex="1" parent="1">
          <mxGeometry x="710" y="90" width="150" height="230" as="geometry" />
        </mxCell>

        <!-- Stage 5: Risk-Constrained Optimization -->
        <mxCell id="s5_box" value="&lt;b&gt;5. Risk-Constrained&lt;br&gt;Action Selection&lt;/b&gt;&lt;hr&gt;$$A^* = \\arg\\min [|A| + \\lambda C(A) + \\beta R(A)]$$&lt;br&gt;s.t. $$P(F_{rec}|do(A)) \\ge \\tau$$&lt;br&gt;$$R_{post}(A) \\le R_{max}$$&lt;br&gt;&lt;b&gt;[Healing Action A*]&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00796b;align=center;" vertex="1" parent="1">
          <mxGeometry x="880" y="90" width="160" height="230" as="geometry" />
        </mxCell>

        <!-- Output: Self-Healed Network -->
        <mxCell id="output_box" value="&lt;b&gt;Self-Healed&lt;br&gt;Network&lt;/b&gt;&lt;hr&gt;&amp;#10004; Failure recovered&lt;br&gt;&amp;#10004; Risk within limit&lt;br&gt;&amp;#10004; Service restored&lt;br&gt;&amp;#10004; Improved resilience" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d4edda;strokeColor=#28a745;align=center;" vertex="1" parent="1">
          <mxGeometry x="1060" y="90" width="110" height="230" as="geometry" />
        </mxCell>

        <!-- Pipeline Connectors -->
        <mxCell id="c1" edge="1" parent="1" source="input_box" target="s1_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />
        <mxCell id="c2" edge="1" parent="1" source="s1_box" target="s2_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />
        <mxCell id="c3" edge="1" parent="1" source="s2_box" target="s3_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />
        <mxCell id="c4" edge="1" parent="1" source="s3_box" target="s4_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />
        <mxCell id="c5" edge="1" parent="1" source="s4_box" target="s5_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />
        <mxCell id="c6" edge="1" parent="1" source="s5_box" target="output_box" style="strokeWidth=2;strokeColor=#555555;endArrow=block;" />

        <!-- Lower Section Container: Substrate -->
        <mxCell id="substrate" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8f9fa;strokeColor=#b0bec5;dashed=1;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="50" y="340" width="1120" height="340" as="geometry" />
        </mxCell>

        <!-- CIHF Algorithm Box -->
        <mxCell id="cihf_title" value="&lt;b&gt;&lt;font style=&quot;font-size: 14px;&quot;&gt;Causal Intervention Healing Field (CIHF) Algorithm&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="250" y="350" width="400" height="30" as="geometry" />
        </mxCell>

        <mxCell id="cihf_1" value="&lt;b&gt;1. Identify&lt;/b&gt;&lt;br&gt;candidate causes &amp;&lt;br&gt;interventions" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1976d2;" vertex="1" parent="1">
          <mxGeometry x="80" y="390" width="130" height="60" as="geometry" />
        </mxCell>
        <mxCell id="cihf_2" value="&lt;b&gt;2. Compute&lt;/b&gt;&lt;br&gt;causal impact&lt;br&gt;($$\\Delta C, \\Delta R, P$$)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#388e3c;" vertex="1" parent="1">
          <mxGeometry x="240" y="390" width="130" height="60" as="geometry" />
        </mxCell>
        <mxCell id="cihf_3" value="&lt;b&gt;3. Construct&lt;/b&gt;&lt;br&gt;healing field&lt;br&gt;$$H(a)$$" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#7b1fa2;" vertex="1" parent="1">
          <mxGeometry x="400" y="390" width="130" height="60" as="geometry" />
        </mxCell>
        <mxCell id="cihf_4" value="&lt;b&gt;4. Optimize&lt;/b&gt;&lt;br&gt;minimum intervention&lt;br&gt;under risk constraint" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#f57c00;" vertex="1" parent="1">
          <mxGeometry x="560" y="390" width="140" height="60" as="geometry" />
        </mxCell>

        <mxCell id="cihf_arrow1" edge="1" parent="1" source="cihf_1" target="cihf_2" style="strokeWidth=2;strokeColor=#1976d2;endArrow=block;" />
        <mxCell id="cihf_arrow2" edge="1" parent="1" source="cihf_2" target="cihf_3" style="strokeWidth=2;strokeColor=#388e3c;endArrow=block;" />
        <mxCell id="cihf_arrow3" edge="1" parent="1" source="cihf_3" target="cihf_4" style="strokeWidth=2;strokeColor=#7b1fa2;endArrow=block;" />

        <mxCell id="cihf_banner" value="Select intervention(s) with highest causal healing value and minimum cost under risk constraints" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ede7f6;strokeColor=#673ab7;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="120" y="465" width="540" height="30" as="geometry" />
        </mxCell>

        <!-- Risk Assessment Module -->
        <mxCell id="ram_box" value="&lt;b&gt;&lt;font color=&quot;#b71c1c&quot;&gt;Risk Assessment Module&lt;/font&gt;&lt;/b&gt;&lt;hr&gt;&bull; &lt;b&gt;Operational Risk&lt;/b&gt; (service disruption, cost)&lt;br&gt;&bull; &lt;b&gt;Propagation Risk&lt;/b&gt; (cascading failures)&lt;br&gt;&bull; &lt;b&gt;Global Risk Evaluation&lt;/b&gt; ($$R_{post} \\le R_{max}$$)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffebee;strokeColor=#d32f2f;align=left;spacingLeft=10;" vertex="1" parent="1">
          <mxGeometry x="750" y="370" width="390" height="110" as="geometry" />
        </mxCell>

        <!-- Digital Twin of Network -->
        <mxCell id="dt_box" value="&lt;b&gt;Digital Twin of Network&lt;/b&gt;&lt;br&gt;What-if Simulation &amp;nbsp;|&amp;nbsp; Causal Reasoning &amp;nbsp;|&amp;nbsp; Predictive Risk Estimation &amp;nbsp;|&amp;nbsp; Healing Field Modeling" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8eaf6;strokeColor=#3f51b5;fontStyle=0;" vertex="1" parent="1">
          <mxGeometry x="120" y="520" width="940" height="40" as="geometry" />
        </mxCell>

        <!-- Continuous Learning -->
        <mxCell id="learn_box" value="&lt;b&gt;Continuous Learning and Adaptation&lt;/b&gt;&lt;br&gt;Update causal graph &amp;nbsp;|&amp;nbsp; Refine intervention policy &amp;nbsp;|&amp;nbsp; Adapt to topology and traffic changes" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f7fa;strokeColor=#00838f;" vertex="1" parent="1">
          <mxGeometry x="120" y="580" width="940" height="40" as="geometry" />
        </mxCell>

        <!-- Feedback Loop Arrow -->
        <mxCell id="fb_arrow" edge="1" parent="1" source="learn_box" target="input_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2.5;strokeColor=#00838f;endArrow=block;dashed=1;">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="60" y="600" />
              <mxPoint x="60" y="330" />
              <mxPoint x="110" y="330" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="fb_label" value="&lt;b&gt;Continuous Feedback Loop&lt;/b&gt;" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=11;fontColor=#00838f;" vertex="1" connectable="0" parent="fb_arrow">
          <mxGeometry x="-0.2" y="1" relative="1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Generated Draw.io XML file: {drawio_path}")
    return drawio_path

def generate_clean_publication_png():
    """Generates a crisp 300 DPI vector graphic for the paper."""
    png_path = os.path.join(FIG_DIR, "fig1_clean_architecture.png")

    fig = plt.figure(figsize=(15, 9.5), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Header Banner
    banner = patches.FancyBboxPatch((0.5, 9.1), 14.0, 0.7, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    facecolor="#003366", edgecolor="#002244", linewidth=1.5)
    ax.add_patch(banner)
    ax.text(7.5, 9.45, "CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing",
            color="white", fontsize=13, fontweight="bold", ha="center", va="center")

    # Pipeline Boxes (Row 1)
    stages = [
        {"x": 0.5, "w": 1.7, "title": "Network Input", "color": "#e8f0fe", "border": "#4285f4",
         "items": ["• Topology Data", "• Traffic Matrix", "• Syslogs & Alerts", "• Telemetry Metrics"], "footer": ""},
        {"x": 2.5, "w": 1.9, "title": "1. Failure Observation\n& Detection", "color": "#e3f2fd", "border": "#1976d2",
         "items": ["• Anomaly detection", "• Failure localization", "• Affected SLAs isolated"], "footer": "Observed Failures"},
        {"x": 4.6, "w": 1.9, "title": "2. Causal Failure Graph\nConstruction", "color": "#e8f5e9", "border": "#388e3c",
         "items": ["• Causal discovery", "• Bayesian influence", "• Propagation model"], "footer": "Causal Graph G"},
        {"x": 6.7, "w": 2.0, "title": "3. Intervention Search\n(Minimum-Causal)", "color": "#f3e5f5", "border": "#7b1fa2",
         "items": ["• do(fi = 0), do(aj)", "• Causal impact ΔC", "• Combinatorial search"], "footer": "Candidate Set A*"},
        {"x": 8.9, "w": 1.9, "title": "4. Healing-Field\nPropagation", "color": "#fff8e1", "border": "#ffa000",
         "items": ["• Laplacian diffusion", "• Spatial stress relief", "• Digital twin sim."], "footer": "Healing Field H(a)"},
        {"x": 11.0, "w": 2.3, "title": "5. Risk-Constrained\nAction Selection", "color": "#e0f2f1", "border": "#00796b",
         "items": ["min [ |A| + λC + βR ]", "s.t. P(Frec|do) ≥ τ", "     Rpost ≤ Rmax"], "footer": "Healing Action A*"},
        {"x": 13.5, "w": 1.0, "title": "Self-Healed\nNetwork", "color": "#d4edda", "border": "#28a745",
         "items": ["✔ Restored", "✔ R ≤ Rmax", "✔ SLA Met"], "footer": "✔"}
    ]

    for st in stages:
        box = patches.FancyBboxPatch((st["x"], 5.8), st["w"], 3.0, boxstyle="round,pad=0.08,rounding_size=0.12",
                                     facecolor=st["color"], edgecolor=st["border"], linewidth=1.5)
        ax.add_patch(box)
        # Title
        ax.text(st["x"] + st["w"]/2, 8.4, st["title"], fontsize=9.5, fontweight="bold", ha="center", va="center", color="#111")
        # Line
        ax.plot([st["x"] + 0.1, st["x"] + st["w"] - 0.1], [8.0, 8.0], color=st["border"], linewidth=1)
        # Items
        y_text = 7.6
        for it in st["items"]:
            ax.text(st["x"] + 0.12, y_text, it, fontsize=8, ha="left", va="center", color="#222")
            y_text -= 0.35
        # Footer Pill
        if st["footer"]:
            pill = patches.FancyBboxPatch((st["x"] + 0.15, 5.95), st["w"] - 0.3, 0.45, boxstyle="round,pad=0.04,rounding_size=0.1",
                                          facecolor="white", edgecolor=st["border"], linewidth=1.2)
            ax.add_patch(pill)
            ax.text(st["x"] + st["w"]/2, 6.17, st["footer"], fontsize=8, fontweight="bold", ha="center", va="center", color=st["border"])

    # Connecting Arrows in Row 1
    for i in range(len(stages) - 1):
        x_start = stages[i]["x"] + stages[i]["w"]
        x_end = stages[i+1]["x"]
        ax.annotate("", xy=(x_end, 7.3), xytext=(x_start, 7.3),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=2, mutation_scale=15))

    # Lower Section: Autonomous Reasoning Substrate
    sub_bg = patches.FancyBboxPatch((0.5, 0.6), 14.0, 4.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    facecolor="#fafbfc", edgecolor="#90a4ae", linewidth=1.8, linestyle="--")
    ax.add_patch(sub_bg)

    # CIHF Module Container
    cihf_bg = patches.FancyBboxPatch((0.8, 2.5), 8.5, 2.7, boxstyle="round,pad=0.08,rounding_size=0.12",
                                     facecolor="#f8f9fa", edgecolor="#673ab7", linewidth=1.5)
    ax.add_patch(cihf_bg)
    ax.text(5.05, 4.95, "Causal Intervention Healing Field (CIHF) Algorithm", fontsize=11, fontweight="bold", ha="center", va="center", color="#4a148c")

    cihf_steps = [
        ("1. Identify Causes\n& Interventions", 1.0, "#e3f2fd", "#1976d2"),
        ("2. Compute Impact\n(ΔC, ΔR, P_rec)", 3.1, "#e8f5e9", "#388e3c"),
        ("3. Construct Field\nLaplacian H(a)", 5.2, "#f3e5f5", "#7b1fa2"),
        ("4. Optimize Action\nunder Risk Constraint", 7.3, "#fff3e0", "#f57c00")
    ]
    for title, x_pos, fc, ec in cihf_steps:
        sbox = patches.FancyBboxPatch((x_pos, 3.7), 1.8, 0.95, boxstyle="round,pad=0.05,rounding_size=0.08",
                                      facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(sbox)
        ax.text(x_pos + 0.9, 4.17, title, fontsize=8, fontweight="bold", ha="center", va="center")

    # Step arrows
    for i in range(len(cihf_steps)-1):
        x1 = cihf_steps[i][1] + 1.8
        x2 = cihf_steps[i+1][1]
        ax.annotate("", xy=(x2, 4.17), xytext=(x1, 4.17),
                    arrowprops=dict(arrowstyle="->", color="#673ab7", lw=1.8, mutation_scale=12))

    banner_step = patches.FancyBboxPatch((1.5, 2.75), 7.1, 0.55, boxstyle="round,pad=0.04,rounding_size=0.08",
                                         facecolor="#ede7f6", edgecolor="#673ab7", linewidth=1.0)
    ax.add_patch(banner_step)
    ax.text(5.05, 3.02, "Select intervention(s) with highest causal healing value and minimum cost under risk constraints",
            fontsize=8.5, fontweight="bold", ha="center", va="center", color="#311b92")

    # Risk Assessment Module
    ram_bg = patches.FancyBboxPatch((9.7, 2.5), 4.5, 2.7, boxstyle="round,pad=0.08,rounding_size=0.12",
                                    facecolor="#ffebee", edgecolor="#d32f2f", linewidth=1.5)
    ax.add_patch(ram_bg)
    ax.text(11.95, 4.95, "Risk Assessment Module", fontsize=11, fontweight="bold", ha="center", va="center", color="#b71c1c")
    ax.text(10.0, 4.3, "• Operational Risk: service disruption, rule churn", fontsize=8.5, ha="left", va="center")
    ax.text(10.0, 3.7, "• Propagation Risk: cascading spillover congestion", fontsize=8.5, ha="left", va="center")
    ax.text(10.0, 3.1, "• Global Risk Evaluation: verify R_post ≤ R_max", fontsize=8.5, ha="left", va="center")

    # Digital Twin
    dt_box = patches.FancyBboxPatch((0.8, 1.7), 13.4, 0.65, boxstyle="round,pad=0.05,rounding_size=0.08",
                                    facecolor="#e8eaf6", edgecolor="#3f51b5", linewidth=1.2)
    ax.add_patch(dt_box)
    ax.text(7.5, 2.02, "Digital Twin of Network:  What-if Simulation  |  Causal Reasoning  |  Predictive Risk  |  Healing Field Modeling",
            fontsize=9.5, fontweight="bold", ha="center", va="center", color="#1a237e")

    # Continuous Learning
    cl_box = patches.FancyBboxPatch((0.8, 0.85), 13.4, 0.65, boxstyle="round,pad=0.05,rounding_size=0.08",
                                    facecolor="#e0f7fa", edgecolor="#00838f", linewidth=1.2)
    ax.add_patch(cl_box)
    ax.text(7.5, 1.17, "Continuous Learning & Adaptation:  Update causal graph  |  Refine intervention policy  |  Adapt to topology drift",
            fontsize=9.5, fontweight="bold", ha="center", va="center", color="#006064")

    # Vertical connectors between pipeline and substrate
    for x_arr in [3.45, 5.55, 7.65, 9.85]:
        ax.annotate("", xy=(x_arr, 5.25), xytext=(x_arr, 5.8),
                    arrowprops=dict(arrowstyle="<->", color="#78909c", lw=1.5, mutation_scale=10))

    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated clean publication PNG: {png_path}")
    return png_path

if __name__ == "__main__":
    generate_drawio_xml()
    generate_clean_publication_png()
