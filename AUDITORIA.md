# Auditoría técnica: Cuidarte+ (BACKEND y FRONTEND)

> Documento de contexto para redactar casos de prueba e informe. Es una **revisión estática** del código: no se levantó la app ni se probaron endpoints en ejecución. Salvo `npm audit`, nada se ejecutó. No se modificó ningún archivo del proyecto.
> El README del backend declara que la API es "intencionalmente vulnerable para fines académicos" (asignatura ISY1102, Caso A "Sistema de Gestión Cuidarte+"), por lo que varios hallazgos pueden ser deliberados.
> Las referencias `archivo:línea` son relativas a `BACKEND/src/` o `FRONTEND/src/` según corresponda.

**No revisado línea por línea:** páginas informativas del frontend (`Ayuda`, `AcercaDe`, `PoliticaPrivacidad`, `TerminosUso`), maquetación interna de los formularios grandes, `theme.js`, `index.css`, `App.css`, `lib/utils.js`, `Cuidarte-Plus-Stack.docx`. Los conteos de vulnerabilidades de `npm audit` salen del resumen final de cada ejecución.

---

## 1. Resumen del sistema

Sistema web para que médicos registren pacientes y exámenes médicos, pacientes vean su información clínica y administradores auditen y administren usuarios.

| Capa | Tecnología |
|---|---|
| Backend | Node 18 (imagen Docker), Express 4, `pg` (PostgreSQL 15), `jsonwebtoken` (HS256), `yup`, `multer` (memoria), `swagger-ui-express`, `morgan`, `cors`, `dotenv` |
| Frontend | React 19, Vite 7, MUI 7 + Emotion, Tailwind 3, axios, Formik y react-hook-form, yup, material-react-table, sonner (toasts), jwt-decode, @mui/x-charts, react-router-dom 7 |
| Infra | `docker-compose.yml` con 3 servicios: Postgres, API y Nginx (sirve el SPA compilado) |
| Tests / CI | No existen |

### Puertos y URLs

| Servicio | Contenedor | Host (por defecto) | URL |
|---|---|---|---|
| Frontend (Nginx) | 80 | 3333 | `http://localhost:3333` |
| Backend (Express) | 4000 (`PORT=4000` en compose) | 4444 | `http://localhost:4444` |
| PostgreSQL | 5432 | 15442 | usuario `postgres` / clave `postgres` / BD `cuidarteplus` |

Sin Docker, el backend usa `PORT` o 3000 por defecto (el README del backend dice 4000). El frontend usa `VITE_API_URL` o `http://localhost:4444`.

### Datos semilla (de `BACKEND/sql/dump-cuidarteplus.sql`, el que usa Docker)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin` | admin (rol id 1) |
| `medico` | `medico` | medico (rol id 2) |
| `paciente` | `paciente` | paciente (rol id 3) |

Además hay 20 pacientes (ids 1 a 20, RUT como `11111111-1`) y 86 tipos de examen. El usuario `paciente` (id 3) no queda enlazado automáticamente a un registro de `pacientes` salvo que el dump lo haga (no se verificó el campo `usuario_id` de los 20 pacientes).

`BACKEND/sql/init.sql` (alternativa manual del README) **no coincide** con el dump: trae solo 10 tipos de examen y **ningún usuario ni paciente**.

### Formato común de errores

`{ "error": "<título>", "glosa": "<detalle>" }`. En los 500, `glosa` es `err.message` (incluye mensajes de PostgreSQL). Los 400 de validación añaden `detalles: [{field, message}]`. Algunos 401/404 devuelven solo `{error}`.

### JWT emitido por el login

Firmado con `JWT_SECRET` (o `"inseguro"` si no está definido), expira en 2 h. Payload: `usuarioId, nombreUsuario, rolId, rolNombre, pacienteId, roles[{id,nombre}]`. **No incluye `empresaId`.** Nota: `usuarioId` y `pacienteId` provienen de columnas `BIGINT`, que `pg` entrega como **string**.

---

## 2. Catálogo de endpoints (32 de API + 4 utilitarios)

Leyenda de acceso: **Pub** = sin autenticación, **JWT** = cualquier token válido (sin comprobar rol), **M/A** = rol `medico` o `admin`, **A** = rol `admin`.
Los roles se consultan en BD en cada petición (tabla `usuario_roles`), no se leen del token, salvo `GET /autenticacion/login` que los incluye en él solo como información.
Columna "Acceso real" = lo que hace el código. Columna "Comentario/intención" = lo que dicen los comentarios o la documentación, cuando difiere.

