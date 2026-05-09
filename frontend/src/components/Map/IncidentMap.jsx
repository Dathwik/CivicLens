import { useRef, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import mapboxgl from "mapbox-gl";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || "";

const CATEGORY_COLORS = {
  noise: "#f59e0b",
  crime: "#ef4444",
  transit: "#3b82f6",
  sanitation: "#10b981",
  infrastructure: "#8b5cf6",
  emergency: "#f97316",
  other: "#6b7280",
};

export default function IncidentMap() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const geojson = useSelector((s) => s.incidents.geojson);

  useEffect(() => {
    if (map.current) return;
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-73.9857, 40.7484],
      zoom: 11,
    });

    map.current.on("load", () => {
      map.current.addSource("incidents", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

      // Heatmap layer
      map.current.addLayer({
        id: "incidents-heat",
        type: "heatmap",
        source: "incidents",
        maxzoom: 15,
        paint: {
          "heatmap-weight": 1,
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 1, 15, 3],
          "heatmap-color": [
            "interpolate", ["linear"], ["heatmap-density"],
            0, "rgba(33,102,172,0)", 0.2, "rgb(103,169,207)",
            0.4, "rgb(209,229,240)", 0.6, "rgb(253,219,199)",
            0.8, "rgb(239,138,98)", 1, "rgb(178,24,43)",
          ],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 15, 20],
          "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 7, 1, 15, 0.6],
        },
        layout: { visibility: "none" },
      });

      // Circle layer for individual pins
      map.current.addLayer({
        id: "incidents-points",
        type: "circle",
        source: "incidents",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 4, 2, 8, 4, 15, 8],
          "circle-color": [
            "match", ["get", "category"],
            "noise", CATEGORY_COLORS.noise,
            "crime", CATEGORY_COLORS.crime,
            "transit", CATEGORY_COLORS.transit,
            "sanitation", CATEGORY_COLORS.sanitation,
            "infrastructure", CATEGORY_COLORS.infrastructure,
            "emergency", CATEGORY_COLORS.emergency,
            CATEGORY_COLORS.other,
          ],
          "circle-stroke-width": 1,
          "circle-stroke-color": "#fff",
          "circle-opacity": 0.85,
        },
      });

      // Popup on click
      map.current.on("click", "incidents-points", (e) => {
        const props = e.features[0].properties;
        new mapboxgl.Popup({ offset: 10 })
          .setLngLat(e.lngLat)
          .setHTML(`<div style="color:#111;font-size:13px"><strong>${props.title}</strong><br/>${props.category} · ${props.borough}<br/><small>${props.timestamp?.slice(0, 10)}</small></div>`)
          .addTo(map.current);
      });

      map.current.on("mouseenter", "incidents-points", () => { map.current.getCanvas().style.cursor = "pointer"; });
      map.current.on("mouseleave", "incidents-points", () => { map.current.getCanvas().style.cursor = ""; });
    });
  }, []);

  useEffect(() => {
    if (!map.current || !geojson) return;
    const source = map.current.getSource("incidents");
    if (source) source.setData(geojson);
  }, [geojson]);

  const toggleHeatmap = () => {
    if (!map.current) return;
    const vis = showHeatmap ? "none" : "visible";
    map.current.setLayoutProperty("incidents-heat", "visibility", vis);
    setShowHeatmap(!showHeatmap);
  };

  return (
    <div style={{ position: "relative", flex: 1 }}>
      <div ref={mapContainer} style={{ width: "100%", height: "100%" }} />
      <button
        onClick={toggleHeatmap}
        style={{
          position: "absolute", top: 12, right: 12,
          background: showHeatmap ? "#3b82f6" : "#1e293b",
          color: "#fff", border: "1px solid #334155",
          borderRadius: 6, padding: "6px 12px", cursor: "pointer", fontSize: 13,
        }}
      >
        {showHeatmap ? "Heatmap ON" : "Heatmap OFF"}
      </button>
    </div>
  );
}
