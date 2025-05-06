import React, { useState } from 'react';
import axios from 'axios';

interface ChatPageProps {
  setChatbotResponse: (text: string) => void;
}

export default function ChatPage({ setChatbotResponse }: ChatPageProps) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [casoEstudio, setCasoEstudio] = useState('');
  const [loading, setLoading] = useState(false);

  // Valores seleccionables para los filtros
  const paises = ['Ecuador', 'México', 'Colombia', 'Argentina', 'España'];
  const sectores = ['Salud', 'Educación', 'Automotriz', 'Alimentos', 'Tecnología'];
  const tiposEmpresa = ['Pública', 'Privada', 'ONG', 'Startup'];
  const tamanosEmpresa = ['Microempresa', 'Pequeña', 'Mediana', 'Grande'];

  const [pais, setPais] = useState(paises[0]);
  const [sector, setSector] = useState(sectores[0]);
  const [tipoEmpresa, setTipoEmpresa] = useState(tiposEmpresa[0]);
  const [tamanoEmpresa, setTamanoEmpresa] = useState(tamanosEmpresa[0]);

  const handleSend = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:5000/chat', {
        message,
      });

      const reply = res.data.respuesta || res.data.error;
      setResponse(reply);
      setChatbotResponse(reply);
      setCasoEstudio(''); // Limpiar caso anterior si hay
    } catch (error) {
      console.error('Error enviando mensaje:', error);
      const errorMsg = '❌ Error al enviar la solicitud.';
      setResponse(errorMsg);
      setChatbotResponse(errorMsg);
    }
    setLoading(false);
  };

  const handleGenerateCase = async () => {
    setLoading(true);
    try {
      const casoRes = await axios.post('http://localhost:5000/generar_caso', {
        pais,
        sector,
        tipo_empresa: tipoEmpresa,
        tamano_empresa: tamanoEmpresa,
      });

      const casoTexto = casoRes.data.caso_estudio || casoRes.data.error;
      setCasoEstudio(casoTexto); // Mostrar el caso generado

      if (!casoTexto || casoTexto.startsWith('❌')) {
        setResponse(casoTexto);
        setChatbotResponse(casoTexto);
        setLoading(false);
        return;
      }

      // Analizar el caso automáticamente
      const analisisRes = await axios.post('http://localhost:5000/chat', {
        message: casoTexto,
      });

      const analisisTexto = analisisRes.data.respuesta || analisisRes.data.error;
      setResponse(analisisTexto);
      setChatbotResponse(analisisTexto);

    } catch (error) {
      console.error('Error generando o analizando caso:', error);
      const errorMsg = '❌ Error al generar o analizar el caso de estudio.';
      setResponse(errorMsg);
      setChatbotResponse(errorMsg);
    }
    setLoading(false);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Chatbot ISO 9001</h1>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Escribe tu mensaje..."
        className="w-full p-2 border rounded mb-4"
        rows={4}
      />

      <button
        onClick={handleSend}
        disabled={loading}
        className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded mb-6"
      >
        {loading ? 'Enviando...' : 'Enviar'}
      </button>

      <hr className="my-6" />

      <h2 className="text-xl font-semibold mb-4">🎯 Generar Caso de Estudio con Filtros</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <select value={pais} onChange={(e) => setPais(e.target.value)} className="p-2 border rounded">
          {paises.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select value={sector} onChange={(e) => setSector(e.target.value)} className="p-2 border rounded">
          {sectores.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select value={tipoEmpresa} onChange={(e) => setTipoEmpresa(e.target.value)} className="p-2 border rounded">
          {tiposEmpresa.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <select value={tamanoEmpresa} onChange={(e) => setTamanoEmpresa(e.target.value)} className="p-2 border rounded">
          {tamanosEmpresa.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <button
        onClick={handleGenerateCase}
        disabled={loading}
        className="bg-purple-700 hover:bg-purple-800 text-white px-4 py-2 rounded"
      >
        {loading ? 'Generando...' : 'Generar caso de estudio'}
      </button>

      {casoEstudio && (
        <div className="mt-6">
          <h2 className="font-semibold mb-2">📘 Caso de Estudio Generado:</h2>
          <div className="p-4 bg-blue-50 border border-blue-200 rounded whitespace-pre-line">
            {casoEstudio}
          </div>
        </div>
      )}

      <div className="mt-6">
        <h2 className="font-semibold mb-2">🧠 Respuesta (Análisis IA):</h2>
        <div className="p-4 bg-gray-100 border rounded whitespace-pre-line">
          {response}
        </div>
      </div>
    </div>
  );
}
