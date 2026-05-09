import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChat } from "../services/chatService";

export const submitMessage = createAsyncThunk("chat/submit", async ({ message, history }) => {
  const data = await sendChat(message, history);
  return { userMessage: message, response: data.response, toolCalls: data.tool_calls || [] };
});

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearChat: (state) => { state.messages = []; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitMessage.pending, (state, action) => {
        state.loading = true;
        state.error = null;
        state.messages.push({ role: "user", content: action.meta.arg.message });
      })
      .addCase(submitMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({
          role: "assistant",
          content: action.payload.response,
          toolCalls: action.payload.toolCalls,
        });
      })
      .addCase(submitMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { clearChat } = chatSlice.actions;
export default chatSlice.reducer;
