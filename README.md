**Chatbot de Auditoría ISO 9001

Este proyecto es un chatbot especializado en realizar auditorías de calidad basadas en la norma ISO 9001:2015. El sistema analiza casos de estudio enviados mediante texto o imagen y proporciona una respuesta automática siguiendo los requisitos de la norma.

El proyecto está dockerizado y se puede desplegar fácilmente usando Docker o Docker Compose.

Tecnologías Utilizadas

Python 3.10

Flask

OpenAI / OpenRouter API

EasyOCR (extracción de texto de imágenes)

Docker

Docker Compose

Estructura del Proyecto

Chatbot_Legislacion/
├── static/
│   ├── chatbot.jpeg
│   ├── style.css
│   └── scripts.js
├── templates/
│   ├── chat.html
│   └── compare.html
├── app.py
├── dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env

Variables de Entorno

El archivo .env debe contener:

OPENROUTER_API_KEY="<tu_api_key_aqui>"
FLASK_ENV=development
FLASK_APP=app.py

Instalación Manual

Clonar el repositorio:

git clone: https://github.com/JordinPinzon/Chatbot-Legislacion.git
cd Chatbot_Legislacion

Crear entorno virtual e instalar dependencias:

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

Ejecutar localmente:

flask run --host=0.0.0.0 --port=5000

Despliegue con Docker

Construir y correr la imagen:

docker build -t chatbot-legislacion .
docker run -p 5000:5000 --env-file .env chatbot-legislacion

Despliegue con Docker Compose

Ejecutar:

docker compose --env-file .env up --build

Características Principales

Análisis de texto escrito o extraído de imágenes.

Comparación de respuestas con un análisis propio del usuario.

Resúmenes automáticos mediante IA.

Prediseño web responsivo y moderno.

Totalmente portable mediante contenedores Docker.

Licencia

Este proyecto se encuentra bajo la licencia MIT.

Autor

Desarrollado por: [Tu Nombre]GitHub: [Tu Perfil GitHub]

✨ ¡Gracias por utilizar el Chatbot de Auditoría ISO 9001! ✨
