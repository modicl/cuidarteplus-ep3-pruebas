from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-01"); e.w("CP-01 ejecutado", time.strftime("%Y-%m-%d %H:%M"))
e.step(1, "UI login MED1")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(WEB + "/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill(PW["qa_medico1"])
    pg.get_by_role("button", name="Entrar").click(); pg.wait_for_url("**/home", timeout=15000); pg.wait_for_timeout(2500)
    e.w("URL tras login:", pg.url)
    nav = pg.get_by_role("navigation", name="Navegación principal").inner_text().replace("\n"," | "); e.w("Menú:", nav)
    pg.screenshot(path=os.path.join(EVD,"CP-01_paso1_home_medico.png"))
    ls = pg.evaluate("Object.keys(localStorage)"); e.w("localStorage claves:", ls)
    e.step(4, "UI cerrar sesión")
    pg.get_by_role("button", name="Menú de usuario").click(); pg.get_by_role("menuitem", name="Cerrar sesión").click(); pg.wait_for_timeout(1500)
    e.w("URL tras cerrar sesión:", pg.url); e.w("localStorage claves:", pg.evaluate("Object.keys(localStorage)"))
    pg.go_back(); pg.wait_for_timeout(1500); e.w("URL tras Atrás:", pg.url); e.w("Texto visible:", pg.inner_text("body")[:150].replace("\n"," | "))
    pg.screenshot(path=os.path.join(EVD,"CP-01_paso4_atras.png")); b.close()
e.step(2, "API login"); r = api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]}); e.w(short(r,80))
T1 = r.json()["token"]
e.step(3, "payload JWT"); pl = jwt(T1); e.w(json.dumps(pl)); e.w("exp - iat (min):", (pl["exp"]-pl["iat"])/60)
e.w("contiene contraseña:", "Med2026" in json.dumps(pl) or "password" in json.dumps(pl).lower())
e.step(5, "logout API")
for m,pth in [("POST","/autenticacion/logout"),("GET","/autenticacion/logout"),("POST","/logout")]:
    e.w(m,pth,short(api(m,pth,token=T1)))
e.step(6, "reutilizar T1")
e.w("GET /pacientes", short(api("GET","/pacientes",token=T1),100)); e.w("GET /examenes", short(api("GET","/examenes",token=T1),100))
e.step(7, "refresh en Swagger")
oa = api("GET","/openapi.json").json(); paths = [k for k in oa["paths"] if "refresh" in k.lower() or "renov" in k.lower() or "logout" in k.lower()]
e.w("rutas refresh/logout en openapi:", paths); e.w("rutas /autenticacion en openapi:", [k for k in oa["paths"] if "autenticacion" in k])
e.w("POST /autenticacion/refresh:", short(api("POST","/autenticacion/refresh",token=T1)))
