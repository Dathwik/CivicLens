import { useRef, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { submitMessage, clearChat } from "../../store/chatSlice";
import { searchIncidents } from "../../store/incidentsSlice";
import MessageBubble from "./MessageBubble";

const SUGGESTIONS = [
  "Show me noise complaints in Brooklyn last 30 days",
  "Which borough has the most crime this week?",
  "Find infrastructure issues near Central Park",
  "Set an alert for transit incidents in Manhattan",
];

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, loading } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const message = input.trim();
    if (!message || loading) return;

    setInput("");
    const history = messages.map(({ role, content }) => ({ role, content }));

    const action = await dispatch(submitMessage({ message, history }));

    if (submitMessage.fulfilled.match(action)) {
      const searchCall = action.payload.toolCalls?.find((tc) => tc.tool === "search_incidents");
      if (searchCall?.input) {
        dispatch(searchIncidents(searchCall.input));
      }
    }
  };

  const handleSuggestion = (text) => {
    setInput(text);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#0f1117", borderLeft: "1px solid #1e293b" }}>
      {/* Header */}
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>CivicLens AI</span>
        <button onClick={() => dispatch(clearChat())} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 12 }}>Clear</button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 12px", display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ color: "#475569", fontSize: 13, textAlign: "center", marginTop: 20 }}>
            <div style={{ marginBottom: 16 }}>Ask about NYC incident data in plain English</div>
            {SUGGESTIONS.map((s) => (
              <div
                key={s}
                onClick={() => handleSuggestion(s)}
                style={{ background: "#1e293b", borderRadius: 8, padding: "8px 12px", marginBottom: 8, cursor: "pointer", color: "#94a3b8", fontSize: 12, textAlign: "left" }}
              >
                {s}
              </div>
            ))}
          </div>
        )}
        {messages.map((msg, i) => <MessageBubble key={i} message={msg} />)}
        {loading && (
          <div style={{ alignSelf: "flex-start", color: "#64748b", fontSize: 13 }}>
            <span>Querying data</span>
            <span style={{ animation: "pulse 1s infinite" }}>...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={{ padding: "12px", borderTop: "1px solid #1e293b", display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about incidents..."
          disabled={loading}
          style={{
            flex: 1, background: "#1e293b", border: "1px solid #334155", borderRadius: 8,
            padding: "10px 12px", color: "#e2e8f0", fontSize: 14, outline: "none",
          }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            background: "#3b82f6", border: "none", borderRadius: 8,
            padding: "10px 16px", color: "#fff", cursor: "pointer", fontSize: 14,
            opacity: loading || !input.trim() ? 0.5 : 1,
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
