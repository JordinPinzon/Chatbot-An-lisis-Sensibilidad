from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import os
import re
import numpy as np
import io
from PIL import Image
from fpdf import FPDF
from unidecode import unidecode
from dotenv import load_dotenv
import easyocr
import fitz
from flask_cors import CORS
from bs4 import BeautifulSoup

def html_a_texto_plano(html):
    """Convierte contenido HTML a texto plano legible para el PDF"""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()


def eliminar_emojis(texto):
    return emoji.replace_emoji(texto, replace='')

def markdown_to_html(text):
    # ❗ Eliminar cualquier etiqueta HTML residual que se haya colado del modelo
    text = re.sub(r'<[^>]+>', '', text)

    # Convertir encabezados markdown ### a <h3>
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

    # Convertir negritas markdown **texto** a <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Procesar listas
    lines = text.split('\n')
    html_lines = []
    in_list = False

    for line in lines:
        if line.strip().startswith('*'):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f"<li>{line.strip()[1:].strip()}</li>")
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line.strip():
                html_lines.append(f"<p>{line.strip()}</p>")
            else:
                html_lines.append("<br>")

    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)


# Cargar variables de entorno
load_dotenv()

# Configurar la API de Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("❌ ERROR: No se encontró la clave API de Gemini. Verifica tu archivo .env.")

genai.configure(api_key=gemini_api_key)

# Usar modelo Gemini 1.5 Pro más reciente
MODEL = genai.GenerativeModel("gemini-2.0-flash")

# Inicializar Flask
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
        return "\n".join(resultados).strip() or None
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
    image_data = data.get("image_data")
    extracted_text = ""

    if image_data:
        pass  # Aquí podrías manejar una imagen en base64

    full_prompt = f"{user_input}\n{extracted_text}".strip()

    if not full_prompt:
        return jsonify({"error": "Por favor, ingrese un caso de estudio o suba una imagen válida."}), 400

    # Si pide un caso real
    if pide_caso_estudio_real(full_prompt):
        caso_prompt = (
            "Proporcióname un caso de estudio real y diferente de una empresa conocida que haya implementado la norma ISO 9001.\n"
            "Cada vez que se te solicite, elige una empresa distinta que opere en un país y sector diferentes. Describe el nombre de la empresa, el sector en el que opera, los problemas que enfrentaba antes de certificarse, los cambios que aplicó para cumplir con la norma y los beneficios obtenidos luego de su certificación."
        )
        try:
            response = MODEL.generate_content(
                contents=[{"role": "user", "parts": [f"Eres un experto en certificaciones ISO 9001.\n\n{caso_prompt}"]}],
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 800
                }
            )
            return jsonify({"respuesta": response.text.strip()})
        except Exception as e:
            print(f"❌ Error generando caso de estudio: {str(e)}")
            return jsonify({"error": "No se pudo generar el caso de estudio."}), 500

    try:
        chat = MODEL.start_chat(history=[])

        # 🔹 Solicita la respuesta organizada en secciones separadas
        analisis_prompt = (
            "Eres un auditor experto en la norma ISO 9001.\n\n"
            "Analiza el siguiente caso de estudio de forma estructurada. No respondas de forma general. Todo debe estar enfocado exclusivamente en el caso proporcionado.\n"
            "Estructura la respuesta en las siguientes secciones claramente separadas:\n\n"
            "<strong>🧭 Procedimiento Aplicado:</strong>\n"
            "Describe los procedimientos reales auditados según el caso.\n\n"
            "<strong>🔬 Evidencia Recolectada:</strong>\n"
            "Describe qué evidencias se observaron o recopilaron (registros, entrevistas, documentos específicos del caso).\n\n"
            "<strong>🧠 Hallazgos Identificados:</strong>\n"
            "Indica no conformidades, fortalezas o debilidades encontradas, citando las cláusulas ISO 9001 aplicables.\n\n"
            "<strong>🚀 Mejoras o Recomendaciones:</strong>\n"
            "Redacta acciones específicas de mejora basadas solo en este caso.\n\n"
            f"Caso de estudio:\n{full_prompt}"
        )

        analisis_response = chat.send_message(
            analisis_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )

        # 🔹 Procedimiento general basado en el mismo caso
        procedimiento_prompt = (
            "En base al caso de estudio anterior, redacta los pasos detallados que un auditor ISO 9001 seguiría para realizar una auditoría específica a este caso. "
            "Incluye las fases reales aplicables:\n"
            "- Planificación\n- Revisión documental\n- Listas de verificación\n- Entrevistas y observaciones\n"
            "- Revisión de registros\n- Elaboración del informe y acciones de seguimiento.\n"
            "Evita explicaciones generales. Todo debe enfocarse en el contexto del caso."
        )

        procedimiento_response = chat.send_message(
            procedimiento_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )

        # 🔹 Combinar respuestas con secciones separadas
        respuesta_completa = (
            "<strong>🧭 Procedimiento General de Auditoría aplicado al caso:</strong><br><br>" +
            procedimiento_response.text.strip() +
            "<br><br><hr><br>" +
            analisis_response.text.strip()
        )

        respuesta_html = markdown_to_html(respuesta_completa)
        return jsonify({"respuesta": respuesta_html})

    except Exception as e:
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return jsonify({"error": "Error al comunicarse con el modelo."}), 500



    

