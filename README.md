# 🐾 BeDoggo

BeDoggo es una aplicación diseñada para ayudar a los usuarios a gestionar la información sobre mascotas perdidas y
encontradas. Permite a los usuarios registrar sus mascotas, ubicaciones y accesos, facilitando la búsqueda y
recuperación de mascotas.

## 🚀 Comenzando

Estas instrucciones te ayudarán a configurar y ejecutar el proyecto en tu máquina local.

### 📋 Requisitos

- Python 3.x
- Django 5.x
- PostgreSQL (opcional, si usas una base de datos diferente, ajusta la configuración)
- Django REST Framework
- Django GIS (para el manejo de datos geoespaciales)

### 🔧 Instalación

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/MartinM10/BeDoggo.git
   cd BeDoggo
   ```

2. **Crea un entorno virtual:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configura la base de datos:**

   Asegúrate de que tu base de datos esté configurada en `settings.py`. Si usas PostgreSQL, asegúrate de tener el
   driver `psycopg2` instalado.

5. **Realiza las migraciones:**

   ```bash
   python manage.py migrate
   ```

### 🌱 Cargar Datos Iniciales

Para cargar datos iniciales en la base de datos, utiliza el siguiente comando:

   ```bash
    python manage.py load_data
   ```

Este comando ejecutará el script ubicado en `beDoggo/management/commands/load_data.py`, que creará usuarios, mascotas y
ubicaciones de ejemplo en la base de datos.

### 🏃‍♂️ Ejecutar el Servidor

Para iniciar el servidor de desarrollo, ejecuta:

   ```bash
    python manage.py runserver
   ```

Luego, abre tu navegador y visita `http://127.0.0.1:8000/` para ver la aplicación en acción.

## 📚 API

La aplicación incluye una API RESTful que permite realizar operaciones CRUD sobre los modelos de mascotas, ubicaciones y
accesos. Puedes probar la API utilizando herramientas como Postman o cURL.

### Ejemplo de Endpoints

- **Obtener todas las mascotas:** `GET /api/pets/`
- **Crear una nueva mascota:** `POST /api/pets/`
- **Actualizar una mascota:** `PUT /api/pets/{id}/`
- **Eliminar una mascota:** `DELETE /api/pets/{id}/`

## 🛠️ Contribuciones

Las contribuciones son bienvenidas. Si deseas contribuir, por favor sigue estos pasos:

1. Haz un fork del proyecto.
2. Crea una nueva rama (`git checkout -b feature/nueva-caracteristica`).
3. Realiza tus cambios y haz commit (`git commit -m 'Añadir nueva característica'`).
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`).
5. Abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

Si tienes alguna pregunta o sugerencia, no dudes en contactarme:

- **Email:** martin.salvachua1@gmail.com
- **GitHub:** [@MartinM10](https://github.com/MartinM10)

---

¡Gracias por usar BeDoggo! 🐶