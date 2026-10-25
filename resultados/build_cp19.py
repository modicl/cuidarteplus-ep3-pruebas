import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa import IDS, login, ROOT

spec = json.load(open(os.path.join(ROOT, "..", "BACKEND", "src", "openapi.json")))
items = []
B = "{{base}}"


def req(name, method, path, exp, token=None, body=None, raw=None, form=None, group=""):
    r = {"method": method, "header": [], "url": {"raw": B + path, "host": ["{{base}}"], "path": [p for p in path.strip("/").split("/")]}}
    if token:
        r["header"].append({"key": "Authorization", "value": "Bearer {{%s}}" % token})
    if body is not None:
        r["header"].append({"key": "Content-Type", "value": "application/json"})
        r["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False)}
    if raw is not None:
        r["header"].append({"key": "Content-Type", "value": "application/json"})
        r["body"] = {"mode": "raw", "raw": raw}
    if form is not None:
        r["body"] = {"mode": "formdata", "formdata": form}
    t1 = "pm.test(%s, function(){ pm.expect(pm.response.code).to.be.oneOf(%s); });" % (json.dumps(name + " -> esperado " + "/".join(map(str, exp))), json.dumps(exp))
    t2 = "pm.test('sin HTTP 500', function(){ pm.expect(pm.response.code).to.not.equal(500); });"
    items.append({"name": "[%s] %s" % (group, name), "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": [t1, t2]}}], "request": r})


def fd(file, mime, ex, pac):
    f = [{"key": "examen_medico_id", "value": str(ex), "type": "text"}, {"key": "paciente_id", "value": str(pac), "type": "text"}]
    if file:
        f.append({"key": "documento", "type": "file", "src": file, "contentType": mime})
    return f


for p, v in spec["paths"].items():
    for m, o in v.items():
        if m in ("get", "post", "put", "delete") and o.get("security"):
            path = p.replace("{id}", "999999").replace("{paciente_id}", "999999").replace("{examen_id}", "999999")
            req("%s %s sin token" % (m.upper(), p), m.upper(), path, [401], body=({} if m in ("post", "put") else None), group="401 sin token")

g = "critico"
req("login positivo", "POST", "/autenticacion/login", [200], body={"nombre_usuario": "qa_medico1", "password": "Cuidarte#Med2026"}, group=g)
req("login negativo (contrasena incorrecta)", "POST", "/autenticacion/login", [401], body={"nombre_usuario": "qa_medico1", "password": "mala"}, group=g)
req("registro positivo", "POST", "/autenticacion/registro", [201], body={"nombre_usuario": "qa_nw_reg1", "password": "Cuidarte#Nw2026", "correo": "qa_nw_reg1@example.com"}, group=g)
req("registro negativo (usuario repetido)", "POST", "/autenticacion/registro", [400], body={"nombre_usuario": "qa_nw_reg1", "password": "Cuidarte#Nw2026", "correo": "qa_nw_reg1@example.com"}, group=g)
req("usuarios GET positivo (ADM)", "GET", "/usuarios", [200], token="T_ADM", group=g)
req("usuarios GET negativo (MED1)", "GET", "/usuarios", [403], token="T_MED1", group=g)
req("usuarios POST positivo (ADM)", "POST", "/usuarios", [201], token="T_ADM", body={"nombre_usuario": "qa_nw_user1", "correo": "qa_nw_user1@example.com", "contrasena_hash": "Cuidarte#Nw2026", "rol_id": 3}, group=g)
req("pacientes GET positivo (MED1)", "GET", "/pacientes", [200], token="T_MED1", group=g)
req("pacientes GET negativo (PAC_A)", "GET", "/pacientes", [403], token="T_PAC", group=g)
req("pacientes POST positivo (MED1)", "POST", "/pacientes", [201], token="T_MED1", body={"rut": "5.555.555-5", "primer_nombre": "Newman", "apellido_paterno": "Prueba", "fecha_nacimiento": "1990-01-01", "sexo": "M", "email": "newman.qa@example.com"}, group=g)
req("pacientes POST negativo (PAC_A)", "POST", "/pacientes", [403], token="T_PAC", body={"rut": "5.555.556-3", "primer_nombre": "Newman", "apellido_paterno": "Dos", "fecha_nacimiento": "1990-01-01", "sexo": "M", "email": "newman2.qa@example.com"}, group=g)
req("examenes GET positivo (PAC_A)", "GET", "/examenes", [200], token="T_PAC", group=g)
req("examenes POST positivo (MED1)", "POST", "/examenes", [201], token="T_MED1", body={"tipo_examen_medico_id": 1, "paciente_id": 1, "diagnosis": "newman"}, group=g)
req("examenes POST negativo (PAC_A)", "POST", "/examenes", [403], token="T_PAC", body={"tipo_examen_medico_id": 1, "paciente_id": 1, "diagnosis": "newman"}, group=g)
req("documentos GET positivo (MED1)", "GET", "/documentos/%s" % IDS["DOC_A1"], [200], token="T_MED1", group=g)
req("documentos GET negativo (PAC_A documento ajeno)", "GET", "/documentos/%s" % IDS["DOC_B1"], [403], token="T_PAC", group=g)
req("documentos POST positivo (MED1)", "POST", "/documentos", [201], token="T_MED1", form=fd("resultado_examen_v1.pdf", "application/pdf", IDS["EX_A3"], 1), group=g)
req("documentos POST negativo (PAC_A)", "POST", "/documentos", [403], token="T_PAC", form=fd("resultado_examen_v1.pdf", "application/pdf", IDS["EX_A3"], 1), group=g)
req("auditoria GET positivo (ADM)", "GET", "/auditoria", [200], token="T_ADM", group=g)
req("auditoria GET negativo (MED1)", "GET", "/auditoria", [403], token="T_MED1", group=g)

