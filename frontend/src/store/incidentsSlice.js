import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../services/api";

export const searchIncidents = createAsyncThunk("incidents/search", async (params) => {
  const { data } = await api.get("/api/search/", { params });
  return data;
});

const incidentsSlice = createSlice({
  name: "incidents",
  initialState: {
    results: [],
    geojson: null,
    total: 0,
    loading: false,
    error: null,
    activeCategory: null,
    activeBorough: null,
    days: 30,
  },
  reducers: {
    setFilter: (state, action) => {
      Object.assign(state, action.payload);
    },
    clearResults: (state) => {
      state.results = [];
      state.geojson = null;
      state.total = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchIncidents.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(searchIncidents.fulfilled, (state, action) => {
        state.loading = false;
        state.results = action.payload.results;
        state.geojson = action.payload.geojson;
        state.total = action.payload.total;
      })
      .addCase(searchIncidents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { setFilter, clearResults } = incidentsSlice.actions;
export default incidentsSlice.reducer;
