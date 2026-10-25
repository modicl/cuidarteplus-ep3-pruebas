from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-10"); e.w("CP-10", time.strftime("%Y-%m-%d %H:%M"))
TA=login("paciente"); TADM=login("admin"); DOCA1=IDS["DOC_A1"]; a0=sql("select max(id) from auditoria").split("\n")[2].strip()
N=int(sql("select count(*) from examen_medico where paciente_id=1").split("\n")[2]); e.w("N (BD, paciente 1):",N)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(accept_downloads=True) if False else b.new_context(accept_downloads=True).new_page(); pg.set_viewport_size({"width":1500,"height":1200})
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("paciente"); pg.get_by_label("Contraseña").fill(PW["paciente"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    e.step(1,"Mis Resultados: contar"); pg.goto(WEB+"/mis-resultados"); pg.wait_for_timeout(12000)
    cards=pg.locator("text=Completado").count(); e.w("tarjetas en UI:",cards,"vs N:",N); pg.screenshot(path=os.path.join(EVD,"CP-10_paso1_mis_resultados.png"),full_page=True)
    e.step(2,"detalle de cada examen (UI /examenes/{id})")
    lst=api("GET","/examenes/paciente/1",token=TA).json(); e.w("ids API:",[x['id'] for x in lst])
    pg.goto(WEB+f"/examenes/{IDS['EX_A1']}"); pg.wait_for_timeout(9000); e.w("detalle EX_A1 (texto):",pg.inner_text("main") if pg.locator("main").count() else pg.inner_text("body")[:600].replace("\n"," | ")); pg.screenshot(path=os.path.join(EVD,"CP-10_paso2_detalle.png"))
    e.w("campos del JSON de un examen:",sorted(lst[0].keys()))
    e.step(5,"descarga UI de DOC_A1")
    try:
        with pg.expect_download(timeout=20000) as d:
            pg.get_by_role("button",name="resultado_examen.pdf").first.click()
        f=d.value; path=os.path.join(EVD,"CP-10_descarga_ui.pdf"); f.save_as(path); e.w("descarga UI:",f.suggested_filename,"SHA-256",sha(path))
    except Exception as ex: e.w("descarga UI falló:",str(ex)[:200])
    b.close()
e.step(3,"GET /pacientes/1"); r=api("GET","/pacientes/1",token=TA); e.w(short(r,300))
e.step(4,"ningún examen del paciente B"); e.w("paciente_ids en la lista:",sorted(set(x['paciente_id'] for x in lst)))
e.step(5,"API descarga"); r=api("GET",f"/documentos/{DOCA1}",token=TA); e.w("HTTP",r.status_code,"Content-Type:",r.headers.get("Content-Type"),"Content-Disposition:",r.headers.get("Content-Disposition"),"SHA-256:",sha_b(r.content),"original:",sha(DAT+"/resultado_examen.pdf"),"| igual:",sha_b(r.content)==sha(DAT+"/resultado_examen.pdf"))
e.step(6,"auditoría (ADM)"); r=api("GET","/auditoria",token=TADM); rows=[x for x in r.json() if int(x['id'])>int(a0)]; e.w("GET /auditoria",r.status_code,"registros nuevos:",len(rows)); 
for x in rows: e.w(" ",x)
e.w("registros con 'descarg':",[x for x in rows if 'descarg' in json.dumps(x).lower()])
