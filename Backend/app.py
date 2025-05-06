from flask import Flask, request, jsonify, redirect, url_for, session
import openai
import os
import re
import numpy as np
import io
from PIL import Image
from fpdf import FPDF
from flask import send_file
from unidecode import unidecode
from dotenv import load_dotenv
import easyocr
import difflib
from flask_cors import CORS

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("❌ ERROR: No se encontró la clave API de OpenRouter. Verifica tu archivo .env.")

client = openai.OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave_secreta_segura")

ISO_9001_KEYWORDS = [
    "auditoría", "ISO 9001", "calidad", "requisitos", "sistema de gestión",
    "mejora continua", "documentación", "procesos", "indicadores", "no conformidad"
]

def es_pregunta_iso9001(texto):
    texto = texto.lower()
    return any(kw in texto for kw in ISO_9001_KEYWORDS)

def limpiar_texto(texto):
    if not texto:
        return "No disponible"
    texto = re.sub(r'[^\x00-\x7F]+', '', texto)
    texto = unidecode(texto.strip())
    # Limita longitud máxima por campo (por si acaso)
    return texto[:3000]

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
        return extracted_text if extracted_text else None
    except Exception as e:
        print(f"❌ Error con EasyOCR: {str(e)}")
        return None

@app.route("/")
def index():
    return jsonify({"message": "API para Chatbot ISO 9001 funcionando correctamente."})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    image_data = data.get("image_data")  # Base64 si se usa
    extracted_text = ""

    if image_data:
        # Proceso para decodificar si se maneja imagen base64 desde React (opcional)
        pass

    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        return jsonify({"error": "Por favor, ingrese un caso de estudio o suba una imagen válida."}), 400

    if pide_caso_estudio_real(full_prompt):
        caso_prompt = """
        Proporcióname un caso de estudio real y diferente de una empresa conocida que haya implementado la norma ISO 9001.
        Cada vez que se te solicite, elige una empresa distinta que opere en un país y sector diferentes. Describe el nombre de la empresa, el sector en el que opera, los problemas que enfrentaba antes de certificarse, los cambios que aplicó para cumplir con la norma y los beneficios obtenidos luego de su certificación.
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
            return jsonify({"respuesta": respuesta.choices[0].message.content.strip()})
        except Exception as e:
            print(f"❌ Error generando caso de estudio: {str(e)}")
            return jsonify({"error": "No se pudo generar el caso de estudio."}), 500

    mensajes_previos = [{
        "role": "system",
        "content": (
            "Eres un experto en auditorías de la norma ISO 9001. Analiza el caso de estudio proporcionado "
            "y responde únicamente con base en esta norma. Tu respuesta debe incluir los hallazgos clave de forma estructurada "
            "y enumerada (por ejemplo: 1. ..., 2. ..., etc.), usando saltos de línea para separar claramente cada punto. "
            "No escribas todo en un solo párrafo."
        )
    }, {"role": "user", "content": full_prompt}]

    try:
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=800,
            messages=mensajes_previos
        )
        content = respuesta.choices[0].message.content.strip()
        return jsonify({"respuesta": content})
    except openai.OpenAIError as e:
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return jsonify({"error": "Error al comunicarse con el modelo."}), 500

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    chatbot_response = data.get("chatbot_response", "")
    user_analysis = data.get("user_analysis", "")

    prompt_comparacion = f"""
    Actúa como un auditor experto en la norma ISO 9001.
    📘 Análisis del chatbot:
    {chatbot_response}
    🧑‍💼 Análisis del usuario:
    {user_analysis}
    Compara ambos. Evalúa si están alineados, si uno es más detallado o completo, si hay contradicciones, y redacta un párrafo resumen.
    """

    prompt_porcentaje = f"""
    Eres un evaluador experto en auditorías ISO 9001. Compara la respuesta del usuario con la del chatbot.
    Evalúa cuán alineado está el análisis del usuario. Devuelve solo un porcentaje entero del 0 al 100 seguido del símbolo %.
    Respuesta del chatbot:
    {chatbot_response}
    🧑‍💼 Análisis del usuario:
    {user_analysis}
    """

    prompt_riesgo = f"""
    Evalúa el análisis del usuario comparado con la respuesta del chatbot ISO 9001.
    Devuelve solo dos valores enteros entre 1 y 5 separados por coma: impacto,probabilidad.
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
        ).choices[0].message.content

        efectividad = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0,
            max_tokens=10,
            messages=[
                {"role": "system", "content": "Eres un evaluador que responde solo con un número del 0 al 100."},
                {"role": "user", "content": prompt_porcentaje}
            ]
        ).choices[0].message.content.strip()

        riesgo_valores = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0,
            max_tokens=10,
            messages=[
                {"role": "system", "content": "Eres un experto en evaluación de riesgos ISO 9001. Devuelve dos números entre 1 y 5 separados por coma."},
                {"role": "user", "content": prompt_riesgo}
            ]
        ).choices[0].message.content.strip().split(',')

        impacto = int(riesgo_valores[0])
        probabilidad = int(riesgo_valores[1])
        riesgo = impacto * probabilidad
        nivel = "Alto" if riesgo >= 12 else "Medio" if riesgo >= 6 else "Bajo"

        return jsonify({
            "comparacion_ia": comparacion,
            "efectividad": efectividad,
            "impacto": impacto,
            "probabilidad": probabilidad,
            "riesgo": riesgo,
            "nivel": nivel
        })

    except Exception as e:
        print(f"❌ Error en comparación: {str(e)}")
        return jsonify({"error": "Error en evaluación comparativa"}), 500
    
