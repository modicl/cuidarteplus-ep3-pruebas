import os, re, html, glob
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "evidencia", "cp25"); IMG = os.path.join(OUT, "img")
def shot(pg, name, title, lines, width=1150):
    body = "\n".join(html.escape(l[:150]) for l in lines)
    pg.set_content("<body style='margin:0;background:#0c0c0c'><div id=t style='width:%dpx;box-sizing:border-box;color:#ccc;font:13px Consolas,monospace;padding:12px'><div style='color:#16c60c;margin-bottom:8px'>%s</div><pre style='margin:0;white-space:pre-wrap'>%s</pre></div></body>" % (width, html.escape(title), body))
    pg.locator("#t").screenshot(path=os.path.join(IMG, name))
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1150, "height": 600}, device_scale_factor=3); pg = ctx.new_page()
    for log in sorted(glob.glob(os.path.join(OUT, "*.log"))):
        name = os.path.basename(log)[:-4]
        txt = open(log, encoding="utf8").read(); first = txt.splitlines()[0]
        lines = [l for l in re.sub(r"\x1b\[[0-9;]*m", "", txt).splitlines()[1:] if l.strip()]
        start = next((i for i, l in enumerate(lines) if "THRESHOLDS" in l), max(0, len(lines) - 55))
        script = re.search(r"/work/k6/(\S+)", first).group(1); cpus = re.search(r"--cpus (\S+)", first).group(1)
        shot(pg, name + "_cli.png", "$ docker run --rm --network cuidarteplus-network --cpus %s --memory 4g grafana/k6 run %s   (%s)" % (cpus, script, name), lines[start:start + 58])
    lh = [l[:150] for l in open(os.path.join(OUT, "lh", "parte_d.log"), encoding="utf8").read().splitlines() if l.strip()]
    shot(pg, "lighthouse_cli.png", "$ python parte_d.py   (Lighthouse 13.5.0, móvil, 4G 1,6 Mbps / 150 ms, caché vacía, 5 repeticiones)", lh)
    b.close()
print(sorted(os.listdir(IMG)))