### 2.1 Utilitarios (`app.js`)

| Método | Ruta | Acceso | Notas |
|---|---|---|---|
| GET | `/` | Pub | Responde `{name:"cuidarteplus", status:"ok"}` |
| GET | `/docs` | Pub | Swagger UI |
| GET | `/openapi.json` | Pub | Especificación (documenta solo 26 de las 32 operaciones) |
| GET | `/files/documentos/*` | Pub | `express.static` sobre `BACKEND/uploads/documentos`. Hoy vacía, porque los archivos se guardan en BD. |

### 2.2 `/autenticacion` (`routes/auth.js`)

| Método | Ruta | Acceso | Body | Respuestas |
|---|---|---|---|---|
| POST | `/autenticacion/login` | Pub | `{nombre_usuario (3-50), password}` | 200 `{token}`; 401 `{error:"Credenciales inválidas"}` (mismo mensaje para usuario inexistente y clave errónea); 400 validación; 500. Inserta auditoría `LOGIN: usuario inició sesión`. |
| POST | `/autenticacion/registro` | Pub | `{nombre_usuario (3-50), password (min 6), correo (email), rut?}` | 201 `{message, usuario}`; 400 si RUT ya tiene cuenta (`RUT ya registrado`), si usuario o correo duplicado, o por validación; 500. Asigna rol `paciente`. Si hay RUT: enlaza al paciente existente sin cuenta, o crea uno con datos de relleno (`fecha_nacimiento` 2000-01-01, sexo `M`, `apellido_paterno` vacío, `primer_nombre` = nombre de usuario). |

El RUT se valida con regex `^([0-9]{1,2}(\.[0-9]{3})*-[0-9kK]|[0-9]+-[0-9kK])$` y se normaliza quitando puntos. **No se valida el dígito verificador.**

### 2.3 `/usuarios` (`routes/users.js`)

| Método | Ruta | Acceso real | Comentario/intención | Detalle |
|---|---|---|---|---|
| POST | `/usuarios` | **JWT (cualquier rol)** | no declara restricción | Body `{nombre_usuario, contrasena_hash, correo, rol_id?}`. Inserta usuario (la clave se guarda tal cual en `usuarios.contrasena`). Si hay `rol_id`, inserta en `usuario_roles`. 201 con el usuario creado. |
| GET | `/usuarios` | A (consulta `usuario_roles`) | | Lista todos (`id, nombre_usuario, correo, created_at`). 403 si no es admin. |
| GET | `/usuarios/:id` | JWT. Un usuario con rol `paciente` y sin rol `admin`/`medico` solo puede ver el suyo (403 si no). | | Devuelve datos del usuario + `rol_id`, `rol_nombre`, `es_unico_administrador:false`. Un usuario autenticado **sin ningún rol** pasa sin restricción. |
| PUT | `/usuarios/:id` | A, o el propio usuario | | Valida con `updateUserSchema` (no declara `rol_id`, pero ver hallazgo H-03). Un `paciente` no puede enviar `rol_id` (403). Un médico sí puede, aun editándose a sí mismo. Al cambiar rol borra los existentes y crea el nuevo. |
| DELETE | `/usuarios/:id` | **Pub (no hay chequeo de token ni de rol)** | | Ejecuta `DELETE FROM usuarios`. Luego inserta auditoría usando `authUser?.nombreUsuario` en una columna `BIGINT` (ver H-08). Responde 200 `{deleted:true}` solo si la auditoría no falla. |

### 2.4 `/pacientes` (`routes/pacientes.js`)

| Método | Ruta | Acceso real | Detalle |
|---|---|---|---|
| POST | `/pacientes` | M/A | Valida con `pacienteSchema`. Inserta 22 campos. Acepta `usuario_id` del body (no está en el esquema, pero se lee igual). 400 si RUT/email duplicado (código PG 23505). |
| GET | `/pacientes` | M/A | **Retraso artificial de 5 s** (`delayMiddleware(5000)`) antes de cualquier chequeo. Devuelve todos los pacientes + `nombre_usuario`. |
| GET | `/pacientes/:id` | M/A, o paciente dueño | Un paciente solo ve su propio registro. Un usuario con otro rol (o sin rol) recibe 403. |
| GET | `/pacientes/buscar/rut/:rut` | **Pub** | Comentario: "público para pacientes". Devuelve la ficha completa (`p.*` + `nombre_usuario`). 404 si no existe. |
| PUT | `/pacientes/:id` | M/A, o paciente dueño | Campos editables incluyen `rut` y `usuario_id`. 400 si no hay ningún campo. |
| DELETE | `/pacientes/:id` | A | |

