from qa import *
import re
from playwright.sync_api import sync_playwright
e = Ev("CP-12_complemento"); e.w("CP-12 pasos 1, 2 y 4 repetidos (interfaz por rol y comparación de la BD)", time.strftime("%Y-%m-%d %H:%M"))
print(restore()); 
EX=IDS["EX_A1"]
def login_ui(pg, user):
    pg.goto(WEB + "/login"); pg.get_by_label("Nombre de usuario").fill(user); pg.get_by_label("Contraseña").fill(PW[user])
    pg.get_by_role("button", name="Entrar").click(); pg.wait_for_url("**/home", timeout=20000)
def btns(pg, scope="tbody"):
    return sorted(set(x for x in pg.locator(scope + " button").evaluate_all("els=>els.map(e=>e.getAttribute('aria-label')||e.getAttribute('title')||e.innerText.trim())") if x))
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for user, rol in [("admin", "ADM"), ("qa_medico1", "MED"), ("paciente", "PAC")]:
        pg = b.new_page(viewport={"width": 1500, "height": 1000}); login_ui(pg, user); pg.wait_for_timeout(2000)
        r = {}; r["menú"] = pg.get_by_role("navigation", name="Navegación principal").inner_text().replace("\n", " | ")
        pg.goto(WEB + "/usuarios"); pg.wait_for_timeout(5000); t = pg.inner_text("body")
        r["usuarios"] = {"pantalla de gestión": "No autorizado" not in t, "pestañas": pg.get_by_role("tab").all_inner_texts(), "botones de fila": btns(pg)}
        pg.screenshot(path=os.path.join(EVD, f"CP-12_ui_{rol}_usuarios.png"))
        pg.goto(WEB + "/pacientes"); pg.wait_for_timeout(10000); t = pg.inner_text("body")
        r["pacientes"] = {"se abre la pantalla de gestión": "Gestión de Pacientes" in t, "toast de error": "No autorizado" in t, "pestañas": pg.get_by_role("tab").all_inner_texts(), "botones de fila": btns(pg)}
        pg.screenshot(path=os.path.join(EVD, f"CP-12_ui_{rol}_pacientes.png"))
        pg.goto(WEB + "/examenes"); pg.wait_for_timeout(10000)
        r["exámenes"] = {"pestañas": pg.get_by_role("tab").all_inner_texts(), "botones de fila": btns(pg)}
        pg.screenshot(path=os.path.join(EVD, f"CP-12_ui_{rol}_examenes.png"))
        pg.goto(WEB + f"/examenes/{EX}"); pg.wait_for_timeout(9000)
        r["detalle examen"] = {"botones": sorted(set(pg.locator("main button, button").evaluate_all("els=>els.map(e=>e.getAttribute('aria-label')||e.innerText.trim()).filter(x=>x)"))) }
        pg.screenshot(path=os.path.join(EVD, f"CP-12_ui_{rol}_detalle.png"))
        pg.goto(WEB + "/auditoria"); pg.wait_for_timeout(4000); t = pg.inner_text("body"); r["auditoría"] = {"URL": pg.url, "muestra el listado": "Historial completo" in t, "No autorizado": "No autorizado" in t}
        res[rol] = r; e.w(f"\n=== {rol} ({user}) ===")
        for k, v in r.items(): e.w(" ", k, ":", v)
        pg.close()
    b.close()
# ---- paso 4: comparación de la BD con la instantánea en las operaciones que el informe espera denegadas ----
TB = ["usuarios", "roles", "usuario_roles", "pacientes", "examen_medico", "documentos_examen"]
def snap(): return {t: sql(f"select md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from {t} x").split("\n")[2].strip() for t in TB}
def denied_run(rol, token):
    ops = []
    if rol == "MED":
        ops = [("GET", "/usuarios", None), ("POST", "/usuarios", {"nombre_usuario": "qa_m12b_med", "correo": "qa_m12b_med@example.com", "contrasena_hash": "Cuidarte#Aux2026"}), ("PUT", f"/usuarios/{IDS['qa_rol01']}", {"correo": "x_med@example.com"}), ("DELETE", f"/pacientes/21", None), ("GET", "/auditoria", None)]
    else:
        ops = [("GET", "/usuarios", None), ("POST", "/usuarios", {"nombre_usuario": "qa_m12b_pac", "correo": "qa_m12b_pac@example.com", "contrasena_hash": "Cuidarte#Aux2026"}), ("PUT", f"/usuarios/{IDS['qa_rol01']}", {"correo": "x_pac@example.com"}), ("GET", "/pacientes", None), ("PUT", "/pacientes/2", {"observaciones_medicas_generales": "cp12 pac"}), ("DELETE", "/pacientes/21", None),
               ("POST", "/examenes", {"tipo_examen_medico_id": 1, "paciente_id": 1, "diagnosis": "cp12 pac"}), ("PUT", f"/examenes/{IDS['EX_A3']}", {"diagnosis": "cp12 pac"}), ("DELETE", f"/examenes/{IDS['EX_MAT1']}", None), ("DELETE", f"/documentos/{IDS['DOC_MAT1']}", None),
               ("POST", "/documentos", None), ("GET", "/auditoria", None)]
    out = []
    for m, pth, body in ops:
        if (m, pth) == ("POST", "/documentos"): r = api("POST", pth, token=token, data={"examen_medico_id": IDS["EX_A3"], "paciente_id": 1}, files={"documento": ("m.pdf", open(DAT + "/resultado_examen_v1.pdf", "rb"), "application/pdf")})
        else: r = api(m, pth, token=token, body=body)
        out.append((m, pth, r.status_code))
    return out
for rol, user in [("MED", "qa_medico1"), ("PAC", "paciente")]:
    print(restore()); s0 = snap(); tk = login(user); o = denied_run(rol, tk); s1 = snap()
    ch = [t for t in TB if s0[t] != s1[t]]
    e.w(f"\n=== Paso 4, {rol}: operaciones que la matriz da como denegadas ===")
    for m, pth, c in o: e.w(f"  {m} {pth}: HTTP {c} -> {'denegada' if c in (401, 403) else 'NO denegada'}")
    e.w(f"  Tablas distintas a la instantánea después de las operaciones: {ch if ch else 'ninguna'}")
print(restore()); e.w("\nEstado base restaurado al terminar.")
json.dump(res, open(os.path.join(EVD, "CP-12_ui_matriz.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