@app.route("/analizar_pdf", methods=["POST"])
def analizar_pdf():
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "No se proporcionó un archivo PDF."}), 400
        
        file = request.files['pdf']
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "El archivo debe ser un PDF."}), 400

        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto_pdf = ""
        for page in doc:
            texto_pdf += page.get_text()

        if not texto_pdf.strip():
            return jsonify({"error": "No se pudo extraer texto del PDF."}), 400

        chat = MODEL.start_chat(history=[])

        analisis_prompt = (
            "Eres un auditor experto en la norma ISO 9001.\n\n"
            "Analiza el siguiente caso de estudio de forma estructurada. No respondas de forma general. Todo debe estar enfocado exclusivamente en el caso proporcionado.\n"
            "Estructura la respuesta en las siguientes secciones claramente separadas:\n\n"
            "<strong>🧭 Procedimiento Aplicado:</strong>\n"
            "Describe los procedimientos reales auditados según el caso.\n\n"
            "<strong>🔬 Evidencia Recolectada:</strong>\n"
            "Describe qué evidencias se observaron o recopilaron (registros, entrevistas, documentos específicos del caso).\n\n"
            "<strong>🧠 Hallazgos Identificados:</strong>\n"
            "Indica no conformidades, fortalezas o debilidades encontradas, citando las cláusulas ISO 9001 aplicables.\n\n"
            "<strong>🚀 Mejoras o Recomendaciones:</strong>\n"
            "Redacta acciones específicas de mejora basadas solo en este caso.\n\n"
            f"Caso de estudio:\n{texto_pdf.strip()}"
        )

        analisis_response = chat.send_message(
            analisis_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )

        respuesta_html = markdown_to_html(analisis_response.text.strip())
        return jsonify({
            "texto_extraido": texto_pdf.strip(),
            "respuesta": respuesta_html
        })

    except Exception as e:
        print(f"❌ Error procesando PDF: {str(e)}")
        return jsonify({"error": "Error procesando el PDF."}), 500



