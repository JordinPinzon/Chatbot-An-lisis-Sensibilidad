import React, { useState } from 'react';
import ChatPage from './pages/ChatPage';
import ComparePage from './pages/ComparePage';

export default function App() {
  const [chatbotResponse, setChatbotResponse] = useState('');

  return (
    <div className="flex flex-row h-screen overflow-hidden">
      {/* Chat */}
      <div className="w-1/2 border-r overflow-y-auto p-6 bg-white">
        <ChatPage setChatbotResponse={setChatbotResponse} />
      </div>

      {/* Comparación */}
      <div className="w-1/2 overflow-y-auto p-6 bg-gray-50">
        <ComparePage chatbotResponse={chatbotResponse} />
      </div>
    </div>
  );
}
