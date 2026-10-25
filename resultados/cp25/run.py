"""Orquestador de CP-25 (k6 en Docker dentro de la red del compose).
Uso: python run.py base|A|B|C|E|F|G [repeticion]"""
import os, re, sys, time, json, html, threading, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from qa import ROOT, sql, api, login
from playwright.sync_api import sync_playwright

CP = os.path.join(ROOT, "cp25")
OUT = os.path.join(ROOT, "evidencia", "cp25")
IMG = os.path.join(OUT, "img")
os.makedirs(IMG, exist_ok=True)
ENVV = dict(os.environ, MSYS_NO_PATHCONV="1")


def restore25():
    subprocess.run(["docker", "cp", os.path.join(CP, "base_cp25.dump"), "cuidarteplus-postgres-ev:/tmp/base_cp25.dump"], check=True, env=ENVV)
    r = subprocess.run(["docker", "exec", "cuidarteplus-postgres-ev", "pg_restore", "-U", "postgres", "-d", "cuidarteplus", "--clean", "--if-exists", "/tmp/base_cp25.dump"], capture_output=True, text=True)
    time.sleep(4)
    return r.returncode


def counts():
    return sql("select (select count(*) from examen_medico) examenes,(select count(*) from documentos_examen) docs,(select count(*) from usuarios) usuarios").split("\n")[2].strip()


def sampler(path, stop):
    with open(path, "w", encoding="utf8") as f:
        f.write("hora,contenedor,cpu,memoria\n")
        while not stop.is_set():
            r = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}", "cuidarteplus-backend-ev", "cuidarteplus-postgres-ev"], capture_output=True, text=True)
            for l in r.stdout.strip().splitlines():
                f.write(time.strftime("%H:%M:%S") + "," + l + "\n")
            f.flush()
            stop.wait(8)


def render(name, title, lines):
    body = "\n".join(html.escape(l[:150]) for l in lines)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1150, "height": 600})
        pg.set_content("<body style='margin:0;background:#0c0c0c'><div id=t style='width:1150px;box-sizing:border-box;color:#ccc;font:13px Consolas,monospace;padding:12px'><div style='color:#16c60c;margin-bottom:8px'>%s</div><pre style='margin:0;white-space:pre-wrap'>%s</pre></div></body>" % (html.escape(title), body))
        pg.locator("#t").screenshot(path=os.path.join(IMG, name))
        b.close()


def k6(name, script, env=None, cpus="6", csv=False):
    cmd = ["docker", "run", "--rm", "--network", "cuidarteplus-network", "--cpus", cpus, "--memory", "4g",
           "-v", CP + ":/work", "-v", os.path.join(ROOT, "datos") + ":/datos:ro", "-v", OUT + ":/out", "grafana/k6", "run", "--no-color",
           "--summary-export=/out/%s.json" % name]
    if csv:
        cmd.append("--out=csv=/out/%s_serie.csv" % name)
    for k, v in (env or {}).items():
        cmd += ["-e", "%s=%s" % (k, v)]
    cmd.append("/work/k6/" + script)
    stop = threading.Event()
    th = threading.Thread(target=sampler, args=(os.path.join(OUT, name + "_recursos.csv"), stop), daemon=True)
    th.start()
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf8", errors="replace")
    stop.set()
    th.join(timeout=15)
    log = r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")
    open(os.path.join(OUT, name + ".log"), "w", encoding="utf8").write("$ " + " ".join(cmd) + "\n" + log + "\nCódigo de salida de k6: %s (99 = umbral incumplido)\n" % r.returncode)
    lines = [l for l in log.splitlines() if l.strip()]
    start = next((i for i, l in enumerate(lines) if "THRESHOLDS" in l), max(0, len(lines) - 55))
    render(name + "_cli.png", "$ docker run --rm --network cuidarteplus-network --cpus %s --memory 4g grafana/k6 run %s   (%s)" % (cpus, script, name), lines[start:start + 58])
    print(name, "k6 salió con", r.returncode, "en", round(time.time() - t0), "s")
    return r.returncode


if __name__ == "__main__":
    part = sys.argv[1]
    rep = sys.argv[2] if len(sys.argv) > 2 else "1"
    print("restore", restore25(), "| antes:", counts())
    if part == "base":
        k6("base_1usuario", "a_carga_normal.js", {"VUS": "1", "DUR": "1m"}, cpus="2")
    elif part == "A":
        k6("A_run" + rep, "a_carga_normal.js")
    elif part == "B":
        k6("B_run" + rep, "b_carga_maxima.js", {"PARTE": "B"})
    elif part == "C":
        k6("C_volumen", "c_volumen.js")
    elif part == "E":
        k6("E_documentos", "e_documentos.js")
    elif part == "F":
        k6("F_estres", "b_carga_maxima.js", {"PARTE": "F"}, csv=True)
    elif part == "G":
        k6("G_sin_token", "g_sin_token.js", cpus="2")
    print("después:", counts())
