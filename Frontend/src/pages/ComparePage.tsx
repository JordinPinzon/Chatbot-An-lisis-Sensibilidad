import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import axios from 'axios';

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
      const res = await axios.post('http://localhost:5000/compare', {
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

      const res = await axios.post('http://localhost:5000/descargar_pdf', payload, {
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
          <p className="mb-2"><strong>Resumen IA:</strong> {result.comparacion_ia}</p>
          <p className="mb-2"><strong>Efectividad:</strong> {result.efectividad}</p>

          <div className="mt-6 mb-4">
            <h3 className="text-lg font-semibold mb-2 text-gray-700">📈 Visualización del Riesgo</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={[
                { name: 'Impacto', valor: result.impacto },
                { name: 'Probabilidad', valor: result.probabilidad },
                { name: 'Riesgo', valor: result.riesgo },
              ]}>
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="valor" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p><strong>Nivel de Riesgo:</strong> {result.nivel} ({result.riesgo})</p>
        </div>
      )}
    </div>
  );
}
