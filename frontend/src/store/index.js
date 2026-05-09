import { configureStore } from "@reduxjs/toolkit";
import incidentsReducer from "./incidentsSlice";
import chatReducer from "./chatSlice";
import alertsReducer from "./alertsSlice";

export const store = configureStore({
  reducer: {
    incidents: incidentsReducer,
    chat: chatReducer,
    alerts: alertsReducer,
  },
});
