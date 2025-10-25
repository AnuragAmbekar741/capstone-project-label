import { TokenCookies } from "@/utils/cookie";
import { isTokenExpiringSoon } from "@/utils/tokens";
import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

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

// Initialize Authorization header if access token exists in cookies
const initializeAuth = () => {
  const accessToken = TokenCookies.getAccessToken();
  if (accessToken) {
    apiClient.defaults.headers.common["Authorization"] =
      `Bearer ${accessToken}`;
    console.log("✅ Authorization header initialized from cookies");
  }
};

// Run on module load
initializeAuth();

// Flag to prevent multiple simultaneous refresh requests
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

// REQUEST INTERCEPTOR - Proactively refresh before expiration
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Skip for refresh endpoint
    if (
      config.url?.includes("/auth/refresh") ||
      config.url?.includes("/auth/google")
    ) {
      return config;
    }

    const accessToken = TokenCookies.getAccessToken();

    // If token is expiring soon (within 60 seconds), refresh it
    if (accessToken && isTokenExpiringSoon(accessToken, 60)) {
      // If already refreshing, wait for that promise
      if (isRefreshing && refreshPromise) {
        const newToken = await refreshPromise;
        config.headers["Authorization"] = `Bearer ${newToken}`;
        return config;
      }

      // Start refresh
      isRefreshing = true;
      refreshPromise = (async () => {
        try {
          const refreshToken = TokenCookies.getRefreshToken();

          if (!refreshToken) {
            throw new Error("No refresh token available");
          }

          const response = await axios.post(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken },
            {
              headers: { "Content-Type": "application/json" },
            }
          );

          const { access_token, refresh_token: new_refresh_token } =
            response.data;

          TokenCookies.setAccessToken(access_token);
          TokenCookies.setRefreshToken(new_refresh_token);
          apiClient.defaults.headers.common["Authorization"] =
            `Bearer ${access_token}`;

          return access_token;
        } catch (error) {
          console.error("❌ Proactive refresh failed:", error);
          TokenCookies.clearTokens();
          if (!window.location.pathname.includes("/auth")) {
            window.location.href = "/auth";
          }
          throw error;
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
      })();

      const newToken = await refreshPromise;
      config.headers["Authorization"] = `Bearer ${newToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// RESPONSE INTERCEPTOR - Simple fallback for any 401s
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status && [401, 403].includes(error.response.status)) {
      console.warn("❌ 401 Unauthorized - clearing tokens");
      TokenCookies.clearTokens();

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
