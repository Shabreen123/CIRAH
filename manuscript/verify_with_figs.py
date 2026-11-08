import zipfile, re, os

fname = "manuscript/CIRAH_Springer_WithFigs.docm"
with zipfile.ZipFile(fname) as z:
    parts    = z.namelist()
    doc      = z.read("word/document.xml")
    rels     = z.read("word/_rels/document.xml.rels").decode()
    media    = [p for p in parts if p.startswith("word/media/")]
    media_sizes = {m: len(z.read(m)) // 1024 for m in media}

print(f"File size        : {os.path.getsize(fname)//1024} KB")
print(f"ZIP parts        : {len(parts)}")
print(f"Embedded media   : {len(media)}")
for m, kb in media_sizes.items():
    print(f"  {m}  ({kb} KB)")

rIds = re.findall(r'Id="(rImgId\d+)"', rels)
refs_in_doc = re.findall(rb'r:embed="(rImgId\d+)"', doc)
print(f"\nImage rIds in rels: {rIds}")
print(f"Image refs in doc : {[r.decode() for r in refs_in_doc]}")

springer = {"papertitle","author","abstract","heading1","heading2","heading3",
            "Normal","tablecaption","figurecaption","referenceitem","numitem",
            "programcode","keywords"}
used_str = {s.decode() for s in re.findall(rb'w:val="([^"]+)"', doc)}
found = springer & used_str
missing = springer - used_str
print(f"\nSpringer styles   : {len(found)}/{len(springer)} present")
if missing: print(f"  MISSING: {missing}")
print(f"Has VBA macro     : {'word/vbaProject.bin' in parts}")
print(f"Has Springer UI   : {any('customUI' in p for p in parts)}")
all_ok = (len(media) == len(rIds) == len(refs_in_doc) and len(found) == len(springer))
print(f"\nReady to open in Word: {'YES' if all_ok else 'CHECK WARNINGS ABOVE'}")
