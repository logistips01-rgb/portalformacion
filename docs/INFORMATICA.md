# Portal de Formación · Guía de traspaso para Informática

Este documento resume lo que hay que hacer para pasar el portal de prototipo a producción en la infraestructura de Aldelis.
El uso funcional está descrito en el [README](../README.md).

## Tecnología

| Pieza | Actual (prototipo) | Producción |
|---|---|---|
| Lenguaje / framework | Python 3.12+ · Django 5.2 LTS (soporte hasta abril de 2028) | igual |
| Base de datos | SQLite (archivo `db.sqlite3`) | PostgreSQL o SQL Server (ver abajo) |
| Servidor de aplicación | `manage.py runserver` | `gunicorn config.wsgi` (Linux) o `waitress` (Windows) |
| Estáticos | WhiteNoise (ya configurado) | igual, o servidos por el proxy |
| Archivos subidos (temarios PDF/vídeo) | carpeta `media/` | disco persistente o recurso de red (`DJANGO_MEDIA_ROOT`) |
| HTTPS | — | proxy inverso (IIS, Nginx o el balanceador corporativo) |

No usa servicios externos ni CDN: todo funciona dentro de la red de la empresa.

## Configuración por variables de entorno

Está en `config/settings.py` y se lee del entorno:

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | **obligatoria** en producción; cadena aleatoria larga |
| `DJANGO_DEBUG` | `0` en producción |
| `DJANGO_ALLOWED_HOSTS` | nombres del servidor, separados por comas |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://formacion.aldelis.com` |
| `DJANGO_DB_PATH` | ruta del SQLite (solo si se sigue usando SQLite) |
| `DJANGO_MEDIA_ROOT` | carpeta de temarios subidos |
| `SESION_MINUTOS` | caducidad de la sesión por inactividad (por defecto 30) |

## Conectar la base de datos de la empresa

Sustituir el bloque `DATABASES` de `config/settings.py`. Opciones:

**PostgreSQL**: añadir `psycopg[binary]` a `requirements.txt`.

```python
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["DB_NAME"], "USER": os.environ["DB_USER"], "PASSWORD": os.environ["DB_PASSWORD"],
    "HOST": os.environ["DB_HOST"], "PORT": os.environ.get("DB_PORT", "5432"),
}}
```

**SQL Server**: añadir `mssql-django` y tener instalado el *ODBC Driver 18 for SQL Server*.

```python
DATABASES = {"default": {
    "ENGINE": "mssql",
    "NAME": os.environ["DB_NAME"], "USER": os.environ["DB_USER"], "PASSWORD": os.environ["DB_PASSWORD"],
    "HOST": os.environ["DB_HOST"], "PORT": os.environ.get("DB_PORT", "1433"),
    "OPTIONS": {"driver": "ODBC Driver 18 for SQL Server", "extra_params": "TrustServerCertificate=yes"},
}}
```

Después crear las tablas:

```bash
python manage.py migrate
```

Cargar puestos, cursos e itinerarios de partida:

```bash
python manage.py cargar_datos_iniciales
```

Crear la cuenta de administración:

```bash
python manage.py createsuperuser
```

Para migrar lo que se haya trabajado en el prototipo (cursos, preguntas, usuarios), exportarlo desde la base SQLite:

```bash
python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission --exclude sessions -o datos.json
```

Y cargarlo con la nueva base ya configurada (copiar también la carpeta `media/`):

```bash
python manage.py loaddata datos.json
```

## Despliegue y operación

Pasos de cada despliegue:

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py collectstatic --noinput
```

```bash
gunicorn config.wsgi --bind 127.0.0.1:8000 --workers 3
```

Para operar el servicio:
- **Copias de seguridad**: la base de datos y la carpeta `DJANGO_MEDIA_ROOT`. Ahí están los temarios, los resultados de los exámenes y los certificados, que pueden ser evidencias para auditorías de calidad o PRL.
- **Comprobar la configuración** antes de cada despliegue:

  ```bash
  python manage.py check --deploy
  ```

- **Tests**:

  ```bash
  python manage.py test formacion
  ```

## Acceso y usuarios

- **Operarios y personal externo**: DNI + PIN de 6 cifras, sin email ni cuenta corporativa.
  - Lo gestiona `formacion/auth.py` (`PinBackend`).
  - Los PIN se guardan con hash, igual que las contraseñas de Django.
  - Tras 5 fallos la cuenta se bloquea 15 minutos.
- **RR. HH. y oficina**: usuario y contraseña de Django. Para ver el seguimiento y la gestión necesitan `is_staff`.
- **Inicio de sesión con Microsoft 365 (opcional)**: se puede añadir para quien tenga cuenta corporativa, por ejemplo con `django-allauth` (proveedor Microsoft) o `mozilla-django-oidc` contra Entra ID. Basta con añadir el backend a `AUTHENTICATION_BACKENDS`; el acceso DNI + PIN se mantiene.

## Integraciones posibles con sistemas de la empresa

| Integración | Dónde engancharla |
|---|---|
| Alta automática de empleados desde el sistema de RR. HH. / nóminas | `formacion/altas.py` → `dar_de_alta(...)`. Hoy se usa con un CSV exportado de Excel; se puede llamar desde un comando programado o un endpoint |
| Bajas | desactivar el usuario (`is_active = False`) conserva su histórico de formación |
| Informes en Power BI / Excel | tablas `formacion_matricula`, `formacion_intento` y `formacion_perfilempleado`, o la exportación CSV de `/seguimiento/` |
| Temarios en SharePoint | el campo «enlace de vídeo» de cada tema admite cualquier URL |
| Avisos de cursos vencidos (correo o Teams) | consulta `Matricula` con `fecha_completado` vacía y `fecha_limite` pasada; programar un comando diario |

## Modelo de datos (resumen)

```
Departamento 1─N Puesto
Curso 1─N Tema            Curso 1─1 Examen 1─N Pregunta 1─N Opcion
Itinerario N─M Curso (ItinerarioCurso: orden, plazo en días)
Itinerario → se asigna a: todo el personal interno / personal externo / departamentos / puestos
User 1─1 PerfilEmpleado (tipo, puesto, DNI, PIN, fecha de incorporación)
User 1─N Matricula (curso, fecha límite, fecha completado, nota)
User 1─N TemaLeido · User 1─N Intento 1─N RespuestaIntento
```

## Pendiente antes de producción

- [ ] Sustituir el contenido de ejemplo por el temario oficial (Formación / RR. HH.).
- [ ] Elegir la base de datos (PostgreSQL o SQL Server) y el servidor.
- [ ] Dominio interno o externo y certificado HTTPS. Si el personal externo hace la formación antes de llegar, tiene que ser accesible desde Internet.
- [ ] Copias de seguridad de la base de datos y de `media/`.
- [ ] Revisión de protección de datos (RGPD): se guardan nombre, DNI y resultados de formación.
- [ ] Opcional: inicio de sesión con Microsoft 365 para el personal de oficina.
