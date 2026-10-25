import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
casos = json.load(open(os.path.join(ROOT, "casos.json"), encoding="utf8"))
FP = "Fecha: 2026-10-24. Ejecutó: Felipe Villarroel."
SONAR = "Análisis estático: resultados/evidencia/sonar/hallazgos_relevantes.txt, %s."


def put(cid, resultado, evidencia, impacto=None):
    casos[cid]["resultado"] = resultado
    casos[cid]["evidencia"] = evidencia
    casos[cid]["impacto"] = impacto


put("CP-14",
    "falla (falla esperada por diseño: sin límite de intentos, JWT_SECRET en el repositorio y clave por defecto, CLAUDE.md y AUDITORIA.md H-06, H-12 y H-19)<br>"
    "Incidente: 15 intentos fallidos seguidos no activan ningún bloqueo y la contraseña correcta entrega token; un token firmado con el JWT_SECRET publicado en el README.md es aceptado (HTTP 200 con datos de pacientes); la API arranca sin JWT_SECRET y acepta tokens firmados con \"inseguro\".<br>" + FP,
    "Paso 1: HTTP 400 con {\"field\":\"password\",\"message\":\"La contraseña es requerida\"}, sin token.<br>"
    "Paso 2: 15 intentos sobre qa_paciente_b, uno por segundo: HTTP 401 en los 15, sin 429 ni 423 ni cabecera Retry-After.<br>"
    "Paso 3: contraseña correcta después de los 15 intentos: HTTP 200 con token.<br>"
    "Paso 4, GET /pacientes: token 1 (rolNombre = admin sin re-firmar), 2 (otra clave), 3 (alg none), 4 (exp pasado), 5 (clave \"inseguro\"), 7 (esquema \"Token\" y sin cabecera): HTTP 401. Token 6 (JWT_SECRET del README.md, igual al de .env): HTTP 200 con la lista de pacientes.<br>"
    "Paso 5: la API arrancó sin JWT_SECRET (GET / HTTP 200). Con BACKEND/.env presente carga el secreto desde el archivo; sin ese archivo, un token firmado con \"inseguro\" recibe HTTP 200 en GET /pacientes.<br>"
    "Archivos: resultados/evidencia/CP-14.txt", "CRITICO")

put("CP-15",
    "falla (falla esperada por diseño: el registro vincula una ficha por RUT sin verificar al titular, CLAUDE.md y AUDITORIA.md H-10)<br>"
    "Incidente: qa_intruso2 se registra con el RUT 14.321.987-9 (HTTP 201), queda vinculado a la ficha 19 de otra persona y GET /pacientes/19 responde HTTP 200 con la ficha completa. Los pasos 1 a 3 sí se rechazan.<br>" + FP,
    "Pasos 1, 2 y 3 con T_PAC_A: PUT /pacientes/11, PUT /usuarios/14 y PUT /examenes/5: HTTP 403 los tres.<br>"
    "Paso 4: SQL de ficha B (telefono +56981230001), cuenta PAC_B (correo sebastian.alarcon@gmail.com) y EX_B1 (diagnosis \"Dato sintetico B1\") idéntico antes y después.<br>"
    "Paso 5: POST /autenticacion/registro con rut 14.321.987-9: HTTP 201. SQL pacientes id 19: usuario_id pasa de NULL a 15.<br>"
    "Paso 6: login de qa_intruso2: token con pacienteId 19; GET /pacientes/19: HTTP 200 con los datos de Claudio Ibarra; GET /examenes: HTTP 200 con lista vacía (la ficha 19 no tiene exámenes).<br>"
    "Archivos: resultados/evidencia/CP-15.txt", "GRAVE")

