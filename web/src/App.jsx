import React, { useState, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import PropTypes from "prop-types";

const BOT_NAME = "Autobot";

// Detecta ambiente: usa o mesmo domínio/porta do frontend, via proxy reverso
const API_BASE_URL = "/api";

function TreinamentoIA({ onVoltar }) {
  const [prompt, setPrompt] = useState("");
  const [resposta, setResposta] = useState("");
  const [loading, setLoading] = useState(false);

  async function treinarIA(e) {
    e.preventDefault();
    setLoading(true);
    setResposta("");
    try {
      const res = await fetch(`${API_BASE_URL}/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exemplos: prompt }),
      });
      const data = await res.json();
      if (data.status === "ok") {
        setResposta("Treinamento iniciado!\n" + (data.output || ""));
      } else {
        setResposta("Erro ao treinar: " + (data.output || ""));
      }
    } catch (err) {
      setResposta("Erro ao conectar ao backend. " + (err?.message || ""));
    }
    setLoading(false);
  }

  return (
    <div className="treinamento-container">
      <h2>Treinamento da IA</h2>
      <form onSubmit={treinarIA} className="treinamento-form">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Exemplo: Pergunta? | Resposta\nOutra pergunta? | Outra resposta"
          rows={5}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Treinando..." : "Iniciar Treinamento"}
        </button>
      </form>
      {resposta && <div className="treinamento-resposta">{resposta}</div>}
      <button className="voltar-btn" onClick={onVoltar}>
        Voltar ao Chat
      </button>
    </div>
  );
}

function GeminiScreen({ onVoltar }) {
  const [messages, setMessages] = useState([
    { id: uuidv4(), from: "Gemini", text: "Envie um prompt para o Gemini!" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendGemini(e) {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { id: uuidv4(), from: "Você", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg.text }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        {
          id: uuidv4(),
          from: "Gemini",
          text: data.resposta || "[Sem resposta]",
        },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        {
          id: uuidv4(),
          from: "Gemini",
          text: "Erro ao conectar ao backend. " + (err?.message || ""),
        },
      ]);
    }
    setLoading(false);
  }

  return (
    <div className="telegram-bg">
      <div className="chat-container">
        <div className="chat-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Gemini (API)</span>
          <button className="voltar-btn" onClick={onVoltar}>
            Voltar
          </button>
        </div>
        <div className="chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={
                msg.from === "Você" ? "msg user-msg" : "msg bot-msg"
              }
            >
              <span className="msg-from">{msg.from}:</span> {msg.text}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <form className="chat-input" onSubmit={sendGemini}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite seu prompt para o Gemini..."
            autoFocus
            disabled={loading}
          />
          <button type="submit" disabled={loading}>{loading ? "Enviando..." : "Enviar"}</button>
        </form>
      </div>
    </div>
  );
}

// Modal Extras com botões modernos e alinhados
function ExtrasModal({ onClose, onTreinar, onGemini }) {
  return (
    <div className="extras-modal-bg">
      <div className="extras-modal">
        <h3>Extras</h3>
        <div className="extras-btn-group">
          <button className="extras-action-btn" onClick={onTreinar}>Treinar IA</button>
          <button className="extras-action-btn" onClick={onGemini}>Gemini</button>
        </div>
        <button onClick={onClose} className="fechar-btn">
          Fechar
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    { id: uuidv4(), from: BOT_NAME, text: "Olá! Como posso ajudar?" },
  ]);
  const [input, setInput] = useState("");
  const [tela, setTela] = useState("chat");
  const [extrasOpen, setExtrasOpen] = useState(false);
  const [iaSelecionada, setIaSelecionada] = useState("gemini");
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { id: uuidv4(), from: "Você", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: input, ia: iaSelecionada }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        {
          id: uuidv4(),
          from: BOT_NAME,
          text: data.resposta || "[Erro ao responder]",
        },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        {
          id: uuidv4(),
          from: BOT_NAME,
          text: "Erro ao conectar ao backend. " + (err?.message || ""),
        },
      ]);
    }
  }

  if (tela === "treinamento") {
    return <TreinamentoIA onVoltar={() => setTela("chat")} />;
  }
  if (tela === "gemini") {
    return <GeminiScreen onVoltar={() => setTela("chat")} />;
  }
  return (
    <div className="telegram-bg">
      <div className="chat-container">
        <div className="chat-header">
          <span style={{fontWeight: 700, fontSize: '1.3rem', letterSpacing: 1}}>Autobot Chat</span>
          <button className="extras-btn" onClick={() => setExtrasOpen(true)}>
            Extras
          </button>
        </div>
        {/* Modal de Extras */}
        {extrasOpen && (
          <ExtrasModal
            onClose={() => setExtrasOpen(false)}
            onTreinar={() => {
              setExtrasOpen(false);
              setTela("treinamento");
            }}
            onGemini={() => {
              setExtrasOpen(false);
              setTela("gemini");
            }}
          />
        )}
        <div className="chat-messages">
          {messages.map((msg) => {
            // Destaca mensagens de erro do Ollama/backend
            const isError =
              typeof msg.text === "string" &&
              (msg.text.toLowerCase().includes("erro ao conectar") ||
                msg.text.toLowerCase().includes("model not found") ||
                msg.text.toLowerCase().includes("erro ao responder") ||
                msg.text.toLowerCase().includes("error"));
            return (
              <div
                key={msg.id}
                className={
                  (msg.from === "Você" ? "msg user-msg" : "msg bot-msg") +
                  (isError ? " msg-error" : "")
                }
              >
                <span className="msg-from">{msg.from}:</span> {msg.text}
              </div>
            );
          })}
          <div ref={chatEndRef} />
        </div>
        <div className="ia-toggle-group">
          <button
            type="button"
            className={`ia-toggle-btn${iaSelecionada === "gemini" ? " selected" : ""}`}
            onClick={() => setIaSelecionada("gemini")}
            style={{ marginRight: 8 }}
          >
            Gemini
          </button>
          <button
            type="button"
            className={`ia-toggle-btn${iaSelecionada === "ollama" ? " selected" : ""}`}
            onClick={() => setIaSelecionada("ollama")}
          >
            Minha IA (Ollama)
          </button>
        </div>
        <form className="chat-input" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua mensagem..."
            autoFocus
          />
          <button type="submit">Enviar</button>
        </form>
      </div>
    </div>
  );
}

TreinamentoIA.propTypes = {
  onVoltar: PropTypes.func.isRequired,
};
GeminiScreen.propTypes = {
  onVoltar: PropTypes.func.isRequired,
};
ExtrasModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  onTreinar: PropTypes.func.isRequired,
  onGemini: PropTypes.func.isRequired,
};
