"""
Converts CIRAH_Journal_Paper.md to a fully print-ready academic HTML paper.

Design goals:
- NO horizontal scrollbars. Every table fits within the A4 page width.
- All text wraps. No content ever overflows its container.
- Tables use font-size 8pt and word-wrap so they lay out like a real journal PDF.
- Equations rendered by MathJax (no scrolling, no overflow).
- Code blocks wrap or truncate gracefully.
- A single 'Print / Save as PDF' button. Everything else prints clean.
"""

import os
import re

MANUSCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(MANUSCRIPT_DIR, "CIRAH_Journal_Paper.md")
HTML_PATH = os.path.join(MANUSCRIPT_DIR, "CIRAH_Journal_Paper.html")


# ── helpers ────────────────────────────────────────────────────────────────

def inline_md(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def is_table_row(line: str) -> bool:
    """
    Return True only if this line is a genuine Markdown table row.
    Rules:
    - Must contain at least two | characters (pipe-delimited columns).
    - Must NOT be a line whose only | characters are inside $...$ math expressions.
    - Must NOT be a line starting with $ or $$ (display math that happens to contain |).
    """
    stripped = line.strip()
    if stripped.count('|') < 2:
        return False
    # If the line starts with $$ or $ it's a math equation, not a table
    if stripped.startswith('$$') or (stripped.startswith('$') and not stripped.startswith('$|')):
        return False
    # Remove content inside $...$ and $$...$$ to see if | remains
    no_math = re.sub(r'\$\$.*?\$\$', '', stripped, flags=re.DOTALL)
    no_math = re.sub(r'\$[^$\n]+?\$', '', no_math)
    return no_math.count('|') >= 2


def parse_table_row(line: str):
    """Return list of cell strings from a Markdown table row."""
    cells = line.split('|')
    # Strip leading/trailing empty segments from outer pipes
    if cells and cells[0].strip() == '':
        cells = cells[1:]
    if cells and cells[-1].strip() == '':
        cells = cells[:-1]
    return [c.strip() for c in cells]


def build_figure_html(fig_id, img_name, caption, width_pct=95):
    return (
        f'<figure class="fig" id="{fig_id}">'
        f'<img src="../figures/{img_name}" alt="{caption}" '
        f'style="max-width:{width_pct}%;">'
        f'<figcaption>{inline_md(caption)}</figcaption>'
        f'</figure>\n'
    )


# ── main converter ──────────────────────────────────────────────────────────

def convert(md_text: str) -> str:
    lines = md_text.splitlines()
    parts = []          # list of HTML strings
    in_code  = False
    in_table = False
    in_ul    = False
    in_ol    = False
    code_buf = []
    tbl_rows = []       # (is_header: bool, cells: list[str])
    tbl_header_done = False

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            parts.append('</ul>')
            in_ul = False
        if in_ol:
            parts.append('</ol>')
            in_ol = False

    def flush_table():
        nonlocal in_table, tbl_rows, tbl_header_done
        if not in_table:
            return
        parts.append('<div class="tbl-wrap"><table>')
        for is_hdr, cells in tbl_rows:
            tag = 'th' if is_hdr else 'td'
            row_html = '<tr>' + ''.join(
                f'<{tag}>{inline_md(c)}</{tag}>' for c in cells
            ) + '</tr>'
            parts.append(row_html)
        parts.append('</table></div>')
        in_table = False
        tbl_rows = []
        tbl_header_done = False

    for raw in lines:
        line = raw.rstrip()

        # ── code fence ────────────────────────────────────────────────────
        if line.strip().startswith('```'):
            if in_code:
                in_code = False
                escaped = '\n'.join(code_buf).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                parts.append(f'<pre><code>{escaped}</code></pre>')
                code_buf = []
            else:
                flush_list()
                flush_table()
                in_code = True
                code_buf = []
            continue
        if in_code:
            code_buf.append(line)
            continue

        # ── table ─────────────────────────────────────────────────────────
        if is_table_row(line):
            flush_list()
            if bool(re.match(r'^\s*\|?[\s\-:|]+\|[\s\-:|]+', line.strip())):
                # Separator row — next rows are body rows
                tbl_header_done = True
                continue
            cells = parse_table_row(line)
            if not in_table:
                in_table = True
                tbl_header_done = False
            is_hdr = not tbl_header_done
            tbl_rows.append((is_hdr, cells))
            continue
        else:
            flush_table()

        stripped = line.strip()

        # ── blank line ────────────────────────────────────────────────────
        if not stripped:
            flush_list()
            continue

        # ── hr ────────────────────────────────────────────────────────────
        if stripped in ('---', '***', '___'):
            flush_list()
            parts.append('<hr>')
            continue

        # ── headings ──────────────────────────────────────────────────────
        m = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if m:
            flush_list()
            level = len(m.group(1))
            text  = inline_md(m.group(2))
            cls   = {1: 'h-paper', 2: 'h-sec', 3: 'h-sub', 4: 'h-subsub'}[level]
            parts.append(f'<h{level} class="{cls}">{text}</h{level}>')
            continue

        # ── blockquote ────────────────────────────────────────────────────
        if stripped.startswith('>'):
            flush_list()
            content = inline_md(stripped.lstrip('> '))
            parts.append(f'<blockquote>{content}</blockquote>')
            continue

        # ── unordered list ────────────────────────────────────────────────
        if re.match(r'^[\*\-]\s+', stripped):
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            if not in_ul:
                parts.append('<ul>')
                in_ul = True
            content = inline_md(re.sub(r'^[\*\-]\s+', '', stripped))
            parts.append(f'<li>{content}</li>')
            continue

        # ── ordered list ──────────────────────────────────────────────────
        if re.match(r'^\d+\.\s+', stripped):
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if not in_ol:
                parts.append('<ol>')
                in_ol = True
            content = inline_md(re.sub(r'^\d+\.\s+', '', stripped))
            parts.append(f'<li>{content}</li>')
            continue

        # ── normal paragraph ──────────────────────────────────────────────
        flush_list()
        parts.append(f'<p>{inline_md(line)}</p>')

    flush_list()
    flush_table()

    body = '\n'.join(parts)

    # ── inline figure injections ──────────────────────────────────────────
    figs = [
        ('h-sub">3.1 End', 'fig1', 'fig1_academic_architecture.png',
         'Figure 1. CIRAH three-tier architecture: Tier 1 (Telemetry & Observation), '
         'Tier 2 (Cognitive Causal Optimization), Tier 3 (Digital Twin Adaptation).', 98),
        ('h-sub">5.1 Multi', 'fig5', 'fig5_success_vs_severity.png',
         'Figure 5. Recovery success rate across k = 0–4 simultaneous link failures '
         'on the Abilene topology (N = 50 runs, 95 % CI).', 88),
        ('h-sub">5.2 Control', 'fig7', 'fig7_switches_modified_footprint.png',
         'Figure 7. Mean switches modified per recovery across all compared methods '
         'at k = 1, 2, 3 failures.', 88),
        ('h-sub">5.3 Telemetry', 'fig8_fig10', None,
         None, 88),   # two figures — handled separately below
        ('h-sub">5.4 Rebuilt', 'fig9', 'fig9_component_ablations.png',
         'Figure 9. Six-way ablation results: success rate, residual risk, switch churn, '
         'and intervention cost.', 95),
    ]

    for marker, fid, img, cap, w in figs:
        if img is None:
            # Special: insert fig8 + fig10 together
            f8 = build_figure_html('fig8', 'fig8_residual_risk_bound.png',
                'Figure 8. Post-recovery residual risk across failure severities '
                'versus the hard ceiling R_max = 35.0.', 88)
            f10 = build_figure_html('fig10', 'fig10_telemetry_noise_resilience.png',
                'Figure 10. Recovery success under telemetry measurement noise '
                '(sigma_noise = 0.0–0.30) for Bayesian SCM vs. rule-based diagnosis.', 88)
            inject = f8 + f10
        else:
            inject = build_figure_html(fid, img, cap, w)

        tag_str = f'class="{marker}'
        idx = body.find(tag_str)
        if idx != -1:
            end_tag = body.find('>', idx)
            insert_after = body.find('\n', end_tag)
            if insert_after == -1:
                insert_after = end_tag + 1
            body = body[:insert_after] + '\n' + inject + body[insert_after:]

    return body


# ── CSS ────────────────────────────────────────────────────────────────────

CSS = """
/* ── Reset & base ────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

@page {
    size: A4;
    margin: 22mm 18mm 20mm 18mm;
}

html, body {
    margin: 0;
    padding: 0;
    background: #eaecef;
    font-family: "Times New Roman", Times, serif;
    font-size: 10pt;
    color: #111;
    line-height: 1.45;
}

/* ── Paper sheet (visible in browser, transparent on print) ── */
.page {
    max-width: 800px;
    margin: 28px auto 48px;
    background: #fff;
    padding: 54px 60px;
    box-shadow: 0 2px 18px rgba(0,0,0,.10);
}

/* ── Print button ─────────────────────────────────────── */
.print-btn {
    position: fixed;
    bottom: 28px;
    right: 28px;
    background: #003366;
    color: #fff;
    font-family: system-ui, sans-serif;
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 11px 20px;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(0,0,40,.30);
    z-index: 9999;
}
.print-btn:hover { background: #002255; }

/* ── Typography ───────────────────────────────────────── */
.h-paper {
    font-size: 17pt;
    font-weight: bold;
    text-align: center;
    line-height: 1.25;
    margin: 0 0 14px;
    color: #0a1628;
}
.h-sec {
    font-size: 12pt;
    font-weight: bold;
    color: #003366;
    border-bottom: 1px solid #003366;
    padding-bottom: 2px;
    margin: 26px 0 9px;
    page-break-after: avoid;
}
.h-sub {
    font-size: 10.5pt;
    font-weight: bold;
    margin: 16px 0 5px;
    page-break-after: avoid;
}
.h-subsub {
    font-size: 10pt;
    font-weight: bold;
    font-style: italic;
    margin: 12px 0 4px;
    page-break-after: avoid;
}
p {
    margin: 0 0 8px;
    text-align: justify;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
blockquote {
    border-left: 3px solid #003366;
    margin: 10px 0 10px 8px;
    padding: 4px 12px;
    font-style: italic;
    color: #333;
}
ul, ol {
    margin: 4px 0 8px 20px;
    padding: 0;
}
li {
    margin-bottom: 3px;
    text-align: justify;
    word-wrap: break-word;
}
strong { font-weight: bold; }
em     { font-style: italic; }
code   {
    font-family: "Courier New", monospace;
    font-size: 8.5pt;
    background: #f4f6f9;
    padding: 1px 3px;
    border-radius: 2px;
}
hr {
    border: none;
    border-top: 0.5pt solid #bbb;
    margin: 18px 0;
}

/* ── Tables  — THE KEY FIX ───────────────────────────── */
/*
   Tables must fit within the column. Fixed layout + word-wrap.
*/
.tbl-wrap {
    width: 100%;
    margin: 16px 0;
    page-break-inside: avoid;
}
table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;          /* FIXED layout: columns share width evenly */
    font-size: 8pt;
    line-height: 1.30;
    border-top: 1.5pt solid #111;
    border-bottom: 1.5pt solid #111;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
th {
    font-weight: bold;
    padding: 5px 6px;
    border-bottom: 1pt solid #111;
    text-align: left;
    background: #f7f8fa;
    word-wrap: break-word;
    overflow-wrap: break-word;
    vertical-align: top;
}
td {
    padding: 4px 6px;
    border-bottom: 0.4pt solid #ddd;
    vertical-align: top;
    word-wrap: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
}
/* Wider tables: let the browser wrap freely */
th, td {
    white-space: normal !important;
}

/* ── Figures ──────────────────────────────────────────── */
figure.fig {
    text-align: center;
    margin: 20px 0;
    page-break-inside: avoid;
}
figure.fig img {
    max-width: 100%;
    height: auto;
    border: 1px solid #ddd;
}
figcaption {
    font-size: 8.5pt;
    color: #333;
    margin-top: 6px;
    line-height: 1.35;
    padding: 0 10px;
}

/* ── Code / Algorithm blocks ──────────────────────────── */
pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 7.8pt;
    line-height: 1.35;
    background: #f8fafc;
    border: 1px solid #dce1e8;
    border-left: 3px solid #003366;
    padding: 9px 12px;
    margin: 12px 0;
    page-break-inside: avoid;
    white-space: pre-wrap;       /* wrap long lines instead of scrolling */
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* ── Print overrides ──────────────────────────────────── */
@media print {
    html, body { background: #fff; font-size: 9.5pt; }
    .page {
        max-width: 100%;
        width: 100%;
        margin: 0;
        padding: 0;
        box-shadow: none;
    }
    .print-btn { display: none !important; }
    .h-sec, .h-sub, .h-subsub { page-break-after: avoid; }
    figure.fig, .tbl-wrap, pre { page-break-inside: avoid; }
    a { color: #000; text-decoration: none; }
}
"""


# ── HTML template ───────────────────────────────────────────────────────────

def wrap_html(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$','$'],['\\\\(','\\\\)']],
    displayMath: [['$$','$$'],['\\\\[','\\\\]']],
    processEscapes: true,
    tags: 'ams'
  }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre'] }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>
<style>{CSS}</style>
</head>
<body>

<button class="print-btn" onclick="window.print()">&#128438; Print / Save as PDF</button>

<div class="page">
{body}
</div>

</body>
</html>"""


# ── entry point ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md = f.read()

    body = convert(md)
    title = 'CIRAH: Minimum-Causal-Intervention Optimization for Risk-Constrained Autonomous Network Self-Healing'
    html = wrap_html(body, title)

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Academic paper successfully generated at: {HTML_PATH}')
