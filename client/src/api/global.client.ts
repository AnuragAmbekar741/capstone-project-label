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

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // If 401 Unauthorized, clear auth and redirect to login
    if (error.response?.status === 401) {
      console.warn("Unauthorized - redirecting to login");
      localStorage.removeItem("jwt_token");
      localStorage.removeItem("user");
      window.location.href = "/auth";
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
