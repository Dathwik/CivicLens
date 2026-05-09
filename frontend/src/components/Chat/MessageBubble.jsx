import { useState } from "react";

const styles = {
  user: { alignSelf: "flex-end", background: "#3b82f6", color: "#fff", borderRadius: "12px 12px 2px 12px", padding: "10px 14px", maxWidth: "75%", fontSize: 14 },
  assistant: { alignSelf: "flex-start", background: "#1e293b", color: "#e2e8f0", borderRadius: "12px 12px 12px 2px", padding: "10px 14px", maxWidth: "85%", fontSize: 14, lineHeight: 1.5 },
  toolCard: { marginTop: 8, background: "#0f172a", border: "1px solid #334155", borderRadius: 6, padding: "6px 10px", fontSize: 12, color: "#94a3b8" },
};

export default function MessageBubble({ message }) {
  const [expanded, setExpanded] = useState(false);
  const isUser = message.role === "user";

  return (
    <div style={isUser ? styles.user : styles.assistant}>
      <span style={{ whiteSpace: "pre-wrap" }}>{message.content}</span>
      {message.toolCalls?.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{ marginTop: 6, background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 11 }}
          >
            {expanded ? "▼" : "▶"} {message.toolCalls.length} tool call{message.toolCalls.length > 1 ? "s" : ""}
          </button>
          {expanded && message.toolCalls.map((tc, i) => (
            <div key={i} style={styles.toolCard}>
              <strong>{tc.tool}</strong>
              <pre style={{ marginTop: 4, overflow: "auto", fontSize: 11 }}>{JSON.stringify(tc.input, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
