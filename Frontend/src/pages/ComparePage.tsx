import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ComparePageProps {
  chatbotResponse: string;
}

export default function ComparePage({ chatbotResponse }: ComparePageProps) {
  const [userAnalysis, setUserAnalysis] = useState('');
  const [localChatbotResponse, setLocalChatbotResponse] = useState(chatbotResponse);
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
    setLocalChatbotResponse(chatbotResponse);
  }, [chatbotResponse]);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await axios.post('http://localhost:5000/compare', {
        chatbot_response: localChatbotResponse,
        user_analysis: userAnalysis
      });

      setResult(res.data);
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
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Comparar con tu propio análisis</h1>

      <label className="font-semibold">Respuesta del Chatbot:</label>
      <textarea
        value={localChatbotResponse}
        onChange={(e) => setLocalChatbotResponse(e.target.value)}
        placeholder="Pega aquí la respuesta del chatbot..."
        className="w-full p-2 border rounded mb-4"
        rows={5}
      />

      <label className="font-semibold">Tu análisis:</label>
      <textarea
        value={userAnalysis}
        onChange={(e) => setUserAnalysis(e.target.value)}
        placeholder="Pega aquí tu análisis como auditor..."
        className="w-full p-2 border rounded mb-4"
        rows={5}
      />

      <div className="flex gap-4">
        <button
          onClick={handleCompare}
          disabled={loading}
          className="bg-green-700 hover:bg-green-800 text-white px-4 py-2 rounded"
        >
          {loading ? 'Comparando...' : 'Comparar'}
        </button>

        {result && (
          <button
            onClick={handleDownloadPDF}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded"
          >
            Descargar informe PDF
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 text-red-700 bg-red-100 border border-red-400 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 bg-gray-100 p-4 rounded border">
          <h2 className="text-xl font-semibold mb-2">Resultado de la comparación</h2>
          <p><strong>Resumen IA:</strong> {result.comparacion_ia}</p>
          <p><strong>Efectividad:</strong> {result.efectividad}</p>
          <p><strong>Impacto:</strong> {result.impacto}</p>
          <p><strong>Probabilidad:</strong> {result.probabilidad}</p>
          <p><strong>Nivel de Riesgo:</strong> {result.nivel} ({result.riesgo})</p>
        </div>
      )}
    </div>
  );
}
