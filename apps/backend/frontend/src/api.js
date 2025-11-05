// src/api.js
import axios from "axios";

// ✅ Vite usa import.meta.env en lugar de process.env
const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: API_URL
});

api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access_token");
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const refreshUrl = `${API_URL}/auth/refresh`;
          const res = await axios.post(refreshUrl, { refresh_token: refresh });
          localStorage.setItem("access_token", res.data.access_token);
          return api(originalRequest);
        } catch (err) {
          console.error("Refresh failed", err);
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;