### 2.5 `/examenes` (`routes/examenes.js`)

| Método | Ruta | Acceso real | Detalle |
|---|---|---|---|
| POST | `/examenes` | M/A | **5 s de retraso.** Body `{tipo_examen_medico_id, paciente_id, diagnosis?, tratamiento?, observaciones?, notas?}` (textos máx 2000). No comprueba que el paciente exista (lo hace la FK). |
| GET | `/examenes` | M/A/paciente | **5 s de retraso.** Paciente: solo los suyos (404 si no tiene ficha asociada). Incluye `tipo_examen_nombre` y datos básicos del paciente. |
| GET | `/examenes/:id` | M/A/paciente | Paciente: filtra por su `paciente_id`; si el examen es de otro, 404 (no 403). |
| GET | `/examenes/paciente/:paciente_id` | M/A/paciente | Paciente: 403 si el id no es el suyo. |
| PUT | `/examenes/:id` | M/A | **5 s de retraso.** Permite cambiar `tipo_examen_medico_id` y `paciente_id`. |
| DELETE | `/examenes/:id` | A | |

### 2.6 `/documentos` (`routes/documentos.js`)

| Método | Ruta | Acceso real | Detalle |
|---|---|---|---|
| POST | `/documentos` | M/A | **5 s de retraso.** `multipart/form-data`, campos `examen_medico_id`, `paciente_id`, archivo `documento`. Límite 10 MB. Tipos permitidos por `file.mimetype` (declarado por el cliente): `application/pdf`, `image/jpeg`, `image/jpg`, `image/png`. Guarda el binario en `documentos_examen.documento` (`BYTEA`). Responde 201 `{documento:{id,nombre_archivo,created_at}}`. |
| GET | `/documentos/examen/:examen_id` | M/A/paciente | Lista `{id, nombre_archivo, created_at}`. Un paciente solo si el examen es suyo (403). |
| GET | `/documentos/:id` | M/A/paciente | Descarga con `Content-Disposition: attachment; filename="<nombre original>"`. El `Content-Type` se deduce de la extensión (por defecto `application/pdf`). Un paciente solo si es suyo (403). Un usuario sin ningún rol también pasa el primer chequeo; el `else if` sí lo bloquea (403). |
| DELETE | `/documentos/:id` | A | |

### 2.7 `/tipo-examen` (`routes/tipo-examen.js`)

| Método | Ruta | Acceso real | Comentario |
|---|---|---|---|
| GET | `/tipo-examen` | **Pub** | "público para autenticados" |
| GET | `/tipo-examen/:id` | **Pub** | |

### 2.8 `/auditoria` (`routes/audit.js`)

| Método | Ruta | Acceso real | Detalle |
|---|---|---|---|
| POST | `/auditoria` | JWT | Body `{accion, detalles?}` sin validación. Inserta `"accion: detalles"` como texto libre. |
| GET | `/auditoria` | A | Solo admin ve todo. Un usuario con `empresaId` en el token tomaría otra rama, pero el login nunca lo emite. |

### 2.9 `/roles` (`routes/roles.js`)

| Método | Ruta | Acceso real | Detalle |
|---|---|---|---|
| POST | `/roles` | **Pub** | Body `{nombre}` sin validación |
| GET | `/roles` | **Pub** | |
| GET | `/roles/:id` | **Pub** | |
| PUT | `/roles/:id` | **Pub** | Renombra |
| DELETE | `/roles/:id` | **Pub** | `usuario_roles` borra en cascada (`ON DELETE CASCADE`) |

### 2.10 Cobertura de la documentación OpenAPI (`src/openapi.json`)

Documenta 26 de las 32 operaciones. **No documentadas:** `POST /auditoria`, `POST /roles`, `GET /roles/:id`, `PUT /roles/:id`, `DELETE /roles/:id`, `GET /pacientes/buscar/rut/:rut`. Solo `GET /roles` está documentada.

---

## 3. Modelo de datos (PostgreSQL)