g = "vector"
req("V1 login con {}", "POST", "/autenticacion/login", [400], body={}, group=g)
req("V2 registro con correo invalido", "POST", "/autenticacion/registro", [400], body={"nombre_usuario": "qa_nw_v2", "password": "Cuidarte#Nw2026", "correo": "no-es-correo"}, group=g)
req("V3 POST /usuarios nombre_usuario de 2 caracteres", "POST", "/usuarios", [400], token="T_ADM", body={"nombre_usuario": "ab", "correo": "qa_nw_v3@example.com", "contrasena_hash": "Cuidarte#Nw2026"}, group=g)
req("V4 PUT /usuarios/{qa_borrar} con {}", "PUT", "/usuarios/%s" % IDS["qa_borrar"], [400], token="T_ADM", body={}, group=g)
req("V5 POST /pacientes sin rut", "POST", "/pacientes", [400], token="T_MED1", body={"primer_nombre": "Sin", "apellido_paterno": "Rut", "fecha_nacimiento": "1990-01-01", "sexo": "M", "email": "sinrut@example.com"}, group=g)
req("V6 PUT /pacientes/{Nuevo5} con sexo X", "PUT", "/pacientes/21", [400], token="T_MED1", body={"sexo": "X"}, group=g)
req("V7 POST /examenes paciente_id abc", "POST", "/examenes", [400], token="T_MED1", body={"tipo_examen_medico_id": 1, "paciente_id": "abc"}, group=g)
req("V8 POST /examenes paciente_id -1", "POST", "/examenes", [400], token="T_MED1", body={"tipo_examen_medico_id": 1, "paciente_id": -1}, group=g)
req("V9 POST /documentos sin archivo", "POST", "/documentos", [400], token="T_MED1", form=fd(None, None, IDS["EX_A3"], 1), group=g)
req("V10 POST /roles con {} (ADM)", "POST", "/roles", [400], token="T_ADM", body={}, group=g)
req("V11 GET /examenes/abc", "GET", "/examenes/abc", [400, 404], token="T_ADM", group=g)
req("V12 POST /pacientes con JSON mal formado", "POST", "/pacientes", [400], token="T_MED1", raw='{"rut": "1-9", "primer_nombre": ', group=g)
req("V13 script_malicioso.exe (application/x-msdownload)", "POST", "/documentos", [400, 415], token="T_MED1", form=fd("script_malicioso.exe", "application/x-msdownload", IDS["EX_A3"], 1), group=g)
req("V14 resultado_falso.pdf (MZ como application/pdf)", "POST", "/documentos", [400, 415], token="T_MED1", form=fd("resultado_falso.pdf", "application/pdf", IDS["EX_A3"], 1), group=g)
req("V15 foto_falsa.jpg (HTML/JS como image/jpeg)", "POST", "/documentos", [400, 415], token="T_MED1", form=fd("foto_falsa.jpg", "image/jpeg", IDS["EX_A3"], 1), group=g)
req("V16 GET /pacientes/abc", "GET", "/pacientes/abc", [400, 404], token="T_ADM", group=g)
req("V17 resultado_grande.pdf 11 MB", "POST", "/documentos", [400, 413], token="T_MED1", form=fd("resultado_grande.pdf", "application/pdf", IDS["EX_A3"], 1), group=g)
req("V18 POST /documentos con paciente_id distinto al del examen", "POST", "/documentos", [400], token="T_MED1", form=fd("resultado_examen_v1.pdf", "application/pdf", IDS["EX_A3"], 11), group=g)

col = {"info": {"name": "Cuidarte+ CP-19", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}, "item": items}
out = os.path.join(ROOT, "evidencia", "newman")
os.makedirs(out, exist_ok=True)
json.dump(col, open(os.path.join(out, "coleccion_cp19.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
env = {"id": "e", "name": "qa", "values": [{"key": "base", "value": "http://host.docker.internal:4444", "enabled": True}] + [{"key": k, "value": login(u), "enabled": True} for k, u in [("T_ADM", "admin"), ("T_MED1", "qa_medico1"), ("T_PAC", "paciente")]]}
json.dump(env, open(os.path.join(out, "_env_tmp.json"), "w"))
print(len(items), "requests")
