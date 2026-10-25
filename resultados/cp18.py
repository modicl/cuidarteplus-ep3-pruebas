from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-18"); e.w("CP-18", time.strftime("%Y-%m-%d %H:%M"))
TM1=login("qa_medico1")
P1="<script>alert('XSS-1')</script>"; P2="<img src=x onerror=alert('XSS-2')>"; P3="\"><svg onload=alert('XSS-3')>"
e.step(1,"POST /pacientes con P2"); r=api("POST","/pacientes",token=TM1,body={"rut":"13.572.468-8","primer_nombre":P2,"apellido_paterno":"Lillo","apellido_materno":"Bravo","fecha_nacimiento":"1991-04-04","sexo":"F","email":"marta.lillo.qa@example.com"}); e.w(short(r,250),"| Content-Type:",r.headers.get("Content-Type")); pid=r.json()["id"]
e.step(2,"POST /examenes con P1 y P3"); r=api("POST","/examenes",token=TM1,body={"tipo_examen_medico_id":1,"paciente_id":1,"diagnosis":P1,"observaciones":P3}); e.w(short(r,250),"| Content-Type:",r.headers.get("Content-Type")); xid=r.json()["id"]
checks="""()=>({imgX:document.querySelectorAll('img[src="x"]').length, svgOnload:document.querySelectorAll('svg[onload]').length, scriptXSS:[...document.scripts].filter(s=>s.textContent.includes('XSS-1')).length, onerror:document.querySelectorAll('[onerror]').length})"""
def run(browser_name, pw):
    e.w(f"\n--- {browser_name} ---"); b=getattr(pw,browser_name).launch(); dialogs=[]
    def ctx(user):
        c=b.new_context(); pg=c.new_page(); pg.set_viewport_size({"width":1500,"height":1100}); pg.on("dialog", lambda d:(dialogs.append((user,d.message)), d.dismiss()))
        pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill(user); pg.get_by_label("Contraseña").fill(PW[user]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=20000); return pg
    pa=ctx("admin")
    pa.goto(WEB+"/pacientes"); pa.wait_for_timeout(9000)
    s=pa.get_by_placeholder("Buscar"); 
    if s.count(): s.first.fill("Lillo"); pa.wait_for_timeout(1500)
    e.w("3 lista de pacientes: filas con 'Lillo':",pa.locator("tr",has_text="Lillo").count(),"| texto de la celda:",pa.locator("tr",has_text="Lillo").first.inner_text().replace("\n"," | ")[:200] if pa.locator("tr",has_text="Lillo").count() else "(no visible)","| DOM:",pa.evaluate(checks)); pa.screenshot(path=os.path.join(EVD,f"CP-18_{browser_name}_lista_pacientes.png"))
    pa.goto(WEB+f"/pacientes/{pid}/editar"); pa.wait_for_timeout(5000); e.w("3 registro del paciente: valor del campo primer_nombre:",pa.input_value("input[name=primer_nombre]"),"| DOM:",pa.evaluate(checks)); pa.screenshot(path=os.path.join(EVD,f"CP-18_{browser_name}_registro_paciente.png"))
    pp=ctx("paciente"); pp.goto(WEB+"/mis-resultados"); pp.wait_for_timeout(12000); t=pp.inner_text("body"); e.w("4 Mis Resultados: texto visible incluye '<script>':","<script>" in t,"| DOM:",pp.evaluate(checks)); pp.screenshot(path=os.path.join(EVD,f"CP-18_{browser_name}_mis_resultados.png"))
    pp.goto(WEB+f"/examenes/{xid}"); pp.wait_for_timeout(9000); t=pp.inner_text("body"); e.w("4 detalle del examen: muestra el payload como texto:","<script>alert('XSS-1')</script>" in t,"y P3:",P3 in t,"| DOM:",pp.evaluate(checks)); pp.screenshot(path=os.path.join(EVD,f"CP-18_{browser_name}_detalle_examen.png"))
    pa.goto(WEB+"/auditoria"); pa.wait_for_timeout(5000); t=pa.inner_text("body"); e.w("5 Auditoría: muestra la acción PACIENTES_CREAR con el nombre como texto:","onerror=alert('XSS-2')" in t,"| DOM:",pa.evaluate(checks)); pa.screenshot(path=os.path.join(EVD,f"CP-18_{browser_name}_auditoria.png"))
    e.w("6 diálogos de alerta detectados:",dialogs); b.close(); return dialogs
with sync_playwright() as p:
    d1=run("chromium",p); d2=run("firefox",p)
e.step(7,"resumen"); e.w("diálogos en Chromium:",len(d1),"| en Firefox:",len(d2))