put("CP-16",
    "falla (falla esperada por diseño: POST /usuarios acepta cualquier JWT, el médico cambia roles, /roles y DELETE /usuarios/:id son públicos, CLAUDE.md y AUDITORIA.md H-01, H-02, H-03, H-04, H-08 y H-18)<br>"
    "Incidente: 1 de 9 escalamientos responde 403; el médico se asigna el rol admin y crea un usuario admin; sin token se crean, leen y borran roles, se lee una ficha y se borra un usuario (qa_borrar); el usuario sin rol lee otro usuario.<br>" + FP,
    "Paso 1 (esperado 403): intentos (1) a (3), PUT con solo rol_id: HTTP 400 \"Debe proporcionar al menos un campo\" (el rol no cambió); (4) T_ESC_MED POST /usuarios con rol_id 1: HTTP 201, SQL qa_intruso con rol_id 1 (admin); (5) T_ESC_PAC POST /usuarios: HTTP 500 (correo duplicado); (6) a (8) sobre /roles con T_ESC_PAC: HTTP 500 \"invalid input syntax for type bigint\", pero SQL final: existe qa_rol_intruso y qa_rol_borrar1 ya no existe; (9) DELETE /pacientes/21 con T_ESC_MED: HTTP 403. Prueba complementaria: PUT propio {correo, rol_id: 1} con T_ESC_MED: HTTP 200 y rol_nombre admin; con T_ESC_PAC: HTTP 403 \"No puede cambiar su rol\".<br>"
    "Paso 2, 11 operaciones sin token: 10 con HTTP 401; DELETE /usuarios/13: HTTP 200 {\"deleted\":true}.<br>"
    "Paso 3, 6 operaciones no documentadas sin token: solo POST /auditoria responde 401; GET /pacientes/buscar/rut/11111111-1 HTTP 200 con la ficha; GET /roles/5 HTTP 200; POST /roles HTTP 201 (qa_rol_intruso2); PUT /roles/5 HTTP 500; DELETE /roles/5 HTTP 200.<br>"
    "Paso 4: GET /files/documentos/ y GET /files/documentos/resultado_examen.pdf: HTTP 404 (la carpeta uploads/documentos está vacía; los documentos están en la BD).<br>"
    "Paso 5, token vencido: 10 de 13 con HTTP 401; GET /pacientes/buscar/rut/11111111-1 HTTP 200; DELETE /usuarios/13 y GET /roles/5 HTTP 404 (recursos ya borrados).<br>"
    "Paso 6, qa_sinrol: GET /examenes y GET /documentos/2 HTTP 403; GET /usuarios/3 HTTP 200 con datos de otro usuario.<br>"
    "Paso 7: /tipo-examen, /tipo-examen/1, /roles, /, /docs y /openapi.json: HTTP 200.<br>"
    "Paso 8: roles finales admin, medico, paciente, qa_rol_intruso, qa_rol_intruso2; qa_intruso existe con rol admin; qa_borrar eliminado. Paso 9: estado base restaurado (usuarios 14, pacientes 21, exámenes 8, documentos 7, roles 5).<br>"
    "Archivos: resultados/evidencia/CP-16.txt", "CRITICO")

put("CP-17",
    "aprobado",
    "V1, V2 y V3 en /autenticacion/login: HTTP 401 {\"error\":\"Credenciales inválidas\"}. V4 GET /pacientes/buscar/rut/%27%20OR%20%271%27%3D%271: HTTP 404.<br>"
    "V5 POST /pacientes con primer_nombre Robert'); DROP TABLE pacientes;--: HTTP 201, guardado como texto literal (SQL id 22); to_regclass('public.pacientes') = pacientes. V1 desde la pantalla de login: toast \"Credenciales inválidas\", localStorage vacío.<br>"
    "Cantidades antes y después: usuarios 14 y 14, roles 5 y 5, exámenes 8 y 8, pacientes 21 y 22 (el paciente literal de V5). Sin HTTP 500 ni trazas. El log del contenedor de la API registra las 6 solicitudes.<br>"
    "OWASP ZAP 2.17.0, escaneo activo con reglas de inyección SQL (40018, 40019, 40020, 40021 y 40022) sobre POST /autenticacion/login, POST /pacientes y GET /pacientes/{id}: 0 alertas de inyección SQL (las reglas 40024 y 90018 no existen en esa versión).<br>"
    "Archivos: resultados/evidencia/CP-17.txt, CP-17_paso6_ui.png, zap/cp17_zap_reporte.json, zap/zap_cp17.log, zap/plan_cp17.yaml<br>" + SONAR % "0 hallazgos relevantes")

