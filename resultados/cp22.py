from qa import *
import re
e = Ev("CP-22"); e.w("CP-22", time.strftime("%Y-%m-%d %H:%M"))
TM=login("qa_medico1"); PWD="Cuidarte#Hash2026"
e.step(1,"registro qa_hash01 y qa_hash02"); 
for u in ["qa_hash01","qa_hash02"]: e.w(u,short(api("POST","/autenticacion/registro",body={"nombre_usuario":u,"password":PWD,"correo":u+"@example.com"}),120))
e.step(2,"contraseñas almacenadas"); e.w(sql("SELECT nombre_usuario, contrasena FROM usuarios WHERE nombre_usuario IN ('qa_hash01','qa_hash02')"))
e.step(3,"consulta de conformidad (todas las filas, incluidas las semilla)"); e.w(sql(r"SELECT count(*) AS no_conformes FROM usuarios WHERE contrasena !~ '^\$(argon2id\$|2[aby]\$(1[0-9]|[2-3][0-9])\$)'")); e.w(sql("SELECT count(*) AS total FROM usuarios")); e.w(sql("SELECT nombre_usuario, contrasena FROM usuarios WHERE nombre_usuario IN ('admin','medico','paciente','qa_medico1','qa_paciente_b')"))
e.step(4,"login qa_hash01"); e.w(short(api("POST","/autenticacion/login",body={"nombre_usuario":"qa_hash01","password":PWD}),90))
e.step(5,"datos clínicos y documento con marcadores")
r=api("POST","/pacientes",token=TM,body={"rut":"4.444.444-4","primer_nombre":"Marcador","apellido_paterno":"Cifrado","fecha_nacimiento":"1990-01-01","sexo":"M","email":"marcador.qa@example.com","alergias":"Penicilina QA-MARKER-7391","enfermedades_cronicas":"Asma QA-MARKER-7391","observaciones_medicas_generales":"Obs QA-MARKER-7391"}); e.w(short(r,150)); pid=r.json()["id"]
ex=api("POST","/examenes",token=TM,body={"tipo_examen_medico_id":1,"paciente_id":int(pid),"diagnosis":"Dx QA-MARKER-7391"}).json()["id"]
body="BT /F1 12 Tf 72 720 Td (QA-DOC-MARKER-5524) Tj ET"; objs=["<</Type/Catalog/Pages 2 0 R>>","<</Type/Pages/Kids[3 0 R]/Count 1>>","<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>","<</Length %d>>\nstream\n%s\nendstream"%(len(body),body),"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
pdf=b"%PDF-1.4\n"; offs=[]
for i,o in enumerate(objs,1): offs.append(len(pdf)); pdf+=f"{i} 0 obj\n{o}\nendobj\n".encode()
x=len(pdf); pdf+=f"xref\n0 6\n0000000000 65535 f \n".encode()+b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)+f"trailer\n<</Size 6/Root 1 0 R>>\nstartxref\n{x}\n%%EOF\n".encode()
open(os.path.join(DAT,"marcador.pdf"),"wb").write(pdf)
r=api("POST","/documentos",token=TM,data={"examen_medico_id":ex,"paciente_id":pid},files={"documento":("marcador.pdf",pdf,"application/pdf")}); e.w(short(r,150)); did=r.json()["documento"]["id"]
e.w(sql(f"SELECT alergias, enfermedades_cronicas, observaciones_medicas_generales FROM pacientes WHERE id={pid}")); e.w(sql(f"SELECT diagnosis FROM examen_medico WHERE id={ex}"))
e.w(sql(f"SELECT encode(substring(documento from 1 for 8), 'escape') AS primeros_bytes FROM documentos_examen WHERE id={did}"))
e.step(6,"búsqueda de marcadores en archivos físicos y en respaldos")
sql("CHECKPOINT"); 
g=subprocess.run(["docker","exec","cuidarteplus-postgres-ev","sh","-c","grep -rlai 'QA-MARKER-7391' /var/lib/postgresql/data | head -5; echo ---; grep -rlai 'QA-DOC-MARKER-5524' /var/lib/postgresql/data | head -5"],capture_output=True,text=True); e.w("archivos físicos con el marcador:\n"+g.stdout.strip(), g.stderr.strip()[:200])
env=dict(os.environ,MSYS_NO_PATHCONV="1")
subprocess.run(["docker","exec","cuidarteplus-postgres-ev","sh","-c","pg_dump -U postgres -Fc cuidarteplus -f /tmp/cp22.dump && pg_dump -U postgres -Fp cuidarteplus -f /tmp/cp22.sql"],check=True)
g=subprocess.run(["docker","exec","cuidarteplus-postgres-ev","sh","-c","echo -Fc:; grep -c 'QA-MARKER-7391' /tmp/cp22.dump; echo -Fp texto:; grep -c 'QA-MARKER-7391' /tmp/cp22.sql; grep -o 'Penicilina QA-MARKER-7391' /tmp/cp22.sql | head -1; echo documento en -Fp (hex/escape):; grep -c 'QA-DOC-MARKER-5524' /tmp/cp22.sql"],capture_output=True,text=True); e.w("respaldo:",g.stdout.strip())
d=subprocess.run(["docker","exec","cuidarteplus-postgres-ev","sh","-c","zcat -f /tmp/cp22.dump 2>/dev/null | head -c 0; pg_restore -f - /tmp/cp22.dump | grep -c 'QA-MARKER-7391'"],capture_output=True,text=True); e.w("pg_restore -f - del respaldo -Fc (SQL descomprimido), apariciones del marcador de texto:",d.stdout.strip())
e.step(7,"cifrado de disco/volumen"); e.w(subprocess.run(["docker","volume","inspect","cuidarteplus-ev_postgres_data"],capture_output=True,text=True).stdout[:500]); e.w("extensiones/funciones de cifrado (pgcrypto) instaladas:",sql("select extname from pg_extension"))
e.w("columnas con tipo bytea en pacientes/usuarios:",sql("select table_name,column_name,data_type from information_schema.columns where table_name in ('usuarios','pacientes') and data_type='bytea'"))
