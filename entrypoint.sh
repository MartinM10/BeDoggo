#!/bin/bash

# Salir si algo falla
set -e

# Esperar a que la base de datos esté disponible
/app/wait-for-db.sh

# Aplicar las migraciones pendientes
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Recopilar los archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar el servidor Gunicorn
echo "Iniciando servidor Django..."
exec gunicorn BeDoggo.wsgi:application --bind 0.0.0.0:8000