put("CP-18",
    "aprobado",
    "POST /pacientes (P2, RUT 13.572.468-8) y POST /examenes (P1 y P3, paciente A): HTTP 201, Content-Type application/json.<br>"
    "7 combinaciones de navegador, con ADM y PAC_A, en lista de pacientes, registro del paciente, Mis Resultados, detalle del examen y Auditoría (100 filas por página): Playwright 1.64.1 (N) con Chromium 156.0.8078.4, Firefox 157.0, WebKit 27.2 y Edge real 156.0.4314.42; Playwright 1.63.0 (N-1) con Chromium 153.0.8010.12, Firefox 155.0 y WebKit 26.6.<br>"
    "En las 7 combinaciones el payload se muestra como texto (por ejemplo \"<img src=x onerror=alert('XSS-2')> Lillo Bravo\"); DOM: 0 elementos img[src=x], 0 svg[onload], 0 atributos onerror y 0 scripts con XSS-1; diálogos de alerta: 0. \"Mis Resultados\" no muestra diagnóstico.<br>"
    "Archivos: resultados/evidencia/CP-18_navegadores.txt, CP-18_N_*_detalle_examen.png, CP-18_N-1_*_detalle_examen.png (la ejecución inicial con Playwright 1.57.0, Chromium 143 y Firefox 144, queda en CP-18.txt y CP-18_chromium_*.png y CP-18_firefox_*.png)<br>" + SONAR % "0 hallazgos relevantes")

put("CP-19",
    "falla (parte falla esperada por diseño: Swagger documenta 26 de 32 operaciones, archivos disfrazados aceptados y HTTP 500 por id no numérico, límite de archivo y errores de rol, CLAUDE.md y AUDITORIA.md H-07, H-08, H-09, H-11 y H-14; parte hallazgo nuevo: las operaciones POST y PUT validan el cuerpo antes de autenticar)<br>"
    "Incidente: 8 de los 18 vectores no se rechazan con el código esperado (V10, V11, V13, V16 y V17 responden HTTP 500; V14, V15 y V18 responden HTTP 201); 7 de 21 operaciones con bearerAuth no responden 401 sin token (6 responden HTTP 400 y DELETE /usuarios/{id} responde 404); 6 operaciones no están en el Swagger.<br>" + FP,
    "Paso 2: 32 operaciones implementadas contra 26 del Swagger. Faltan GET /pacientes/buscar/rut/{rut}, POST /auditoria, POST /roles, GET /roles/{id}, PUT /roles/{id} y DELETE /roles/{id}. 21 operaciones declaran bearerAuth.<br>"
    "Pasos 3 y 6, Newman 6.1.3 (59 solicitudes, 118 aserciones, 20 fallidas): sin token, 14 de 21 operaciones responden 401 (POST /usuarios, PUT /usuarios, POST /pacientes, PUT /pacientes, POST /examenes y PUT /examenes responden 400; DELETE /usuarios/{id} responde 404). Endpoints críticos (login, registro, /usuarios, /pacientes, /examenes, /documentos y /auditoria): 20 de 20 pruebas positivas y negativas pasan, cobertura 7 de 7.<br>"
    "Paso 4, vectores 1 a 12 y 16: V1 a V9 y V12 responden HTTP 400; V10 (POST /roles con {}) HTTP 500; V11 (GET /examenes/abc) HTTP 500; V16 (GET /pacientes/abc) HTTP 500.<br>"
    "Paso 5, vectores 13, 14, 15, 17 y 18: V13 (.exe) HTTP 500; V14 (resultado_falso.pdf) HTTP 201; V15 (foto_falsa.jpg) HTTP 201; V17 (11 MB) HTTP 500; V18 (paciente_id 11 con examen del paciente 1) HTTP 201. V13 desde la interfaz: el diálogo \"Subir Documento\" no envía el archivo ni muestra mensaje.<br>"
    "Total de respuestas HTTP 500 en la colección: 5.<br>"
    "Archivos: resultados/evidencia/CP-19.txt, CP-19_paso5_ui_exe.png, newman/coleccion_cp19.json, newman/reporte_cp19.json, newman/newman_cp19.log, newman/resumen_cp19.txt, newman/openapi_descargado.json", "GRAVE")

