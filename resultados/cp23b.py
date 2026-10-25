from qa import *
import subprocess, shutil
e = Ev.__new__(Ev); e.case="CP-23"; e.f=open(os.path.join(EVD,"CP-23.txt"),"a",encoding="utf8")
e.w("(Continuación tras la caída de la API: al ejecutar DROP DATABASE el proceso de la API terminó con un error no controlado de pg (Node.js v18.20.8) y Docker lo reinició por 'restart: unless-stopped'; el script de prueba se interrumpió en ese punto. Los pasos 5 y 6 se ejecutan a continuación con el mismo respaldo.)")
env=dict(os.environ,MSYS_NO_PATHCONV="1")
D=lambda *a,**k: subprocess.run(list(a),capture_output=True,text=True,env=env,**k)
tD=time.time()-25
tables=["usuarios","roles","usuario_roles","tipo_examen_medico","pacientes","examen_medico","documentos_examen","auditoria"]
base={'usuarios': 14, 'roles': 5, 'usuario_roles': 12, 'tipo_examen_medico': 86, 'pacientes': 21, 'examen_medico': 8, 'documentos_examen': 7, 'auditoria': 32}
sha0="cdfc0a08e62c80dce3e644171e9fb5eb6a7d4d3ad7c5404aed73ab7e70aeaa99"
def q(container,db="cuidarteplus"):
    def f(s):
        r=D("docker","exec",container,"psql","-U","postgres","-d",db,"-t","-A","-c",s); return r.stdout.strip()
    return f
cnt=lambda host_exec: {t:int(host_exec(f"select count(*) from {t}")) for t in tables}
e.step(5,"restauración en una segunda instancia vacía"); D("docker","rm","-f","qa-pg2")
r=D("docker","run","-d","--name","qa-pg2","-e","POSTGRES_PASSWORD=postgres","-p","15443:5432","postgres:15-alpine"); e.w("segunda instancia:",r.stdout.strip()[:12])
for _ in range(30):
    if D("docker","exec","qa-pg2","pg_isready","-U","postgres").returncode==0: break
    time.sleep(1)
time.sleep(2); D("docker","exec","qa-pg2","psql","-U","postgres","-c","CREATE DATABASE cuidarteplus")
D("docker","cp",os.path.join(ROOT,"respaldo_qa.dump"),"qa-pg2:/tmp/respaldo_qa.dump"); tr=time.time()
r=D("docker","exec","qa-pg2","pg_restore","-U","postgres","-d","cuidarteplus","--no-owner","/tmp/respaldo_qa.dump"); tr2=time.time(); e.w("pg_restore código",r.returncode,"stderr:",r.stderr[:200],"| tiempo de pg_restore (s):",round(tr2-tr,1))
e.step(6,"comparación y uso del sistema con la base restaurada"); after=cnt(q("qa-pg2")); e.w(after); e.w("cantidades iguales a la línea base:",after==base)
D("docker","rm","-f","qa-api2")
r=D("docker","run","-d","--name","qa-api2","-p","4445:4000","-e","PORT=4000","-e","DATABASE_URL=postgres://postgres:postgres@host.docker.internal:15443/cuidarteplus","-e","JWT_SECRET=0d1d8132f0fde5beabb417b434ff10f1cae8635a461686b0f46ac9c2bbfbd0e8","cuidarteplus-ev-cuidarteplus-backend-ev"); time.sleep(5)
rr=requests.post("http://localhost:4445/autenticacion/login",json={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]},timeout=20); e.w("login MED1 en la API conectada a la base restaurada:",rr.status_code)
T=rr.json().get("token"); d=requests.get(f"http://localhost:4445/documentos/{IDS['DOC_A1']}",headers={"Authorization":"Bearer "+T},timeout=30); e.w("descarga DOC_A1:",d.status_code,len(d.content),"bytes SHA-256",sha_b(d.content),"= línea base:",sha_b(d.content)==sha0)
tF=time.time(); e.w("tiempo transcurrido desde el DROP DATABASE hasta la descarga verificada (s):",round(tF-tD,1),"(umbral RTO: 3600 s; no incluye el tiempo humano de decisión)")
e.step("fin","limpieza y regreso al ambiente base"); D("docker","rm","-f","qa-api2","qa-pg2")
r=D("docker","exec","cuidarteplus-postgres-ev","psql","-U","postgres","-d","postgres","-c","CREATE DATABASE cuidarteplus"); e.w("CREATE DATABASE:",r.stdout.strip(),r.stderr.strip())
r=D("docker","exec","cuidarteplus-postgres-ev","pg_restore","-U","postgres","-d","cuidarteplus","--no-owner","/tmp/respaldo_qa.dump"); e.w("restauración en la base del ambiente:",r.returncode,r.stderr[:100])
time.sleep(3); e.w("API del ambiente operativa:",short(api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]}),60)); e.w(sql("select count(*) usuarios from usuarios"))
