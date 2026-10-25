import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from qa import *
PWD = "Cuidarte#Perf2026"
TADM = login("admin"); TM1 = login("qa_medico1")
accts = []
def mk(n, rol): 
    r = api("POST", "/usuarios", token=TADM, body={"nombre_usuario": n, "correo": n + "@example.com", "contrasena_hash": PWD, "rol_id": rol}); assert r.status_code == 201, r.text; return r.json()["id"]
for i in range(1, 5): accts.append({"user": f"qa_perf_adm{i:02d}", "role": "adm", "uid": mk(f"qa_perf_adm{i:02d}", 1)})
for i in range(1, 9): accts.append({"user": f"qa_perf_med{i:02d}", "role": "med", "uid": mk(f"qa_perf_med{i:02d}", 2)})
for i in range(1, 9): accts.append({"user": f"qa_perf_pac{i:02d}", "role": "pac", "uid": mk(f"qa_perf_pac{i:02d}", 3)})
print("cuentas creadas:", len(accts))
pacs = [a for a in accts if a["role"] == "pac"]
for i, a in enumerate(pacs, 1):
    r = api("POST", "/pacientes", token=TM1, body={"rut": f"17.000.00{i}-0", "primer_nombre": "Carga%02d" % i, "apellido_paterno": "Prueba", "fecha_nacimiento": "1990-01-01", "sexo": "M", "email": f"carga{i:02d}.qa@example.com", "usuario_id": int(a["uid"])}); assert r.status_code == 201, r.text
    a["pacienteId"] = r.json()["id"]
print("fichas:", [a["pacienteId"] for a in pacs])
def mkex(pid, k): 
    r = api("POST", "/examenes", token=TM1, body={"tipo_examen_medico_id": 1, "paciente_id": int(pid), "diagnosis": f"Carga sintetica {k}"}, timeout=60); assert r.status_code == 201, r.text; return r.json()["id"]
t0 = time.time()
for a in pacs[1:]: a["examenId"] = mkex(a["pacienteId"], "u")
with cf.ThreadPoolExecutor(25) as ex: ids = list(ex.map(lambda k: mkex(pacs[0]["pacienteId"], k), range(200)))
pacs[0]["examenId"] = ids[0]
print("200 exámenes en", round(time.time() - t0, 1), "s;", sql("select count(*) from examen_medico where paciente_id=%s" % pacs[0]["pacienteId"]).split("\n")[2].strip())
data = {"password": PWD, "accounts": accts, "paciente200": pacs[0]["pacienteId"], "examen_ref": IDS["EX_A1"], "examen_a3": IDS["EX_A3"], "doc_a1": IDS["DOC_A1"]}
json.dump(data, open(os.path.join(ROOT, "cp25", "perf_data.json"), "w"), indent=1)
env = dict(os.environ, MSYS_NO_PATHCONV="1")
subprocess.run(["docker", "exec", "cuidarteplus-postgres-ev", "pg_dump", "-U", "postgres", "-Fc", "cuidarteplus", "-f", "/tmp/base_cp25.dump"], check=True)
subprocess.run(["docker", "cp", "cuidarteplus-postgres-ev:/tmp/base_cp25.dump", os.path.join(ROOT, "cp25", "base_cp25.dump")], check=True, env=env)
print(sql("select (select count(*) from usuarios) u,(select count(*) from pacientes) p,(select count(*) from examen_medico) e"))
