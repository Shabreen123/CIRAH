import re

with open('manuscript/CIRAH_Journal_Paper.html', encoding='utf-8') as f:
    html = f.read()

checks = {
    'table-layout: fixed':   'table-layout: fixed' in html,
    'NO overflow-x: auto':   'overflow-x: auto' not in html,
    'NO overflow-x: scroll': 'overflow-x: scroll' not in html,
    'word-wrap on td/th':    'word-wrap: break-word' in html,
    'white-space: normal':   'white-space: normal' in html,
    'pre-wrap on code':      'white-space: pre-wrap' in html,
    'tbl-wrap class':        'tbl-wrap' in html,
    'Table 2a present':      'Table 2a' in html,
    'Table 5 present':       'Table 5' in html,
    'Table 6 present':       'Table 6' in html,
    'Table 7 present':       'Table 7' in html,
    'Table 8 present':       'Table 8' in html,
    'MathJax loaded':        'mathjax@3' in html,
    'Print button':          'Print / Save as PDF' in html,
    'A4 page size':          'size: A4' in html,
    'max-width 100%':        'max-width: 100%' in html,
    'Figure 1 injected':     'fig1_academic_architecture.png' in html,
    'Figure 9 injected':     'fig9_component_ablations.png' in html,
}

for name, ok in checks.items():
    print(f"  {'OK  ' if ok else 'FAIL'}: {name}")

tbls = len(re.findall(r'<table', html))
rows = len(re.findall(r'<tr>', html))
print(f"\n  Tables: {tbls}")
print(f"  Table rows: {rows}")
print(f"  File size: {len(html)//1024} KB")
print(f"  All checks passed: {all(checks.values())}")
