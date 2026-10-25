from qa import *
e = Ev("CP-20"); e.w("CP-20", time.strftime("%Y-%m-%d %H:%M"))
TADM,TM,TP=login("admin"),login("qa_medico1"),login("paciente"); n0=sql("select count(*) from auditoria").split("\n")[2].strip(); e.w("filas auditoria inicial:",n0)
logn=lambda: int(subprocess.run("docker logs cuidarteplus-backend-ev 2>&1 | wc -l",shell=True,capture_output=True,text=True).stdout.strip()); l0=logn()
e.step(1,"GET /auditoria"); 
for n,t in [("T_PAC_A",TP),("T_MED1",TM),("sin token",None)]: e.w(n,short(api("GET","/auditoria",token=t),130))
e.step(2,"POST falso, PUT y DELETE"); r=api("POST","/auditoria",token=TP,body={"accion":"USUARIOS_ELIMINAR","detalles":"registro falso"}); e.w("POST con T_PAC_A:",short(r,200))
first=api("GET","/auditoria",token=TADM).json()[-1]["id"]
for m in ["PUT","DELETE"]: e.w(f"{m} /auditoria/{first} con T_ADM:",short(api(m,f"/auditoria/{first}",token=TADM,body={"accion":"x"} if m=="PUT" else None),120).replace("\n"," ")[:160])
e.w("filas auditoria tras el paso:",sql("select count(*) from auditoria").split("\n")[2].strip()); e.w(sql("select id,usuario_id,accion from auditoria where accion like '%registro falso%'"))
e.step(3,"MED1 consulta datos; revisar logs"); r=api("POST","/autenticacion/login",body={"nombre_usuario":"qa_medico1","password":PW["qa_medico1"]}); tk=r.json()["token"]
api("GET","/pacientes/buscar/rut/11111111-1"); api("GET",f"/examenes/{IDS['EX_A1']}",token=tk)
out=subprocess.run("docker logs cuidarteplus-backend-ev 2>&1 | tail -n +%d"%(l0+1),shell=True,capture_output=True,text=True,encoding="utf8").stdout
import re
e.w("--- líneas del log del contenedor de la API durante el caso (sin colores) ---"); clean=re.sub(r"\x1b\[[0-9;]*m","",out); e.w(clean[-2500:])
e.w("¿aparece la contraseña?",PW["qa_medico1"] in clean,"| ¿aparece el token completo?",tk in clean,"| ¿aparece el RUT 11111111-1 en texto claro?","11111111-1" in clean,"| ¿aparece el diagnóstico?","Dato sintetico" in clean)
e.step(4,"contenido de la auditoría (acciones)"); e.w(sql("select count(*) filas_con_contrasena_o_diagnostico from auditoria where accion ilike '%Cuidarte#%' or accion ilike '%Dato sintetico%' or accion ilike '%Anemia%'")); e.w(sql("select accion from auditoria where accion ilike 'PACIENTES_CREAR%' limit 2"))
e.step(5,"errores provocados")
def chk(n,r):
    body=r.text[:260].replace("\n"," "); bad=[w for w in ["pg_","bigint","violates","constraint","syntax","stack"," at ","node_modules","relation","column"] if w in r.text]
    e.w(f"{n}: HTTP {r.status_code} | cuerpo: {body!r} | cabeceras: {dict((k,v) for k,v in r.headers.items() if k in('X-Powered-By','Server','Content-Type'))} | textos internos detectados: {bad}")
chk("GET /examenes/abc",api("GET","/examenes/abc",token=TADM))
chk("POST /pacientes con RUT repetido",api("POST","/pacientes",token=TM,body={"rut":"11.111.111-1","primer_nombre":"Dup","apellido_paterno":"Rut","fecha_nacimiento":"1990-01-01","sexo":"M","email":"dup.rut@example.com"}))
chk("PUT /usuarios/{id} con rol_id inexistente (+correo)",api("PUT",f"/usuarios/{IDS['qa_rol01']}",token=TADM,body={"correo":"qa_rol01@example.com","rol_id":999}))
chk("POST /documentos con .exe",api("POST","/documentos",token=TM,data={"examen_medico_id":IDS["EX_A3"],"paciente_id":1},files={"documento":("script_malicioso.exe",open(DAT+"/script_malicioso.exe","rb"),"application/x-msdownload")}))
