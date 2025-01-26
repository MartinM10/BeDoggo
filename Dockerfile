# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala las dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos de requirements.txt e instala las dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia el proyecto al contenedor
COPY . /app/

# Agrega permisos de ejecución al script de entrada
RUN chmod +x /app/entrypoint.sh

# Expone el puerto 8000
EXPOSE 8000

# Ejecuta el script de entrada por defecto
ENTRYPOINT ["/app/entrypoint.sh"]
