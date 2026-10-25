"""CP-18 repetido en las dos últimas versiones de Playwright (N y N-1) y en Edge real.
Uso: <python del venv> cp18_nav.py <etiqueta> <chromium,firefox,webkit,msedge>"""
import sys
from qa import *
from playwright.sync_api import sync_playwright
import playwright

label = sys.argv[1]
kinds = sys.argv[2].split(",")
e = Ev.__new__(Ev)
e.case = "CP-18"
e.f = open(os.path.join(EVD, "CP-18_navegadores.txt"), "a", encoding="utf8")
e.w("\n=== %s | %s | %s ===" % (label, time.strftime("%Y-%m-%d %H:%M"), ", ".join(kinds)))
TM1 = login("qa_medico1")
P1 = "<script>alert('XSS-1')</script>"
P2 = "<img src=x onerror=alert('XSS-2')>"
P3 = "\"><svg onload=alert('XSS-3')>"
pid = sql("select id from pacientes where rut='13572468-8'").split("\n")[2].strip()
if not pid.isdigit():
    pid = api("POST", "/pacientes", token=TM1, body={"rut": "13.572.468-8", "primer_nombre": P2, "apellido_paterno": "Lillo", "apellido_materno": "Bravo", "fecha_nacimiento": "1991-04-04", "sexo": "F", "email": "marta.lillo.qa@example.com"}).json()["id"]
xid = sql("select id from examen_medico where diagnosis like '<script>%' order by id desc limit 1").split("\n")[2].strip()
if not xid.isdigit():
    xid = api("POST", "/examenes", token=TM1, body={"tipo_examen_medico_id": 1, "paciente_id": 1, "diagnosis": P1, "observaciones": P3}).json()["id"]
e.w("paciente con P2 id", pid, "| examen con P1 y P3 id", xid)
checks = """()=>({imgX:document.querySelectorAll('img[src="x"]').length, svgOnload:document.querySelectorAll('svg[onload]').length, scriptXSS:[...document.scripts].filter(s=>s.textContent.includes('XSS-1')).length, onerror:document.querySelectorAll('[onerror]').length})"""


def run(pw, kind):
    if kind == "msedge":
        b = pw.chromium.launch(channel="msedge")
    else:
        b = getattr(pw, kind).launch()
    ver = b.version
    name = "%s %s (Playwright %s)" % ("Edge real" if kind == "msedge" else kind, ver, label)
    e.w("\n--- %s ---" % name)
    dialogs = []

    def ctx(user):
        c = b.new_context()
        pg = c.new_page()
        pg.set_viewport_size({"width": 1500, "height": 1100})
        pg.on("dialog", lambda d: (dialogs.append((user, d.message)), d.dismiss()))
        pg.goto(WEB + "/login")
        pg.get_by_label("Nombre de usuario").fill(user)
        pg.get_by_label("Contraseña").fill(PW[user])
        pg.get_by_role("button", name="Entrar").click()
        pg.wait_for_url("**/home", timeout=30000)
        return pg

    ok = True
    pa = ctx("admin")
    pa.goto(WEB + "/pacientes")
    pa.wait_for_timeout(9000)
    s = pa.get_by_placeholder("Buscar")
    if s.count():
        s.first.fill("Lillo")
        pa.wait_for_timeout(1500)
    t = pa.locator("tr", has_text="Lillo").first.inner_text() if pa.locator("tr", has_text="Lillo").count() else ""
    dom = pa.evaluate(checks)
    e.w("3 lista de pacientes: payload como texto:", "<img src=x onerror=alert('XSS-2')>" in t, "| DOM:", dom)
    ok &= ("<img src=x onerror=alert('XSS-2')>" in t) and not any(dom.values())
    pa.goto(WEB + "/pacientes/%s/editar" % pid)
    pa.wait_for_timeout(5000)
    dom = pa.evaluate(checks)
    v = pa.input_value("input[name=primer_nombre]")
    e.w("3 registro del paciente: campo =", v, "| DOM:", dom)
    ok &= (v == P2) and not any(dom.values())
    pp = ctx("paciente")
    pp.goto(WEB + "/mis-resultados")
    pp.wait_for_timeout(12000)
    dom = pp.evaluate(checks)
    e.w("4 Mis Resultados: DOM:", dom)
    ok &= not any(dom.values())
    pp.goto(WEB + "/examenes/%s" % xid)
    pp.wait_for_timeout(9000)
    t = pp.inner_text("body")
    dom = pp.evaluate(checks)
    e.w("4 detalle del examen: P1 como texto:", P1 in t, "P3:", P3 in t, "| DOM:", dom)
    pp.screenshot(path=os.path.join(EVD, "CP-18_%s_%s_detalle_examen.png" % (label, kind)))
    ok &= (P1 in t) and (P3 in t) and not any(dom.values())
    pa.goto(WEB + "/auditoria")
    pa.wait_for_timeout(5000)
    cbx = pa.get_by_role("combobox")
    if cbx.count():
        cbx.first.click()
        pa.get_by_role("option").last.click()
        pa.wait_for_timeout(1500)
    t = pa.inner_text("body")
    dom = pa.evaluate(checks)
    e.w("5 Auditoría: acción con el nombre como texto:", "onerror=alert('XSS-2')" in t, "| DOM:", dom)
    ok &= ("onerror=alert('XSS-2')" in t) and not any(dom.values())
    e.w("6 diálogos de alerta:", dialogs, "=> %s" % ("sin ejecución de scripts" if ok and not dialogs else "REVISAR"))
    b.close()
    return ver, ok and not dialogs


with sync_playwright() as p:
    e.w("Playwright (paquete):", __import__("importlib.metadata", fromlist=["version"]).version("playwright"))
    res = {}
    for k in kinds:
        try:
            res[k] = run(p, k)
        except Exception as ex:
            e.w("--- %s: no se pudo ejecutar: %s" % (k, str(ex)[:200]))
            res[k] = (None, None)
    e.w("RESUMEN", label, res)
