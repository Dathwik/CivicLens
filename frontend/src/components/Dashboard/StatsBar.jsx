import { useSelector } from "react-redux";
import { useDispatch } from "react-redux";
import { setFilter, clearResults } from "../../store/incidentsSlice";
import { searchIncidents } from "../../store/incidentsSlice";

const CATEGORIES = ["noise", "crime", "transit", "sanitation", "infrastructure", "emergency"];
const BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"];

export default function StatsBar() {
  const dispatch = useDispatch();
  const { total, loading, activeCategory, activeBorough, days } = useSelector((s) => s.incidents);

  const applyFilter = (updates) => {
    dispatch(setFilter(updates));
    dispatch(searchIncidents({ ...updates }));
  };

  return (
    <div style={{ background: "#0f1117", borderBottom: "1px solid #1e293b", padding: "8px 12px", display: "flex", alignItems: "center", gap: 8, flexWrap: "nowrap", flexShrink: 0, overflowX: "auto", whiteSpace: "nowrap" }}>
      <div style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 700, marginRight: 8 }}>
        CivicLens
      </div>

      <div style={{ color: "#64748b", fontSize: 12 }}>
        {loading ? "Loading..." : `${total.toLocaleString()} incidents`}
      </div>

      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => applyFilter({ activeCategory: activeCategory === cat ? null : cat, category: activeCategory === cat ? null : cat })}
            style={{
              background: activeCategory === cat ? "#3b82f6" : "#1e293b",
              color: activeCategory === cat ? "#fff" : "#94a3b8",
              border: "1px solid #334155", borderRadius: 6,
              padding: "4px 10px", cursor: "pointer", fontSize: 12, textTransform: "capitalize",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {BOROUGHS.map((b) => (
          <button
            key={b}
            onClick={() => applyFilter({ activeBorough: activeBorough === b ? null : b, borough: activeBorough === b ? null : b })}
            style={{
              background: activeBorough === b ? "#8b5cf6" : "#1e293b",
              color: activeBorough === b ? "#fff" : "#94a3b8",
              border: "1px solid #334155", borderRadius: 6,
              padding: "4px 10px", cursor: "pointer", fontSize: 12,
            }}
          >
            {b}
          </button>
        ))}
      </div>

      <select
        value={days}
        onChange={(e) => applyFilter({ days: parseInt(e.target.value) })}
        style={{ background: "#1e293b", color: "#94a3b8", border: "1px solid #334155", borderRadius: 6, padding: "4px 8px", fontSize: 12 }}
      >
        {[7, 14, 30, 90].map((d) => <option key={d} value={d}>Last {d} days</option>)}
      </select>

      <button
        onClick={() => { dispatch(clearResults()); dispatch(setFilter({ activeCategory: null, activeBorough: null })); }}
        style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 12 }}
      >
        Clear
      </button>
    </div>
  );
}
