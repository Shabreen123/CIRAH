import re

with open('manuscript/CIRAH_Springer.html', encoding='utf-8') as f:
    html = f.read()

checks = {
    'Springer title block (spr-title)':  'spr-title' in html,
    'Author block (spr-authors)':        'spr-authors' in html,
    'Affiliation block (spr-affil)':     'spr-affil' in html,
    'Abstract section':                   'Abstract.' in html,
    'Keywords line':                      'Keywords:' in html,
    'Numbered section 1 Introduction':   '>1 &nbsp;Introduction<' in html,
    'Numbered section 2 Lit Review':     '>2 &nbsp;Literature Review<' in html,
    'Numbered section 3 Methodology':   '>3 &nbsp;The CIRAH Framework<' in html,
    'Numbered section 4 Experiment':     '>4 &nbsp;Experimental Setup<' in html,
    'Numbered section 5 Results':        '>5 &nbsp;Experimental Results<' in html,
    'Numbered section 6 Discussion':     '>6 &nbsp;Discussion<' in html,
    'Numbered section 7 Threats':        '>7 &nbsp;Threats to Validity<' in html,
    'Numbered section 8 Conclusion':     '>8 &nbsp;Conclusion<' in html,
    'References section':                '>References<' in html,
    'Algorithm 1 present':               'Algorithm 1' in html,
    'Table 1 comparison':                'Table 1.' in html,
    'Table 2 Abilene results':           'Table 2.' in html,
    'Table 3 Ablation':                  'Table 3.' in html,
    'Table 4 Hypothesis tests':          'Table 4.' in html,
    'Table 5 Constrained baseline':      'Table 5.' in html,
    'Table 6 Risk sensitivity':          'Table 6.' in html,
    'Table 2a Parameters':               'Table 2a.' in html,
    'MathJax loaded':                    'mathjax@3' in html,
    'Print button':                      'Print / Save as PDF' in html,
    'A4 page size':                      'size: A4' in html,
    'table-layout fixed':                'table-layout: fixed' in html,
    'NO overflow-x: auto':               'overflow-x: auto' not in html,
    'word-wrap on cells':                'word-wrap: break-word' in html,
    'white-space: normal':               'white-space: normal' in html,
    'Figure 1 (architecture)':           'fig1_academic_architecture.png' in html,
    'Figure 2 (success vs severity)':    'fig5_success_vs_severity.png' in html,
    'Figure 3 (noise resilience)':       'fig10_telemetry_noise_resilience.png' in html,
    'Figure 4 (ablation)':               'fig9_component_ablations.png' in html,
}

all_ok = True
for name, ok in checks.items():
    print(f"  {'OK  ' if ok else 'FAIL'}: {name}")
    if not ok:
        all_ok = False

tbls = len(re.findall(r'<table', html))
print(f"\n  Tables: {tbls}")
print(f"  File size: {len(html)//1024} KB")
print(f"\n  ALL CHECKS PASSED: {all_ok}")
