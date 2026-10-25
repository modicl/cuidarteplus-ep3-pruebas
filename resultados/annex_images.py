import os, re, html, json
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.abspath(__file__)); EVD = os.path.join(ROOT, "evidencia"); OUT = os.path.join(EVD, "anexos")
os.makedirs(OUT, exist_ok=True)
def rd(rel): return open(os.path.join(EVD, rel), encoding="utf8", errors="replace").read()
def clean(t): return re.sub(r"\x1b\[[0-9;]*m", "", t)
def render(pg, name, title, lines, width=1200, maxlen=170):
    body = "\n".join(html.escape(l[:maxlen]) for l in lines)
    pg.set_viewport_size({"width": width, "height": 600})
    pg.set_content(f"<body style='margin:0;background:#0c0c0c'><div id=t style='width:{width}px;box-sizing:border-box;color:#cccccc;font:13px Consolas,monospace;padding:12px'><div style='color:#16c60c;margin-bottom:8px'>{html.escape(title)}</div><pre style='margin:0;white-space:pre-wrap'>{body}</pre></div></body>")
    pg.locator("#t").screenshot(path=os.path.join(OUT, name))
    return name
ZAP = lambda f: [l for l in clean(rd(f)).splitlines()]
def zap_alerts(f):
    d = json.load(open(os.path.join(EVD, f), encoding="utf8")); out = ["OWASP ZAP %s - informe %s" % (d.get("@version"), d.get("@generated"))]
    for s in d["site"]:
        out.append("Sitio: %s (%d alertas)" % (s["@name"], len(s["alerts"])))
        for a in s["alerts"]: out.append("  [%s] %s  (instancias: %s, plugin %s)" % (a["riskdesc"], a["name"], a["count"], a["pluginid"]))
    return out
