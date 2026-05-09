import api from "./api";

export async function sendChat(message, history = []) {
  const { data } = await api.post("/api/ai/chat/", { message, history });
  return data;
}

export async function sendAgentTask(task) {
  const { data } = await api.post("/api/ai/agent/", { task });
  return data;
}
