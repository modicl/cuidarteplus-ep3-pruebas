# Bienvenido/a

Este proyecto fue desarrollado para la asignatura ISY1102 - Calidad y seguridad en el desarrollo de software. En este repositorio se incluye un Frontend y Backend asociados al Caso A de la asignatura llamado "Sistema de Gestión Cuidarte+".

Cuidarte+ permitirá a médicos registrar pacientes y exámenes médicos, a pacientes visualizar su información clínica y a administradores supervisar, auditar y administrar usuarios y datos del sistema, adicionalmente se debe garantizar el cumplimiento de normativa de protección de datos y estándares de seguridad.

Este proyecto está pensando para ser utilizado de las siguientes maneras:
 - Podrás inicializar el backend y frontend por separado y según tu lo requieras
 - Podrás efectuar análisis de código estático para frontend y backend.
 - Podrás efectuar análisis de código dinámico al levantar ambos servicios.
 - Utilizar docker en lugar de levantar manualmente cada servicio ya que se incluye una imagen para el proyecto completo que inicializa y configura cada elemento del software construido.
 

## Estructura

Abre el proyecto mediante terminal o editor de código de preferencia Visual Studio Code. El software tiene la siguiente estructura de carpetas y archivos
 
```
root
	|/BACKEND
	|/FRONTEND
	|.env
	|.gitignore
	|docker-compose.yml
	|package.json
	|README.md
```
En el archivo `.env` se definen las variables de entorno que utilizará docker al momento de crear las imágenes, por lo que puedes modificarlas en el caso de tener otros servicios corriendo en tu equipo que utilicen los mismos puertos.

1. JWT_SECRET: `0d1d8132f0fde5beabb417b434ff10f1cae8635a461686b0f46ac9c2bbfbd0e8` Llave utilizada para cifrar y generar los tokens de sesión
2. PORT_POSTGRES: `15442` Puerto expuesto que utilizará tu equipo para permitir acceder a la conexión a la base de datos
3. PORT_BACKEND: `4444` Puerto expuesto que utilizará tu equipo para acceder a la API
4. PORT_FRONTEND: `3333` Puerto expuesto que utilizará tu equipo para acceder al cliente - frontend

## Inicialización con Docker
Abre la terminal y situate en la raíz del proyecto y ejecuta el comando:

1. Ejecuta `docker-compose up -d` para levantar todos los servicios
2. El frontend estará disponible en `http://localhost:3333` (o el puerto configurado en .env)
3. El backend estará disponible en `http://localhost:4444` (o el puerto configurado en .env)
4. La base de datos estará disponible para conectarse mediante:
	4.1 Host: `localhost`
	4.2 Port: `15442 `(o el configurado en .env)
	4.3 Database: `cuidarteplus`
	4.4 Nombre de usuario: `postgres`
	4.5 Contraseña: `postgres`


## Pruebas de calidad y seguridad (EP3 ISY1102)

Los resultados de la ejecución de los casos de prueba están en [`resultados/`](resultados/README.md). Esta tabla indica qué herramientas se necesitan para repetir cada caso.

**Requisitos generales:** Docker Desktop (Engine 29.6.1 y Compose 5.2.0) con el ambiente levantado (`docker-compose up -d`), Python 3.13 con `requests`, `playwright` y `Pillow`, y Node.js. Los scripts de cada caso están en `resultados/cpXX.py`; las utilidades comunes en `resultados/qa.py`.

| Caso | Prueba | Herramientas necesarias |
|---|---|---|
| CP-01 | Inicio y cierre de sesión | Playwright (Chromium), Python + requests, decodificación de JWT (base64) |
| CP-02 | Credenciales inválidas | Playwright, Python + requests |
| CP-03 | Registro y política de contraseñas | Playwright, Python + requests, psql |
| CP-04 | Un paciente no ve datos de otro | Playwright, Python + requests |
| CP-05 | Gestión de pacientes | Playwright, Python + requests, psql |
| CP-06 | Administración de usuarios | Playwright, Python + requests, psql |
| CP-07 | Registro y edición de exámenes | Playwright, Python + requests, psql, SHA-256 |
| CP-08 | Eliminación de exámenes y documentos | Playwright, Python + requests, psql |
| CP-09 | Documentos: subida y formatos | Playwright, Python + requests, psql, SHA-256, archivos de prueba (`resultados/gen_dm04.py`; Word y PowerPoint solo para crear los `.doc` y `.ppt`) |
| CP-10 | Paciente ve y descarga sus exámenes | Playwright, Python + requests, psql, SHA-256 |
| CP-11 | Auditoría de acciones críticas | Playwright, Python + requests, psql |
| CP-12 | Matriz de permisos por rol | Playwright, Python + requests, psql, pg_restore |
| CP-13 | Derechos del titular | Playwright, Python + requests, psql |
| CP-14 | Intentos fallidos y tokens inválidos | Python + requests, Node.js + jsonwebtoken 9.0.2 |
| CP-15 | Modificación y apropiación de fichas | Python + requests, psql |
| CP-16 | Escalamiento de privilegios y acceso sin autenticación | Python + requests, Node.js + jsonwebtoken, psql, pg_restore |
| CP-17 | Inyección SQL | Python + requests, Playwright, OWASP ZAP 2.17.0 (Docker), psql |
| CP-18 | XSS almacenado | Playwright (versiones N y N-1) y Edge real |
| CP-19 | Validación, archivos y contrato de la API | Newman 6.1.3 (Docker), Python (`resultados/build_cp19.py`), Playwright |
| CP-20 | Integridad de auditoría y logs | Python + requests, `docker logs`, psql |
| CP-21 | TLS, CORS/CSRF y escaneo | testssl.sh 3.2.4 (Docker), Caddy 2.11.7 (proxy TLS), tcpdump (imagen netshoot) en lugar de Wireshark, OWASP ZAP, npm audit, Playwright, psql |
| CP-22 | Hash de contraseñas y cifrado en reposo | Python + requests, psql, pg_dump |
| CP-23 | Respaldo y recuperación | pg_dump y pg_restore, Docker (segunda instancia de PostgreSQL), Python + requests, SHA-256 |
| CP-24 | Disponibilidad y migración (pendiente) | Uptime Kuma, Docker, pg_dump y pg_restore |
| CP-25 | Rendimiento | k6 2.3.0 (Docker), Lighthouse 13.5.0 (Node.js) con Chromium de Playwright, `docker stats`, matplotlib, Docker con límites de recursos (`resultados/cp25/`) |
| CP-26 | Compatibilidad (pendiente) | Playwright (Chromium, Firefox y WebKit), Chrome y Edge reales, Safari real, tablet y móvil |
| CP-27 | Usabilidad y accesibilidad (pendiente) | axe-core, Lighthouse, participantes de 60 años o más, cuestionario SUS |
| CP-17, 18, 20, 21, 22 | Análisis estático (evidencia complementaria) | SonarQube Community Build 26.10.0.133078 (Java 21) y SonarScanner CLI 8.1.0.6389 (Docker) |

Las versiones de cada herramienta están en la sección 5.5 de `resultados/seccion5_hq.docx`.
