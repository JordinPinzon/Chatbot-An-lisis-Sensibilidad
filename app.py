from flask import Flask, render_template, request, redirect, url_for, session
import openai
import os
import pytesseract
import re
import numpy as np
from PIL import Image
from dotenv import load_dotenv
import cv2

# Cargar variables de entorno
load_dotenv()

# API Key de OpenRouter
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_api_key:
    raise ValueError("❌ ERROR: No se encontró la clave API de OpenRouter. Verifica tu archivo .env.")

# Configurar cliente OpenRouter
client = openai.OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave_secreta_segura")  # Seguridad mejorada

# Expresiones regulares para capturar números en la tabla
NUMERIC_PATTERN = r"\d+\.\d+|\d+"

# Palabras clave relacionadas exclusivamente con Programación Lineal
ISO_9001_KEYWORDS = [
    "auditoría", "ISO 9001", "calidad", "requisitos", "sistema de gestión",
    "mejora continua", "documentación", "procesos", "indicadores", "no conformidad"
]

def es_pregunta_iso9001(texto):
    texto = texto.lower()
    return any(kw in texto for kw in ISO_9001_KEYWORDS)

def extraer_texto_desde_imagen(image_file):
    try:
        image = Image.open(image_file)
        image = np.array(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        extracted_text = pytesseract.image_to_string(thresh)
        extracted_text = re.sub(r"[^\w\s\.\,\-\:\;]", "", extracted_text)  # Limpiar caracteres raros

        texto_filtrado = []
        for line in extracted_text.split("\n"):
            if any(kw in line.lower() for kw in ISO_9001_KEYWORDS) or re.search(NUMERIC_PATTERN, line):
                texto_filtrado.append(line.strip())

        texto_final = "\n".join(texto_filtrado)

        if not texto_final.strip():
            return None

        print(f"📸 Texto extraído:\n{texto_final}")
        return texto_final

    except Exception as e:
        print(f"❌ Error procesando la imagen: {str(e)}")
        return None

@app.route("/")
def index():
    return redirect(url_for("chat"))

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "historial" not in session:
        session["historial"] = []

    if request.method == "GET":
        return render_template("chat.html", historial=session["historial"])

    user_input = request.form.get("message", "").strip()
    image_file = request.files.get("image")
    extracted_text = ""

    if image_file:
        texto_extraido = extraer_texto_desde_imagen(image_file)
        if texto_extraido is None:
            extracted_text = "⚠️ No se pudo extraer texto válido de la imagen."
        else:
            extracted_text = f"Datos extraídos:\n{texto_extraido}"

    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        return render_template("chat.html", historial=session["historial"], bot_respuesta="Por favor, ingrese un caso de estudio o suba una imagen válida.")

    if not es_pregunta_iso9001(user_input):
       return render_template("chat.html", historial=session["historial"], bot_respuesta="Por favor, asegúrese de que el caso de estudio esté relacionado con auditorías de la norma ISO 9001.")

    mensajes_previos = [{"role": "system", "content": "Eres un experto en auditorías de la norma ISO 9001. Analiza el caso de estudio proporcionado y responde únicamente con base en esta norma, proporcionando información clara y precisa."}]
    
    for msg in session["historial"]:
        mensajes_previos.append({"role": "user", "content": msg["user"]})
        mensajes_previos.append({"role": "assistant", "content": msg["bot"]})

    mensajes_previos.append({"role": "user", "content": full_prompt})

    try:
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=800,
            messages=mensajes_previos
        )

        if not respuesta or not respuesta.choices or not respuesta.choices[0].message:
            bot_respuesta = "⚠️ No se recibió respuesta del modelo. Intente de nuevo."
            print("⚠️ Error: No se recibió respuesta del modelo.")
        else:
            bot_respuesta = respuesta.choices[0].message.content
            print(f"🤖 Respuesta generada:\n{bot_respuesta}")

        session["historial"].append({"user": full_prompt, "bot": bot_respuesta})
        session.modified = True

        return render_template("chat.html", historial=session["historial"])

    except openai.OpenAIError as e:
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return render_template("chat.html", historial=session["historial"], bot_respuesta="❌ Error al comunicarse con el modelo. Verifique su conexión o intente más tarde.")

if __name__ == "__main__":
    app.run(debug=True)