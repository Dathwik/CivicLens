import { useSelector } from "react-redux";

const CATEGORY_COLORS = {
  noise: "#f59e0b", crime: "#ef4444", transit: "#3b82f6",
  sanitation: "#10b981", infrastructure: "#8b5cf6", emergency: "#f97316", other: "#6b7280",
};

export default function AlertFeed() {
  const { feed, connected } = useSelector((s) => s.alerts);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#0f1117" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e293b", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Live Alerts</span>
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: connected ? "#10b981" : "#ef4444", display: "inline-block" }} />
        <span style={{ fontSize: 11, color: "#64748b" }}>{connected ? "live" : "disconnected"}</span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
        {feed.length === 0 && (
          <div style={{ color: "#475569", fontSize: 12, textAlign: "center", marginTop: 20 }}>
            No alerts yet. Ask AI to set an alert.
          </div>
        )}
        {feed.map((alert, i) => (
          <div
            key={i}
            style={{
              background: "#1e293b", borderRadius: 8, padding: "10px 12px", marginBottom: 8,
              borderLeft: `3px solid ${CATEGORY_COLORS[alert.incident?.category] || "#64748b"}`,
            }}
          >
            {alert.type === "test" ? (
              <div style={{ color: "#94a3b8", fontSize: 12 }}>{alert.message}</div>
            ) : (
              <>
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>
                  Alert: <strong style={{ color: "#94a3b8" }}>{alert.alert_query}</strong>
                </div>
                <div style={{ fontSize: 13, color: "#e2e8f0" }}>{alert.incident?.title}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>
                  {alert.incident?.borough} · {alert.incident?.timestamp?.slice(0, 10)}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