put("CP-20",
    "falla (falla esperada por diseño: POST /auditoria acepta texto libre, los errores 500 devuelven mensajes de PostgreSQL y morgan(\"dev\") registra las URL, AUDITORIA.md H-11, H-12 y H-17)<br>"
    "Incidente: el POST falso de PAC_A se acepta y queda en la auditoría; los logs de acceso muestran el RUT 11111111-1 en texto claro; 3 de 4 errores provocados devuelven HTTP 500, dos de ellos con textos internos de PostgreSQL.<br>" + FP,
    "Paso 1: GET /auditoria con T_PAC_A: HTTP 403; con T_MED1: HTTP 403; sin token: HTTP 401.<br>"
    "Paso 2: POST /auditoria con T_PAC_A: HTTP 201 {\"id\":\"50\",\"accion\":\"USUARIOS_ELIMINAR: registro falso\"}; SQL: la fila existe y la tabla pasa de 48 a 49 filas. PUT y DELETE /auditoria/2 con T_ADM: HTTP 404.<br>"
    "Paso 3: en docker logs de la API no aparecen la contraseña, el token ni el diagnóstico; sí aparece GET /pacientes/buscar/rut/11111111-1 con el RUT en texto claro.<br>"
    "Paso 4: SQL, 0 filas de auditoría con contraseñas o diagnósticos.<br>"
    "Paso 5: GET /examenes/abc: HTTP 500 \"invalid input syntax for type bigint: \\\"abc\\\"\"; POST /pacientes con RUT repetido: HTTP 400 \"El RUT o email ya existe\"; PUT /usuarios/{id} con {correo, rol_id: 999}: HTTP 500 \"violates foreign key constraint usuario_roles_rol_id_fkey\" (se agregó correo porque con solo rol_id la API responde 400 por falta de campos); POST /documentos con .exe: HTTP 500 \"Internal Server Error\" (HTML). Todas las respuestas llevan X-Powered-By: Express.<br>"
    "Archivos: resultados/evidencia/CP-20.txt<br>" + SONAR % "0 hallazgos relevantes", "MODERADO")

put("CP-21",
    "falla (falla esperada por diseño: sin HTTPS, CORS abierto, sin helmet ni cabeceras de seguridad, dependencias y base Docker desactualizadas, CLAUDE.md y AUDITORIA.md H-12 y H-13; con el proxy TLS del equipo cumple TLS 1.2/1.3 pero no HSTS: \"no cumple en la entrega; cumple parcialmente con proxy del equipo\")<br>"
    "Incidente: el frontend y la API responden por HTTP plano sin redirección, la contraseña y el token viajan en texto claro, CORS devuelve Access-Control-Allow-Origin: * para cualquier origen, no hay cabeceras de seguridad ni HSTS, npm audit reporta 1 vulnerabilidad crítica en el backend y 10 altas entre ambos proyectos, la imagen node:18-alpine está sin soporte y ZAP reporta 4 alertas de riesgo medio sin plan de corrección.<br>" + FP,
    "Paso 1: GET http://localhost:3333 y http://localhost:4444: HTTP 200, sin redirección ni Strict-Transport-Security. El JS del frontend llama a http://localhost:4444. Con el proxy Caddy 2.11.7 (https://localhost:3443 y :4443) y testssl.sh 3.2.4: solo TLS 1.2 y 1.3, sin SSLv2/SSLv3/TLS 1.0/TLS 1.1, sin RC4/3DES/NULL/EXPORT, HSTS \"not offered\", cadena de confianza incompleta (CA local), calificación B.<br>"
    "Paso 2: captura tcpdump 4.99.6 (en lugar de Wireshark) en el contenedor de la API: la contraseña Cuidarte#Med2026 y el token JWT completo aparecen en texto claro.<br>"
    "Paso 3: SHOW ssl = off; DATABASE_URL del docker-compose no incluye sslmode.<br>"
    "Pasos 4 y 5: sin cookies; el token y el usuario quedan en localStorage. fetch PUT desde http://localhost:9999 con credentials include: bloqueado por el navegador (Failed to fetch); sin credentials: HTTP 401; teléfono del paciente sin cambios.<br>"
    "Paso 6: OPTIONS /usuarios con Origin http://evil.example.test y con Origin http://localhost:3333: HTTP 204 con Access-Control-Allow-Origin: * en ambos.<br>"
    "Paso 7: OWASP ZAP 2.17.0 (spider del frontend y escaneo activo de GET con sesión de MED1; sin sesión de PAC_A): 0 alertas altas; medias: falta CSP, falta cabecera anti-clickjacking, falta Subresource Integrity (frontend) y configuración CORS entre dominios (API); bajas: cabecera Server con versión (nginx/1.31.6), X-Powered-By, X-Content-Type-Options ausente.<br>"
    "Paso 8: npm audit --omit=dev: BACKEND 7 (1 crítica, 4 altas, 2 moderadas); FRONTEND 8 (6 altas, 2 moderadas). Imagen base del backend node:18-alpine (Node v18.20.8, fin de soporte 2025-04-30).<br>"
    "Paso 9: sin CSP, X-Content-Type-Options, X-Frame-Options ni Referrer-Policy en frontend ni API; /docs público; GET /files/documentos/ HTTP 404.<br>"
    "Archivos: resultados/evidencia/CP-21.txt, tls/testssl_3443.txt, tls/testssl_4443.txt, tls/captura_tcpdump_api.txt, tls/Caddyfile, zap/cp21_zap_reporte.json, npm_audit_backend.json, npm_audit_frontend.json<br>" + SONAR % "4 hallazgos relevantes", "GRAVE")

