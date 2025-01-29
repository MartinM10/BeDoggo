# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala las dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev gcc gdal-bin libgdal-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos necesarios para el contenedor
COPY requirements.txt /app/
COPY generate_env.sh /app/
COPY wait-for-db.sh /app/
RUN chmod +x /app/generate_env.sh /app/wait-for-db.sh

# Ejecuta el script para generar el archivo .env durante la construcción
RUN /app/generate_env.sh

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto al contenedor
COPY . /app/

# Agrega permisos de ejecución al script de entrada
RUN chmod +x /app/entrypoint.sh

# Expone el puerto 8000 para el servidor
EXPOSE 8000

# Ejecuta el script de entrada por defecto
ENTRYPOINT ["/app/entrypoint.sh"]
