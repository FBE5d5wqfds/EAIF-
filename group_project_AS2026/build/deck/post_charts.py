"""Per-point and per-series chart styling that pptxgenjs cannot write: run after build_deck.js on the finished .pptx."""
import sys, zipfile, shutil, os
path = sys.argv[1]
DPT = '<c:dPt><c:idx val="{i}"/><c:invertIfNegative val="0"/><c:bubble3D val="0"/><c:spPr><a:solidFill><a:srgbClr val="FAC300"/></a:solidFill></c:spPr></c:dPt>'
def series(xml):
    parts = xml.split('<c:ser>'); return parts[0], parts[1:]
def highlight_point(xml, ser_idx, pt_idx):
    head, sers = series(xml); s = sers[ser_idx]; k = '<c:invertIfNegative val="0"/>'
    assert s.count(k) == 1; sers[ser_idx] = s.replace(k, k + DPT.format(i=pt_idx)); return head + ''.join('<c:ser>' + x for x in sers)
def line_style(xml, ser_idx, dash=None, width=None):
    head, sers = series(xml); s = sers[ser_idx]
    if dash: assert '<a:prstDash val="solid"/>' in s; s = s.replace('<a:prstDash val="solid"/>', f'<a:prstDash val="{dash}"/>', 1)
    if width: assert 'w="25400"' in s; s = s.replace('w="25400"', f'w="{width}"', 1)
    sers[ser_idx] = s; return head + ''.join('<c:ser>' + x for x in sers)
tmp = path + ".tmp"
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith("ppt/charts/chart") and item.filename.endswith(".xml"):
            x = data.decode("utf-8")
            if "Naive mean (baseline)" in x: x = highlight_point(x, 2, 0)          # slide 4: naive forecast's test bar
            elif "Formation years from 2021" in x: x = highlight_point(x, 1, 2)    # slide 5: Europe, from 2021
            elif "<c:lineChart>" in x: x = line_style(line_style(x, 1, dash="dash"), 3, width=38100)  # slide 6
            data = x.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, path); print("charts styled")
