#!/usr/bin/env bash
# Script de construcción para Render.com (versión de demostración).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py cargar_datos_iniciales --demo
