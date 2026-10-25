from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-03"); e.w("CP-03", time.strftime("%Y-%m-%d %H:%M"))
vec = {"a":"Segura#2026","b":"cuidarte#2026x","c":"CUIDARTE#2026X","d":"Cuidarte#Segura","e":"Cuidarte2026ab","f":"Cuidarte#2026"}
def ui_reg(pg, u, c, pw, rut=None):
    pg.goto(WEB+"/registro"); pg.fill("input[name=nombre_usuario]",u); pg.fill("input[name=correo]",c); pg.fill("input[name=password]",pw)
    if rut: pg.fill("input[name=rut]",rut)
    pg.get_by_role("button",name="Crear cuenta").click(); pg.wait_for_timeout(2500)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    e.step(1,"UI registro qa_registro01 con vector f"); ui_reg(pg,"qa_registro01","qa_registro01@example.com",vec["f"]); e.w("URL:",pg.url); pg.screenshot(path=os.path.join(EVD,"CP-03_paso1_registro_f.png"))
    e.w("toasts/mensajes:", [t for t in pg.locator("[data-sonner-toast]").all_inner_texts()])
    e.step(2,"login y rol en BD")
    T = login("qa_registro01", vec["f"]); e.w("login:", bool(T))
    e.w(sql("select u.nombre_usuario, r.nombre as rol from usuarios u join usuario_roles ur on ur.usuario_id=u.id join roles r on r.id=ur.rol_id where u.nombre_usuario='qa_registro01'"))
    e.step(3,"UI pantallas de gestión con esa sesión")
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_registro01"); pg.get_by_label("Contraseña").fill(vec["f"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    for ru in ["/pacientes","/usuarios","/auditoria"]:
        pg.goto(WEB+ru); pg.wait_for_timeout(2500); e.w(ru,"-> URL final",pg.url,"| texto:",pg.inner_text("body")[:200].replace("\n"," | ")); pg.screenshot(path=os.path.join(EVD,f"CP-03_paso3{ru.replace('/','_')}.png"))
    e.w("menú:", pg.get_by_role("navigation",name="Navegación principal").inner_text().replace("\n"," | "))
    pg.evaluate("localStorage.clear()")
    e.step(4,"duplicados")
    r1 = api("POST","/autenticacion/registro",body={"nombre_usuario":"qa_registro01","password":vec["f"],"correo":"otro_dup@example.com"}); e.w("mismo usuario:",short(r1))
    r2 = api("POST","/autenticacion/registro",body={"nombre_usuario":"qa_registro_dup","password":vec["f"],"correo":"qa_registro01@example.com"}); e.w("mismo correo:",short(r2))
    e.step(5,"qa_registro02 con RUT 15.678.234-3")
    r = api("POST","/autenticacion/registro",body={"nombre_usuario":"qa_registro02","password":vec["f"],"correo":"qa_registro02@example.com","rut":"15.678.234-3"}); e.w(short(r))
    e.w(sql("select id,rut,primer_nombre,apellido_paterno,fecha_nacimiento,sexo,usuario_id from pacientes where rut='15678234-3'"))
    e.step(6,"API vectores a-e")
    for k in "abcde":
        r = api("POST","/autenticacion/registro",body={"nombre_usuario":f"qa_reg_{k}","password":vec[k],"correo":f"qa_reg_{k}@example.com"}); e.w(f"vector {k} ({vec[k]}):",short(r,200))
        e.w("  ¿usuario creado en BD?", sql(f"select count(*) from usuarios where nombre_usuario='qa_reg_{k}'").split("\n")[2].strip())
    e.step(6,"UI vectores a y f")
    ui_reg(pg,"qa_reg_ui_a","qa_reg_ui_a@example.com",vec["a"]); e.w("UI vector a -> URL:",pg.url,"| toasts:",pg.locator("[data-sonner-toast]").all_inner_texts()); pg.screenshot(path=os.path.join(EVD,"CP-03_paso6_ui_vector_a.png"))
    e.w("  ¿creado?", sql("select count(*) from usuarios where nombre_usuario='qa_reg_ui_a'").split("\n")[2].strip())
    ui_reg(pg,"qa_reg_ui_f","qa_reg_ui_f@example.com",vec["f"]); e.w("UI vector f -> URL:",pg.url,"| toasts:",pg.locator("[data-sonner-toast]").all_inner_texts())
    b.close()
e.step(7,"auditoría de registros"); e.w(sql("select id,usuario_id,accion from auditoria where accion ilike 'REGISTRO%' order by id"))
