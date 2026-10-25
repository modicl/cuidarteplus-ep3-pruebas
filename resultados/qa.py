import json, os, sys, time, base64, subprocess, hashlib, requests
ROOT = os.path.dirname(os.path.abspath(__file__))
API = "http://localhost:4444"; WEB = "http://localhost:3333"
EVD = os.path.join(ROOT, "evidencia"); DAT = os.path.join(ROOT, "datos")
IDS = json.load(open(os.path.join(ROOT, "ids.json")))
PW = {"admin":"Cuidarte#Adm2026","qa_medico1":"Cuidarte#Med2026","qa_medico2":"Cuidarte#Med2026",
      "paciente":"Cuidarte#Pac2026","qa_paciente_b":"Cuidarte#Pac2026"}
class Ev:
    def __init__(s, case): s.f = open(os.path.join(EVD, case + ".txt"), "w", encoding="utf8"); s.case = case
    def w(s, *a):
        t = " ".join(str(x) for x in a); print(t); s.f.write(t + "\n"); s.f.flush()
    def step(s, n, t): s.w(f"\n### Paso {n}: {t}")
def api(method, path, token=None, body=None, files=None, data=None, headers=None, timeout=60, raw=False):
    h = dict(headers or {})
    if token: h["Authorization"] = "Bearer " + token
    t0 = time.time()
    r = requests.request(method, API + path, headers=h, json=body, files=files, data=data, timeout=timeout)
    r.elapsed_s = round(time.time() - t0, 2)
    return r
def short(r, n=300):
    try: b = json.dumps(r.json(), ensure_ascii=False)
    except Exception: b = r.text[:n]
    return f"HTTP {r.status_code} ({r.elapsed_s}s) {b[:n]}"
def login(u, p=None):
    r = api("POST", "/autenticacion/login", body={"nombre_usuario": u, "password": p or PW[u]})
    return r.json().get("token") if r.status_code == 200 else None
def jwt(t):
    p = t.split(".")[1]; p += "=" * (-len(p) % 4)
    return json.loads(base64.urlsafe_b64decode(p))
def sql(q):
    r = subprocess.run(["docker","exec","cuidarteplus-postgres-ev","psql","-U","postgres","-d","cuidarteplus","-c",q],capture_output=True,text=True,encoding="utf8")
    return (r.stdout + r.stderr).strip()
def sha(path): return hashlib.sha256(open(path,"rb").read()).hexdigest()
def sha_b(b): return hashlib.sha256(b).hexdigest()
def restore():
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    subprocess.run(["docker","cp",os.path.join(ROOT,"base.dump"),"cuidarteplus-postgres-ev:/tmp/base.dump"],check=True,env=env)
    r = subprocess.run(["docker","exec","cuidarteplus-postgres-ev","pg_restore","-U","postgres","-d","cuidarteplus","--clean","--if-exists","/tmp/base.dump"],capture_output=True,text=True)
    return r.returncode, r.stderr[-300:]
