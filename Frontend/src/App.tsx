import React, { useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import ComparePage from './pages/ComparePage';
import ChatbotIcon from './assets/Chatbot.png';
import axios from 'axios';

export default function App() {
  const [chatbotResponse, setChatbotResponse] = useState('');
  const [cleanResponse, setCleanResponse] = useState('');

  const [historial, setHistorial] = useState({
    casoEstudio: '',
    respuestaIA: '',
    respuestaUsuario: '',
  });

  const handleDescargarPDF = async () => {
    try {
      const payload = {
        caso_estudio: historial.casoEstudio,
        respuesta_ia: historial.respuestaIA,
        respuesta_usuario: historial.respuestaUsuario,
        comparacion: 'Generado desde App',
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

      setHistorial({
        casoEstudio: '',
        respuestaIA: '',
        respuestaUsuario: '',
      });
      setChatbotResponse('');
      setCleanResponse('');
    } catch (err) {
      alert('❌ Error al descargar el PDF.');
      console.error(err);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white p-6 flex flex-col items-center gap-6">
        <div className="w-24 h-24 rounded-full bg-white shadow-lg overflow-hidden flex items-center justify-center">
          <img
            src={ChatbotIcon}
            alt="Chatbot Auditor Icon"
            className="w-full h-full object-cover"
          />
        </div>

        <p className="text-sm font-semibold text-center text-white">Chatbot Auditor</p>

        <div className="w-full flex flex-col gap-4 mt-4">
          <Link
            to="/chat"
            className="text-left hover:bg-gray-700 px-4 py-2 rounded bg-gray-700 font-bold"
          >
            🤖 Chatbot
          </Link>

          <Link
            to="/comparar"
            className="text-left hover:bg-gray-700 px-4 py-2 rounded"
          >
            📊 Comparar
          </Link>

          <button
            onClick={handleDescargarPDF}
            className="text-left hover:bg-gray-700 px-4 py-2 rounded"
          >
            📥 Descargar PDF
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6 bg-gray-100">
        <Routes>
          <Route
            path="/chat"
            element={
              <ChatPage
                setChatbotResponse={setChatbotResponse}
                setCleanResponse={setCleanResponse}
                historial={historial}
                setHistorial={setHistorial}
              />
            }
          />
          <Route
            path="/comparar"
            element={
              <ComparePage
                chatbotResponse={chatbotResponse}
                cleanChatbotResponse={cleanResponse}
                historial={historial}
                setHistorial={setHistorial}
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}
