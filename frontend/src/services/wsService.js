import { store } from "../store";
import { addAlert, setConnected } from "../store/alertsSlice";

let socket = null;

export function connectAlerts() {
  const wsUrl = (import.meta.env.VITE_WS_URL || "ws://localhost:8000") + "/ws/alerts/";
  socket = new WebSocket(wsUrl);

  socket.onopen = () => store.dispatch(setConnected(true));
  socket.onclose = () => {
    store.dispatch(setConnected(false));
    setTimeout(connectAlerts, 5000); // auto-reconnect
  };
  socket.onerror = () => store.dispatch(setConnected(false));
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "new_incident" || data.type === "test") {
      store.dispatch(addAlert(data));
    }
  };
}

export function sendPing() {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "ping" }));
  }
}
