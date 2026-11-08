import zipfile, re

with zipfile.ZipFile(r'C:\Users\LENOVO\Downloads\splnproc2510.docm') as z:
    with z.open('word/styles.xml') as f:
        data = f.read().decode('utf-8')

names = re.findall(r'w:styleId="([^"]+)"', data)
print("STYLE IDs IN TEMPLATE:")
for n in sorted(set(names)):
    print(" ", n)
