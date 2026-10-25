import os, re, html, sys
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.abspath(__file__)); EVD=os.path.join(ROOT,"evidencia")
SRC={"CP-14":"CP-14.txt","CP-15":"CP-15.txt","CP-16":"CP-16.txt","CP-19":os.path.join("newman","resumen_cp19.txt"),"CP-20":"CP-20.txt","CP-21":os.path.join("tls","testssl_3443.txt"),"CP-22":"CP-22.txt","CP-23":"CP-23.txt"}
def pick(case,lines):
    if case=="CP-19": return [l for l in lines if l.startswith(("FALLA","Operaciones","Vectores","Pruebas","Respuestas"))][:40]
    if case=="CP-21": return [l for l in lines if re.search(r"SSLv|TLS 1|HSTS|Strict|Chain of trust|Overall|Grade",l)][:16]
    out=[]
    for i,l in enumerate(lines):
        if l.startswith("### "): out.append(l); out+= [x for x in lines[i+1:i+3] if x.strip() and not x.startswith("###")]
    return out[:42]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1100,"height":800})
    for case,f in SRC.items():
        lines=open(os.path.join(EVD,f),encoding="utf8").read().splitlines()
        sel=[l[:150] for l in pick(case,lines)]
        body="\n".join(html.escape(l) for l in sel)
        pg.set_content(f"<body style='margin:0;background:#1e1e1e'><div style='color:#d4d4d4;font:12px Consolas,monospace;padding:10px'><div style='color:#9cdcfe;margin-bottom:6px'>{case} · extracto de resultados/evidencia/{html.escape(f)}</div><pre style='margin:0;white-space:pre-wrap'>{body}</pre></div></body>")
        pg.locator("div").first.screenshot(path=os.path.join(EVD,"img",f"{case}_salida.png"))
    b.close()
print(os.listdir(os.path.join(EVD,"img")))