| Tabla | Columnas relevantes | Relaciones |
|---|---|---|
| `usuarios` | `id` (identity), `nombre_usuario` UNIQUE, `contrasena` TEXT (texto plano), `correo` UNIQUE, `created_at` | |
| `roles` | `id`, `nombre` UNIQUE | Semilla: admin(1), medico(2), paciente(3) |
| `usuario_roles` | `usuario_id`, `rol_id`, UNIQUE(usuario_id, rol_id) | FK a usuarios y roles, ambas `ON DELETE CASCADE` |
| `tipo_examen_medico` | `id`, `nombre` UNIQUE | |
| `pacientes` | `rut` UNIQUE, nombres, `fecha_nacimiento`, `sexo` CHECK(M/F/O), `estado_civil` CHECK, `email` (no UNIQUE en el SQL), datos de contacto, previsión, datos médicos (`grupo_sanguineo`, `alergias`, `enfermedades_cronicas`, `discapacidades`, `observaciones_medicas_generales`), `usuario_id` | FK a usuarios `ON DELETE SET NULL` |
| `examen_medico` | `tipo_examen_medico_id`, `paciente_id`, `diagnosis`, `tratamiento`, `observaciones`, `notas`, `created_at` | FK a paciente `ON DELETE CASCADE` |
| `documentos_examen` | `examen_medico_id`, `paciente_id`, `documento` BYTEA, `nombre_archivo` | FKs `ON DELETE CASCADE` |
| `auditoria` | `usuario_id` **BIGINT** FK a usuarios (`SET NULL`), `accion` TEXT, `fecha_hora` | |

Nota: el mensaje de error del backend para email duplicado dice "El RUT o email ya existe", pero según `init.sql` solo `rut` es UNIQUE. Hay que revisar el dump para saber si `email` tiene restricción (no se verificó).

Los índices existen sobre `pacientes(rut)`, `pacientes(usuario_id)`, `examen_medico(paciente_id)`, `documentos_examen(examen_medico_id, paciente_id)` y `auditoria(usuario_id, fecha_hora)`.

---

## 4. Hallazgos de seguridad del backend

Cada hallazgo lleva un ID para poder referenciarlo en casos de prueba. "Reproducción" describe la prueba, no se ejecutó.

### Críticos

**H-01 — `DELETE /usuarios/:id` sin autenticación** (`routes/users.js:571-597`)
Ni el middleware ni el handler comprueban token o rol. Reproducción: `DELETE /usuarios/<id>` sin cabecera `Authorization` devuelve 200 y borra el usuario (con cascada a `usuario_roles`; `pacientes.usuario_id` y `auditoria.usuario_id` quedan en NULL).

**H-02 — `/roles` completamente público** (`routes/roles.js`, todas las rutas)
Sin token se puede crear, leer, renombrar y borrar roles. Renombrar el rol `admin` rompe la autorización basada en nombres; borrar un rol elimina por cascada las asignaciones de los usuarios. Reproducción: `PUT /roles/1 {"nombre":"x"}` sin token.

**H-03 — Escalada de privilegios por rol** (`routes/users.js:23-72` y `246-281`, `437-532`)
- `POST /usuarios` solo exige un token válido: un `paciente` puede enviar `rol_id` = id de admin y crear un administrador.
- En `PUT /usuarios/:id`, el middleware `validate` valida pero **no reemplaza `req.body`** (ver H-07), así que `rol_id` llega al handler aunque el esquema no lo declare. En la rama de sistema médico, la condición `isAdminOrMedico` permite a un `medico` cambiar roles, incluido el suyo propio (la rama de empresa sí bloquea cambio de rol propio; la médica no).

**H-04 — Ficha de paciente expuesta sin autenticación** (`routes/pacientes.js:248-273`)
`GET /pacientes/buscar/rut/:rut` devuelve `p.*` (datos personales y médicos, contacto de emergencia, previsión) sin token. El RUT es enumerable (formato chileno, validación solo por regex).

**H-05 — Contraseñas en texto plano** (`routes/auth.js:21`, `110-112`; `users.js:36`)
Se almacenan y comparan con `!==`/`===`. El campo se llama `contrasena_hash` en el API pero no hay hash. Credenciales semilla trivialmente iguales al usuario.

**H-06 — Secretos y credenciales en el código y el repositorio**
- `JWT_SECRET` real publicado en `README.md` (raíz) y presente en `.env`, `BACKEND/.env`.
- Valor de respaldo `"inseguro"` en 7 archivos de rutas.
- `docker-compose.yml`: respaldo `your-secret-key-change-in-production`.
- `db.js:5-6`: conexión por defecto con contraseña escrita en el código.
- `.gitignore` solo ignora `node_modules`, por lo que los `.env` se versionan. La carpeta analizada no es un repositorio git.