sel = lambda ls, rx, n=60: [l for l in ls if re.search(rx, l)][:n]
imgs = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    # --- SonarQube: capturas reales del tablero (autenticadas con el token de análisis, sin cambiar la clave admin) ---
    ctx = b.new_context(viewport={"width": 1400, "height": 900})
    sp = ctx.new_page()
    sp.goto("http://localhost:9000/sessions/new"); sp.wait_for_timeout(2500)
    sp.locator("input[name=login]").fill("qa_viewer"); sp.locator("input[name=password]").fill("Qa-Viewer-2026xyz"); sp.locator("button[type=submit]").click(); sp.wait_for_timeout(4000)
    for k in ["backend", "frontend"]:
        sp.goto("http://localhost:9000/dashboard?id=cuidarteplus-%s" % k); sp.wait_for_timeout(7000)
        for _ in range(3):
            for bt in sp.get_by_role("button", name="Dismiss").all():
                try: bt.click(timeout=1500)
                except Exception: pass
        try: sp.get_by_role("tab", name=re.compile("Overall Code")).click(timeout=3000)
        except Exception: pass
        sp.wait_for_timeout(2500)
        sp.screenshot(path=os.path.join(OUT, "sonar_dashboard_%s.png" % k), full_page=True); imgs["sonar_%s" % k] = "sonar_dashboard_%s.png" % k
    sp.goto("http://localhost:9000/project/issues?id=cuidarteplus-backend&issueStatuses=OPEN&impactSoftwareQualities=SECURITY"); sp.wait_for_timeout(7000)
    for bt in sp.get_by_role("button", name="Dismiss").all():
        try: bt.click(timeout=1500)
        except Exception: pass
    sp.screenshot(path=os.path.join(OUT, "sonar_issues_backend_seguridad.png"), full_page=True)
    # --- CLI renderizados ---
    render(pg, "sonar_cli.png", "$ docker run --rm -e SONAR_TOKEN=*** sonarsource/sonar-scanner-cli ... (SonarScanner CLI 8.1.0.6389) + extracción por API", rd("sonar/comandos.txt").splitlines()[:6] + [""] + rd("sonar/resumen_backend.txt").splitlines()[:9] + ["..."] + rd("sonar/resumen_frontend.txt").splitlines()[:3])
    render(pg, "sonar_relevantes.png", "resultados/evidencia/sonar/hallazgos_relevantes.txt (extracto)", rd("sonar/hallazgos_relevantes.txt").splitlines()[:34], maxlen=190)
    render(pg, "zap_cli_cp17.png", "$ docker run --rm ghcr.io/zaproxy/zaproxy:stable zap.sh -cmd -autorun /zap/wrk/plan_run.yaml   (CP-17)", sel(ZAP("zap/zap_cp17.log"), r"^Job .*(started|finished|set rule 4001|set rule 4002)|Unrecognised|ZAP|alerts", 40) + [""] + zap_alerts("zap/cp17_zap_reporte.json"))
    render(pg, "zap_cli_cp21.png", "$ docker run --rm ghcr.io/zaproxy/zaproxy:stable zap.sh -cmd -autorun /zap/wrk/plan_run.yaml   (CP-21)", sel(ZAP("zap/zap_cp21.log"), r"^Job .*(started|finished)|Unrecognised", 24) + [""] + zap_alerts("zap/cp21_zap_reporte.json"))
    nl = clean(rd("newman/newman_cp19.log")).splitlines()
    render(pg, "newman_cli.png", "$ docker run --rm postman/newman run coleccion_cp19.json -e env.json --working-dir /datos   (Newman 6.1.3)", [l for l in nl if l.strip()][:30] + ["..."] + nl[-32:], maxlen=130)
    render(pg, "testssl_cli.png", "$ docker run --rm drwetter/testssl.sh --ip 192.168.65.254 localhost:3443   (testssl.sh 3.2.4, proxy TLS del equipo)", clean(rd("tls/testssl_3443.txt")).splitlines()[:46])
    tcp = rd("tls/captura_tcpdump_api.txt").splitlines(); hit = [i for i, l in enumerate(tcp) if "Cuidarte#Med2026" in l or "password" in l.lower()]
    i0 = max(0, (hit[0] if hit else 0) - 6)
    render(pg, "tcpdump_cli.png", "$ docker run --rm --net container:cuidarteplus-backend-ev nicolaka/netshoot tcpdump -i eth0 -A -s0 -l tcp port 4000   (tcpdump 4.99.6)", tcp[:4] + ["..."] + tcp[i0:i0 + 26])
    render(pg, "npm_audit_cli.png", "$ npm audit --omit=dev   (BACKEND, npm 11.6.2)", rd("anexos/npm_audit_backend.txt").splitlines()[-14:] + ["", "$ npm audit --omit=dev   (FRONTEND)"] + rd("anexos/npm_audit_frontend.txt").splitlines()[-8:])
    render(pg, "playwright_cli.png", "$ python cp18_nav.py N chromium,firefox,webkit,msedge ; python cp18_nav.py N-1 chromium,firefox,webkit   (Playwright 1.64.1 y 1.63.0)", sel(rd("CP-18_navegadores.txt").splitlines(), r"^===|^---|diálogos|RESUMEN|Playwright \(paquete\)", 40))
    render(pg, "versiones_cli.png", "Versiones de las herramientas (salida de los comandos)", rd("anexos/versiones_cli.txt").splitlines())
    render(pg, "psql_cli.png", "psql, sha256sum y pg_restore (estado base)", rd("anexos/psql_pg_sha.txt").splitlines())
    render(pg, "caddy_cli.png", "evidencia/tls/Caddyfile (proxy TLS del equipo) y docker run caddy:2", ["$ docker run -d --name qa-caddy -p 3443:3443 -p 4443:4443 -v Caddyfile:/etc/caddy/Caddyfile:ro caddy:2   (Caddy 2.11.7)", ""] + rd("tls/Caddyfile").splitlines())
    b.close()
print(sorted(os.listdir(OUT)))
