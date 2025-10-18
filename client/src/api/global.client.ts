import { TokenCookies } from "@/utils/cookie";
import axios, { AxiosError, type AxiosInstance } from "axios";

//Base API Configuration

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_TIMEOUT = 15000; // 30 seconds

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// RESPONSE INTERCEPTOR - Handle ONLY 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // ONLY handle 401 Unauthorized (not 404, 500, etc.)
    if (error.response?.status && [401, 403].includes(error.response.status)) {
      console.warn("❌ 401 Unauthorized - clearing tokens");
      TokenCookies.clearTokens();

      // Avoid redirect loop - only redirect if not already on auth page
      if (!window.location.pathname.includes("/auth")) {
        window.location.href = "/auth";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Set the authorization token in the API client
 */
export const setAuthToken = (token: string) => {
  apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
};

/**
 * Clear the authorization token from the API client
 */
export const clearAuthToken = () => {
  delete apiClient.defaults.headers.common["Authorization"];
};

export default apiClient;