### Altos

**H-07 — `validate` no aplica `stripUnknown` al body** (`middleware/validate.js:5`)
Usa `schema.validate(data, {stripUnknown: true})`, pero **descarta el resultado** y sigue con `req.body` original. Consecuencias: campos no declarados llegan al handler (asignación masiva). Los parámetros de ruta (`:id`) no se validan en ningún lugar: un `id` no numérico produce un error de PostgreSQL (22P02) y un 500 con el mensaje técnico.

**H-08 — Bitácora de auditoría incorrecta** (`routes/roles.js:24-27, 64-67, 82-85`; `routes/users.js:580-587`)
Insertan `authUser?.nombreUsuario` (texto) en `auditoria.usuario_id` (BIGINT). Con token válido la inserción falla y el endpoint responde 500 **después** de haber ejecutado el cambio (la operación principal ya se aplicó, sin transacción). Sin token se inserta NULL y funciona. Los eventos de roles y de eliminación de usuarios, por tanto, no quedan auditados correctamente.

**H-09 — Asignación masiva y falta de verificación de propiedad**
- `PUT /pacientes/:id`: `allowedFields` incluye `usuario_id` y `rut`, así que un paciente dueño puede cambiar el `usuario_id` de su ficha o su RUT.
- `PUT /examenes/:id`: permite reasignar `paciente_id`.
- `POST /documentos`: no comprueba que `paciente_id` corresponda al paciente del `examen_medico_id`.
- `POST /pacientes`: acepta `usuario_id` arbitrario para enlazar una ficha a cualquier usuario.

**H-10 — Registro permite apropiarse de una ficha por RUT** (`routes/auth.js:71-166`)
Quien conozca el RUT de un paciente ya cargado y sin cuenta puede registrarse con ese RUT y quedar enlazado a su ficha, sin verificación (correo, código). Además el mensaje `RUT ya registrado` y `Usuario o correo duplicado` permiten enumerar RUT, usuarios y correos.

**H-11 — Información interna en errores**
Todos los `catch` devuelven `glosa: err.message || err.toString()`. Se filtran mensajes de PostgreSQL (nombres de columna, tipos, etc.).

**H-12 — Sin endurecimiento HTTP**
No hay `helmet`, rate limiting ni bloqueo por intentos fallidos en `/autenticacion/login`; `cors()` abierto a cualquier origen; `morgan("dev")` en producción; sin HTTPS.

**H-13 — Dependencias vulnerables (`npm audit --omit=dev`)**
- Backend: 7 vulnerabilidades (1 crítica: `proxy-addr`; 3 altas, entre ellas `path-to-regexp`; 3 moderadas, entre ellas `qs`). Corregibles con `npm audit fix`.
- Frontend: 8 vulnerabilidades (6 altas, 2 moderadas), casi todas de `react-router` / `react-router-dom` (7.0.0-pre.0 a 7.11.0), más `yaml` en una dependencia transitiva.
- Imagen base del backend `node:18-alpine` (versión sin soporte).

**H-14 — Subida de archivos**
- Validación solo por `mimetype` declarado por el cliente, sin comprobar el contenido (firma de archivo).
- `nombre_archivo` (nombre original) se escribe en `Content-Disposition` sin sanear.
- Si `fileFilter` rechaza un archivo, el error cae en el manejador por defecto de Express (no hay manejador de errores propio).
- Documentos clínicos almacenados sin cifrado en `BYTEA`.

**H-15 — Retraso artificial `delayMiddleware(5000)`** en `GET /pacientes`, `POST/GET/PUT /examenes` y `POST /documentos`. Se ejecuta antes de la autenticación, de modo que cualquier petición, incluso sin token, mantiene la conexión abierta 5 s (vector de agotamiento de recursos). Probablemente sea intencional para pruebas de carga o de tiempos.

### Medios y bajos

