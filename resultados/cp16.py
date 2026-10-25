from qa import *
import subprocess
e = Ev("CP-16"); e.w("CP-16", time.strftime("%Y-%m-%d %H:%M"))
SECRET=open(os.path.join(ROOT,"..",".env")).read().split("JWT_SECRET=")[1].split()[0]
TADM=login("admin"); TP=login("qa_esc_pac","Cuidarte#Aux2026"); TM=login("qa_esc_med","Cuidarte#Aux2026")
UP,UM,US,UB=IDS["qa_esc_pac"],IDS["qa_esc_med"],IDS["qa_sinrol"],IDS["qa_borrar"]; R1,R2=4,5; N5=21
e.w("ids: qa_esc_pac",UP,"qa_esc_med",UM,"qa_sinrol",US,"qa_borrar",UB,"roles borrar1/2",R1,R2,"Nuevo5",N5)
e.w(sql("select id,nombre from roles order by id")); init_ur=sql("select usuario_id,rol_id from usuario_roles order by 1,2"); e.w(init_ur)
e.step(1,"escalamiento (9 intentos)")
tests=[(1,"T_ESC_PAC PUT /usuarios/{esc_pac} rol_id 1",lambda:api("PUT",f"/usuarios/{UP}",token=TP,body={"rol_id":1})),
 (2,"T_ESC_MED PUT /usuarios/{esc_med} rol_id 1",lambda:api("PUT",f"/usuarios/{UM}",token=TM,body={"rol_id":1})),
 (3,"T_ESC_MED PUT /usuarios/{esc_pac} rol_id 1",lambda:api("PUT",f"/usuarios/{UP}",token=TM,body={"rol_id":1})),
 (4,"T_ESC_MED POST /usuarios qa_intruso rol_id 1",lambda:api("POST","/usuarios",token=TM,body={"nombre_usuario":"qa_intruso","correo":"qa_intruso@example.com","contrasena_hash":"Cuidarte#Aux2026","rol_id":1})),
 (5,"T_ESC_PAC POST /usuarios qa_intruso rol_id 1",lambda:api("POST","/usuarios",token=TP,body={"nombre_usuario":"qa_intruso","correo":"qa_intruso@example.com","contrasena_hash":"Cuidarte#Aux2026","rol_id":1})),
 (6,"T_ESC_PAC POST /roles qa_rol_intruso",lambda:api("POST","/roles",token=TP,body={"nombre":"qa_rol_intruso"})),
 (7,"T_ESC_PAC PUT /roles/{borrar1}",lambda:api("PUT",f"/roles/{R1}",token=TP,body={"nombre":"qa_rol_hackeado"})),
 (8,"T_ESC_PAC DELETE /roles/{borrar1}",lambda:api("DELETE",f"/roles/{R1}",token=TP)),
 (9,"T_ESC_MED DELETE /pacientes/{Nuevo5}",lambda:api("DELETE",f"/pacientes/{N5}",token=TM))]
ok1=0
for n,d,f in tests:
    r=f(); ok1+= r.status_code==403; e.w(f"({n}) {d}: {short(r,160)} -> {'OK' if r.status_code==403 else 'NO CUMPLE (esperado 403)'}")
e.w("escalamientos rechazados con 403:",ok1,"de 9")
e.step(2,"11 operaciones con bearerAuth sin token")
ops2=[("GET",f"/pacientes/1"),("GET","/pacientes"),("GET","/examenes"),("GET",f"/examenes/{IDS['EX_A1']}"),("GET","/examenes/paciente/1"),("GET",f"/documentos/{IDS['DOC_A1']}"),("GET",f"/documentos/examen/{IDS['EX_A1']}"),("GET","/usuarios"),("GET",f"/usuarios/{US}"),("DELETE",f"/usuarios/{UB}"),("GET","/auditoria")]
def run(ops,tok,label):
    n=0
    for m,p in ops:
        r=requests.request(m,API+p,headers=({"Authorization":"Bearer "+tok} if tok else {}),timeout=30); good=r.status_code==401; n+=good
        e.w(f"  {label} {m} {p}: HTTP {r.status_code} ({round(r.elapsed.total_seconds(),1)}s) {r.text[:90]!r} -> {'OK' if good else 'NO CUMPLE (esperado 401)'}")
    return n
