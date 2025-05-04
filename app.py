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

def pide_caso_estudio_real(texto):
    texto = texto.lower()
    return any(kw in texto for kw in ["dame un caso de estudio", "caso de empresa real", "quiero un caso real", "proporcióname un caso de estudio"])

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

    prompt_comparacion = f"""
    Actúa como un auditor experto en la norma ISO 9001.

    A continuación se muestran dos análisis sobre un mismo caso de auditoría:

    📘 Análisis del chatbot:
    {chatbot_response}

    🧑‍💼 Análisis del usuario:
    {user_analysis}

    Compara ambos. Evalúa si están alineados, si uno es más detallado o completo, si hay contradicciones, y redacta un párrafo resumen con tus observaciones.
    """

    prompt_porcentaje = f"""
    Analiza el siguiente análisis de auditoría de un usuario comparado con la respuesta correcta del chatbot. En base a su alineación, detalle y precisión con respecto a la norma ISO 9001, proporciona un porcentaje estimado de efectividad del 0 al 100. Proporciona únicamente un número entero del 0 al 100 seguido del símbolo de porcentaje (%), sin ningún texto adicional ni explicación.

    📘 Respuesta del chatbot:
    {chatbot_response}

    🧑‍💼 Análisis del usuario:
    {user_analysis}
    """

    prompt_riesgo = f"""
    Analiza el siguiente análisis de auditoría del usuario comparado con la respuesta del chatbot ISO 9001. Con base en la gravedad de los errores o desviaciones, estima un nivel de impacto (1 a 5) y probabilidad (1 a 5). Devuelve únicamente dos valores enteros separados por coma: impacto,probabilidad

    📘 Respuesta del chatbot:
    {chatbot_response}

    🧑‍💼 Análisis del usuario:
    {user_analysis}
    """

    try:
        comparacion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=300,
            messages=[
                {"role": "system", "content": "Eres un auditor experto en ISO 9001."},
                {"role": "user", "content": prompt_comparacion}
            ]
        )
        comparacion_ia = comparacion.choices[0].message.content if comparacion.choices else "No se pudo generar una comparación."

        porcentaje = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0,
            max_tokens=10,
            messages=[
                {"role": "system", "content": "Eres un evaluador que responde solo con un número del 0 al 100."},
                {"role": "user", "content": prompt_porcentaje}
            ]
        )
        efectividad = porcentaje.choices[0].message.content.strip()

        # Evaluación de riesgo IA
        riesgo_eval = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0,
            max_tokens=10,
            messages=[
                {"role": "system", "content": "Eres un experto en evaluación de riesgos ISO 9001. Solo devuelve dos números enteros del 1 al 5 separados por coma: impacto,probabilidad."},
                {"role": "user", "content": prompt_riesgo}
            ]
        )

        valores = riesgo_eval.choices[0].message.content.strip().split(',')
        impacto = int(valores[0])
        probabilidad = int(valores[1])
        riesgo = impacto * probabilidad

        if riesgo >= 12:
            nivel = "Alto"
        elif riesgo >= 6:
            nivel = "Medio"
        else:
            nivel = "Bajo"

    except Exception as e:
        print(f"❌ Error en comparación o evaluación: {str(e)}")
        comparacion_ia = "❌ No se pudo generar la comparación."
        efectividad = "❌ No disponible"
        impacto = 0
        probabilidad = 0
        riesgo = 0
        nivel = "No calculado"

    return render_template("compare.html",
                           chatbot_response=chatbot_response,
                           user_analysis=user_analysis,
                           diff_html=diff_html,
                           comparacion_ia=comparacion_ia,
                           efectividad=efectividad,
                           impacto=impacto,
                           probabilidad=probabilidad,
                           riesgo=riesgo,
                           nivel=nivel)


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

    # Si se pide un caso de estudio real:
    if pide_caso_estudio_real(full_prompt):
        caso_prompt = """
        Proporcióname un caso de estudio real y diferente de una empresa conocida que haya implementado la norma ISO 9001.
        Cada vez que se te solicite, elige una empresa distinta que opere en un país y sector diferentes. Describe el nombre de la empresa, el sector en el que opera, los problemas que enfrentaba antes de certificarse, los cambios que aplicó para cumplir con la norma y los beneficios obtenidos luego de su certificación.
        Evita repetir empresas o información ya mencionada anteriormente.
        """

        try:
            respuesta = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=600,
                messages=[
                    {"role": "system", "content": "Eres un experto en certificaciones ISO 9001."},
                    {"role": "user", "content": caso_prompt}
                ]
            )
            caso_generado = respuesta.choices[0].message.content.strip()
            session["historial"].append({"user": full_prompt, "bot": caso_generado})
            session.modified = True
            return render_template("chat.html", historial=session["historial"], bot_respuesta=caso_generado)

        except Exception as e:
            print(f"❌ Error generando caso de estudio: {str(e)}")
            return render_template("chat.html", historial=session["historial"], bot_respuesta="❌ No se pudo generar el caso de estudio.")

    mensajes_previos = [{
        "role": "system",
        "content": (
            "Eres un experto en auditorías de la norma ISO 9001. Analiza el caso de estudio proporcionado "
            "y responde únicamente con base en esta norma. Tu respuesta debe incluir los hallazgos clave de forma estructurada "
            "y enumerada (por ejemplo: 1. ..., 2. ..., etc.), usando saltos de línea para separar claramente cada punto. "
            "No escribas todo en un solo párrafo."
        )
    }]

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

@app.route("/evaluar_riesgo", methods=["POST"])
def evaluar_riesgo():
    try:
        impacto = int(request.form.get("impacto", 0))
        probabilidad = int(request.form.get("probabilidad", 0))
        riesgo = impacto * probabilidad

        if riesgo >= 12:
            nivel = "Alto"
        elif riesgo >= 6:
            nivel = "Medio"
        else:
            nivel = "Bajo"

        return render_template("riesgo_resultado.html",
                               impacto=impacto,
                               probabilidad=probabilidad,
                               riesgo=riesgo,
                               nivel=nivel)
    except Exception as e:
        print(f"❌ Error al calcular el riesgo: {str(e)}")
        return "Error al evaluar riesgo"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