@app.route("/generar_caso", methods=["POST"])
def generar_caso_estudio_filtrado():
    data = request.get_json()
    pais = data.get("pais", "un país hispanohablante")
    sector = data.get("sector", "una industria")
    tipo_empresa = data.get("tipo_empresa", "una empresa")
    tamano_empresa = data.get("tamano_empresa", "una organización")

    prompt = f"""
    Proporcióname un caso de estudio realista sobre una empresa que implementó la norma ISO 9001.
    Filtros:
    - País: {pais}
    - Sector o área de actividad: {sector}
    - Tipo de empresa: {tipo_empresa}
    - Tamaño de empresa: {tamano_empresa}

    Describe:
    1. Nombre ficticio de la empresa.
    2. Problemas que enfrentaba antes de certificarse.
    3. Acciones implementadas para cumplir con ISO 9001.
    4. Beneficios obtenidos tras la certificación.
    """

    try:
        respuesta = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=600,
            messages=[
                {"role": "system", "content": "Eres un experto en casos de implementación ISO 9001."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({"caso_estudio": respuesta.choices[0].message.content.strip()})
    except Exception as e:
        print("❌ Error generando caso de estudio filtrado:", e)
        return jsonify({"error": "No se pudo generar el caso de estudio"}), 500
    
@app.route("/descargar_pdf", methods=["POST"])
def descargar_pdf():
    try:
        data = request.get_json()

        caso = limpiar_texto(data.get("caso_estudio", "No proporcionado"))
        respuesta_ia = limpiar_texto(data.get("respuesta_ia", "No disponible"))
        respuesta_usuario = limpiar_texto(data.get("respuesta_usuario", "No disponible"))
        comparacion = limpiar_texto(data.get("comparacion", "No realizada"))

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', size=14)
        pdf.cell(0, 10, "Informe de Auditoría ISO 9001", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, f"Caso de estudio:\n{caso}\n", align="L")
        pdf.multi_cell(0, 10, f"Respuesta del Chatbot:\n{respuesta_ia}\n", align="L")
        pdf.multi_cell(0, 10, f"Análisis del Usuario:\n{respuesta_usuario}\n", align="L")
        pdf.multi_cell(0, 10, f"Comparación IA:\n{comparacion}\n", align="L")

        buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin1')  # 'S' devuelve como string, .encode a bytes
        buffer.write(pdf_bytes)
        buffer.seek(0)


        return send_file(buffer, as_attachment=True, download_name="informe_auditoria.pdf", mimetype='application/pdf')

    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return jsonify({"error": "Hubo un error al generar el PDF."}), 500

@app.route("/evaluar_riesgo", methods=["POST"])
def evaluar_riesgo():
    try:
        data = request.get_json()
        impacto = int(data.get("impacto", 0))
        probabilidad = int(data.get("probabilidad", 0))
        riesgo = impacto * probabilidad
        nivel = "Alto" if riesgo >= 12 else "Medio" if riesgo >= 6 else "Bajo"
        return jsonify({"impacto": impacto, "probabilidad": probabilidad, "riesgo": riesgo, "nivel": nivel})
    except Exception as e:
        print(f"❌ Error en cálculo de riesgo: {str(e)}")
        return jsonify({"error": "Error en cálculo de riesgo"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