@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    chatbot_response = data.get("chatbot_response", "")
    user_analysis = data.get("user_analysis", "")

    prompt_comparacion = f"""
    Eres un auditor experto en la norma ISO 9001.

    Compara profesionalmente las siguientes dos respuestas sobre un mismo caso de auditoría: la del chatbot y la del usuario.

    Sigue esta estructura estricta SOLO en formato Markdown PURO. No uses etiquetas HTML como <p>, <br>, <strong>, <h1>, <h3>, etc. Usa exclusivamente encabezados markdown (###) y listas con asterisco (*). NO uses HTML.

    ### 🟦 Diferencias:
    * Explica qué aspectos menciona el chatbot que el usuario omite.
    * ¿Faltan evidencias? ¿No hay recomendaciones? ¿La respuesta es genérica?

    ### 🟩 Coincidencias:
    * ¿Qué puntos están correctamente alineados?
    * ¿El usuario replica bien algún razonamiento del chatbot?

    ### 🟥 Retroalimentación crítica:
    * Evalúa si el análisis del usuario es deficiente, incompleto o superficial.
    * Sé directo y profesional, como si corrigieras una auditoría real.

    ### 📌 Conclusión final:
    Resume en pocas líneas la calidad del análisis del usuario comparado con el del chatbot.

    📘 Respuesta del chatbot:
    {chatbot_response}

    🧑‍💼 Análisis del usuario:
    {user_analysis}
    """

    prompt_porcentaje = f"""
    Eres un evaluador experto en auditorías ISO 9001.

    Compara la respuesta del usuario con la del chatbot y asigna un **porcentaje de efectividad** del 0% al 100%, según qué tan alineado y completo es el análisis del usuario respecto a la norma ISO 9001 y al análisis del chatbot.

    Evalúa considerando estos criterios:

    1. ¿El usuario responde al caso concreto o da una respuesta genérica?
    2. ¿Incluye evidencias, hallazgos o recomendaciones concretas según la norma?
    3. ¿Cita o aplica cláusulas reales de la ISO 9001?
    4. ¿Demuestra comprensión técnica o es superficial?
    5. ¿Su análisis coincide al menos parcialmente con el del chatbot?

    Puntúa de la siguiente manera:

    - 0–30%: La respuesta es irrelevante, sin relación con el caso, sin fundamentos o completamente incorrecta.
    - 31–70%: La respuesta tiene partes correctas pero es incompleta, ambigua o poco técnica.
    - 71–100%: La respuesta está bien fundamentada, es coherente con el caso, y demuestra comprensión profunda de la norma ISO 9001.

    Devuelve **solo** un número entero seguido del símbolo %, sin palabras adicionales.

    📘 Respuesta del chatbot:
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
        comparacion = MODEL.generate_content(
            f"Eres un auditor experto en ISO 9001.\n\n{prompt_comparacion}",
            generation_config={"temperature": 0.5, "max_output_tokens": 1000}
        ).text.strip()

        efectividad = MODEL.generate_content(
            f"Eres un evaluador que responde solo con un número del 0 al 100.\n\n{prompt_porcentaje}",
            generation_config={"temperature": 0, "max_output_tokens": 10}
        ).text.strip()

        riesgo_response = MODEL.generate_content(
            "Eres un experto en evaluación de riesgos ISO 9001. Devuelve dos números enteros entre 1 y 5 separados por coma.\n\n" + prompt_riesgo,
            generation_config={"temperature": 0, "max_output_tokens": 10}
        ).text.strip()

        riesgo_valores = riesgo_response.split(',')
        if len(riesgo_valores) != 2:
            raise ValueError("Formato de riesgo inválido: se esperaban dos valores separados por coma")

        impacto = int(riesgo_valores[0].strip())
        probabilidad = int(riesgo_valores[1].strip())
        riesgo = impacto * probabilidad
        nivel = "Alto" if riesgo >= 12 else "Medio" if riesgo >= 6 else "Bajo"

        prompt_explicacion_efectividad = f"""
        Eres un auditor experto en ISO 9001. Acabas de calificar con {efectividad} la efectividad del análisis del usuario comparado con el del chatbot.

        Escribe una explicación clara y profesional del porqué se asignó ese porcentaje. No repitas literalmente la comparación. Enfócate en hacer que el usuario comprenda el valor del puntaje recibido.
        """

        explicacion_efectividad = MODEL.generate_content(
            prompt_explicacion_efectividad,
            generation_config={"temperature": 0.5, "max_output_tokens": 800}
        ).text.strip()

        prompt_explicacion_riesgo = f"""
        Eres un experto en gestión de riesgos según ISO 9001.

        Acabas de calcular un nivel de riesgo basado en:
        - Impacto: {impacto}
        - Probabilidad: {probabilidad}
        - Riesgo total: {riesgo}
        - Nivel: {nivel}

        Genera una explicación en lenguaje claro y profesional sobre lo que significa ese nivel de riesgo en el contexto de auditoría.
        """

        explicacion_riesgo = MODEL.generate_content(
            prompt_explicacion_riesgo,
            generation_config={"temperature": 0.5, "max_output_tokens": 800}
        ).text.strip()

        return jsonify({
            "comparacion_ia": markdown_to_html(comparacion),
            "efectividad": efectividad,
            "impacto": impacto,
            "probabilidad": probabilidad,
            "riesgo": riesgo,
            "nivel": nivel,
            "explicacion_efectividad": explicacion_efectividad,
            "explicacion_riesgo": explicacion_riesgo
        })

    except Exception as e:
        print(f"❌ Error en evaluación comparativa: {str(e)}")
        return jsonify({"error": "Error en evaluación comparativa"}), 500




@app.route("/descargar_pdf", methods=["POST"])
def descargar_pdf():
    try:
        data = request.get_json()

        caso = html_a_texto_plano(data.get("caso_estudio", "No proporcionado"))
        respuesta_ia = html_a_texto_plano(data.get("respuesta_ia", "No disponible"))
        respuesta_usuario = html_a_texto_plano(data.get("respuesta_usuario", "No disponible"))
        comparacion = html_a_texto_plano(data.get("comparacion", "No realizada"))


        # Eliminar emojis y caracteres especiales no soportados por latin-1
        def limpiar_texto_pdf(texto):
            texto = re.sub(r'[^\x00-\xFF]', '', texto)  # Solo latin-1
            texto = unidecode(texto)  # Transforma acentos y otros
            return texto.strip()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(0, 10, "Informe de Auditoría ISO 9001", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"Caso de estudio:\n{limpiar_texto_pdf(caso)}\n", align="L")
        pdf.multi_cell(0, 10, f"Respuesta del Chatbot:\n{limpiar_texto_pdf(respuesta_ia)}\n", align="L")
        pdf.multi_cell(0, 10, f"Análisis del Usuario:\n{limpiar_texto_pdf(respuesta_usuario)}\n", align="L")
        pdf.multi_cell(0, 10, f"Comparación IA:\n{limpiar_texto_pdf(comparacion)}\n", align="L")

        buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
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
    
@app.route("/generar_caso", methods=["POST"])
def generar_caso():
    data = request.get_json()
    pais = data.get("pais", "Ecuador")
    sector = data.get("sector", "tecnología")
    tipo_empresa = data.get("tipo_empresa", "privada")
    tamano_empresa = data.get("tamano_empresa", "mediana")

    prompt = f"""
    Eres un experto en auditorías ISO 9001 y en generación de casos de estudio realistas para capacitación empresarial.

    Genera un caso de estudio detallado y profesional basado en los siguientes filtros:

    - País: {pais}
    - Sector o área de actividad: {sector}
    - Tipo de empresa: {tipo_empresa}
    - Tamaño de empresa: {tamano_empresa}

    Incluye estas secciones en tu respuesta:

    1. Nombre de la empresa ficticia (solo escribe el nombre, sin encabezado).
    2. **Contexto breve de la organización** según los filtros.
    3. **Problema principal detectado antes de implementar ISO 9001**. Este problema debe ser puntual, realista y crítico para su sector (por ejemplo: retrasos en producción, errores en facturación, baja satisfacción del cliente, falta de trazabilidad en procesos, errores humanos en inventario, incumplimiento normativo, fallos de calidad, incidentes de seguridad, etc.).
    4. **Datos numéricos del impacto**:
    - Número de clientes afectados o quejas registradas.
    - Tiempo promedio de demora o respuesta.
    - Pérdidas económicas estimadas o costos operativos.
    - Tasa de error o incumplimiento.

    No incluyas acciones implementadas ni resultados obtenidos después de la certificación. No pongas las secciones 5 ni 6. Redacta el caso como un informe profesional, con estilo formal, en párrafos separados y con enfoque técnico. No uses viñetas ni numeraciones. Asegúrate de que todo esté vinculado al contexto específico de la empresa según los filtros proporcionados.
    """
    try:
        chat = MODEL.start_chat(history=[])
        response = chat.send_message(
            "Eres un experto en ISO 9001.\n" + prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 2000}
        )
        html_formatted = markdown_to_html(response.text.strip())
        return jsonify({"caso_estudio": html_formatted})
    except Exception as e:
        print(f"❌ Error generando caso filtrado: {str(e)}")
        return jsonify({"error": "No se pudo generar el caso de estudio."}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
