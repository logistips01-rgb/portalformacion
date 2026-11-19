#!/usr/bin/env bash
# Instalación / actualización del Portal de Formación en PythonAnywhere.
# Uso (desde una consola Bash de PythonAnywhere, dentro de ~/portalformacion):
#     bash despliegue/pythonanywhere.sh
# Se puede ejecutar tantas veces como se quiera: la primera vez instala y
# las siguientes actualiza (trae cambios de GitHub, migra y recarga la web).
set -e
cd "$(dirname "$0")/.."
PROYECTO="$(pwd)"
DOMINIO="${USER}.pythonanywhere.com"
VENV="$HOME/.virtualenvs/portalformacion"
WSGI="/var/www/${USER}_pythonanywhere_com_wsgi.py"

echo "== Trayendo la última versión de GitHub"
git pull --ff-only || echo "(sin cambios o sin conexión; sigo con la versión actual)"

if [ ! -d "$VENV" ]; then
  PY=""
  for v in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$v" >/dev/null; then PY="$v"; break; fi
  done
  [ -z "$PY" ] && { echo "No encuentro Python 3.10 o superior"; exit 1; }
  echo "== Creando entorno con $PY"
  "$PY" -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements.txt

PRIMERA_VEZ=0
if [ ! -f .env ]; then
  PRIMERA_VEZ=1
  echo "== Creando configuración (.env)"
  CLAVE=$("$VENV/bin/python" -c "import secrets; print(secrets.token_urlsafe(50))")
  ADMIN_PASS=$("$VENV/bin/python" -c "import secrets; print(secrets.token_urlsafe(10))")
  cat > .env <<CONF
DJANGO_SECRET_KEY=$CLAVE
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=$DOMINIO
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMINIO
DJANGO_DETRAS_DE_PROXY=1
DEMO_ADMIN_PASSWORD=$ADMIN_PASS
CONF
  chmod 600 .env
fi

echo "== Preparando base de datos y archivos"
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v0
if [ "$PRIMERA_VEZ" = "1" ]; then
  "$VENV/bin/python" manage.py cargar_datos_iniciales --demo
fi

if [ -f "$WSGI" ]; then
  cat > "$WSGI" <<PYW
import os, sys
ruta = "$PROYECTO"
if ruta not in sys.path:
    sys.path.insert(0, ruta)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
PYW
  touch "$WSGI"   # recarga la web
  echo "== Web recargada: https://$DOMINIO"
else
  echo
  echo "Falta crear la web en la pestaña Web (paso 3 de la guía) y volver a ejecutar este script."
fi

echo
echo "Datos para la pestaña Web de PythonAnywhere (solo la primera vez):"
echo "  Python del entorno: $("$VENV/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')  (la web debe usar la misma versión)"
echo "  Virtualenv:        $VENV"
echo "  Static files:      URL /static/   ->  Directory $PROYECTO/staticfiles"
if [ "$PRIMERA_VEZ" = "1" ]; then
  echo
  echo "Acceso de administración:  usuario admin  /  contraseña $(grep DEMO_ADMIN_PASSWORD .env | cut -d= -f2)"
  echo "(guárdala; también está en el archivo .env)"
fi
