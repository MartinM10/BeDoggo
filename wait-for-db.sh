#!/bin/bash

# Salir si algo falla
set -e

# Esperar a que la base de datos esté disponible
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  echo "Esperando a que la base de datos esté disponible..."
  sleep 2
done

echo "¡Base de datos disponible!"
exec "$@"
