from qa import *
import subprocess
e = Ev("CP-14"); e.w("CP-14", time.strftime("%Y-%m-%d %H:%M"))
SECRET=open(os.path.join(ROOT,"..",".env")).read().split("JWT_SECRET=")[1].split()[0]
README_SECRET=[l for l in open(os.path.join(ROOT,"..","README.md"),encoding="utf8") if "JWT_SECRET" in l][0].split("`")[1]
e.w("JWT_SECRET de .env == publicado en README.md:",SECRET==README_SECRET)
js=lambda payload,secret,opts="{}": subprocess.run(["node","-e",f"const jwt=require(process.argv[1]);console.log(jwt.sign({json.dumps(payload)},{json.dumps(secret)},{opts}))",os.path.join(ROOT,"..","BACKEND","node_modules","jsonwebtoken")],capture_output=True,text=True).stdout.strip()
e.step(1,"contraseña vacía"); r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":""}); e.w(short(r,250))
e.step(2,"15 intentos fallidos (qa_paciente_b), 1 por segundo"); first=None
for i in range(1,16):
    r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_paciente_b","password":f"Intento#{i:03d}"}); e.w(f"intento {i}: HTTP {r.status_code} {r.text[:60]}  Retry-After={r.headers.get('Retry-After')}")
    if r.status_code in (423,429) and first is None: first=i
    time.sleep(1)
e.w("primer intento con bloqueo/limitación:",first)
e.step(3,"contraseña correcta tras los 15 intentos"); r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_paciente_b","password":PW["qa_paciente_b"]}); e.w(short(r,100))
e.step(4,"7 tokens inválidos contra GET /pacientes")
T=login("qa_medico1"); pl=jwt(T); base={k:v for k,v in pl.items() if k not in("iat","exp")}
parts=T.split("."); import base64
b64=lambda d: base64.urlsafe_b64encode(json.dumps(d,separators=(",",":")).encode()).rstrip(b"=").decode()
pl2=dict(pl); pl2["rolNombre"]="admin"; t1=parts[0]+"."+b64(pl2)+"."+parts[2]
t2=js(base,"clave-equivocada-123","{expiresIn:'2h'}")
t3=b64({"alg":"none","typ":"JWT"})+"."+b64({**base,"iat":int(time.time()),"exp":int(time.time())+7200})+"."
t4=js({**base,"exp":int(time.time())-3600},SECRET) if False else js({**base,"iat":int(time.time())-7200,"exp":int(time.time())-3600},SECRET)
t5=js(base,"inseguro","{expiresIn:'2h'}"); t6=js(base,README_SECRET,"{expiresIn:'2h'}")
cases=[("1 payload rolNombre=admin sin re-firmar",t1,"Bearer"),("2 firmado con clave-equivocada-123",t2,"Bearer"),("3 alg none",t3,"Bearer"),("4 exp en el pasado (firmado con JWT_SECRET)",t4,"Bearer"),("5 firmado con 'inseguro'",t5,"Bearer"),("6 firmado con JWT_SECRET del README",t6,"Bearer"),("7a cabecera 'Authorization: Token <jwt>'",T,"Token"),]
for n,t,sch in cases:
    r=requests.get(API+"/pacientes",headers={"Authorization":f"{sch} {t}"},timeout=30); e.w(f"token {n}: HTTP {r.status_code} ({round(r.elapsed.total_seconds(),1)}s) {r.text[:90]!r}")
r=requests.get(API+"/pacientes",timeout=30); e.w("token 7b sin cabecera: HTTP",r.status_code,r.text[:90])
e.step(5,"API sin JWT_SECRET")
env=dict(os.environ,PORT="4555",DATABASE_URL="postgres://postgres:postgres@localhost:15442/cuidarteplus"); env.pop("JWT_SECRET",None)
pr=subprocess.Popen(["node","src/app.js"],cwd=os.path.join(ROOT,"..","BACKEND"),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); time.sleep(4)
e.w("proceso sigue vivo (arrancó):",pr.poll() is None)
try:
    r=requests.get("http://localhost:4555/",timeout=5); e.w("GET / en puerto 4555:",r.status_code,r.text)
    r=requests.get("http://localhost:4555/pacientes",headers={"Authorization":"Bearer "+t5},timeout=30); e.w("GET /pacientes con token firmado con 'inseguro' contra la API sin JWT_SECRET: HTTP",r.status_code,r.text[:80])
finally: pr.terminate()
e.step("5b","repetición sin .env: cwd distinto para que dotenv no cargue BACKEND/.env (la primera prueba del paso 5 cargó el JWT_SECRET desde BACKEND/.env)")
import tempfile
td=tempfile.mkdtemp()
env=dict(os.environ,PORT="4556",DATABASE_URL="postgres://postgres:postgres@localhost:15442/cuidarteplus"); env.pop("JWT_SECRET",None)
pr=subprocess.Popen(["node",os.path.join(ROOT,"..","BACKEND","src","app.js")],cwd=td,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); time.sleep(4)
e.w("proceso vivo (arrancó sin JWT_SECRET):",pr.poll() is None)
try:
    r=requests.get("http://localhost:4556/",timeout=5); e.w("GET / :",r.status_code,r.text)
    r=requests.get("http://localhost:4556/pacientes",headers={"Authorization":"Bearer "+t5},timeout=30); e.w("GET /pacientes con token firmado con 'inseguro': HTTP",r.status_code,r.text[:80])
finally: pr.terminate(); time.sleep(1); e.w("salida del proceso:",(pr.stdout.read() or "")[:300])
