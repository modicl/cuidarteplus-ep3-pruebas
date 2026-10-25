from qa import *
import urllib.parse
from playwright.sync_api import sync_playwright
e = Ev("CP-17"); e.w("CP-17", time.strftime("%Y-%m-%d %H:%M"))
TM1=login("qa_medico1"); cnt=lambda: sql("select (select count(*) from usuarios) usuarios,(select count(*) from pacientes) pacientes,(select count(*) from roles) roles,(select count(*) from examen_medico) examenes")
e.step(0,"cantidades iniciales"); c0=cnt(); e.w(c0); l0=int(subprocess.run("docker logs cuidarteplus-backend-ev 2>&1 | wc -l",shell=True,capture_output=True,text=True).stdout.strip())
def lg(n,r,extra=""): e.w(f"{n}: HTTP {r.status_code} ({r.elapsed_s}s) {r.text[:200]!r} {extra}")
e.step(1,"V1 en nombre_usuario"); lg("V1",api("POST","/autenticacion/login",body={"nombre_usuario":"' OR '1'='1","password":"x"}))
e.step(2,"V2 admin'--"); lg("V2",api("POST","/autenticacion/login",body={"nombre_usuario":"admin'--","password":"x"}))
e.step(3,"V3 en password con usuario existente"); lg("V3",api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":"' OR '1'='1"}))
e.step(4,"V4 RUT en URL"); lg("V4",api("GET","/pacientes/buscar/rut/"+urllib.parse.quote("' OR '1'='1",safe="")))
e.step(5,"V5 DROP TABLE en primer_nombre"); lg("V5",api("POST","/pacientes",token=TM1,body={"rut":"6.543.210-K","primer_nombre":"Robert'); DROP TABLE pacientes;--","apellido_paterno":"Tables","fecha_nacimiento":"1990-01-01","sexo":"M","email":"robert.tables.qa@example.com"}))
e.w(sql("select to_regclass('public.pacientes') tabla_pacientes")); e.w(sql("select id,primer_nombre from pacientes order by id desc limit 1"))
e.step(6,"V1 desde la pantalla de login")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("' OR '1'='1"); pg.get_by_label("Contraseña").fill("x"); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_timeout(2500)
    e.w("URL:",pg.url,"toasts:",pg.locator("[data-sonner-toast]").all_inner_texts(),"localStorage:",pg.evaluate("Object.keys(localStorage)")); pg.screenshot(path=os.path.join(EVD,"CP-17_paso6_ui.png")); b.close()
e.step(8,"cantidades finales (antes de ZAP) y log del servidor"); c1=cnt(); e.w(c1); e.w("cantidades iguales a las iniciales, salvo el paciente de V5 (si se creó):",c0==c1)
out=subprocess.run("docker logs cuidarteplus-backend-ev 2>&1 | tail -n +%d"%(l0+1),shell=True,capture_output=True,text=True,encoding="utf8").stdout
e.w("líneas nuevas del log:\n"+"\n".join(l for l in out.splitlines() if "login" in l or "buscar" in l or "POST /pacientes" in l)[:1500])
