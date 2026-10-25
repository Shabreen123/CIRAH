"""
Converts CIRAH_Journal_Paper.md to a publication-grade academic HTML paper
formatted strictly for A4 print/PDF export with:
- NO artificial publisher headers or "pre-proof" watermarks
- Clean academic serif font (Times New Roman, 10pt body, 1.4 line-height)
- Figures placed IN-LINE directly within their respective sections
- Proper academic table formatting (Elsevier three-line table standard)
- Pure print CSS with page-break-inside: avoid on figures, tables, and algorithms.
"""

import os
import re

MANUSCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(MANUSCRIPT_DIR, "CIRAH_Journal_Paper.md")
HTML_PATH = os.path.join(MANUSCRIPT_DIR, "CIRAH_Journal_Paper.html")
FIGURES_DIR = os.path.abspath(os.path.join(MANUSCRIPT_DIR, "..", "figures"))

def build_figure_html(fig_id: str, img_name: str, caption: str, width_pct: int = 90) -> str:
    return f"""
    <div class="figure-container" id="{fig_id}">
        <img src="../figures/{img_name}" alt="{caption}" style="max-width:{width_pct}%;">
        <div class="figure-caption"><strong>{caption.split('.')[0]}.</strong> {'.'.join(caption.split('.')[1:])}</div>
    </div>
    """

