import axios from "axios";

const SESSION_KEY = "currentSession";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "https://digitallogichub-graduation-production.up.railway.app",
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request interceptor ───────────────────────────────────────────────────────
// Automatically attaches the JWT token to every request that needs it.
// Public routes (register, login, verify) don't need a token, but sending
// it on those is harmless — the backend simply ignores it.
api.interceptors.request.use(
  (config) => {
    const session = localStorage.getItem(SESSION_KEY);
    if (session) {
      try {
        const user = JSON.parse(session);
        if (user?.token) {
          config.headers["Authorization"] = `Bearer ${user.token}`;
        }
      } catch {
        // Corrupted session — ignore, login page will handle it
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor ──────────────────────────────────────────────────────
// If any request returns 401 (expired / invalid token), clear the session
// and reload the page so the user is sent back to login cleanly.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only clear session if this wasn't the login request itself
      const url = error.config?.url || "";
      const isAuthRoute = url.includes("/auth/login") || url.includes("/auth/verify");
      if (!isAuthRoute) {
        localStorage.removeItem(SESSION_KEY);
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Named exports (kept for backward compatibility) ───────────────────────────

export async function getRecommendations(userId) {
  const res = await api.get(`/recommender/recommendations/${userId}`);
  return res.data;
}

export const fetchRecommendations = async (userId) => {
  const res = await api.get(`/recommender/recommendations/${userId}`);
  return res.data;
};

export const trackResource = async (userId, resourceId) => {
  const res = await api.post(`/recommender/track/${userId}/${resourceId}`);
  return res.data;
};