- **H-16** Registro (`/registro`) y alta de usuario ejecutan 3 a 5 `INSERT` sin transacción: un fallo intermedio deja datos huérfanos.
- **H-17** `POST /auditoria` permite a cualquier usuario autenticado escribir texto libre en la bitácora (falsificación de registros).
- **H-18** `GET /usuarios/:id`: un usuario autenticado sin ningún rol no tiene restricción de lectura sobre otros usuarios.
- **H-19** El JWT de 2 h no tiene refresh ni revocación; no se fija el algoritmo de verificación (`jwt.verify` sin `algorithms`).
- **H-20** Funciones de autenticación y autorización duplicadas en 6 archivos (`getUserFromAuthHeader` en `audit.js`, `auth.js` no, `documentos.js`, `examenes.js`, `pacientes.js`, `roles.js`, `users.js`; `requireRole` en `documentos.js`, `examenes.js`, `pacientes.js`). Sin middleware común.
- **H-21** Los datos de relleno que el registro crea en `pacientes` (sexo `M`, nacimiento 2000-01-01, apellido vacío) pueden contaminar datos clínicos reales.

### Código muerto o desactualizado (backend)

- Ramas `if (authUser.empresaId)` en `routes/users.js` y `routes/audit.js` y las funciones `updateUsuarioEmpresa`: **nunca se ejecutan**, el login no emite `empresaId`. Vienen de otro proyecto.
- `validations/empresa_usuarios.js`: no se importa en ninguna ruta.
- `README.md` del backend documenta endpoints inexistentes (`/clientes`, `/contratos`, `/empresas`, `/empresa-usuarios`), campos `contrasena_hash` en login (el login usa `password`) y puerto 4000.
- `BACKEND/uploads/contracts/`: carpeta residual del otro proyecto. El Dockerfile la crea.

---

## 5. Frontend

### 5.1 Estructura

`FRONTEND/src`: `App.jsx` (rutas), `main.jsx`, `components/` (`Layout`, `PageHeader`, `RoleGuard`), `context/AuthContext.jsx` (+ `authContextInstance.js`), `hooks/useAuth.js`, `lib/api.jsx` (cliente axios), `lib/utils.js`, `pages/` (auth, pacientes, examenes, usuarios, auditoria, informacion, Home), `validations/` (yup).
Aproximadamente 8.100 líneas. Archivos más grandes: `UsuarioForm.jsx` (862), `Layout.jsx` (686), `Home.jsx` (682), `ExamenForm.jsx` (622), `PacientesTabCreate.jsx` (515).

### 5.2 Rutas del cliente (react-router 7)

| Ruta | Componente | Protección en cliente |
|---|---|---|
| `/login` | Login | Pública |
| `/registro` | Register | Pública (llama a `POST /autenticacion/registro`) |
| `/` y `/home` | Home | `RequireAuth` (solo comprueba que haya token) |
| `/pacientes`, `/pacientes/nuevo`, `/pacientes/:id/editar` | PacientesList, PacienteForm | `RequireAuth` solamente |
| `/examenes`, `/examenes/:id` | ExamenesList, ExamenDetalle | `RequireAuth` solamente |
| `/mis-resultados` | MisResultados | `RequireAuth` solamente |
| `/auditoria` | AuditoriaList | `RequireAdmin` |
| `/usuarios` | UsuariosList | `RequireAdmin` |
| `/usuarios/:id/editar` | UsuarioForm | `RequireAdminOrOwnUser` |
| `/politica-privacidad`, `/terminos-uso`, `/acerca-de`, `/ayuda` | Páginas informativas | `RequireAuth` |
| `*` | | Redirige a `/login` |

El menú lateral (`Layout.jsx:48-87`) filtra ítems por rol: `admin`, `medico`, `paciente`. Esa visibilidad es solo de interfaz.

### 5.3 Comunicación con la API

- Cliente axios (`lib/api.jsx`), `baseURL = VITE_API_URL` (inyectado al compilar; en Docker `http://localhost:${PORT_BACKEND}`).
- Interceptor de petición: añade `Authorization: Bearer <token>` leyendo `localStorage.token`, salvo en login, en un supuesto "registro" (`POST` a una URL con `/empresas` sin token) y en `/public/contratos`. Estas dos últimas condiciones son residuos de otro proyecto.
- Interceptor de respuesta: muestra un toast por cada error usando `{error, glosa}`. **No hay manejo especial del 401** (no redirige ni limpia la sesión).
- Llamadas usadas por las páginas: login, registro, `/examenes` (GET/POST/PUT/DELETE, `/examenes/:id`, `/examenes/paciente/:id`), `/documentos` (POST, `/documentos/examen/:id`, GET/DELETE `/:id`), `/pacientes` (GET/POST/PUT/DELETE, `/:id`), `/usuarios` (GET/POST/PUT/DELETE, `/:id`), `/roles` (GET lista), `/tipo-examen` (GET lista), `/auditoria` (GET).
- **No usa:** `GET /pacientes/buscar/rut`, `POST /auditoria`, `GET /tipo-examen/:id`, ni los métodos de `/roles` distintos a listar.

