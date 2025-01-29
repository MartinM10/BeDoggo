#!/bin/bash

# Ruta del archivo .env
ENV_FILE="/app/.env"

# Verifica si el archivo .env ya existe
if [ ! -f "$ENV_FILE" ]; then
    echo "Generando archivo .env..."
    cat <<EOT > $ENV_FILE
DEBUG=False
SECRET_KEY=$(openssl rand -base64 32)
ALLOWED_HOSTS=127.0.0.1,localhost
POSTGRES_DB=bedoggodb
POSTGRES_USER=doggo
POSTGRES_PASSWORD=$(openssl rand -base64 12)
POSTGRES_HOST=db
POSTGRES_PORT=5432
EOT
    echo "Archivo .env generado correctamente."
else
    echo "El archivo .env ya existe. No se generará uno nuevo."
fi
