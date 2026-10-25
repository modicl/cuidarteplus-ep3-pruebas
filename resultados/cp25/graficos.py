import csv, os, re, datetime as dt, statistics, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVD = os.path.join(ROOT, "evidencia", "cp25")
IMG = os.path.join(EVD, "img")
PARTS = [("base_1usuario", "Base\n1 usuario"), ("A_run1", "A1"), ("A_run2", "A2"), ("A_run3", "A3"), ("B_run1", "B1"), ("B_run2", "B2"), ("B_run3", "B3"), ("C_volumen", "C"), ("E_documentos", "E"), ("F_estres", "F\nestrés"), ("G_sin_token", "G")]
TODAY = dt.date.today()


def mem_mib(s):
    used = s.split("/")[0].strip()
    m = re.match(r"([\d.]+)\s*([KMG]i?B)", used)
    v, u = float(m.group(1)), m.group(2)
    return v * {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024, "KB": 1 / 1024, "MB": 1, "GB": 1024}[u]


series = {"cuidarteplus-backend-ev": [], "cuidarteplus-postgres-ev": []}
bands = []
for key, label in PARTS:
    f = os.path.join(EVD, key + "_recursos.csv")
    rows = list(csv.DictReader(open(f, encoding="utf8")))
    ts = []
    for r in rows:
        t = dt.datetime.combine(TODAY, dt.datetime.strptime(r["hora"], "%H:%M:%S").time())
        series[r["contenedor"]].append((t, float(r["cpu"].strip("%")), mem_mib(r["memoria"])))
        ts.append(t)
    bands.append((min(ts), max(ts), label, key))

fig, ax = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
col = {"cuidarteplus-backend-ev": "#1f77b4", "cuidarteplus-postgres-ev": "#d62728"}
nom = {"cuidarteplus-backend-ev": "API (límite 1 CPU / 512 MiB)", "cuidarteplus-postgres-ev": "PostgreSQL (límite 1 CPU / 1 GiB)"}
for c, pts in series.items():
    pts.sort()
    ax[0].plot([p[0] for p in pts], [p[1] for p in pts], color=col[c], label=nom[c], lw=1.2)
    ax[1].plot([p[0] for p in pts], [p[2] for p in pts], color=col[c], label=nom[c], lw=1.2)
ax[0].axhline(100, color="gray", ls="--", lw=0.8)
ax[0].text(bands[0][0], 102, "límite de CPU de cada contenedor = 100 %", fontsize=8, color="gray")
ax[1].axhline(512, color=col["cuidarteplus-backend-ev"], ls="--", lw=0.8)
ax[1].axhline(1024, color=col["cuidarteplus-postgres-ev"], ls="--", lw=0.8)
for i, (a, b, label, key) in enumerate(bands):
    for x in ax:
        x.axvspan(a, b, color="#eeeeee" if i % 2 == 0 else "#ffffff", zorder=0)
    ax[0].text(a + (b - a) / 2, ax[0].get_ylim()[1] * 0.97, label, ha="center", va="top", fontsize=8)
ax[0].set_ylabel("CPU (%)")
ax[1].set_ylabel("Memoria usada (MiB)")
ax[0].set_title("CP-25: uso de CPU y memoria de la API y de la base de datos durante las cargas (k6, docker stats cada 8 s)")
ax[0].legend(loc="upper left", fontsize=8, bbox_to_anchor=(0.0, 0.88))
ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax[1].set_xlabel("Hora local (cada franja es una ejecución; B = 0 a 200 usuarios; F = 20 a 400 usuarios)")
for x in ax:
    x.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(os.path.join(IMG, "CP-25_hardware_global.png"), dpi=220)
plt.close()

# ---- Detalle de F: usuarios virtuales, solicitudes por segundo, CPU y latencia p95 ----
vus, req, dur = [], collections.Counter(), collections.defaultdict(list)
W = 15
import gzip
with gzip.open(os.path.join(EVD, "F_estres_serie.csv.gz"), "rt", encoding="utf8") as f:
    for row in csv.DictReader(f):
        m = row["metric_name"]
        if m == "vus":
            vus.append((int(row["timestamp"]), float(row["metric_value"])))
        elif m == "http_reqs":
            req[int(row["timestamp"]) // W] += 1
        elif m == "http_req_duration":
            op = re.search(r"op=(\w+)", row["extra_tags"] or "")
            if op and op.group(1) in ("post", "login", "get_examen"):
                dur[(op.group(1), int(row["timestamp"]) // W)].append(float(row["metric_value"]))
t0 = min(v[0] for v in vus)
toD = lambda e: dt.datetime.fromtimestamp(e)
fig, ax = plt.subplots(4, 1, figsize=(15, 11), sharex=True)
ax[0].step([toD(t) for t, _ in vus], [v for _, v in vus], color="#2ca02c", where="post")
ax[0].set_ylabel("Usuarios virtuales")
ax[0].set_title("CP-25 parte F (estrés): de 20 a 400 usuarios virtuales y vuelta a 20")
ks = sorted(req)
ax[1].plot([toD(k * W) for k in ks], [req[k] / W for k in ks], color="#9467bd")
ax[1].set_ylabel("Solicitudes por segundo")
for c in series:
    pts = [p for p in series[c] if t0 - 30 <= p[0].timestamp() <= t0 + 15 * 60]
    ax[2].plot([p[0] for p in pts], [p[1] for p in pts], color=col[c], label=nom[c])
ax[2].axhline(100, color="gray", ls="--", lw=0.8)
ax[2].set_ylabel("CPU (%)")
ax[2].legend(fontsize=8, loc="upper left")
for op, colr in [("post", "#d62728"), ("login", "#1f77b4"), ("get_examen", "#ff7f0e")]:
    ks2 = sorted(k for (o, k) in dur if o == op)
    p95 = [sorted(dur[(op, k)])[int(0.95 * len(dur[(op, k)]))] for k in ks2]
    ax[3].plot([toD(k * W) for k in ks2], p95, label="p95 " + op, color=colr)
ax[3].axhline(300, color="black", ls="--", lw=0.8)
ax[3].text(toD(t0), 330, "umbral 300 ms", fontsize=8)
ax[3].set_yscale("log")
ax[3].set_ylabel("Latencia p95 (ms, escala log)")
ax[3].legend(fontsize=8, loc="center left")
ax[3].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax[3].set_xlabel("Hora local")
for x in ax:
    x.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(os.path.join(IMG, "CP-25_estres_detalle.png"), dpi=220)
print("ok")
mx = {c: (max(p[1] for p in series[c]), max(p[2] for p in series[c])) for c in series}
print({k: (round(v[0], 1), round(v[1], 1)) for k, v in mx.items()})
for key, label in PARTS:
    r = [list(csv.DictReader(open(os.path.join(EVD, key + "_recursos.csv"), encoding="utf8")))][0]
    api = [float(x["cpu"].strip("%")) for x in r if "backend" in x["contenedor"]]
    db = [float(x["cpu"].strip("%")) for x in r if "postgres" in x["contenedor"]]
    am = [mem_mib(x["memoria"]) for x in r if "backend" in x["contenedor"]]
    dm = [mem_mib(x["memoria"]) for x in r if "postgres" in x["contenedor"]]
    print(f"{key:14s} API CPU máx {max(api):6.1f}% prom {statistics.mean(api):5.1f}% mem máx {max(am):6.1f} MiB | BD CPU máx {max(db):6.1f}% prom {statistics.mean(db):5.1f}% mem máx {max(dm):7.1f} MiB")
