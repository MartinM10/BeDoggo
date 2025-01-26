#!/bin/bash

# Salir si algo falla
set -e

# Aplicar las migraciones pendientes
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Recopilar los archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar el servidor
echo "Iniciando servidor Django..."
gunicorn proyecto.wsgi:application --bind 0.0.0.0:8000

exec "$@"
