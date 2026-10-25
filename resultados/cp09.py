from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-09"); e.w("CP-09", time.strftime("%Y-%m-%d %H:%M"))
TM1=login("qa_medico1"); EXA1, EXA3 = IDS["EX_A1"], IDS["EX_A3"]; a0=sql("select max(id) from auditoria").split("\n")[2].strip()
e.w("SHA-256 originales:"); 
for f in ["resultado_examen.pdf","informe.doc","presentacion.ppt","radiografia.jpg","imagen.png"]: e.w(" ",f,os.path.getsize(DAT+"/"+f),"bytes",sha(DAT+"/"+f))
e.step(1,"UI adjuntar resultado_examen.pdf a EX_A3")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1500,"height":1100})
    pg.on("response", lambda r: e.w("  respuesta UI:",r.status,r.request.method,r.url,r.text()[:160]) if r.request.method=="POST" and "documentos" in r.url else None)
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill(PW["qa_medico1"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    pg.goto(WEB+f"/examenes/{EXA3}"); pg.wait_for_timeout(9000); pg.get_by_role("button",name="Subir Documento").click(); pg.wait_for_timeout(800)
    pg.locator("input[type=file]").set_input_files(DAT+"/resultado_examen.pdf"); pg.wait_for_timeout(12000); e.w("toasts:",pg.locator("[data-sonner-toast]").all_inner_texts()); pg.screenshot(path=os.path.join(EVD,"CP-09_paso1_ui.png")); b.close()
e.step(2,"API 5 formatos a EX_A1")
mt={"resultado_examen.pdf":"application/pdf","informe.doc":"application/msword","presentacion.ppt":"application/vnd.ms-powerpoint","radiografia.jpg":"image/jpeg","imagen.png":"image/png"}
up={}
for f,m in mt.items():
    r=api("POST","/documentos",token=TM1,data={"examen_medico_id":EXA1,"paciente_id":1},files={"documento":(f,open(DAT+"/"+f,"rb"),m)},timeout=120); e.w(f"{f} ({m}):",short(r,250))
    if r.status_code==201: up[f]=r.json()["documento"]["id"]
e.step(3,"BD"); e.w(sql(f"select id,examen_medico_id,paciente_id,nombre_archivo,length(documento) bytes from documentos_examen where examen_medico_id in ({EXA1},{EXA3}) order by id"))
e.step(4,"descarga y SHA-256")
for f,i in up.items():
    x=api("GET",f"/documentos/{i}",token=TM1); e.w(f"{f} id {i}: HTTP {x.status_code} Content-Type={x.headers.get('Content-Type')} Content-Disposition={x.headers.get('Content-Disposition')} bytes={len(x.content)} SHA-256 igual al original: {sha_b(x.content)==sha(DAT+'/'+f)}")
e.step(5,"auditoría"); e.w(sql(f"select id,usuario_id,accion from auditoria where id>{a0} and accion ilike 'DOCUMENTOS%' order by id"))
e.w("mimetypes aceptados por el código:", subprocess.run(["grep","-n","mimetype\|allowed\|application/","../BACKEND/src/routes/documentos.js"],capture_output=True,text=True).stdout[:600])
