import json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
casos = json.load(open(os.path.join(ROOT, "casos.json"), encoding="utf8"))
FECHA_OLD = "Fecha: 2026-10-24. Ejecutó: Felipe Villarroel."
FECHA_NEW = "Fecha: 2026-10-24 (pasos corregidos el 2026-10-25). Ejecutó: Felipe Villarroel."
MARK = "Pasos corregidos"
def fix(cid, incidente_extra, evidencia_extra):
    c = casos[cid]
    if MARK in c["evidencia"]: return
    r = c["resultado"]
    assert FECHA_OLD in r, cid
    if incidente_extra: r = r.replace(FECHA_OLD, incidente_extra + "<br>" + FECHA_NEW)
    else: r = r.replace(FECHA_OLD, FECHA_NEW)
    c["resultado"] = r
    c["evidencia"] += "<br>" + evidencia_extra
fix("CP-01", None,
    "Pasos corregidos (2026-10-25), paso 4 repetido: con sesión de MED1 se abrieron /pacientes (RUT visibles) y /examenes; tras \"Cerrar sesión\" la URL es /login y localStorage queda vacío; el botón Atrás 3 veces: dos veces /login sin datos y la tercera about:blank; abrir /pacientes sin sesión redirige a /login. Archivos: resultados/evidencia/CP-01_complemento.txt, CP-01_paso4_antes_de_cerrar.png, CP-01_paso4_atras_1.png, CP-01_paso4_atras_3.png")
fix("CP-10", None,
    "Pasos corregidos (2026-10-25), paso 2 repetido con el estado base (N = 7): se abrió en la interfaz el detalle de cada uno de los 7 exámenes de PAC_A; los 7 muestran tipo, fecha, diagnóstico, tratamiento, observaciones y documentos iguales a los de la API (7 de 7). Archivos: resultados/evidencia/CP-10_complemento.txt, CP-10_paso2_detalle_examen_2.png, CP-10_paso2_detalle_examen_3.png")
fix("CP-12",
    "Incidente adicional de la interfaz: el médico ve el botón Eliminar paciente en la lista (10 de 10 filas) aunque la API responde 403, y no ve Eliminar examen ni Eliminar documento aunque la matriz se lo permite; la interfaz del paciente abre las pantallas /pacientes, /pacientes/nuevo y /examenes (con toast de error en la lista).",
    "Pasos corregidos (2026-10-25), pasos 1 y 2 por interfaz con ADM, MED1 y PAC_A: ADM ve el menú Pacientes / Exámenes Médicos / Auditoría / Usuarios, crear, editar y eliminar usuario, registrar paciente, editar y eliminar examen, subir documento y eliminar documento; MED1 ve el menú Pacientes / Exámenes Médicos, sin Usuarios ni Auditoría (\"No autorizado\"), registrar paciente, editar examen y subir documento, y ve el botón Eliminar paciente (10 de 10 filas); PAC_A ve el menú Exámenes Médicos / Mis Resultados, sin botones de gestión, y /usuarios y /auditoria muestran \"No autorizado\".<br>"
    "Paso 4, comparación de la BD con la instantánea (md5 por tabla) tras las operaciones esperadas como denegadas: MED1 (5 operaciones) y PAC_A (12 operaciones) reciben HTTP 403 salvo POST /usuarios (HTTP 201); la única tabla que cambia en ambos casos es usuarios. Archivos: resultados/evidencia/CP-12_complemento.txt, CP-12_ui_matriz.json, CP-12_ui_MED_pacientes_con_eliminar.png, CP-12_ui_PAC_pacientes.png")
fix("CP-13",
    "Incidente adicional (paso 3): la política de privacidad no identifica a un responsable del tratamiento, no menciona oposición ni bloqueo entre los derechos, y declara \"encriptación de datos sensibles en tránsito y en reposo\", lo que CP-21 y CP-22 no confirman.",
    "Pasos corregidos (2026-10-25), paso 3: la política en /politica-privacidad (solo con sesión iniciada) tiene 9 secciones: describe usos de la información (sección 3), lista derechos de acceso, corrección, eliminación, copia de los datos y retiro del consentimiento (sección 6), y da un contacto (email, teléfono y dirección); no menciona responsable del tratamiento, oposición ni bloqueo; indica \"Encriptación de datos sensibles en tránsito y en reposo\" (sección 4). Archivos: resultados/evidencia/CP-13_complemento.txt, CP-13_paso3_politica.png")
json.dump(casos, open(os.path.join(ROOT, "casos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
# imágenes
P = json.load(open(os.path.join(ROOT, "imagenes.json"), encoding="utf8"))
P["CP-01"] = ["CP-01_paso1_home_medico.png", "CP-01_paso4_antes_de_cerrar.png", "CP-01_paso4_atras_1.png", "CP-01_paso4_atras_3.png"]
P["CP-10"] = ["CP-10_paso1_mis_resultados.png", "CP-10_paso2_detalle_examen_2.png", "CP-10_paso2_detalle_examen_3.png"]
P["CP-12"] = ["CP-12_paso3_pacientes_nuevo.png", "CP-12_paso3_rol_manipulado.png", "CP-12_ui_MED_pacientes_con_eliminar.png", "CP-12_ui_PAC_pacientes.png"]
P["CP-13"] = ["CP-13_paso1_registro.png", "CP-13_paso3_politica.png"]
json.dump(P, open(os.path.join(ROOT, "imagenes.json"), "w", encoding="utf8"), indent=1)
print("ok")
