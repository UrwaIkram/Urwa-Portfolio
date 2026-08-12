"use client";

import { useRef, useState, useEffect } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  imageUrl?: string | null;
};

type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
};

const BACKEND_URL = "https://urwa-portfolio-production.up.railway.app";
export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem("permanent_chat_sessions");
    if (saved) {
      try {
        setSessions(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse chat history:", e);
      }
    }
  }, []);

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice recognition.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
    };
    
    recognition.start();
  };

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      chatWindowRef.current?.scrollTo({
        top: chatWindowRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const updatedMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
    ];

    setMessages(updatedMessages);
    setInput("");
    setError("");
    setLoading(true);
    scrollToBottom();

    let activeId = currentSessionId;

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updatedMessages }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }

      const finalMessages: ChatMessage[] = [
        ...updatedMessages, 
        { role: "assistant", content: data.reply, imageUrl: data.image_url }
      ];

      setMessages(finalMessages);

      if (!activeId) {
        const newId = Date.now().toString();
        const newSession: ChatSession = {
          id: newId,
          title: text.length > 30 ? text.substring(0, 30) + "..." : text,
          messages: finalMessages,
        };
        setCurrentSessionId(newId);
        setSessions((prev) => {
          const updatedList = [newSession, ...prev];
          localStorage.setItem("permanent_chat_sessions", JSON.stringify(updatedList));
          return updatedList;
        });
      } else {
        setSessions((prev) => {
          const updatedList = prev.map((s) => (s.id === activeId ? { ...s, messages: finalMessages } : s));
          localStorage.setItem("permanent_chat_sessions", JSON.stringify(updatedList));
          return updatedList;
        });
      }

    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }

  function newChat() {
    setCurrentSessionId(null);
    setMessages([]);
    setError("");
  }

  function selectSession(session: ChatSession) {
    setCurrentSessionId(session.id);
    setMessages(session.messages);
    setError("");
  }

  function deleteSession(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    const updated = sessions.filter((s) => s.id !== id);
    setSessions(updated);
    localStorage.setItem("permanent_chat_sessions", JSON.stringify(updated));
    if (currentSessionId === id) {
      newChat();
    }
  }

  return (
    <div className="app" style={{ display: "flex", height: "100vh" }}>
      <aside className="sidebar" style={{ width: "260px", background: "#171717", color: "#fff", display: "flex", flexDirection: "column", padding: "10px" }}>
        <button className="new-chat-btn" onClick={newChat} style={{ padding: "10px", background: "#2f2f2f", border: "1px solid #444", color: "#fff", borderRadius: "6px", cursor: "pointer", marginBottom: "15px" }}>
          + New chat
        </button>
        <div className="history-list" style={{ overflowY: "auto", flex: 1 }}>
          {sessions.map((s) => (
            <div 
              key={s.id} 
              onClick={() => selectSession(s)}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 10px",
                margin: "4px 0",
                borderRadius: "6px",
                cursor: "pointer",
                background: currentSessionId === s.id ? "#2f2f2f" : "transparent",
                fontSize: "14px"
              }}
            >
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, marginRight: "10px" }}>
                {s.title}
              </span>
              <button 
                onClick={(e) => deleteSession(e, s.id)}
                style={{ background: "transparent", border: "none", color: "#aaa", cursor: "pointer", fontSize: "12px" }}
                title="Delete chat"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      </aside>

      <main className="main" style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
        <div className="chat-window" ref={chatWindowRef} style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
          {messages.length === 0 && (
            <div className="empty-state" style={{ textAlign: "center", marginTop: "20vh" }}>
              <h1>Ask me about something</h1>
              <p>Type a message below to start the conversation.</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`} style={{ margin: "15px 0" }}>
              <div className="role" style={{ fontWeight: "bold", fontSize: "12px", color: "#666" }}>
                {m.role === "user" ? "You" : "AI"}
              </div>
              <div className="bubble" style={{ background: m.role === "user" ? "#f0f0f0" : "#e6f4ea", padding: "10px 14px", borderRadius: "8px", marginTop: "4px" }}>
                <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{m.content}</p>
                {m.imageUrl && (
                  <img 
                    src={m.imageUrl} 
                    alt="Reference diagram" 
                    style={{ maxWidth: "100%", borderRadius: "8px", marginTop: "10px" }} 
                  />
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant" style={{ margin: "15px 0" }}>
              <div className="role" style={{ fontWeight: "bold", fontSize: "12px", color: "#666" }}>AI</div>
              <div className="bubble typing" style={{ padding: "10px 14px", background: "#e6f4ea", borderRadius: "8px" }}>Thinking...</div>
            </div>
          )}
        </div>

        {error && <div className="error-banner" style={{ background: "#ffebee", color: "#c62828", padding: "10px", textAlign: "center" }}>⚠️ {error}</div>}

        <form className="chat-input-bar" onSubmit={handleSubmit} style={{ display: "flex", padding: "15px", borderTop: "1px solid #ddd", background: "#fff" }}>
          <button 
            type="button" 
            onClick={startListening} 
            className={`voice-btn ${isListening ? "active" : ""}`}
            style={{ marginRight: "10px", background: "none", border: "1px solid #ccc", borderRadius: "6px", padding: "8px 12px", cursor: "pointer" }}
          >
            {isListening ? "⏹️" : "🎤"}
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message the assistant..."
            rows={1}
            style={{ flex: 1, resize: "none", padding: "10px", borderRadius: "6px", border: "1px solid #ccc" }}
            required
          />
          <button type="submit" disabled={loading} style={{ marginLeft: "10px", padding: "10px 20px", background: "#000", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer" }}>
            Send
          </button>
        </form>
      </main>
    </div>
  );
}