def markdown_to_academic_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_lines = []
    in_table = False
    in_list = False
    in_code = False
    code_block = []

    for line in lines:
        stripped = line.strip()

        # Handle Code blocks
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                content = "\n".join(code_block)
                html_lines.append(f"<pre><code>{content}</code></pre>")
                code_block = []
            else:
                in_code = True
                code_block = []
            continue

        if in_code:
            code_block.append(line)
            continue

        # Handle Tables
        if "|" in line:
            if not in_table:
                in_table = True
                html_lines.append('<div class="table-container"><table class="academic-table">')
            
            # Skip separator line |:---|:---|
            if re.match(r'^\s*\|?\s*[-:]+[-| :]*$', line):
                continue
            
            cells = [c.strip() for c in line.split("|")]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]

            is_header = False
            last_text = "".join(html_lines[-4:])
            if "<th" not in last_text and ("Table" in last_text or "Severity" in line or "Approach" in line or "Metric" in line or "Ablation" in line):
                is_header = True

            tag = "th" if is_header else "td"
            cell_html = "".join([f"<{tag}>{c}</{tag}>" for c in cells])
            html_lines.append(f"<tr>{cell_html}</tr>")
            continue
        else:
            if in_table:
                html_lines.append("</table></div>")
                in_table = False

        # Handle Headings
        if stripped.startswith("# "):
            html_lines.append(f'<h1 class="paper-title">{stripped[2:]}</h1>')
            continue
        elif stripped.startswith("## "):
            html_lines.append(f'<h2 class="section-title">{stripped[3:]}</h2>')
            continue
        elif stripped.startswith("### "):
            html_lines.append(f'<h3 class="subsection-title">{stripped[4:]}</h3>')
            continue
        elif stripped.startswith("#### "):
            html_lines.append(f'<h4 class="subsubsection-title">{stripped[5:]}</h4>')
            continue

        # Handle Lists
        if stripped.startswith("* ") or stripped.startswith("- "):
            if not in_list:
                in_list = True
                html_lines.append('<ul class="academic-list">')
            content = stripped[2:]
            html_lines.append(f"<li>{content}</li>")
            continue
        elif re.match(r'^\d+\.\s+', stripped):
            if not in_list:
                in_list = True
                html_lines.append('<ol class="academic-list">')
            content = re.sub(r'^\d+\.\s+', '', stripped)
            html_lines.append(f"<li>{content}</li>")
            continue
        else:
            if in_list:
                html_lines.append("</ul>" if "<ul" in html_lines[-2] else "</ol>")
                in_list = False

        if not stripped:
            continue

        if stripped in ["---", "***", "___"]:
            html_lines.append("<hr class='divider'/>")
            continue

        # Regular paragraphs
        html_lines.append(f"<p>{line}</p>")

    if in_table:
        html_lines.append("</table></div>")
    if in_list:
        html_lines.append("</ul>")

    body_content = "\n".join(html_lines)

    # Clean markdown formatting
    body_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_content)
    body_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', body_content)

    # IN-LINE FIGURE INSERTIONS: Place each figure directly after its relevant section/paragraph
    # 1. Figure 1: Academic Architecture Diagram (Section 3.1)
    fig1_html = build_figure_html(
        "fig1", "fig1_academic_architecture.png",
        "Figure 1. Architectural blueprint of the CIRAH framework showing the 3 operational tiers: Telemetry & Observation (Tier 1), Cognitive Causal Optimization Substrate (Tier 2), and Digital Twin Closed-Loop Adaptation (Tier 3).",
        width_pct=98
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">3.1 End-to-End System Architecture</h3>',
        f'<h3 class="subsection-title">3.1 End-to-End System Architecture</h3>\n{fig1_html}'
    )

    # 2. Figure 5: Success vs Severity (Section 5.1)
    fig5_html = build_figure_html(
        "fig5", "fig5_success_vs_severity.png",
        "Figure 5. Recovery success rate across concurrent multi-link failure severities (k = 0 to 4) on the Abilene topology with 95% confidence intervals.",
        width_pct=85
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">5.1 Multi-Failure Severity Evaluation (RQ1, RQ3)</h3>',
        f'<h3 class="subsection-title">5.1 Multi-Failure Severity Evaluation (RQ1, RQ3)</h3>\n{fig5_html}'
    )

    # 3. Figure 7: Switches Modified Footprint (Section 5.2)
    fig7_html = build_figure_html(
        "fig7", "fig7_switches_modified_footprint.png",
        "Figure 7. Control-plane reconfiguration footprint: average number of switches modified during recovery across comparative methods under k = 1, 2, 3 cuts.",
        width_pct=85
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">5.2 Control-Plane Churn and Intervention Footprint (RQ2)</h3>',
        f'<h3 class="subsection-title">5.2 Control-Plane Churn and Intervention Footprint (RQ2)</h3>\n{fig7_html}'
    )

    # 4. Figure 10: Telemetry Noise Resilience (Section 5.3)
    fig10_html = build_figure_html(
        "fig10", "fig10_telemetry_noise_resilience.png",
        "Figure 10. Robustness to telemetry measurement noise (sigma_noise in [0.0, 0.30]) comparing Bayesian SCM against brittle correlation-based heuristics.",
        width_pct=85
    )
    # Also Figure 8: Residual Risk Bound (Section 5.3)
    fig8_html = build_figure_html(
        "fig8", "fig8_residual_risk_bound.png",
        "Figure 8. Residual post-recovery risk R_post across failure severities evaluated against the hard constraint ceiling R_max = 35.0.",
        width_pct=85
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">5.3 Telemetry Noise Robustness (RQ3)</h3>',
        f'<h3 class="subsection-title">5.3 Telemetry Noise Robustness (RQ3)</h3>\n{fig8_html}\n{fig10_html}'
    )

    # 5. Figure 9: Component Ablation Study (Section 5.4)
    fig9_html = build_figure_html(
        "fig9", "fig9_component_ablations.png",
        "Figure 9. Four-panel component ablation breakdown comparing Full CIRAH against noCausal, noRisk, and noInterv variants under k = 2 failures.",
        width_pct=92
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">5.4 Component-Level Ablation Study (RQ4)</h3>',
        f'<h3 class="subsection-title">5.4 Component-Level Ablation Study (RQ4)</h3>\n{fig9_html}'
    )

    # 6. Figure 11: Gamma Parameter Sensitivity (Section 5.5)
    fig11_html = build_figure_html(
        "fig11", "fig11_gamma_sensitivity.png",
        "Figure 11. Hyperparameter sensitivity of the healing-field weight parameter gamma on switch churn and aggregate healing gain Psi(a).",
        width_pct=85
    )
    fig6_html = build_figure_html(
        "fig6", "fig6_latency_loss_stress.png",
        "Figure 6. Dual-panel evaluation of (a) end-to-end latency and (b) packet loss across increasing traffic and link stress levels (rho in [0.1, 0.9]).",
        width_pct=95
    )
    body_content = body_content.replace(
        '<h3 class="subsection-title">5.5 Hyperparameter Sensitivity (gamma and R_max)</h3>',
        f'<h3 class="subsection-title">5.5 Hyperparameter Sensitivity (gamma and R_max)</h3>\n{fig6_html}\n{fig11_html}'
    )

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing</title>

<!-- MathJax 3 for rendering publication-quality LaTeX equations -->
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true
  }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>

<style>
/* Academic Publication Styling - Standard Elsevier / IEEE Format */
@page {{
    size: A4;
    margin: 25mm 20mm 20mm 20mm;
    @bottom-center {{
        content: counter(page);
        font-family: "Times New Roman", Times, serif;
        font-size: 9pt;
    }}
}}

