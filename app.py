from flask import Flask, render_template, request
import openai
import os
import pytesseract
import re
from PIL import Image
from dotenv import load_dotenv

# Configurar manualmente la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Archivos de programa\Tesseract-OCR\tesseract.exe"

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
    
    # Consideramos válida la entrada si hay términos clave y suficientes números
    if coincidencias >= 2 or len(numeros_encontrados) >= 4:
        return True
    return False

def extraer_texto_imagen(image_file):
    """
    Extrae texto de una imagen utilizando OCR y mejora la estructura si es una tabla.
    """
    try:
        image = Image.open(image_file)
        
        # Usamos `image_to_data` para estructurar mejor la extracción de tablas
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Reconstruimos el texto de manera ordenada
        extracted_text = []
        for i in range(len(ocr_data["text"])):
            if ocr_data["text"][i].strip():
                extracted_text.append(ocr_data["text"][i])
        
        texto_final = " ".join(extracted_text)
        print(f"📸 Texto extraído de la imagen:\n{texto_final}")
        
        return texto_final if extracted_text else ""
    
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
            mensaje_error = "❌ No se pudo extraer texto de la imagen. Intenta con una imagen más clara."
            return render_template("chat.html", user_input="", bot_respuesta=mensaje_error)

    # Unir texto de usuario y el extraído de la imagen
    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        mensaje_error = "Por favor, ingrese un mensaje o suba una imagen con resultados válidos."
        return render_template("chat.html", user_input="", bot_respuesta=mensaje_error)

    # Verificar si la pregunta es válida
    if not es_pregunta_valida(full_prompt):
        print(f"⚠️ Pregunta rechazada: {full_prompt}")
        mensaje_error = "Lo siento, solo puedo ayudarte con el análisis de sensibilidad en Programación Lineal o análisis de transporte. Asegúrate de que tu consulta esté relacionada."
        return render_template("chat.html", user_input=full_prompt, bot_respuesta=mensaje_error)

    try:
        # Enviar la solicitud a OpenRouter con contexto mejorado
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=600,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en Programación Lineal y Análisis de Sensibilidad. "
                        "El usuario te proporcionará resultados de un problema de optimización lineal o de transporte, "
                        "y tu tarea es analizar la sensibilidad de los coeficientes, variables y restricciones. "
                        "Si la información contiene valores como 'Objective Value', 'Reduced Cost', 'Dual Price', "
                        "o 'Destino', 'Oferta', 'Demanda', 'Costo', debes interpretarlos y proporcionar un análisis detallado de cómo afectan al modelo."
                    )
                },
                {"role": "user", "content": full_prompt}
            ]
        )

        # Obtener la respuesta del bot
        bot_respuesta = respuesta.choices[0].message.content

        return render_template(
            "chat.html",
            user_input=full_prompt,
            bot_respuesta=bot_respuesta
        )

    except Exception as e:
        mensaje_error = f"❌ Error al procesar la solicitud: {str(e)}"
        return render_template("chat.html", user_input=full_prompt, bot_respuesta=mensaje_error)

if __name__ == "__main__":
    app.run(debug=True)
