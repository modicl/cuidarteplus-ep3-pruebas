from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-13"); e.w("CP-13", time.strftime("%Y-%m-%d %H:%M"))
e.w("Condición: ejecutar la parte A si REQ-PROP-01 se incorpora al ERS. REQ-PROP-01 es un requisito propuesto; se ejecuta para registrar el estado (brecha) y no se asume incorporado.")
TM1,TA,TADM=login("qa_medico1"),login("paciente"),login("admin"); a0=sql("select max(id) from auditoria").split("\n")[2].strip()
e.step(1,"A: /registro y política de privacidad")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1300,"height":1000})
    pg.goto(WEB+"/registro"); pg.wait_for_timeout(2000)
    e.w("casillas de verificación en /registro:",pg.locator("input[type=checkbox]").count(),"| enlaces a política:",pg.get_by_role("link",name="Política de Privacidad").count()); e.w("campos:",pg.locator("input").evaluate_all("els=>els.map(e=>e.name+':'+e.type)")); pg.screenshot(path=os.path.join(EVD,"CP-13_paso1_registro.png"))
    pg.goto(WEB+"/politica-privacidad"); pg.wait_for_timeout(2000); e.w("sin sesión /politica-privacidad ->",pg.url)
    e.step(2,"A: enviar sin casilla"); pg.goto(WEB+"/registro"); pg.fill("input[name=nombre_usuario]","qa_consent01"); pg.fill("input[name=correo]","qa_consent01@example.com"); pg.fill("input[name=password]","Cuidarte#Cons2026")
    pg.get_by_role("button",name="Crear cuenta").click(); pg.wait_for_timeout(2500); e.w("UI sin casilla: URL",pg.url,"toasts",pg.locator("[data-sonner-toast]").all_inner_texts()); b.close()
e.w(sql("select count(*) from usuarios where nombre_usuario='qa_consent01'"))
r=api("POST","/autenticacion/registro",body={"nombre_usuario":"qa_consent02","password":"Cuidarte#Cons2026","correo":"qa_consent02@example.com"}); e.w("API sin campo de consentimiento:",short(r,200))
e.step(3,"A: consentimiento en BD"); e.w(sql("select table_name from information_schema.tables where table_schema='public' order by 1")); e.w(sql("select column_name,table_name from information_schema.columns where table_schema='public' and (column_name ilike '%consent%' or column_name ilike '%politica%' or column_name ilike '%acept%')"))
e.step(4,"B: PAC_A intenta corregir su teléfono"); e.w("teléfono antes:",sql("select telefono from pacientes where id=1").split("\n")[2].strip())
r=api("PUT","/pacientes/1",token=TA,body={"telefono":"+56911112222"}); e.w("PUT con T_PAC_A:",short(r,200)); e.w("teléfono después:",sql("select telefono from pacientes where id=1").split("\n")[2].strip())
e.step(5,"B: MED1 corrige"); r=api("PUT","/pacientes/1",token=TM1,body={"telefono":"+56912345678"}); e.w("PUT con T_MED1:",short(r,200)); r=api("GET","/pacientes/1",token=TA); e.w("PAC_A consulta teléfono:",r.json().get("telefono"))
e.step(6,"B: auditoría"); rows=[x for x in api("GET","/auditoria",token=TADM).json() if int(x["id"])>int(a0)]
for x in rows: e.w(" ",x["id"],x["usuario_id"],x["nombre_usuario"],x["fecha_hora"],"|",x["accion"])