### 5.4 Gestión de sesión

- `AuthContext.jsx`: guarda `token` y `user` (JSON con el payload del JWT decodificado con `jwt-decode`) en **`localStorage`**.
- El rol efectivo para la UI sale de `user.rolNombre` (si falta, de `user.rolId` 1/2/3), es decir, de un valor que el usuario puede alterar en su navegador. La autorización real depende del backend.
- `logout` borra `token` y `user`. No hay llamada al servidor ni revocación.

### 5.5 Hallazgos del frontend

- **F-01** Token JWT y datos de usuario en `localStorage`: accesibles ante cualquier XSS.
- **F-02** Guardas de ruta insuficientes: `RequireMedico` está definida en `RoleGuard.jsx` pero **no se usa en `App.jsx`**. `/pacientes`, `/pacientes/nuevo` y `/examenes` no restringen por rol en el cliente (el backend responde 403 a quien no corresponde).
- **F-03** Sin manejo de expiración (2 h): al vencer el token, las pantallas muestran toasts de error en vez de redirigir al login.
- **F-04** Código heredado: `validations/clients.js`, `validations/contracts.js` y `validations/empresas.js` no se importan en ninguna página (solo se usan `auth`, `pacientes` y `users`). `lib/api.jsx` aún referencia `/empresas` y `/public/contratos`.
- **F-05** Dos librerías de formularios (Formik y react-hook-form) y dos sistemas de estilos (MUI/Emotion y Tailwind) conviven en el mismo proyecto.
- **F-06** Componentes de gran tamaño y lógica duplicada (descarga de documentos con `createObjectURL` repetida en `ExamenDetalle`, `ExamenForm`, `MisResultados`; pares `*TabList` / `*TabCreate`).
- **F-07** Validaciones yup del cliente copiadas a mano respecto de las del servidor (riesgo de divergencia).
- **F-08** `index.html` declara `<html lang="en">` aunque la interfaz es en español; la tipografía se carga desde Google Fonts (dependencia externa, relevante para política de privacidad/CSP).
- **F-09** Dependencias con vulnerabilidades (ver H-13).
- **F-10** `Home.jsx` consulta `/pacientes` y `/examenes` con `.catch(() => ({data: []}))`, pero el interceptor de respuesta igualmente muestra un toast de error para los roles sin permiso (por ejemplo, un paciente recibe un 403 al cargar `Home`). No verificado en ejecución.

---

## 6. Infraestructura y despliegue

| Elemento | Observación |
|---|---|
| `BACKEND/Dockerfile` | `node:18-alpine` (sin soporte); corre como root; `EXPOSE 3000` pero la app usa `PORT=4000` en compose; sin `HEALTHCHECK`; `npm ci --only=production` (flag obsoleto); copia `uploads/` (debe existir en el contexto). |
| `FRONTEND/Dockerfile` | Multi-stage (`node:20` + `nginx:alpine`). Borra `package-lock.json` y reinstala, por lo que los builds no son reproducibles. Reinstala `@rollup/rollup-linux-x64-gnu` y `esbuild` como parches. |
| `FRONTEND/nginx.conf` | Solo SPA fallback (`try_files … /index.html`), gzip y un `location /static` que no corresponde a la salida de Vite (`/assets`). Sin cabeceras de seguridad ni HTTPS. |
| `docker-compose.yml` | Postgres expone `15442` al host con `postgres/postgres`. El backend monta `./BACKEND/uploads`. `depends_on` con `service_healthy` para la BD. |
| `BACKEND/sql/init-db.sh` | Filtra con `grep -v` líneas del dump (`DROP/CREATE DATABASE`, `CREATE SCHEMA public`, etc.) y lo carga con `ON_ERROR_STOP=0`: los errores del dump no detienen la carga y pasan desapercibidos. |
| Raíz `package.json` | El script `start` encadena backend y frontend con `&&`, por lo que el segundo nunca arranca mientras el primero siga corriendo. |
| Repositorio | `.gitignore` solo contiene `BACKEND/node_modules` y `FRONTEND/node_modules`. No hay tests, linter en el backend ni CI. |

