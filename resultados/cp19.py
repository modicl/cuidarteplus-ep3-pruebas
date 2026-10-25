from qa import *
import glob, re
from playwright.sync_api import sync_playwright
e = Ev("CP-19"); e.w("CP-19", time.strftime("%Y-%m-%d %H:%M"))
e.step(1,"Swagger y openapi.json"); r=requests.get(API+"/docs/",timeout=10); e.w("GET /docs/: HTTP",r.status_code); r=requests.get(API+"/openapi.json",timeout=10); e.w("GET /openapi.json: HTTP",r.status_code,len(r.content),"bytes"); open(os.path.join(EVD,"newman","openapi_descargado.json"),"wb").write(r.content)
e.step(2,"operaciones implementadas vs documentadas")
impl=[]
pref={"auth.js":"/autenticacion","users.js":"/usuarios","pacientes.js":"/pacientes","examenes.js":"/examenes","documentos.js":"/documentos","tipo-examen.js":"/tipo-examen","audit.js":"/auditoria","roles.js":"/roles"}
for f,p in pref.items():
    for m,path in re.findall(r"router\.(get|post|put|delete)\(\s*[\"']([^\"']*)[\"']",open(os.path.join(ROOT,"..","BACKEND","src","routes",f),encoding="utf8").read()):
        impl.append((m.upper(),(p+(path if path!="/" else "")).replace(":id","{id}").replace(":paciente_id","{paciente_id}").replace(":examen_id","{examen_id}").replace(":rut","{rut}")))
spec=r.json(); doc={(m.upper(),p) for p,v in spec["paths"].items() for m in v if m in("get","post","put","delete")}
e.w("implementadas:",len(impl),"| documentadas en Swagger:",len(doc))
missing=[x for x in impl if x not in doc]; e.w("no documentadas:",len(missing)); 
for m,p in missing: e.w("  ",m,p)
extra=[x for x in doc if x not in impl]; e.w("documentadas pero no encontradas en el código:",extra)
rb={(m.upper(),p):bool(o.get("security")) for p,v in spec["paths"].items() for m,o in v.items() if m in("get","post","put","delete")}; e.w("operaciones documentadas con bearerAuth:",sum(rb.values()))
e.step("3-4-6","Newman: colección, vectores y reporte"); e.w(open(os.path.join(EVD,"newman","resumen_cp19.txt"),encoding="utf8").read())
e.step(5,"vector 13 desde la interfaz (Subir Documento, MED1, EX_A3)")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1400,"height":1000})
    pg.on("response", lambda r: e.w("  respuesta UI:",r.status,r.request.method,r.url,r.text()[:150].replace("\n"," ")) if r.request.method=="POST" and "documentos" in r.url else None)
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill(PW["qa_medico1"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    pg.goto(WEB+f"/examenes/{IDS['EX_A3']}"); pg.wait_for_timeout(9000); pg.get_by_role("button",name="Subir Documento").click(); pg.wait_for_timeout(800)
    pg.locator("input[type=file]").set_input_files(DAT+"/script_malicioso.exe"); pg.wait_for_timeout(9000); e.w("toasts:",pg.locator("[data-sonner-toast]").all_inner_texts(),"| texto del diálogo:",pg.get_by_role("dialog").inner_text().replace("\n"," | ")[:250]); pg.screenshot(path=os.path.join(EVD,"CP-19_paso5_ui_exe.png")); b.close()
e.step(7,"cantidades finales"); e.w(sql("select (select count(*) from usuarios) usuarios,(select count(*) from pacientes) pacientes,(select count(*) from examen_medico) examenes,(select count(*) from documentos_examen) documentos"),"(iniciales: 14, 21, 8, 7)")
e.w(sql("select id,examen_medico_id,paciente_id,nombre_archivo,length(documento) from documentos_examen where nombre_archivo in ('script_malicioso.exe','resultado_falso.pdf','foto_falsa.jpg') or paciente_id=11 order by id"))
