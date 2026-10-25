"""Parte D: Lighthouse móvil 4G sobre /login y /home (PAC_A). Se ejecuta con el python del venv de Playwright N."""
import os, sys, json, time, statistics, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from qa import ROOT, WEB, PW, sql
from playwright.sync_api import sync_playwright

OUT = os.path.join(ROOT, "evidencia", "cp25", "lh")
os.makedirs(OUT, exist_ok=True)
PORT = 9333
prof = os.path.join(OUT, "perfil_chromium")
log = open(os.path.join(OUT, "parte_d.log"), "w", encoding="utf8")


def w(*a):
    t = " ".join(str(x) for x in a)
    print(t)
    log.write(t + "\n")
    log.flush()


def lh(url, name, keep, ctx):
    allr = []
    for i in range(1, 6):
        extra = ctx.new_page()  # Lighthouse usa la pestaña más reciente y la cierra al terminar
        ctx.new_cdp_session(extra).send("Network.clearBrowserCache")  # caché vacía en cada repetición (la sesión en localStorage se conserva)
        r = subprocess.run(["node", os.path.join(ROOT, "cp25", "lh_run.mjs"), url, str(PORT), "1", os.path.join(OUT, f"{name}_rep{i}.json"), "1" if keep else "0"], capture_output=True, text=True, encoding="utf8")
        w(f"[rep {i}]", r.stdout.strip(), r.stderr.strip()[:300])
        try: extra.close()
        except Exception: pass
        d = json.load(open(os.path.join(OUT, f"{name}_rep{i}.json"), encoding="utf8"))
        allr.append(d["results"][0] | {"rep": i}); ver = d["lighthouse"]
    out = {"url": url, "lighthouse": ver, "results": allr}
    json.dump(out, open(os.path.join(OUT, name + ".json"), "w", encoding="utf8"), indent=1)
    return out


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(prof, headless=True, args=["--remote-debugging-port=%d" % PORT], viewport={"width": 412, "height": 823})
    w("Chromium", ctx.browser.version, "| Playwright", __import__("importlib.metadata", fromlist=["version"]).version("playwright"))
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    res = {}
    w("== /login (sin sesión, caché vacía) ==")
    res["login"] = lh(WEB + "/login", "lh_login", False, ctx)
    w("== /home con sesión de PAC_A ==")
    pg.goto(WEB + "/login")
    pg.get_by_label("Nombre de usuario").fill("paciente")
    pg.get_by_label("Contraseña").fill(PW["paciente"])
    pg.get_by_role("button", name="Entrar").click()
    pg.wait_for_url("**/home", timeout=30000)
    pg.wait_for_timeout(3000)
    res["home"] = lh(WEB + "/home", "lh_home", True, ctx)
    ctx.close()
w("\nResumen (mediana de 5 repeticiones):")
for k, v in res.items():
    L = [x["load_ms"] for x in v["results"]]
    C = [x["lcp_ms"] for x in v["results"]]
    w(f"  {k}: URL final {v['results'][0]['finalUrl']} | load mediana {round(statistics.median(L))} ms | LCP mediana {round(statistics.median(C))} ms | Lighthouse {v['lighthouse']}")
json.dump({k: {"load_med": statistics.median([x["load_ms"] for x in v["results"]]), "lcp_med": statistics.median([x["lcp_ms"] for x in v["results"]])} for k, v in res.items()}, open(os.path.join(OUT, "resumen.json"), "w"))
