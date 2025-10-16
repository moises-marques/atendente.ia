import React, { useState, useEffect, useRef } from "react";
import "./Chat.css";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const popSound = useRef(null);
  const [apiKey, setApiKey] = useState(""); // Estado para chave da OpenAI
  const [savedKey, setSavedKey] = useState(localStorage.getItem("openai_api_key") || "");


// Função para salvar a chave no localStorage
const handleSaveKey = () => {
  if (!apiKey.trim()) {
    alert("Por favor, insira uma chave válida.");
    return;
  }
  localStorage.setItem("openai_api_key", apiKey.trim());
  setSavedKey(apiKey.trim());
  setApiKey("");
  alert("✅ Chave salva com sucesso!");
};


  useEffect(() => {
    popSound.current = new Audio("/pop.mp3");
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage = { from: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Ativa o efeito de digitação
    setIsTyping(true);

    try {
      const res = await fetch("https://atendente-ia.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!res.ok) throw new Error("Erro ao conectar com o servidor.");
      const data = await res.json();

      // Simula o delay do "pensando" antes de mostrar a resposta
      setTimeout(() => {
        setIsTyping(false);
        const botMessage = { from: "bot", text: data.reply };
        setMessages((prev) => [...prev, botMessage]);

        // Toca o som
        if (popSound.current) {
          popSound.current.currentTime = 0;
          popSound.current.play();
        }
      }, 800 + Math.random() * 600); // delay entre 0.8 e 1.4s

    } catch (err) {
      setTimeout(() => {
        setIsTyping(false);
        const errorMsg = { from: "bot", text: "⚠️ Erro ao conectar com o servidor." };
        setMessages((prev) => [...prev, errorMsg]);

        if (popSound.current) {
          popSound.current.currentTime = 0;
          popSound.current.play();
        }
      }, 800);
    }
  }

  function handleKeyPress(e) {
    if (e.key === "Enter") sendMessage();
  }

  return (
    <div className="chat-wrapper">
      <div className="chat-header">
        🤖 RobôBot <span className="chat-subtitle">Atendente IA</span>
      </div>

      {/* NOVO: campo de chave só aparece se ainda não foi salva */}
      {!savedKey && (
        <div className="chat-api-key">
          <input
            type="password" // ← 🔒 campo tipo senha
            placeholder="Coloque sua chave OpenAI aqui"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button onClick={handleSaveKey}>Salvar chave</button>
        </div>
      )}


       {/* Campo da chave da OpenAI
      <div className="chat-api-key">
        <input
          type="text"
          placeholder="Cole sua chave da OpenAI aqui"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </div> */}


      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message ${msg.from === "user" ? "user-msg" : "bot-msg"}`}
            >
              {msg.text}
            </div>
          ))}

          {isTyping && (
            <div className="message bot-msg typing">...</div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button onClick={sendMessage}>Enviar</button>
        </div>
      </div>
    </div>
  );
}

export default Chat;
