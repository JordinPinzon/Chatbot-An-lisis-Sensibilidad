from flask import Flask, render_template, request, redirect, url_for
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

# 🔹 Ruta principal redirige a /chat
@app.route("/")
def index():
    return redirect(url_for("chat"))  # Redirige automáticamente al chat

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return render_template("chat.html")

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
        return render_template("chat.html", user_input="", bot_respuesta="Por favor, ingrese un mensaje o suba una imagen válida.")

    # Verificar si la pregunta es válida
    if not es_pregunta_valida(full_prompt):
        return render_template("chat.html", user_input=full_prompt, bot_respuesta="⚠️ Solo puedo ayudarte con análisis de sensibilidad en Programación Lineal.")

    try:
        # Enviar la solicitud a OpenRouter con un enfoque en análisis de sensibilidad
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en Programación Lineal y Análisis de Sensibilidad. "
                        "Cuando recibas una imagen con resultados óptimos, valores de variables, "
                        "holguras o costos reducidos, tu tarea es interpretar los datos y proporcionar "
                        "un análisis detallado de cómo afectan a la solución óptima. "
                        "Si algún coeficiente cambia, analiza cómo impacta en la solución. "
                        "Indica qué pasaría si las restricciones aumentan o disminuyen, "
                        "y cómo afectarían al resultado final del modelo.\n\n"
                    )
                },
                {"role": "user", "content": full_prompt}
            ]
        )

        bot_respuesta = respuesta.choices[0].message.content

        return render_template("chat.html", user_input=full_prompt, bot_respuesta=bot_respuesta)

    except Exception as e:
        return render_template("chat.html", user_input=full_prompt, bot_respuesta=f"❌ Error en la solicitud: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True)
