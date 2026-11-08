import zipfile

with zipfile.ZipFile('manuscript/CIRAH_FINAL_Springer.docm') as z:
    parts = z.namelist()
    doc_xml = z.read('word/document.xml')
    styles  = z.read('word/styles.xml')

print(f"Total parts in ZIP:   {len(parts)}")
print(f"word/document.xml:    {len(doc_xml)//1024} KB")
print(f"word/styles.xml:      {len(styles)//1024} KB")
print(f"Has vbaProject.bin:   {'word/vbaProject.bin' in parts}")
print(f"Has customUI:         {any('customUI' in p for p in parts)}")
print(f"Has header1.xml:      {'word/header1.xml' in parts}")

# Quick sanity: does document.xml mention our styles?
import re
style_ids = re.findall(rb'w:val="([^"]+)"', doc_xml)
unique_styles = set(s.decode() for s in style_ids)
springer_styles = {'papertitle','author','abstract','heading1','heading2','heading3',
                   'Normal','tablecaption','figurecaption','referenceitem',
                   'numitem','programcode','keywords'}
found = springer_styles & unique_styles
print(f"\nSpringer styles used: {len(found)}/{len(springer_styles)}")
for s in sorted(found):
    print(f"  OK: {s}")
missing = springer_styles - unique_styles
if missing:
    for s in sorted(missing):
        print(f"  MISSING: {s}")
else:
    print("All expected Springer styles present.")
