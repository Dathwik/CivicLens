import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { connectAlerts } from "./services/wsService";
import { searchIncidents } from "./store/incidentsSlice";
import StatsBar from "./components/Dashboard/StatsBar";
import IncidentMap from "./components/Map/IncidentMap";
import ChatPanel from "./components/Chat/ChatPanel";
import AlertFeed from "./components/AlertPanel/AlertFeed";

export default function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    connectAlerts();
    dispatch(searchIncidents({ days: 30 }));
  }, [dispatch]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <StatsBar />
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 180px 180px", minHeight: 0 }}>
        <IncidentMap />
        <ChatPanel />
        <AlertFeed />
      </div>
    </div>
  );
}
