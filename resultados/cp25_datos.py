import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
casos = json.load(open(os.path.join(ROOT, "casos.json"), encoding="utf8"))
FP = "Fecha: 2026-10-25. Ejecutó: Felipe Villarroel."

casos["CP-25"]["resultado"] = (
    "falla (parte falla esperada por diseño: retraso artificial de 5 s en POST y PUT /examenes, GET /pacientes y POST /documentos, y se aplica antes de autenticar, CLAUDE.md y AUDITORIA.md H-15; parte hallazgo nuevo: la página principal supera los 2 s)<br>"
    "Incidente: resultado por parte: A falla, B falla, C aprobada, D falla, E aprobada, F aprobada y G falla. POST y PUT /examenes responden con p95 de 5,0 s (umbral 300 ms) con 20 y con 200 usuarios; una respuesta 401 sin token tarda 5,0 s; /login y /home cargan en 4,3 s con LCP de 4,4 y 5,3 s (umbral 2 s). Con 200 y con 400 usuarios no hubo errores ni caídas.<br>" + FP)
casos["CP-25"]["evidencia"] = (
    "Ambiente: API limitada a 1 CPU y 512 MiB, PostgreSQL a 1 CPU y 1 GiB, frontend a 0,5 CPU y 256 MiB (docker update); k6 v2.3.0 en un contenedor con 6 CPU y 4 GB dentro de la misma red de Docker (equipo con Ryzen 7 9800X3D y Docker con 16 CPU y 16 GB); sin latencia de red. Datos: 20 cuentas qa_perf_* (4 ADM, 8 MED, 8 PAC), 8 fichas y un paciente con 200 exámenes; estado inicial de cada ejecución restaurado desde cp25/base_cp25.dump. Medición base con 1 usuario: POST 5.006 ms, PUT 5.011 ms, GET 2 ms, DELETE 5 ms (medianas).<br>"
    "Parte A, 20 usuarios por 3 min, 3 repeticiones (1.444 solicitudes y 360 ciclos completos por repetición, 0 % de errores): p95 de POST 5.028 / 5.037 / 5.024 ms, PUT 5.035 / 5.024 / 5.030 ms, GET 21 / 19 / 20 ms, DELETE 22 / 20 / 26 ms. Umbral 300 ms incumplido en POST y PUT.<br>"
    "Parte B, rampa de 0 a 200 usuarios en 2 min y 5 min sostenidos, 3 repeticiones (unas 147.600 solicitudes por repetición, 0 % de errores, 200 usuarios sostenidos): p95 de login 6 ms, GET /pacientes/{id} 4 ms, GET /examenes/{id} 4 ms y POST /examenes 5.006 ms en las tres. CPU máxima de la API 51 % y de PostgreSQL 28 %; memoria máxima de la API 71 MiB.<br>"
    "Parte C: 50 consultas con el token del médico y 50 con el del paciente dueño: HTTP 200 con los 200 exámenes completos, p95 de 4 ms en ambos; \"Mis Resultados\" muestra 200 tarjetas de examen.<br>"
    "Parte D, Lighthouse 13.5.0, móvil, 4G (1,6 Mbps, 150 ms), caché vacía, 5 repeticiones, Chromium 156.0.8078.4: /login load 4.263 ms y LCP 4.415 ms (medianas); /home con sesión de PAC_A load 4.269 ms y LCP 5.274 ms. No se midió con un teléfono real (no disponible). Una primera pasada de /home sin limpiar la caché dio 363 ms y se descartó por no cumplir la condición de caché vacía.<br>"
    "Parte E: 10 subidas de resultado_examen.pdf (2 MB) con p95 de 5.036 ms y máximo 5.036 ms; 10 descargas con p95 de 29 ms y tamaño 2.097.152 bytes en las 10. Todas dentro de 10 s.<br>"
    "Parte F: de 20 a 200 y a 400 usuarios, 306.556 solicitudes, 0 % de errores, hasta unas 850 solicitudes por segundo; CPU máxima de la API 86,6 % (límite 100 %) y de PostgreSQL 44,8 %; memoria máxima 90 MiB. No apareció punto de quiebre hasta 400 usuarios. Al volver a 20 usuarios el sistema respondió normal sin ayuda manual. Filas: 215 exámenes iniciales + 10.081 creados = 10.296 en la base, sin pérdidas.<br>"
    "Parte G: 20 solicitudes GET /pacientes sin token: HTTP 401 con mediana de 5.006 ms y máximo de 5.010 ms.<br>"
    "Archivos: resultados/evidencia/cp25/ (logs *.log, resúmenes *.json, recursos *_recursos.csv, serie de la parte F), cp25/lh/ (Lighthouse), CP-25_parteC_ui.txt; scripts en resultados/cp25/")
casos["CP-25"]["impacto"] = "GRAVE"
json.dump(casos, open(os.path.join(ROOT, "casos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(casos["CP-25"]["resultado"][:80])
