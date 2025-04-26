from flask import Flask, render_template, request, redirect, url_for, session
import openai
import os
import re
import numpy as np
from PIL import Image
from dotenv import load_dotenv
import easyocr
import difflib

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

# Palabras clave relacionadas con ISO 9001
ISO_9001_KEYWORDS = [
    "auditoría", "ISO 9001", "calidad", "requisitos", "sistema de gestión",
    "mejora continua", "documentación", "procesos", "indicadores", "no conformidad"
]

def es_pregunta_iso9001(texto):
    texto = texto.lower()
    return any(kw in texto for kw in ISO_9001_KEYWORDS)

def extraer_texto_desde_imagen(image_file):
    try:
        image = Image.open(image_file).convert("RGB")
        image_array = np.array(image)
        reader = easyocr.Reader(['es'], gpu=False)
        resultados = reader.readtext(image_array, detail=0)
        extracted_text = "\n".join(resultados).strip()

        if not extracted_text:
            return None

        print(f"📸 Texto extraído con EasyOCR:\n{extracted_text}")
        return extracted_text

    except Exception as e:
        print(f"❌ Error con EasyOCR: {str(e)}")
        return None

@app.route("/")
def index():
    return redirect(url_for("chat"))

@app.route("/compare", methods=["POST"])
def compare():
    chatbot_response = request.form.get("chatbot_response", "")
    user_analysis = request.form.get("user_analysis", "")

    differ = difflib.HtmlDiff()
    diff_html = differ.make_table(
        chatbot_response.splitlines(),
        user_analysis.splitlines(),
        fromdesc='Chatbot',
        todesc='Tu Análisis',
        context=True,
        numlines=2
    )

    prompt = f"""
    Actúa como un auditor experto en la norma ISO 9001.

    A continuación se muestran dos análisis sobre un mismo caso de auditoría:

    📘 Análisis del chatbot:
    {chatbot_response}

    🧑‍💼 Análisis del usuario:
    {user_analysis}

    Compara ambos. Evalúa si están alineados, si uno es más detallado o completo, si hay contradicciones, y redacta un párrafo resumen con tus observaciones.
    """

    try:
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=300,
            messages=[
                {"role": "system", "content": "Eres un auditor experto en ISO 9001."},
                {"role": "user", "content": prompt}
            ]
        )

        comparacion_ia = respuesta.choices[0].message.content if respuesta.choices else "No se pudo generar una comparación."

    except Exception as e:
        print(f"❌ Error al generar la comparación con IA: {str(e)}")
        comparacion_ia = "⚠️ No se pudo generar la comparación inteligente en este momento."

    return render_template("compare.html",
                           chatbot_response=chatbot_response,
                           user_analysis=user_analysis,
                           diff_html=diff_html,
                           comparacion_ia=comparacion_ia)

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

    #if not es_pregunta_iso9001(full_prompt):
     #   return render_template("chat.html", historial=session["historial"], bot_respuesta="Por favor, asegúrese de que el caso de estudio esté relacionado con auditorías de la norma ISO 9001.")

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

        return render_template("chat.html", historial=session["historial"], bot_respuesta=bot_respuesta)

    except openai.OpenAIError as e:
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return render_template("chat.html", historial=session["historial"], bot_respuesta="❌ Error al comunicarse con el modelo. Verifique su conexión o intente más tarde.")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
