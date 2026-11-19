# Portal de Formación Aldelis

Portal web para la formación del personal **interno** (nuevas incorporaciones y formación de puesto) y **externo** (transportistas, contratas, visitas).

- Pensado para usarse desde el **móvil o tablets compartidas en planta**.
- Los operarios **no necesitan cuenta corporativa ni email**: entran con su **DNI + PIN** de 6 cifras.

## Cómo funciona

```
Alta del empleado (DNI, puesto)  ──►  se le asignan automáticamente sus itinerarios
                                         │
   ┌─────────────────────────────────────┼──────────────────────────────────┐
   ▼                                     ▼                                  ▼
Acogida Aldelis               Logística · formación común         Puesto · Recepción / Logística
(todo el personal interno)    (todos los puestos de logística)    interna / Registro de producción /
 · Manual del empleado         · Seguridad y prevención              Expediciones
 · Buenas prácticas de         · Trazabilidad, lotes y registros     (específico de cada puesto)
   manipulación
```

El personal externo recibe solo el itinerario **«Personal externo»** (normas de acceso y seguridad).

Cada curso tiene:
1. **Temas**: texto, PDF, presentación o vídeo. El alumno marca cada tema como leído.
2. **Examen tipo test**: se desbloquea al terminar el temario. Se configuran la nota mínima, el número de intentos, el límite de tiempo, si se barajan las preguntas y si se sacan N preguntas al azar de un banco.
3. **Certificado** imprimible o guardable en PDF al aprobar, con el nombre, el DNI, la nota, la fecha y la versión del temario.

## Pantallas

| Quién | Dónde | Qué hace |
|---|---|---|
| Operario / externo | `/` | «Mi formación»: cursos agrupados por itinerario, avance y plazos |
| RR. HH. / responsables | `/seguimiento/` | Avance de cada persona, filtros (puesto, interno/externo, vencidos) y exportación a Excel |
| RR. HH. | `/seguimiento/alta/` | Alta individual o masiva desde Excel. Genera el PIN y una **ficha de acceso imprimible** |
| RR. HH. / Formación | `/admin/` | Gestión de cursos, temas, exámenes, itinerarios, puestos y empleados |

## Tareas habituales (desde «Gestión»)

- **Subir un temario**: Cursos → elegir curso → añadir temas. Cada tema admite texto y un archivo (PDF, vídeo MP4) o un enlace a un vídeo, por ejemplo de SharePoint o Stream.
- **Crear un examen**:
  - Exámenes → abrir el examen → **«Importar preguntas (CSV/Excel)»**. Plantilla: [`docs/plantilla_preguntas.csv`](docs/plantilla_preguntas.csv).
  - También se pueden añadir las preguntas una a una.
- **Nuevo puesto o departamento**: Departamentos → añadir el puesto. Después se crea un itinerario para ese puesto.
- **Itinerarios**:
  - Cada itinerario define a quién se asigna: todo el personal interno, el personal externo, uno o varios departamentos o uno o varios puestos. También define qué cursos incluye y el plazo en días para completarlos.
  - Si añades cursos a un itinerario que ya está en marcha, usa la acción **«Asignar a los empleados afectados»**.
- **PIN olvidado**: Usuarios → seleccionar a la persona → acción **«Generar PIN nuevo e imprimir fichas de acceso»**.
- **Cambio de puesto**: edita el puesto en la ficha del usuario. Los cursos del nuevo puesto se asignan solos y se conserva lo ya completado.

## Acceso y seguridad

- **Operarios y externos**: DNI + PIN de 6 cifras.
  - Los PIN se guardan cifrados y solo se ven en el momento en que se generan.
  - Tras 5 intentos fallidos, el acceso se bloquea 15 minutos.
- **Oficina, RR. HH. y responsables**: usuario y contraseña. Para ver el seguimiento y la gestión hace falta tener marcado «Es staff».
- **Tablets compartidas**: la sesión se cierra tras 30 minutos sin actividad y al cerrar el navegador. Se ajusta con la variable `SESION_MINUTOS`.
- Los temarios solo se descargan con la sesión iniciada y si el curso está asignado.

## Puesta en marcha (desarrollo)

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python manage.py migrate
```

```bash
.venv/bin/python manage.py cargar_datos_iniciales --demo
```

```bash
.venv/bin/python manage.py runserver
```

`--demo` crea estas cuentas de prueba:
- `admin` / `admin1234`
- operarios con DNI `11111111H` (Recepción), `22222222J` (Expediciones) y `33333333P` (externo), todos con PIN `123456`.

Sin `--demo` solo se cargan los puestos, los cursos y los itinerarios. Para crear la cuenta de administración:

```bash
.venv/bin/python manage.py createsuperuser
```

Tests:

```bash
.venv/bin/python manage.py test formacion
```

> ⚠️ **El contenido de los cursos es un borrador de ejemplo** (marcado como tal en cada tema). Hay que sustituirlo por el temario oficial antes de usarlo con empleados reales.

## Ver los avances en una dirección web (demo gratuita)

Para ver y probar el portal mientras se preparan los cursos se publica una demo gratuita en **PythonAnywhere**. La guía paso a paso está en [`docs/PYTHONANYWHERE.md`](docs/PYTHONANYWHERE.md): son unos 15 minutos y solo se hace una vez.

Para actualizarla después basta con este comando en su consola:

```bash
bash portalformacion/despliegue/pythonanywhere.sh
```

## Producción

Variables de entorno:

| Variable | Ejemplo |
|---|---|
| `DJANGO_SECRET_KEY` | cadena larga aleatoria |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | `formacion.aldelis.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://formacion.aldelis.com` |
| `DJANGO_DB_PATH` / `DJANGO_MEDIA_ROOT` | rutas persistentes para la base de datos y los temarios |
| `SESION_MINUTOS` | `30` |

Comandos:

```bash
python manage.py collectstatic --noinput
```

```bash
gunicorn config.wsgi
```

Pon un proxy HTTPS delante. SQLite es suficiente para cientos de usuarios; si crece, se cambia a PostgreSQL en `DATABASES`.

## Traspaso a Informática

La guía para conectar el portal con los servidores y bases de datos de la empresa está en [`docs/INFORMATICA.md`](docs/INFORMATICA.md).

## Integración con Microsoft 365 (opcional, siguiente fase)

- **Inicio de sesión con Microsoft (Entra ID)** para el personal de oficina que tiene cuenta corporativa. Convive con el acceso DNI + PIN de los operarios.
- **Temarios en SharePoint**: el campo «enlace de vídeo» de cada tema ya admite enlaces de SharePoint o Stream.
- **Avisos por Teams o correo** a los responsables cuando un empleado tenga cursos vencidos.

## Estructura

```
config/                 Configuración de Django
formacion/
  models.py             Departamentos, puestos, cursos, temas, exámenes, itinerarios, matrículas, intentos
  services.py           Asignación de itinerarios, progreso y corrección de exámenes
  auth.py               Acceso DNI + PIN con bloqueo por intentos
  altas.py              Alta individual o masiva de empleados
  admin.py              Gestión (incluye importación de preguntas desde CSV)
  contenido_inicial.py  Cursos, preguntas e itinerarios de partida
  templates/, static/   Interfaz
docs/                   Plantillas CSV para Excel
```
