from flask import Flask, render_template, request
import openai
import os
import pytesseract
import re
from PIL import Image
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# API Key de OpenRouter
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_api_key:
    raise ValueError("❌ ERROR: No se encontró la clave API de OpenRouter. Verifica tu archivo .env.")

print(f"🔑 Clave API cargada correctamente: {openrouter_api_key[:10]}...")

# Configurar cliente OpenRouter
client = openai.OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)

# Palabras clave y patrones que validan un análisis de sensibilidad
KEYWORDS = [
    "objective value", "variable", "reduced cost", "slack", "surplus", "dual price",
    "maximize", "availability", "global optimal solution", "row", "sensitivity analysis",
    "optimización", "lindo", "solver", "programación lineal",
    "destino", "demanda", "oferta", "asignación", "costo"
]

NUMERIC_PATTERN = r"\d+\.\d+"  # Detecta números decimales (ejemplo: 1200.00)

def es_pregunta_valida(texto):
    """
    Verifica si el texto contiene términos clave o estructuras numéricas relevantes.
    """
    texto = texto.lower()
    palabras = set(texto.split())

    # Verifica si al menos dos términos clave están en el texto
    coincidencias = sum(1 for kw in KEYWORDS if kw in texto)

    # Detecta si hay al menos 5 números decimales (datos de sensibilidad o tablas de transporte)
    numeros_encontrados = re.findall(NUMERIC_PATTERN, texto)
    
    return coincidencias >= 2 or len(numeros_encontrados) >= 4

def extraer_texto_imagen(image_file):
    """
    Extrae texto de una imagen utilizando OCR.
    """
    try:
        image = Image.open(image_file)
        extracted_text = pytesseract.image_to_string(image)
        print(f"📸 Texto extraído:\n{extracted_text.strip()}")
        return extracted_text.strip()
    
    except Exception as e:
        return f"❌ Error procesando la imagen: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return render_template("chat.html")

    user_input = request.form.get("message", "").strip()
    image_file = request.files.get("image")

    extracted_text = ""

    # Si el usuario sube una imagen, extraemos el texto con OCR
    if image_file:
        extracted_text = extraer_texto_imagen(image_file)
        
        if not extracted_text:
            return render_template("chat.html", user_input="", bot_respuesta="❌ No se pudo extraer texto de la imagen.")

    # Unir texto de usuario y el extraído de la imagen
    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        return render_template("chat.html", user_input="", bot_respuesta="Por favor, ingrese un mensaje o suba una imagen válida.")

    # Verificar si la pregunta es válida
    if not es_pregunta_valida(full_prompt):
        return render_template("chat.html", user_input=full_prompt, bot_respuesta="⚠️ Solo puedo ayudarte con análisis de sensibilidad en Programación Lineal o transporte.")

    try:
        # Enviar la solicitud a OpenRouter
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=600,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en Programación Lineal y Análisis de Sensibilidad..."
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
