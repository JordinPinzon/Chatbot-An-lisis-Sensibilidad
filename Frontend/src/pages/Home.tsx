import React, { useState } from 'react';
import ChatPage from './ChatPage';
import ComparePage from './ComparePage';

export default function Home() {
  const [chatbotResponse, setChatbotResponse] = useState('');

  return (
    <div className="flex flex-row h-screen">
      {/* Columna izquierda - Chatbot */}
      <div className="w-1/2 h-full border-r overflow-y-auto p-4">
        <ChatPage setChatbotResponse={setChatbotResponse} />
      </div>

      {/* Columna derecha - Comparación */}
      <div className="w-1/2 h-full overflow-y-auto p-4">
        <ComparePage chatbotResponse={chatbotResponse} />
      </div>
    </div>
  );
}