---

## 7. Mapa de pruebas sugerido (para guiar los casos de prueba)

Cada fila liga un comportamiento verificable con su hallazgo.

| Área | Prueba | Resultado esperado hoy (según el código) | Ref. |
|---|---|---|---|
| Auth | Login con `admin/admin` | 200 con `{token}` | H-05 |
| Auth | Login con clave incorrecta / usuario inexistente | 401 con el mismo mensaje en ambos casos | |
| Auth | Registro con RUT de paciente existente sin cuenta | 201, la cuenta queda enlazada a esa ficha | H-10 |
| Auth | Registro con RUT que ya tiene cuenta | 400 `RUT ya registrado` | H-10 |
| Auth | Muchos intentos de login fallidos seguidos | Sin bloqueo ni limitación | H-12 |
| Autorización | `DELETE /usuarios/:id` sin token | 200, el usuario desaparece | H-01 |
| Autorización | `PUT /roles/1` sin token | 200, el rol cambia | H-02 |
| Autorización | `GET /pacientes/buscar/rut/11111111-1` sin token | 200 con la ficha completa | H-04 |
| Autorización | `POST /usuarios` con token de `paciente` y `rol_id`=1 | 201, se crea un usuario admin | H-03 |
| Autorización | `PUT /usuarios/<id médico>` con token de médico y `rol_id`=1 | 200, el médico pasa a admin | H-03 |
| Autorización | `GET /usuarios` con token de médico o paciente | 403 | |
| Autorización | `GET /auditoria` con token de médico | 403 | |
| Aislamiento | Paciente A pide `GET /pacientes/<id de B>` | 403 | |
| Aislamiento | Paciente A pide `GET /examenes/<id de B>` | 404 (no 403) | |
| Aislamiento | Paciente A pide `GET /documentos/<id de B>` | 403 | |
| Aislamiento | Paciente edita su propia ficha enviando `usuario_id` o `rut` | 200, se aplica el cambio | H-09 |
| Validación | `POST /pacientes` con RUT inválido por formato | 400 con `detalles` | |
| Validación | `POST /pacientes` con RUT de formato válido y dígito verificador incorrecto | 201 (no se valida el dígito) | |
| Validación | `GET /pacientes/abc` con token de admin | 500 con mensaje de PostgreSQL | H-07, H-11 |
| Validación | `PUT /usuarios/:id` con cuerpo vacío | 400 `Debe proporcionar al menos un campo` | |
| Archivos | `POST /documentos` con archivo `.exe` declarado como `application/pdf` | 201 (solo se mira el mimetype) | H-14 |
| Archivos | `POST /documentos` con archivo > 10 MB | Error del manejador por defecto de Express | H-14 |
| Archivos | `POST /documentos` con `paciente_id` que no corresponde al examen | 201 | H-09 |
| Auditoría | `DELETE /roles/:id` con token válido | 500 tras aplicar el borrado, sin registro de auditoría | H-08 |
| Auditoría | `POST /auditoria` con texto arbitrario (token de paciente) | 201 | H-17 |
| Rendimiento | `GET /pacientes` | ≥ 5 s de respuesta | H-15 |
| Rendimiento | `POST /examenes` | ≥ 5 s de respuesta | H-15 |
| Sesión (UI) | Editar `user.rolNombre` en `localStorage` y navegar a `/usuarios` | La UI muestra la pantalla, el backend responde 403 a los datos | F-01, F-02 |
| Sesión (UI) | Token vencido y navegar | Toasts de error, sin redirección a login | F-03 |
| UI | Paciente navega manualmente a `/pacientes/nuevo` | Se muestra el formulario; el guardado falla con 403 | F-02 |
| Dependencias | `npm audit` en BACKEND y FRONTEND | Backend: 7 vulnerabilidades; Frontend: 8 | H-13 |

## 8. Referencia normativa (contexto del enunciado)

El README exige "cumplimiento de normativa de protección de datos y estándares de seguridad". En Chile aplican la Ley 19.628 (protección de la vida privada) y la Ley 21.719 (nueva ley de protección de datos personales). Los datos de salud son datos sensibles. Los hallazgos H-01, H-02, H-04, H-05, H-06, H-10 y H-14 son los más relevantes frente a ese requisito (acceso no autorizado a datos sensibles, ausencia de cifrado y de hash, secretos expuestos).
