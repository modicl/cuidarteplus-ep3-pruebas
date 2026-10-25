from qa import *
import threading, http.server, socketserver, re
from playwright.sync_api import sync_playwright
e = Ev("CP-21"); e.w("CP-21", time.strftime("%Y-%m-%d %H:%M"))
TM=login("qa_medico1")
e.step(1,"HTTP plano y respuesta del frontend"); r=requests.get(WEB,allow_redirects=False,timeout=10); e.w("GET http://localhost:3333:",r.status_code,"Location:",r.headers.get("Location"),dict(r.headers))
r=requests.get(API+"/",allow_redirects=False,timeout=10); e.w("GET http://localhost:4444/:",r.status_code,"Location:",r.headers.get("Location"),"Strict-Transport-Security:",r.headers.get("Strict-Transport-Security"))
e.w("HSTS en el frontend:",requests.get(WEB,timeout=10).headers.get("Strict-Transport-Security"))
html=requests.get(WEB,timeout=10).text; js=re.findall(r'src="(/assets/[^"]+\.js)"',html); body=requests.get(WEB+js[0],timeout=20).text if js else ""
e.w("URL de la API incrustada en el JS del frontend:",sorted(set(re.findall(r'https?://localhost:\d+',body))))
e.step(2,"captura de tráfico (tcpdump en el netns de la API, equivalente a Wireshark)")
cap=subprocess.Popen("docker run --rm --net container:cuidarteplus-backend-ev nicolaka/netshoot timeout 20 tcpdump -i eth0 -A -s0 -l tcp port 4000",shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf8",errors="replace"); time.sleep(8)
r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]}); t=r.json()["token"]; api("GET","/pacientes/1",token=t); time.sleep(14); out=cap.communicate()[0]
open(os.path.join(EVD,"tls","captura_tcpdump_api.txt"),"w",encoding="utf8").write(out)
e.w("captura guardada en evidencia/tls/captura_tcpdump_api.txt (",len(out),"caracteres )")
e.w("contraseña 'Cuidarte#Med2026' en texto claro en la captura:",PW["qa_medico1"] in out,"| token JWT completo en texto claro:",t in out)
e.step(3,"SHOW ssl y sslmode"); e.w(sql("show ssl")); e.w("DATABASE_URL del compose:","postgres://...@cuidarteplus-postgres-ev:5432/cuidarteplus (sin sslmode)" ); e.w([l.strip() for l in open(os.path.join(ROOT,"..","docker-compose.yml")) if "DATABASE_URL" in l])
e.w([l.strip() for l in open(os.path.join(ROOT,"..","BACKEND","src","db.js"),encoding="utf8") if "ssl" in l.lower() or "connectionString" in l])
e.step(4,"CSRF: cookies y almacenamiento del token")
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(); pg=c.new_page(); pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("qa_medico1"); pg.get_by_label("Contraseña").fill(PW["qa_medico1"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    e.w("cookies del navegador tras iniciar sesión:",c.cookies(),"| claves en localStorage:",pg.evaluate("Object.keys(localStorage)"))
    e.step(5,"fetch PUT desde otro origen (http://localhost:9999) con credentials include y sin Authorization")
    os.makedirs(os.path.join(ROOT,"evidencia","tls","web9999"),exist_ok=True); open(os.path.join(ROOT,"evidencia","tls","web9999","csrf.html"),"w").write("<html><body>csrf</body></html>")
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(s,*a,**k): super().__init__(*a,directory=os.path.join(ROOT,"evidencia","tls","web9999"),**k)
        def log_message(s,*a): pass
    srv=socketserver.TCPServer(("",9999),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
    before=sql("select telefono from pacientes where id=1")
    pg2=c.new_page(); pg2.goto("http://localhost:9999/csrf.html")
    res=pg2.evaluate("""async()=>{try{const r=await fetch('http://localhost:4444/pacientes/1',{method:'PUT',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({telefono:'+56900009999'})});return {status:r.status,body:(await r.text()).slice(0,120)}}catch(e){return {error:String(e)}}}""")
    e.w("resultado del fetch:",res); e.w("teléfono antes/después:",before.split(chr(10))[2].strip(),"/",sql("select telefono from pacientes where id=1").split(chr(10))[2].strip())
    res2=pg2.evaluate("""async()=>{try{const r=await fetch('http://localhost:4444/pacientes/1',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({telefono:'+56900009999'})});return {status:r.status,body:(await r.text()).slice(0,120)}}catch(e){return {error:String(e)}}}""")
    e.w("variante sin credentials (el navegador sí envía la solicitud):",res2); e.w("teléfono tras la variante:",sql("select telefono from pacientes where id=1").split(chr(10))[2].strip()); b.close(); srv.shutdown()
e.step(6,"CORS: OPTIONS /usuarios")
for o in ["http://evil.example.test",WEB]:
    r=requests.options(API+"/usuarios",headers={"Origin":o,"Access-Control-Request-Method":"GET","Access-Control-Request-Headers":"authorization"},timeout=10); e.w(f"Origin {o}: HTTP {r.status_code} Access-Control-Allow-Origin={r.headers.get('Access-Control-Allow-Origin')} Allow-Headers={r.headers.get('Access-Control-Allow-Headers')}")
e.step(8,"npm audit --omit=dev")
for d in ["BACKEND","FRONTEND"]:
    r=subprocess.run(["npm","audit","--omit=dev","--json"],cwd=os.path.join(ROOT,"..",d),capture_output=True,text=True,shell=True,encoding="utf8"); open(os.path.join(EVD,f"npm_audit_{d.lower()}.json"),"w",encoding="utf8").write(r.stdout)
    try: m=json.loads(r.stdout)["metadata"]["vulnerabilities"]; e.w(d,"vulnerabilidades:",m)
    except Exception as ex: e.w(d,"npm audit sin JSON válido:",r.stdout[:200],r.stderr[:200])
r=subprocess.run("docker run --rm --entrypoint node node:18-alpine -v",shell=True,capture_output=True,text=True); e.w("imagen base del backend node:18-alpine ->",r.stdout.strip(),"(Node 18 llegó al fin de su soporte el 2025-04-30)")
e.w([l.strip() for l in open(os.path.join(ROOT,"..","BACKEND","Dockerfile")) if l.startswith("FROM")]); e.w([l.strip() for l in open(os.path.join(ROOT,"..","FRONTEND","Dockerfile")) if l.startswith("FROM")])
e.step(9,"checklist de cabeceras, /docs, X-Powered-By y /files/documentos")
for n,u in [("frontend","http://localhost:3333/"),("API /","http://localhost:4444/"),("API /docs/","http://localhost:4444/docs/")]:
    h=requests.get(u,timeout=10).headers
    e.w(n,{k:h.get(k) for k in ["Content-Security-Policy","X-Content-Type-Options","X-Frame-Options","Referrer-Policy","Strict-Transport-Security","X-Powered-By","Server"]})
e.w("/docs accesible sin autenticación:",requests.get(API+"/docs/",timeout=10).status_code,"| /files/documentos/:",requests.get(API+"/files/documentos/",timeout=10).status_code)
