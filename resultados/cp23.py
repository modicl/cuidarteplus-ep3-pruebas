from qa import *
import subprocess, shutil
e = Ev("CP-23"); e.w("CP-23", time.strftime("%Y-%m-%d %H:%M"))
print(restore()); e.w("estado base restaurado antes del caso; ", sql("select (select count(*) from usuarios) u,(select count(*) from pacientes) p,(select count(*) from examen_medico) e,(select count(*) from documentos_examen) d"))
env=dict(os.environ,MSYS_NO_PATHCONV="1")
D=lambda *a,**k: subprocess.run(list(a),capture_output=True,text=True,env=env,**k)
e.step(1,"política de respaldo documentada")
hits=subprocess.run("grep -rniE 'respaldo|backup|retenci|RTO|RPO|pg_dump' README.md BACKEND/README.md docker-compose.yml BACKEND/Dockerfile docs/CLAUDE.md --include=* 2>/dev/null | head -20",shell=True,cwd=os.path.join(ROOT,".."),capture_output=True,text=True).stdout
e.w("búsqueda de 'respaldo|backup|retención|RTO|RPO|pg_dump' en README.md, BACKEND/README.md, docker-compose.yml, Dockerfile y docs/CLAUDE.md (CLAUDE.md es contexto del equipo, no del producto):\n"+hits)
e.w("frecuencia / retención / ubicación / responsable definidos en la entrega: no se encontró ninguno (ver búsqueda)")
tables=["usuarios","roles","usuario_roles","tipo_examen_medico","pacientes","examen_medico","documentos_examen","auditoria"]
cnt=lambda host_exec: {t:int(host_exec(f"select count(*) from {t}")) for t in tables}
def q(container,db="cuidarteplus"):
    def f(s):
        r=D("docker","exec",container,"psql","-U","postgres","-d",db,"-t","-A","-c",s); return r.stdout.strip()
    return f
e.step(2,"línea base"); base=cnt(q("cuidarteplus-postgres-ev")); e.w(base)
x=api("GET","/documentos/%s"%IDS["DOC_A1"],token=login("qa_medico1")); sha0=sha_b(x.content); e.w("SHA-256 DOC_A1:",sha0)
e.step(3,"respaldo"); t0=time.time(); e.w("hora del respaldo:",time.strftime("%H:%M:%S"))
r=D("docker","exec","cuidarteplus-postgres-ev","pg_dump","-U","postgres","-Fc","cuidarteplus","-f","/tmp/respaldo_qa.dump"); e.w("pg_dump:",r.returncode,r.stderr[:100])
r=D("docker","cp","cuidarteplus-postgres-ev:/tmp/respaldo_qa.dump",os.path.join(ROOT,"respaldo_qa.dump")); e.w("docker cp:",r.returncode,os.path.getsize(os.path.join(ROOT,"respaldo_qa.dump")),"bytes SHA-256",sha(os.path.join(ROOT,"respaldo_qa.dump")))
e.step(4,"desastre: DROP DATABASE"); tD=time.time()
r=D("docker","exec","cuidarteplus-postgres-ev","psql","-U","postgres","-d","postgres","-c","DROP DATABASE cuidarteplus WITH (FORCE)"); e.w(r.stdout.strip(),r.stderr.strip())
r=requests.get(API+"/examenes/paciente/1",headers={"Authorization":"Bearer "+login("admin") if False else "x"},timeout=10); e.w("API tras el desastre, GET /examenes/paciente/1 con token inválido:",r.status_code)
try: r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]}); e.w("login tras el desastre:",short(r,150))
except Exception as ex: e.w("login tras el desastre: error",str(ex)[:100])
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
