from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-05"); e.w("CP-05", time.strftime("%Y-%m-%d %H:%M"))
TM1, TM2, TADM = login("qa_medico1"), login("qa_medico2"), login("admin")
e.step(0,"cantidad inicial"); e.w(sql("select count(*) from pacientes"))
cnt0 = int(sql("select count(*) from pacientes").split("\n")[2])
e.step(1,"UI registrar Nuevo 1 con MED1")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1400,"height":1000})
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill(PW["qa_medico1"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    pg.goto(WEB+"/pacientes"); pg.get_by_role("tab",name="Registrar Paciente").click(); pg.wait_for_timeout(800)
    for n,v in [("rut","12.345.678-5"),("primer_nombre","Camila"),("apellido_paterno","Rojas"),("apellido_materno","Soto"),("fecha_nacimiento","1992-05-14"),("email","camila.rojas.qa@example.com")]:
        pg.fill(f"input[name={n}]",v)
    pg.locator("[name=sexo]").locator("xpath=..").click() if pg.locator("[name=sexo]").count() else None
    pg.get_by_role("option",name="Femenino").click()
    pg.locator("[name=grupo_sanguineo]").locator("xpath=..").click(); pg.get_by_role("option",name="O+",exact=True).click()
    pg.screenshot(path=os.path.join(EVD,"CP-05_paso1_formulario.png"))
    pg.on("response", lambda r: e.w("  respuesta UI:",r.status,r.request.method,r.url,r.text()[:250]) if r.request.method in("POST","PUT") and "pacientes" in r.url else None)
    pg.get_by_role("button",name="Registrar Paciente").click(); pg.wait_for_timeout(3000)
    e.w("Intento 1 (solo datos de la Tabla 8, sin Estado Civil) toasts:",pg.locator("[data-sonner-toast]").all_inner_texts()); pg.screenshot(path=os.path.join(EVD,"CP-05_paso1_intento1_error.png"))
    e.w("¿Camila Rojas creada tras intento 1?",sql("select count(*) from pacientes where rut='12345678-5'").split(chr(10))[2].strip())
    pg.locator("[name=estado_civil]").locator("xpath=..").click(); pg.get_by_role("option").first.click()
    pg.get_by_role("button",name="Registrar Paciente").click(); pg.wait_for_timeout(3000)
    e.w("Intento 2 (eligiendo un Estado Civil) toasts:",pg.locator("[data-sonner-toast]").all_inner_texts()); pg.screenshot(path=os.path.join(EVD,"CP-05_paso1_intento2.png"))
    e.step(2,"API Nuevo 2 (ADM) y Nuevo 3 (MED2)")
    r=api("POST","/pacientes",token=TADM,body={"rut":"20.111.222-2","primer_nombre":"Tomás","apellido_paterno":"Vega","apellido_materno":"Lara","fecha_nacimiento":"1985-03-10","sexo":"M","email":"tomas.vega.qa@example.com"}); e.w("Nuevo2:",short(r,200)); id2=r.json().get("id")
    r=api("POST","/pacientes",token=TM2,body={"rut":"10.222.333-0","primer_nombre":"Pedro","apellido_paterno":"Soto","apellido_materno":"Diaz","fecha_nacimiento":"1970-07-07","sexo":"M","email":"pedro.soto.qa@example.com"}); e.w("Nuevo3:",short(r,200)); id3=r.json().get("id")
    e.step(3,"RUT en BD"); e.w(sql("select id,rut,primer_nombre,usuario_id from pacientes where rut in ('12345678-5','20111222-2','10222333-0') order by id"))
    id1=sql("select id from pacientes where primer_nombre='Camila' order by id desc limit 1").split("\n")[2].strip(); e.w("id Camila:",id1)
    e.step(4,"vectores inválidos con T_MED1")
    base={"rut":"13.000.000-K","primer_nombre":"Inv","apellido_paterno":"Alido","fecha_nacimiento":"1990-01-01","sexo":"M","email":"inv@example.com"}
    vecs={"a rut 12.345.678-9":{"rut":"12.345.678-9"},"b rut duplicado 11.111.111-1":{"rut":"11.111.111-1"},"c rut ABC":{"rut":"ABC"},"d sin primer_nombre":{"primer_nombre":None},"e fecha 2030-01-01":{"fecha_nacimiento":"2030-01-01"}}
    for k,v in vecs.items():
        body={**base,**v}; body={a:b for a,b in body.items() if b is not None}
        r=api("POST","/pacientes",token=TM1,body=body); e.w(f"vector {k}:",short(r,220))
    r=api("PUT",f"/pacientes/{id1}",token=TM1,body={"rut":"12.345.678-9"}); e.w("PUT rut 12.345.678-9:",short(r,220))
    e.w("cantidad tras inválidos:",sql("select count(*) from pacientes").split("\n")[2].strip(),"(esperado",cnt0+3,")")
    e.step(5,"UI editar Camila (teléfono, dirección) y PUT alergias con ADM")
    pg.goto(WEB+f"/pacientes/{id1}/editar"); pg.wait_for_timeout(2500)
    pg.fill("input[name=telefono]","+56912345678"); pg.fill("[name=direccion]","Av. Apoquindo 4500, Las Condes"); pg.screenshot(path=os.path.join(EVD,"CP-05_paso5_editar.png"))
    pg.get_by_role("button",name="Actualizar").click() if pg.get_by_role("button",name="Actualizar").count() else pg.locator("button[type=submit]").click()
    pg.wait_for_timeout(3000); e.w("toasts:",pg.locator("[data-sonner-toast]").all_inner_texts())
    e.w(sql(f"select id,rut,telefono,direccion,alergias,email from pacientes where id={id1}"))
    r=api("PUT",f"/pacientes/{id1}",token=TADM,body={"alergias":"Penicilina"}); e.w("PUT ADM alergias:",short(r,200))
    e.w(sql(f"select telefono,direccion,alergias,email,fecha_nacimiento,sexo from pacientes where id={id1}"))
    b.close()
e.step(6,"consultas GET con MED1 y ADM")
for n,t in [("MED1",TM1),("ADM",TADM)]:
    r=api("GET","/pacientes",token=t); e.w(n,"GET /pacientes",f"HTTP {r.status_code} ({r.elapsed_s}s) filas={len(r.json())}")
    r=api("GET",f"/pacientes/{id3}",token=t); e.w(n,f"GET /pacientes/{id3} (creado por MED2)",short(r,160))
e.step(7,"auditoría"); e.w(sql("select id,usuario_id,accion from auditoria where accion ilike 'PACIENTES%' order by id")); e.w("cantidad final:",sql("select count(*) from pacientes").split("\n")[2].strip(),"inicial",cnt0)
