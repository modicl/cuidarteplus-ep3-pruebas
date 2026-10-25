from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-11"); e.w("CP-11", time.strftime("%Y-%m-%d %H:%M:%S"))
TM1, TADM = login("qa_medico1"), login("admin"); a0=sql("select max(id) from auditoria").split("\n")[2].strip(); t0=time.strftime("%H:%M:%S"); e.w("hora inicio",t0,"| último id auditoría inicial:",a0)
acc=[]
def A(n,desc,r): acc.append((n,desc,time.strftime("%H:%M:%S"))); e.w(f"acción {n} {desc}: {short(r,160)}"); return r
A(1,"registro de usuario (visitante)",api("POST","/autenticacion/registro",body={"nombre_usuario":"qa_aud_reg","password":"Cuidarte#Aud2026","correo":"qa_aud_reg@example.com"}))
r=A(2,"crear paciente (MED1)",api("POST","/pacientes",token=TM1,body={"rut":"7.654.321-6","primer_nombre":"Aud","apellido_paterno":"Itoria","fecha_nacimiento":"1980-01-01","sexo":"M","email":"aud.itoria.qa@example.com"})); pid=r.json()["id"]
A(3,"editar paciente (MED1)",api("PUT",f"/pacientes/{pid}",token=TM1,body={"telefono":"+56911110000"}))
A(4,"eliminar paciente (ADM)",api("DELETE",f"/pacientes/{pid}",token=TADM))
r=A(5,"crear usuario (ADM)",api("POST","/usuarios",token=TADM,body={"nombre_usuario":"qa_aud_user","correo":"qa_aud_user@example.com","contrasena_hash":"Cuidarte#Aud2026","rol_id":3})); uid=r.json()["id"]
A(6,"editar usuario (ADM)",api("PUT",f"/usuarios/{uid}",token=TADM,body={"correo":"qa_aud_user2@example.com"}))
A(7,"eliminar usuario qa_elim_api por API (ADM)",api("DELETE",f"/usuarios/{IDS['qa_elim_api']}",token=TADM))
r=A(8,"crear examen (MED1)",api("POST","/examenes",token=TM1,body={"tipo_examen_medico_id":1,"paciente_id":1,"diagnosis":"Aud","tratamiento":"Aud"})); xid=r.json()["id"]
A(9,"editar examen (MED1)",api("PUT",f"/examenes/{xid}",token=TM1,body={"diagnosis":"Aud editado"}))
r=A(11,"subir documento (MED1)",api("POST","/documentos",token=TM1,data={"examen_medico_id":xid,"paciente_id":1},files={"documento":("aud.pdf",open(DAT+"/resultado_examen_v1.pdf","rb"),"application/pdf")})); did=r.json()["documento"]["id"]
A(12,"descargar documento (MED1)",api("GET",f"/documentos/{did}",token=TM1))
A(13,"eliminar documento (ADM)",api("DELETE",f"/documentos/{did}",token=TADM))
A(10,"eliminar examen (ADM)",api("DELETE",f"/examenes/{xid}",token=TADM))
e.step("7-UI","eliminar qa_elim_ui desde la interfaz")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1500,"height":1100})
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("admin"); pg.get_by_label("Contraseña").fill(PW["admin"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    pg.goto(WEB+"/usuarios"); pg.wait_for_timeout(3000); pg.get_by_role("textbox",name="Buscar").first.fill("qa_elim_ui") if pg.get_by_role("textbox",name="Buscar").count() else None; pg.wait_for_timeout(1000)
    pg.on("response", lambda r: e.w("  respuesta UI:",r.status,r.request.method,r.url,r.text()[:140]) if r.request.method=="DELETE" else None)
    pg.locator("tr",has_text="qa_elim_ui").first.get_by_role("button",name="Eliminar usuario").click(); pg.wait_for_timeout(600); pg.get_by_test_id("button-usuario-eliminar-confirmar").click(); pg.wait_for_timeout(3000)
    acc.append((7,"eliminar usuario qa_elim_ui (UI)",time.strftime("%H:%M:%S"))); e.w("toasts:",pg.locator("[data-sonner-toast]").all_inner_texts())
    e.step(5,"pantalla Auditoría"); pg.goto(WEB+"/auditoria"); pg.wait_for_timeout(4000); pg.screenshot(path=os.path.join(EVD,"CP-11_paso5_pantalla_auditoria.png")); e.w("texto (parcial):",pg.inner_text("body")[:500].replace("\n"," | ")); b.close()
e.step(2,"GET /auditoria posteriores al id inicial")
rows=[x for x in api("GET","/auditoria",token=TADM).json() if int(x["id"])>int(a0)]
for x in sorted(rows,key=lambda x:int(x["id"])): e.w(" ",x["id"],x["usuario_id"],x["nombre_usuario"],x["fecha_hora"],"|",x["accion"])
e.step(3,"cruce acción ↔ registro")
key={1:"REGISTRO",2:"PACIENTES_CREAR",3:"PACIENTES_ACTUALIZAR",4:"PACIENTES_ELIMINAR",5:"USUARIOS_CREAR",6:"USUARIOS_ACTUALIZAR",7:"USUARIOS_ELIMINAR",8:"EXAMENES_CREAR",9:"EXAMENES_ACTUALIZAR",10:"EXAMENES_ELIMINAR",11:"DOCUMENTOS_CREAR",12:"DOCUMENTOS_DESCARGAR",13:"DOCUMENTOS_ELIMINAR"}
ok=0
for n,d,h in sorted(acc):
    m=[x for x in rows if key[n] in x["accion"].upper() or (n==12 and "DESCARG" in x["accion"].upper())]
    e.w(f"acción {n} ({d}, {h}): registros {key[n]}* -> {len(m)}"); ok+= 1 if m else 0
e.w("acciones con registro:",ok,"de",len(acc),"(13 acciones; la 7 se ejecutó 2 veces)")
e.step(4,"login qa_elim_api"); e.w(short(api("POST","/autenticacion/login",body={"nombre_usuario":"qa_elim_api","password":"Cuidarte#Aux2026"})))
