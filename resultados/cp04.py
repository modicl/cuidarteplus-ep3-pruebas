from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-04"); e.w("CP-04", time.strftime("%Y-%m-%d %H:%M"))
EXA, DOCA, EXB, DOCB = IDS["EX_A1"], IDS["DOC_A1"], IDS["EX_B1"], IDS["DOC_B1"]
e.w("EX_A",EXA,"DOC_A",DOCA,"EX_B",EXB,"DOC_B",DOCB)
e.step(1,"login PA"); TA = login("paciente"); e.w("T_A obtenido:",bool(TA), jwt(TA))
def chk(n, m, p, esp):
    r = api(m,p,token=TA); body=r.text[:200].replace("\n"," ")
    e.w(f"paso {n}: {m} {p} -> HTTP {r.status_code} (esperado {esp}) ({r.elapsed_s}s) {body}"); return r
e.step(2,"propios"); 
for p in [f"/examenes/paciente/1", f"/examenes/{EXA}", f"/documentos/{DOCA}"]: 
    r = api("GET",p,token=TA); e.w(p,"-> HTTP",r.status_code, r.headers.get("Content-Type"), len(r.content),"bytes")
e.step(3,"ajeno"); chk(3,"GET","/examenes/paciente/11","403")
e.step(4,""); chk(4,"GET",f"/examenes/{EXB}","404")
e.step(5,""); chk(5,"GET",f"/documentos/examen/{EXB}","403")
e.step(6,""); r=chk(6,"GET",f"/documentos/{DOCB}","403"); e.w("  SHA-256 del contenido recibido:", sha_b(r.content), "| SHA-256 original DOC_B (resultado_examen.pdf):", sha(DAT+"/resultado_examen.pdf"))
e.step(7,""); chk(7,"GET","/pacientes/11","403")
e.step(8,"listado /examenes"); r = api("GET","/examenes",token=TA); lst=r.json(); e.w(f"HTTP {r.status_code} ({r.elapsed_s}s) cantidad={len(lst)} paciente_ids={sorted(set(x['paciente_id'] for x in lst))}")
e.step(9,"UI abrir /examenes/EX_B como PA")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("paciente"); pg.get_by_label("Contraseña").fill(PW["paciente"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    pg.goto(WEB+f"/examenes/{EXB}"); pg.wait_for_timeout(7000); e.w("URL:",pg.url,"| texto:",pg.inner_text("body")[:300].replace("\n"," | ")); pg.screenshot(path=os.path.join(EVD,"CP-04_paso9_ui_examen_ajeno.png"))
    e.w("¿aparece diagnóstico de EX_B 'Dato sintetico B1'?", "Dato sintetico B1" in pg.inner_text("body")); b.close()