put("CP-22",
    "falla (falla esperada por diseño: contraseñas en texto plano y documentos sin cifrar, CLAUDE.md y AUDITORIA.md H-05 y H-14)<br>"
    "Incidente: las contraseñas se guardan en texto plano (18 de 18 filas no cumplen el formato Argon2id/bcrypt), los datos clínicos y los documentos están en claro en la base de datos, en los archivos físicos y en el respaldo.<br>" + FP,
    "Paso 2: SQL, qa_hash01 y qa_hash02 guardan el mismo valor Cuidarte#Hash2026 (sin sal).<br>"
    "Paso 3: SELECT count(*) ... contrasena !~ '^\\$(argon2id\\$|2[aby]\\$...' = 18 de 18 usuarios (incluidas las cuentas semilla, por ejemplo medico / medico).<br>"
    "Paso 4: login de qa_hash01: HTTP 200.<br>"
    "Paso 5: SQL, alergias \"Penicilina QA-MARKER-7391\", enfermedades_cronicas y observaciones_medicas_generales en claro; los primeros bytes del documento son \"%PDF-1.4\".<br>"
    "Paso 6: grep en /var/lib/postgresql/data encuentra QA-MARKER-7391 en base/16384/17214, base/16384/17221 y pg_wal, y QA-DOC-MARKER-5524 en base/16384/17207 y pg_wal. pg_dump -Fp: 2 apariciones de QA-MARKER-7391; pg_dump -Fc: 0 apariciones directas (archivo comprimido), pero pg_restore -f - genera SQL con 2 apariciones.<br>"
    "Paso 7: sin extensión de cifrado (solo plpgsql), sin columnas bytea cifradas en usuarios/pacientes y sin evidencia de cifrado de volumen (volumen local de Docker).<br>"
    "Archivos: resultados/evidencia/CP-22.txt<br>" + SONAR % "1 hallazgo relevante", "CRITICO")

put("CP-23",
    "falla (hallazgo nuevo: no figura en CLAUDE.md ni en AUDITORIA.md)<br>"
    "Incidente: la entrega no documenta una política de respaldo (frecuencia, retención, ubicación ni responsable); el RPO de 24 h no se puede evaluar porque no existe respaldo programado. La restauración manual sí recupera los datos.<br>" + FP,
    "Paso 1: búsqueda de \"respaldo|backup|retención|RTO|RPO|pg_dump\" en README.md, BACKEND/README.md, docker-compose.yml y Dockerfile: 0 resultados.<br>"
    "Pasos 2 y 3: línea base usuarios 14, roles 5, usuario_roles 12, tipo_examen_medico 86, pacientes 21, examen_medico 8, documentos_examen 7, auditoria 32; SHA-256 de DOC_A1 cdfc0a08…aeaa99. pg_dump -Fc: respaldo_qa.dump de 44.749 bytes (SHA-256 017bfc12…de18f), generado a las 19:42:07.<br>"
    "Paso 4: DROP DATABASE cuidarteplus WITH (FORCE): la API terminó con un error no controlado de pg y Docker la reinició (restart unless-stopped).<br>"
    "Pasos 5 y 6: pg_restore en una segunda instancia postgres:15-alpine vacía: código 0, 0,3 s. Las 8 tablas coinciden, salvo auditoria con 33 filas por un login de verificación hecho antes del respaldo. Login de MED1 y descarga de DOC_A1 contra una API conectada a la base restaurada: HTTP 200 y SHA-256 igual a la línea base. Pasos 5 y 6 completos en 10,3 s (no incluye el tiempo humano de decisión).<br>"
    "Archivos: resultados/evidencia/CP-23.txt, respaldo_qa.dump", "MODERADO")

json.dump(casos, open(os.path.join(ROOT, "casos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print({k: (v["resultado"].split(" ")[0], v["impacto"]) for k, v in casos.items()})
