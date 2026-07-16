import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send } from 'lucide-react';

import logger from '../utils/logger';

const Chat = () => {
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hello! I'm your Laptop Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    // User message ko console mein log karna
    logger.info(`User sent message: "${userMsg}"`, "Chat");

    try {
      const formData = new FormData();
      formData.append('message', userMsg);

      const res = await axios.post('http://localhost:8000/chat', formData);
      
      // Successful response log karna
      logger.info("Successfully received response from backend.", "Chat");
      setMessages(prev => [...prev, { role: 'ai', text: res.data.response }]);
      
    } catch (error) {
      
      logger.error("Failed to connect to backend or get response.", "Chat");
      setMessages(prev => [...prev, { role: 'ai', text: "Error connecting to server." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>LaptopIQ Assistant</h2>
        <a href="/admin" className="admin-link">Admin Panel</a>
      </div>

      <div className="messages-area">
        {messages.map((msg, i) => (
          <div key={i} className={`message-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="message-bubble ai typing">Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={sendMessage} className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about laptops..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}><Send size={20} /></button>
      </form>
    </div>
  );
};

export default Chat;