import { createSlice } from "@reduxjs/toolkit";

const alertsSlice = createSlice({
  name: "alerts",
  initialState: {
    feed: [],
    connected: false,
  },
  reducers: {
    addAlert: (state, action) => {
      state.feed.unshift({ ...action.payload, receivedAt: new Date().toISOString() });
      if (state.feed.length > 50) state.feed.pop();
    },
    setConnected: (state, action) => { state.connected = action.payload; },
    clearFeed: (state) => { state.feed = []; },
  },
});

export const { addAlert, setConnected, clearFeed } = alertsSlice.actions;
export default alertsSlice.reducer;
