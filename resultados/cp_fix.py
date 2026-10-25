from qa import *
import re, hashlib
from playwright.sync_api import sync_playwright
STAMP = time.strftime("%Y-%m-%d %H:%M")
def login_ui(pg, user):
    pg.goto(WEB + "/login"); pg.get_by_label("Nombre de usuario").fill(user); pg.get_by_label("Contraseña").fill(PW[user])
    pg.get_by_role("button", name="Entrar").click(); pg.wait_for_url("**/home", timeout=20000)

with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------------- CP-01 paso 4 ----------------
    e = Ev("CP-01_complemento"); e.w("CP-01 paso 4 repetido", STAMP)
    pg = b.new_page(viewport={"width": 1400, "height": 900}); login_ui(pg, "qa_medico1")
    pg.goto(WEB + "/pacientes"); pg.wait_for_timeout(9000)
    t = pg.inner_text("body"); HAS = lambda t: bool(re.search(r"\d{6,8}-[\dkK]", t)) or "Dato sintetico" in t
    e.w("1) Con sesión, /pacientes muestra datos de pacientes (RUT visibles):", HAS(t), "| URL:", pg.url)
    pg.goto(WEB + "/examenes"); pg.wait_for_timeout(9000); e.w("2) /examenes con sesión: URL", pg.url)
    pg.screenshot(path=os.path.join(EVD, "CP-01_paso4_antes_de_cerrar.png"))
    pg.get_by_role("button", name="Menú de usuario").click(); pg.get_by_role("menuitem", name="Cerrar sesión").click(); pg.wait_for_timeout(2000)
    e.w("3) Tras 'Cerrar sesión': URL", pg.url, "| localStorage:", pg.evaluate("Object.keys(localStorage)"))
    for i in range(1, 4):
        pg.go_back(); pg.wait_for_timeout(2500); t = pg.inner_text("body")
        try: ls = pg.evaluate("Object.keys(localStorage)")
        except Exception: ls = "(about:blank, sin acceso)"
        e.w(f"4.{i}) Botón Atrás #{i}: URL {pg.url} | muestra datos clínicos: {HAS(t)} | localStorage: {ls} | texto: {t[:90]!r}")
        pg.screenshot(path=os.path.join(EVD, f"CP-01_paso4_atras_{i}.png"))
    pg.goto(WEB + "/pacientes"); pg.wait_for_timeout(2500); e.w("5) Abrir /pacientes directamente sin sesión: URL", pg.url)
    # ---------------- CP-10 paso 2 ----------------
    e = Ev("CP-10_complemento"); e.w("CP-10 paso 2 repetido", STAMP)
    TA = login("paciente"); lst = api("GET", "/examenes/paciente/1", token=TA).json(); e.w("Exámenes de PAC_A (API):", [x["id"] for x in lst], "N =", len(lst))
    pg = b.new_page(viewport={"width": 1400, "height": 1000}); login_ui(pg, "paciente"); okc = 0
    for x in sorted(lst, key=lambda x: int(x["id"])):
        pg.goto(WEB + "/examenes/%s" % x["id"]); pg.wait_for_timeout(9000); t = pg.inner_text("body")
        docs = api("GET", "/documentos/examen/%s" % x["id"], token=TA).json()
        checks = {"tipo": x["tipo_examen_nombre"] in t, "fecha": "Fecha" in t,
                  "diagnóstico": (not x.get("diagnosis")) or x["diagnosis"] in t, "tratamiento": (not x.get("tratamiento")) or x["tratamiento"] in t,
                  "observaciones": (not x.get("observaciones")) or x["observaciones"] in t, "documentos": all(d["nombre_archivo"] in t for d in docs)}
        okc += all(checks.values()); e.w(f"Examen {x['id']} ({x['tipo_examen_nombre']}), documentos API {len(docs)}: {checks} -> {'OK' if all(checks.values()) else 'REVISAR'}")
        if x["id"] in (str(IDS["EX_A1"]), str(IDS["EX_A2"])): pg.screenshot(path=os.path.join(EVD, f"CP-10_paso2_detalle_examen_{x['id']}.png"))
    e.w("Detalles completos y correctos:", okc, "de", len(lst))
    # ---------------- CP-13 paso 3 ----------------
    e = Ev("CP-13_complemento"); e.w("CP-13 paso 3 repetido", STAMP)
    pg = b.new_page(viewport={"width": 1400, "height": 1000}); login_ui(pg, "paciente")
    pg.goto(WEB + "/politica-privacidad"); pg.wait_for_timeout(3000); t = pg.inner_text("body"); e.w("URL:", pg.url, "| caracteres:", len(t))
    for k in ["finalidad", "responsable", "derechos", "datos personales", "consentimiento", "Ley", "acceso", "rectific", "supresi", "oposici", "portabilidad", "bloqueo"]: e.w(f"  menciona '{k}':", bool(re.search(k, t, re.I)))
    e.w("Texto de la política (primeros 1500 caracteres):\n" + t[:1500]); pg.screenshot(path=os.path.join(EVD, "CP-13_paso3_politica.png"), full_page=True)
    e.w("Consentimiento en la BD: tablas/columnas con 'consent': 0 (ver CP-13.txt)")
    b.close()
