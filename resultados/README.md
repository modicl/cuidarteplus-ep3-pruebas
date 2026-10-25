# Resultados de las pruebas (EP3 ISY1102, Cuidarte+)

Evidencia y scripts de la ejecución de los casos CP-01 a CP-23 y CP-25 sobre el sistema Cuidarte+ (código del caso B, vulnerable a propósito).

- `seccion5_hq.docx`: sección 5 del informe (resumen, detalle por caso, criticidad, casos no ejecutados y herramientas con versiones).
- `anexos_evidencias_hq.docx`: imágenes de evidencia, un capítulo por caso (CP-XX).
- `evidencia/`: logs, capturas, reportes de ZAP, Newman, testssl, SonarQube y CP-25 (k6, Lighthouse).
- `cp25/`: scripts de k6, Lighthouse y gráficos de la prueba de rendimiento.
- `cp01.py` ... `cp23.py`, `qa.py`: scripts de ejecución de cada caso (Python + Playwright + requests).
- `graficos_cp25/`: gráficos e imágenes de CP-25 en alta resolución.
- `base.dump`: estado base de la base de datos (pg_dump -Fc).

Nota: los tokens JWT y de SonarQube de los archivos de texto y JSON se reemplazaron por `<JWT>` y `<SONAR_TOKEN>` antes de publicar. Las cuentas `qa_*` son datos sintéticos de un ambiente local.

La tabla de herramientas por caso está en el [README principal](../README.md#pruebas-de-calidad-y-seguridad-ep3-isy1102).
