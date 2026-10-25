from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-02"); e.w("CP-02", time.strftime("%Y-%m-%d %H:%M"))
e.step("1-2","UI contraseña incorrecta")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill("Cuidarte#Med2027")
    pg.get_by_role("button", name="Entrar").click(); pg.wait_for_timeout(2000)
    e.w("URL:", pg.url); e.w("Mensaje visible:", [t for t in pg.locator("[data-sonner-toast], [role=alert], .Mui-error, p").all_inner_texts() if t.strip()][:6])
    e.w("localStorage:", pg.evaluate("Object.keys(localStorage)")); pg.screenshot(path=os.path.join(EVD,"CP-02_paso1_ui_error.png"))
    e.step(7,"sin sesión abrir /home"); pg.goto(WEB+"/home"); pg.wait_for_timeout(1500); e.w("URL final:", pg.url); b.close()
e.step(3,"API RESP_A"); A = api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":"Cuidarte#Med2027"}); e.w(short(A)); e.w("headers:", dict(A.headers))
e.step(4,"API RESP_B"); B = api("POST","/autenticacion/login",body={"nombre_usuario":"qa_inexistente","password":"Cuidarte#Mala2027"}); e.w(short(B)); e.w("headers:", dict(B.headers))
e.step(5,"comparar"); e.w("mismo código:", A.status_code==B.status_code, "| mismo cuerpo:", A.text==B.text)
e.step(6,"datos técnicos/token/cookie"); e.w("Set-Cookie:", A.headers.get("Set-Cookie"), B.headers.get("Set-Cookie")); e.w("token en cuerpo:", "token" in A.text or "token" in B.text)
e.step(8,"sin token GET /examenes/paciente/1"); r = api("GET","/examenes/paciente/1"); e.w(short(r))
