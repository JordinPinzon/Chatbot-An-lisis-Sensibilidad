import React, { useState, useEffect } from 'react';
import axios from 'axios';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;


interface ComparePageProps {
  chatbotResponse: string;
  cleanChatbotResponse: string;
  historial: {
    casoEstudio: string;
    respuestaIA: string;
    respuestaUsuario: string;
  };
  setHistorial: React.Dispatch<
    React.SetStateAction<{
      casoEstudio: string;
      respuestaIA: string;
      respuestaUsuario: string;
    }>
  >;
}

export default function ComparePage({
  chatbotResponse,
  cleanChatbotResponse,  
  historial,
  setHistorial,
}: ComparePageProps) {

  const [userAnalysis, setUserAnalysis] = useState(historial.respuestaUsuario || '');
  const [localChatbotResponse, setLocalChatbotResponse] = useState(cleanChatbotResponse);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<null | {
  comparacion_ia: string;
  efectividad: string;
  impacto: number;
  probabilidad: number;
  riesgo: number;
  nivel: string;
  explicacion_efectividad?: string;
  explicacion_riesgo?: string;
}>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
  setLocalChatbotResponse(cleanChatbotResponse);
  }, [cleanChatbotResponse]);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await axios.post(`${BACKEND_URL}/compare`, {
        chatbot_response: localChatbotResponse,
        user_analysis: userAnalysis,
      });

      setResult(res.data);

      setHistorial((prev) => ({
        ...prev,
        respuestaUsuario: userAnalysis,
      }));
    } catch (err) {
      console.error('❌ Error en comparación:', err);
      setError('Hubo un error al procesar la comparación.');
    }

    setLoading(false);
  };

  const handleDownloadPDF = async () => {
    try {
      const payload = {
        caso_estudio: localChatbotResponse,
        respuesta_ia: localChatbotResponse,
        respuesta_usuario: userAnalysis,
        comparacion: result?.comparacion_ia || 'No disponible',
      };

      const res = await axios.post(`${BACKEND_URL}/descargar_pdf`, payload, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'informe_auditoria.pdf');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('❌ Error al descargar PDF:', error);
      alert('Hubo un error al generar el PDF.');
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: '#EDE8D0' }}>

<h1 className="text-3xl font-bold mb-6 text-center text-black">Comparación de los análisis</h1>


      <div className="bg-white rounded-lg shadow-md p-6 mb-6 transition-all duration-300">
        <label className="block text-gray-700 font-semibold mb-2">📘 Respuesta del Chatbot:</label>
        <div
            className="w-full p-3 border border-gray-300 rounded-md mb-4 bg-gray-50 text-gray-800"
            dangerouslySetInnerHTML={{ __html: chatbotResponse }}
          />


        <label className="block text-gray-700 font-semibold mb-2">🧑‍💼 Tu análisis:</label>
        <textarea
          value={userAnalysis}
          onChange={(e) => setUserAnalysis(e.target.value)}
          placeholder="Pega aquí tu análisis como auditor..."
          className="w-full p-3 border border-gray-300 rounded-md mb-6"
          rows={5}
        />

        <div className="flex gap-4">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="bg-green-700 hover:bg-green-800 text-white px-6 py-2 rounded-md transition-all duration-300"
          >
            {loading ? 'Comparando...' : 'Comparar'}
          </button>

          {result && (
            <button
              onClick={handleDownloadPDF}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md transition-all duration-300"
            >
              Descargar informe PDF
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 text-red-700 bg-red-100 border border-red-400 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white rounded-lg shadow-md p-6 transition-all duration-300">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">📊 Resultado de la comparación</h2>
          <div
              className="mb-4 text-gray-800 bg-gray-50 border border-gray-200 rounded-md p-4"
              dangerouslySetInnerHTML={{ __html: result.comparacion_ia }}
            />

          <p className="mb-2"><strong>Efectividad:</strong> {result.efectividad}</p>

          <div className="mt-6 mb-4">
          <h3 className="text-lg font-semibold mb-2 text-gray-700">📈 Visualización del Riesgo</h3>

          {/* Tabla de valores antes de la gráfica */}
          <table className="table-auto border-collapse w-full text-sm text-left text-gray-700 mb-4">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-4 py-2">Indicador</th>
                <th className="border px-4 py-2">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border px-4 py-2">Impacto</td>
                <td className="border px-4 py-2">{result.impacto}</td>
              </tr>
              <tr>
                <td className="border px-4 py-2">Probabilidad</td>
                <td className="border px-4 py-2">{result.probabilidad}</td>
              </tr>
              <tr>
                <td className="border px-4 py-2">Riesgo</td>
                <td className="border px-4 py-2">{result.riesgo}</td>
              </tr>
            </tbody>
          </table>
        </div>


          <p><strong>Nivel de Riesgo:</strong> {result.nivel} ({result.riesgo})</p>
          {/* Explicación de la Efectividad */}
          {result.explicacion_efectividad && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded text-gray-800">
              <h3 className="font-semibold mb-2">📝 Explicación de la Efectividad</h3>
              <p>{result.explicacion_efectividad}</p>
            </div>
          )}

          {/* Explicación del Riesgo */}
          {result.explicacion_riesgo && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded text-gray-800">
              <h3 className="font-semibold mb-2">📉 Explicación del Nivel de Riesgo</h3>
              <p>{result.explicacion_riesgo}</p>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
