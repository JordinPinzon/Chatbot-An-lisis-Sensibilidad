import React, { useState, FormEvent } from 'react';
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

// ✅ Componente auxiliar para los selects
function SelectField({
  label,
  value,
  onChange,
  options
}: {
  label: string;
  value: string;
  onChange: (val: string) => void;
  options: string[];
}) {
  return (
    <div>
      <label className="block text-gray-700 font-medium mb-1">{label}:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 border border-gray-300 rounded-md"
      >
        {options.map(opt => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

export default function ChatPage({ setChatbotResponse, historial, setHistorial }: ChatPageProps) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [casoEstudio, setCasoEstudio] = useState(historial.casoEstudio || '');
  const [loading, setLoading] = useState(false);
  const [pdfFile, setPdfFile] = useState<File | null>(null);

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
      setHistorial(prev => ({ ...prev, respuestaIA: reply }));
      setCasoEstudio('');
    } catch {
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
        pais, sector,
        tipo_empresa: tipoEmpresa,
        tamano_empresa: tamanoEmpresa
      });

      const casoTexto = casoRes.data.caso_estudio || casoRes.data.error;
      setCasoEstudio(casoTexto);

      if (!casoTexto || casoTexto.startsWith('❌')) {
        setResponse(casoTexto);
        setChatbotResponse(casoTexto);
        setLoading(false);
        return;
      }

      const analisisRes = await axios.post('http://localhost:5000/chat', { message: casoTexto });
      const analisisTexto = analisisRes.data.respuesta || analisisRes.data.error;

      setResponse(analisisTexto);
      setChatbotResponse(analisisTexto);
      setHistorial(prev => ({
        ...prev,
        casoEstudio: casoTexto,
        respuestaIA: analisisTexto,
      }));

    } catch {
      const errorMsg = '❌ Error al generar o analizar el caso de estudio.';
      setResponse(errorMsg);
      setChatbotResponse(errorMsg);
    }
    setLoading(false);
  };

  const handleUploadPdf = async (e: FormEvent) => {
    e.preventDefault();
    if (!pdfFile) return;

    const formData = new FormData();
    formData.append("pdf", pdfFile);

    setLoading(true);
    try {
      const res = await axios.post("http://localhost:5000/analizar_pdf", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const { texto_extraido, respuesta } = res.data;
      setCasoEstudio(texto_extraido);
      setResponse(respuesta);
      setChatbotResponse(respuesta);

      setHistorial(prev => ({
        ...prev,
        casoEstudio: texto_extraido,
        respuestaIA: respuesta
      }));
    } catch {
      const errorMsg = '❌ Error al analizar el PDF.';
      setResponse(errorMsg);
      setChatbotResponse(errorMsg);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: '#EDE8D0' }}>
      <div className="text-center text-black text-3xl font-bold mb-6">Chatbot ISO 9001</div>

      {/* Chat y PDF */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Mensaje:</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Escribe tu mensaje..."
          className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={4}
        />
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mt-4">
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
          >
            {loading ? "Enviando..." : "Enviar"}
          </button>
        </div>

        <div className="flex flex-col gap-2 mt-4">
          <input
            type="file"
            name="pdf"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
            className="text-sm text-gray-700"
          />
          <button
            type="button"
            onClick={handleUploadPdf}
            disabled={!pdfFile || loading}
            className="w-32 bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md transition duration-300"
          >
            Analizar PDF
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-4 text-gray-800">🎯 Generar Caso de Estudio con Filtros</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <SelectField label="País" value={pais} onChange={setPais} options={paises} />
          <SelectField label="Sector" value={sector} onChange={setSector} options={sectores} />
          <SelectField label="Tipo de Empresa" value={tipoEmpresa} onChange={setTipoEmpresa} options={tiposEmpresa} />
          <SelectField label="Tamaño de Empresa" value={tamanoEmpresa} onChange={setTamanoEmpresa} options={tamanosEmpresa} />
        </div>
        <button
          onClick={handleGenerateCase}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md"
        >
          {loading ? 'Generando...' : 'Generar caso de estudio'}
        </button>
      </div>

      {/* Resultados */}
      {casoEstudio && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">📘 Caso de Estudio:</h2>
        <div
          className="p-4 bg-blue-50 border border-blue-200 rounded-md text-gray-700"
          dangerouslySetInnerHTML={{ __html: casoEstudio }}
        />
        </div>
      )}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-2 text-gray-800">🧠 Respuesta (Análisis IA):</h2>
      <div
  className="p-4 bg-gray-100 border border-gray-300 rounded-md whitespace-pre-line text-gray-700"
  style={{ overflowY: 'visible', maxHeight: 'none' }}
  dangerouslySetInnerHTML={{ __html: response }}
      />
      </div>
    </div>
  );
}

