import React, { useState } from 'react';
import axios from 'axios';

interface ChatPageProps {
  setChatbotResponse: (text: string) => void;
  historial: {
    casoEstudio: string;
    respuestaIA: string;
    respuestaUsuario: string;
  };
  setHistorial: React.Dispatch<React.SetStateAction<{
    casoEstudio: string;
    respuestaIA: string;
    respuestaUsuario: string;
  }>>;
}

export default function ChatPage({ setChatbotResponse, historial, setHistorial }: ChatPageProps) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [casoEstudio, setCasoEstudio] = useState(historial.casoEstudio || '');
  const [loading, setLoading] = useState(false);

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
      const res = await axios.post('http://localhost:5000/chat', { message });
      const reply = res.data.respuesta || res.data.error;
      setResponse(reply);
      setChatbotResponse(reply);

      setHistorial((prev) => ({
        ...prev,
        respuestaIA: reply,
      }));

      setCasoEstudio('');
    } catch (error) {
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
      setCasoEstudio(casoTexto);

      if (!casoTexto || casoTexto.startsWith('❌')) {
        setResponse(casoTexto);
        setChatbotResponse(casoTexto);
        setLoading(false);
        return;
      }

      const analisisRes = await axios.post('http://localhost:5000/chat', {
        message: casoTexto,
      });

      const analisisTexto = analisisRes.data.respuesta || analisisRes.data.error;
      setResponse(analisisTexto);
      setChatbotResponse(analisisTexto);

      setHistorial((prev) => ({
        ...prev,
        casoEstudio: casoTexto,
        respuestaIA: analisisTexto,
      }));

    } catch (error) {
      const errorMsg = '❌ Error al generar o analizar el caso de estudio.';
      setResponse(errorMsg);
      setChatbotResponse(errorMsg);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: '#EDE8D0' }}>
      <div className="text-center text-black text-3xl font-bold mb-6">Chatbot ISO 9001</div>


      <div className="bg-white rounded-lg shadow-md p-6 mb-6 transition-all duration-300">
        <label className="block text-gray-700 font-semibold mb-2">Mensaje:</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Escribe tu mensaje..."
          className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
          rows={4}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-all duration-300 flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Enviando...
            </>
          ) : 'Enviar'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6 transition-all duration-300">
        <h2 className="text-2xl font-semibold mb-4 text-gray-800">🎯 Generar Caso de Estudio con Filtros</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-gray-700 font-medium mb-1">País:</label>
            <select value={pais} onChange={(e) => setPais(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md">
              {paises.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Sector:</label>
            <select value={sector} onChange={(e) => setSector(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md">
              {sectores.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Tipo de Empresa:</label>
            <select value={tipoEmpresa} onChange={(e) => setTipoEmpresa(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md">
              {tiposEmpresa.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-1">Tamaño de Empresa:</label>
            <select value={tamanoEmpresa} onChange={(e) => setTamanoEmpresa(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md">
              {tamanosEmpresa.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerateCase}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md transition duration-300"
        >
          {loading ? 'Generando...' : 'Generar caso de estudio'}
        </button>
      </div>

      {casoEstudio && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6 transition-all duration-300">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">📘 Caso de Estudio Generado:</h2>
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md whitespace-pre-line text-gray-700">
            {casoEstudio}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6 transition-all duration-300">
        <h2 className="text-xl font-semibold mb-2 text-gray-800">🧠 Respuesta (Análisis IA):</h2>
        <div className="p-4 bg-gray-100 border border-gray-300 rounded-md whitespace-pre-line text-gray-700">
          {response}
        </div>
      </div>
    </div>
  );
}
