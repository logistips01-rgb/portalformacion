"""Configuración del Portal de Formación Aldelis.

Los valores sensibles se leen de variables de entorno para poder desplegar
el mismo código en desarrollo y producción.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Si existe un archivo .env junto a manage.py (no se sube a GitHub), se cargan
# sus variables. Así se configura el servidor sin tocar el código.
_env = BASE_DIR / ".env"
if _env.exists():
    for _linea in _env.read_text(encoding="utf-8").splitlines():
        _linea = _linea.strip()
        if _linea and not _linea.startswith("#") and "=" in _linea:
            _clave, _valor = _linea.split("=", 1)
            os.environ.setdefault(_clave.strip(), _valor.strip())

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "solo-para-desarrollo-cambiar-en-produccion",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
# Detrás de un proxy HTTPS (PythonAnywhere, IIS, Nginx…)
if os.environ.get("DJANGO_DETRAS_DE_PROXY") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "formacion",  # primero, para que sus plantillas personalicen la administración
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # En producción, archivos comprimidos y con huella (requiere collectstatic).
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Temarios (PDF, vídeos, presentaciones) subidos desde la administración
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "formacion:inicio"
LOGOUT_REDIRECT_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Acceso: usuario+contraseña (administración/RR. HH.) o DNI+PIN (operarios).
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "formacion.auth.PinBackend",
]

# Pensado para tablets compartidas en planta: la sesión caduca tras 30 min sin actividad
# y al cerrar el navegador.
SESSION_COOKIE_AGE = int(os.environ.get("SESION_MINUTOS", "30")) * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
