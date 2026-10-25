from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-08"); e.w("CP-08", time.strftime("%Y-%m-%d %H:%M"))
TM1, TADM = login("qa_medico1"), login("admin"); EXD, EXD2, DOCD, DOCD2 = IDS["EX_DEL"], IDS["EX_DEL2"], IDS["DOC_DEL"], IDS["DOC_DEL2"]
e.step(0,"cantidades iniciales"); e.w(sql("select (select count(*) from examen_medico) examenes,(select count(*) from documentos_examen) docs")); a0=sql("select max(id) from auditoria").split("\n")[2].strip()
e.w(sql(f"select column_name from information_schema.columns where table_name in ('examen_medico','documentos_examen') and (column_name ilike '%elimin%' or column_name ilike '%delet%' or column_name ilike '%activo%')"))
with sync_playwright() as p:
    b=p.chromium.launch(); dl=[]
    def ctx(user):
        pg=b.new_page(); pg.set_viewport_size({"width":1500,"height":1100}); pg.on("dialog", lambda d:(dl.append(d.message), d.accept()))
        pg.on("response", lambda r: e.w("  respuesta UI:",r.status,r.request.method,r.url,r.text()[:120]) if r.request.method in("DELETE",) else None)
        pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill(user); pg.get_by_label("Contraseña").fill(PW[user]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000); return pg
    e.step(1,"MED1 busca el botón Eliminar en EX_DEL"); pg=ctx("qa_medico1"); pg.goto(WEB+f"/examenes/{EXD}"); pg.wait_for_timeout(9000)
    e.w("botón 'Eliminar' visible para MED1 en el detalle:", pg.get_by_role("button",name="Eliminar",exact=True).count()>0); pg.screenshot(path=os.path.join(EVD,"CP-08_paso1_detalle_med1.png"))
    pg.goto(WEB+"/examenes"); pg.wait_for_timeout(9000); e.w("botón 'Eliminar examen' en el listado para MED1:", pg.get_by_label("Eliminar examen").count())
    r=api("DELETE",f"/examenes/{EXD}",token=TM1); e.w("DELETE /examenes/%s con T_MED1:"%EXD, short(r,200))
    r=api("DELETE",f"/documentos/{DOCD}",token=TM1); e.w("DELETE /documentos/%s con T_MED1:"%DOCD, short(r,200))
    e.w("Diferencia con RF-3.3 anotada; se sigue con ADM.")
    e.step(2,"ADM: Eliminar y Cancelar"); pa=ctx("admin"); pa.goto(WEB+f"/examenes/{EXD}"); pa.wait_for_timeout(9000)
    pa.get_by_role("button",name="Eliminar",exact=True).first.click(); pa.wait_for_timeout(800); e.w("diálogo:",pa.get_by_role("dialog").inner_text().replace("\n"," | ")); pa.screenshot(path=os.path.join(EVD,"CP-08_paso2_dialogo.png"))
    pa.get_by_role("button",name="Cancelar").click(); pa.wait_for_timeout(1000); e.w(sql(f"select count(*) examen from examen_medico where id={EXD}"))
    e.step(3,"ADM: confirmar"); pa.get_by_role("button",name="Eliminar",exact=True).first.click(); pa.wait_for_timeout(500); pa.get_by_role("dialog").get_by_role("button",name="Eliminar").click(); pa.wait_for_timeout(4000); e.w("URL:",pa.url,"toasts:",pa.locator("[data-sonner-toast]").all_inner_texts())
    e.step(4,"ya no aparece en listados"); r=api("GET","/examenes",token=TM1); e.w("MED1 GET /examenes contiene EX_DEL:",any(x['id']==EXD for x in r.json()))
    TA=login("paciente"); r=api("GET","/examenes/paciente/1",token=TA); e.w("PAC_A /examenes/paciente/1 contiene EX_DEL:",any(x['id']==EXD for x in r.json()))
    e.step(5,"BD"); e.w(sql(f"select id from examen_medico where id={EXD}")); e.w(sql(f"select id,examen_medico_id from documentos_examen where examen_medico_id={EXD}"))
    e.step(6,"eliminar solo el documento de EX_DEL2 (ADM, confirm del navegador)"); dl.clear(); pa.goto(WEB+f"/examenes/{EXD2}"); pa.wait_for_timeout(9000)
    pa.get_by_role("button",name="Eliminar resultado_eliminar2.pdf").click(); pa.wait_for_timeout(4000); e.w("confirm del navegador:",dl,"toasts:",pa.locator("[data-sonner-toast]").all_inner_texts())
    e.w(sql(f"select id,examen_medico_id,nombre_archivo from documentos_examen where id={DOCD2}")); e.w(sql(f"select id from examen_medico where id={EXD2}"))
    b.close()
e.step("0/5","cantidades finales"); e.w(sql("select (select count(*) from examen_medico) examenes,(select count(*) from documentos_examen) docs"),"(iniciales: examenes 10, docs 8 → tras CP-07)")
e.step(7,"auditoría"); e.w(sql(f"select id,usuario_id,accion from auditoria where id>{a0} order by id"))