body {{
    font-family: "Times New Roman", Times, "Nimbus Roman No9 L", serif;
    font-size: 10pt;
    line-height: 1.42;
    color: #111111;
    background-color: #f0f2f5;
    margin: 0;
    padding: 0;
}}

/* Floating print button: visible in browser, completely hidden on paper print */
.floating-print-btn {{
    position: fixed;
    top: 20px;
    right: 25px;
    z-index: 9999;
    background-color: #003366;
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    font-weight: 600;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    cursor: pointer;
    transition: background-color 0.2s ease;
}}
.floating-print-btn:hover {{
    background-color: #002244;
}}

.paper-sheet {{
    max-width: 840px;
    margin: 30px auto;
    background: #ffffff;
    padding: 60px 70px;
    box-shadow: 0 2px 14px rgba(0,0,0,0.08);
    box-sizing: border-box;
}}

/* Title and Authors */
.paper-title {{
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    line-height: 1.25;
    margin-top: 0;
    margin-bottom: 16px;
    color: #0a192f;
}}

p:first-of-type {{
    text-align: center;
    font-size: 10.5pt;
    margin-bottom: 6px;
}}

p:nth-of-type(2) {{
    text-align: center;
    font-size: 9.5pt;
    font-style: italic;
    color: #333333;
    margin-bottom: 24px;
}}

/* Highlights Box */
.section-title:first-of-type {{
    margin-top: 20px;
}}

.section-title {{
    font-size: 12.5pt;
    font-weight: bold;
    color: #003366;
    border-bottom: 1px solid #003366;
    padding-bottom: 3px;
    margin-top: 28px;
    margin-bottom: 10px;
    page-break-after: avoid;
}}

.subsection-title {{
    font-size: 11pt;
    font-weight: bold;
    color: #1a202c;
    margin-top: 18px;
    margin-bottom: 6px;
    page-break-after: avoid;
}}

.subsubsection-title {{
    font-size: 10pt;
    font-weight: bold;
    font-style: italic;
    color: #2d3748;
    margin-top: 14px;
    margin-bottom: 4px;
    page-break-after: avoid;
}}

p {{
    text-align: justify;
    text-justify: inter-word;
    margin-top: 0;
    margin-bottom: 9px;
}}

ul.academic-list, ol.academic-list {{
    margin-top: 4px;
    margin-bottom: 10px;
    padding-left: 24px;
}}
ul.academic-list li, ol.academic-list li {{
    margin-bottom: 4px;
    text-align: justify;
}}

/* Academic Tables - Three Line Format */
.table-container {{
    margin: 20px 0;
    page-break-inside: avoid;
    overflow-x: auto;
}}
.academic-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    line-height: 1.3;
    border-top: 1.5pt solid #111111;
    border-bottom: 1.5pt solid #111111;
}}
.academic-table th {{
    font-weight: bold;
    color: #111111;
    padding: 6px 8px;
    border-bottom: 1pt solid #111111;
    text-align: left;
    background-color: #fafafa;
}}
.academic-table td {{
    padding: 5px 8px;
    border-bottom: 0.5pt solid #e2e8f0;
}}

/* Figures: In-line, bordered, centered */
.figure-container {{
    text-align: center;
    margin: 22px auto;
    page-break-inside: avoid;
}}
.figure-container img {{
    border: 1px solid #dcdcdc;
    border-radius: 2px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}}
.figure-caption {{
    font-size: 8.5pt;
    color: #333333;
    margin-top: 6px;
    line-height: 1.35;
    padding: 0 15px;
}}

/* Pre / Code Blocks */
pre {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #003366;
    padding: 10px 14px;
    font-family: "Courier New", Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.35;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 14px 0;
}}

hr.divider {{
    border: 0;
    height: 0.5pt;
    background: #ccc;
    margin: 20px 0;
}}

/* Print Media Rules */
@media print {{
    body {{
        background: #ffffff !important;
        font-size: 9.5pt;
    }}
    .paper-sheet {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
    }}
    .no-print, .floating-print-btn {{
        display: none !important;
    }}
    .section-title, .subsection-title, .subsubsection-title {{
        page-break-after: avoid !important;
    }}
    .figure-container, .table-container, pre {{
        page-break-inside: avoid !important;
    }}
}}
</style>
</head>
<body>

<button class="floating-print-btn no-print" onclick="window.print()">🖨️ Save as PDF / Print</button>

<div class="paper-sheet">
{body_content}
</div>

</body>
</html>
"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"Academic paper successfully generated at: {HTML_PATH}")
    return HTML_PATH

if __name__ == "__main__":
    with open(MD_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    markdown_to_academic_html(text)