n2=run(ops2,None,"sin token"); e.w("rechazadas con 401:",n2,"de",len(ops2))
e.step(3,"6 operaciones no documentadas sin token")
ops3=[("GET","/pacientes/buscar/rut/11111111-1"),("POST","/auditoria"),("GET",f"/roles/{R2}"),("POST","/roles"),("PUT",f"/roles/{R2}"),("DELETE",f"/roles/{R2}")]
n3=0
for m,p in ops3:
    kw={"json":{"accion":"X","detalles":"sin token"}} if p=="/auditoria" else {"json":{"nombre":"qa_rol_intruso2"}} if m in("POST","PUT") else {}
    r=requests.request(m,API+p,timeout=30,**kw); good=r.status_code==401; n3+=good; e.w(f"  sin token {m} {p}: HTTP {r.status_code} {r.text[:120]!r} -> {'OK' if good else 'NO CUMPLE (esperado 401)'}")
e.w("rechazadas con 401:",n3,"de 6")
e.step(4,"ruta estática /files/documentos")
r=requests.get(API+"/files/documentos/",timeout=10); e.w("GET /files/documentos/:",r.status_code,r.text[:150])
r=requests.get(API+"/files/documentos/resultado_examen.pdf",timeout=10); e.w("GET /files/documentos/resultado_examen.pdf:",r.status_code,r.text[:100]); e.w("archivos en BACKEND/uploads/documentos:",os.listdir(os.path.join(ROOT,"..","BACKEND","uploads","documentos")))
e.step(5,"pasos 2 y 3 con token vencido")
exp=subprocess.run(["node","-e","const jwt=require(process.argv[1]);const s=process.argv[2];console.log(jwt.sign({usuarioId:'1',nombreUsuario:'admin',rolId:'1',rolNombre:'admin',iat:Math.floor(Date.now()/1000)-7200},s,{expiresIn:60}))",os.path.join(ROOT,"..","BACKEND","node_modules","jsonwebtoken"),SECRET],capture_output=True,text=True).stdout.strip()
e.w("payload del token vencido:",jwt(exp))
n5=run(ops2+ops3[:1]+ops3[2:3],exp,"vencido"); e.w("rechazadas con 401 (13 operaciones sin las que escriben roles/auditoría):",n5)
for m,p in [("POST","/auditoria"),("POST","/roles"),("PUT",f"/roles/{R2}"),("DELETE",f"/roles/{R2}")]:
    kw={"json":{"accion":"X","detalles":"vencido"}} if p=="/auditoria" else {"json":{"nombre":"qa_rol_intruso2"}} if m in("POST","PUT") else {}
    r=requests.request(m,API+p,headers={"Authorization":"Bearer "+exp},timeout=30,**kw); e.w(f"  vencido {m} {p}: HTTP {r.status_code} {r.text[:100]!r}")
e.step(6,"usuario sin rol qa_sinrol"); TS=login("qa_sinrol","Cuidarte#Aux2026"); e.w("login:",bool(TS))
for p in [f"/usuarios/{IDS['qa_esc_pac']}" if False else "/usuarios/3","/examenes",f"/documentos/{IDS['DOC_A1']}"]:
    r=api("GET",p,token=TS); e.w(f"  GET {p}: {short(r,150)} -> {'OK' if r.status_code==403 else 'NO CUMPLE (esperado 403)'}")
e.step(7,"operaciones públicas esperadas"); 
for m,p in [("GET","/tipo-examen"),("GET","/tipo-examen/1"),("GET","/roles"),("GET","/"),("GET","/docs/"),("GET","/openapi.json")]:
    r=requests.request(m,API+p,timeout=20); e.w(f"  {m} {p}: HTTP {r.status_code}")
e.step(8,"estado final vs inicial"); e.w(sql("select id,nombre from roles order by id")); fin=sql("select usuario_id,rol_id from usuario_roles order by 1,2"); e.w(fin); e.w("usuario_roles igual al inicial:",fin==init_ur)
e.w(sql("select id,nombre_usuario from usuarios where nombre_usuario in ('qa_intruso','qa_borrar','qa_esc_pac','qa_esc_med')")); e.w(sql("select count(*) paciente_nuevo5 from pacientes where id=21"))
for u,p in [("qa_esc_pac","Cuidarte#Aux2026"),("qa_esc_med","Cuidarte#Aux2026")]:
    t=login(u,p); e.w(u,"token:",jwt(t)["rolNombre"] if t else "login falla")
e.w("admin sigue existiendo y puede iniciar sesión:",bool(login("admin")))
