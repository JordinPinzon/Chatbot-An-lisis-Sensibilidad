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
app.secret_key = "clave_secreta_segura"  # Necesario para manejar sesiones

# Expresiones regulares para capturar números en la tabla
NUMERIC_PATTERN = r"\d+\.\d+|\d+"

# Palabras clave relacionadas exclusivamente con Programación Lineal
KEYWORDS = [
    "solución óptima", "valor óptimo", "variable", "reduced cost", "slack",
    "surplus", "dual price", "maximizar", "restricción", "holgura", "costo",
    "artificial", "base", "coeficiente", "análisis de sensibilidad"
]

def es_pregunta_valida(texto):
    """
    Verifica si el texto contiene términos clave o estructuras numéricas relevantes.
    """
    texto = texto.lower()
    coincidencias = sum(1 for kw in KEYWORDS if kw in texto)
    numeros_encontrados = re.findall(NUMERIC_PATTERN, texto)
    return coincidencias >= 2 or len(numeros_encontrados) >= 3

def extraer_texto_desde_imagen(image_file):
    """
    Extrae texto de una imagen utilizando OCR, enfocándose en variables y resultados óptimos.
    """
    try:
        # Abrir la imagen y convertirla en un array numpy
        image = Image.open(image_file)
        image = np.array(image)

        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Aplicar un umbral para mejorar la detección de caracteres
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # Extraer texto con OCR
        extracted_text = pytesseract.image_to_string(thresh)
        
        # Filtrar solo valores numéricos y palabras clave importantes
        texto_filtrado = []
        for line in extracted_text.split("\n"):
            if any(kw in line.lower() for kw in KEYWORDS) or re.search(NUMERIC_PATTERN, line):
                texto_filtrado.append(line.strip())

        texto_final = "\n".join(texto_filtrado)

        if not texto_final.strip():
            return None  # No se detectó información útil

        print(f"📸 Texto extraído:\n{texto_final}")
        return texto_final

    except Exception as e:
        print(f"❌ Error procesando la imagen: {str(e)}")
        return None

@app.route("/")
def index():
    return redirect(url_for("chat"))  # Redirige automáticamente al chat

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "historial" not in session:
        session["historial"] = []  # Iniciar historial si no existe

    if request.method == "GET":
        return render_template("chat.html", historial=session["historial"])

    user_input = request.form.get("message", "").strip()
    image_file = request.files.get("image")

    extracted_text = ""

    # Si el usuario sube una imagen, extraemos los datos estructurados
    if image_file:
        texto_extraido = extraer_texto_desde_imagen(image_file)

        if texto_extraido is None:
            extracted_text = "⚠️ No se pudo extraer texto válido de la imagen."
        else:
            extracted_text = f"Datos extraídos:\n{texto_extraido}"

    # Unir texto de usuario y el extraído de la imagen
    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        return render_template("chat.html", historial=session["historial"], bot_respuesta="Por favor, ingrese un mensaje o suba una imagen válida.")

    # Agregar contexto previo para mantener la conversación
    mensajes_previos = [{"role": "system", "content": "Eres un experto en Programación Lineal y Análisis de Sensibilidad."}]
    
    for msg in session["historial"]:
        mensajes_previos.append({"role": "user", "content": msg["user"]})
        mensajes_previos.append({"role": "assistant", "content": msg["bot"]})

    mensajes_previos.append({"role": "user", "content": full_prompt})

    try:
        # Enviar la solicitud a OpenRouter con el historial de conversación
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=800,
            messages=mensajes_previos
        )

        # Verificar si la respuesta se generó correctamente
        if not respuesta or not respuesta.choices or not respuesta.choices[0].message:
            bot_respuesta = "⚠️ No se recibió respuesta del modelo. Intente de nuevo."
            print("⚠️ Error: No se recibió respuesta del modelo.")
        else:
            bot_respuesta = respuesta.choices[0].message.content
            print(f"🤖 Respuesta generada:\n{bot_respuesta}")

        # Guardar la conversación en el historial
        session["historial"].append({"user": full_prompt, "bot": bot_respuesta})
        session.modified = True  # Asegurar que Flask guarde los cambios

        return render_template("chat.html", historial=session["historial"])

    except Exception as e:
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return render_template("chat.html", historial=session["historial"], bot_respuesta=f"❌ Error en la solicitud: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
