import { useState, useCallback, useEffect } from "react";
import { useGoogleLogin } from "@react-oauth/google";

interface User {
  id: number;
  google_id: string;
  email: string;
  name: string;
  picture?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthResponse {
  jwt_token: string;
  user: User;
}

interface UseGoogleAuthReturn {
  isLoading: boolean;
  error: string | null;
  user: User | null;
  isAuthenticated: boolean;
  signIn: () => void;
  signOut: () => void;
  clearError: () => void;
}

export const useGoogleAuth = (): UseGoogleAuthReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  const isAuthenticated = !!user || !!localStorage.getItem("jwt_token");

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        setIsLoading(true);
        setError(null);

        console.log("Google token received:", tokenResponse);

        // Send token to backend
        const response = await fetch("http://localhost:8000/auth/google", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ access_token: tokenResponse.access_token }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Backend authentication failed");
        }

        const authData: AuthResponse = await response.json();

        // Store JWT token and user data
        localStorage.setItem("jwt_token", authData.jwt_token);
        localStorage.setItem("user", JSON.stringify(authData.user));

        // Update state
        setUser(authData.user);

        console.log("Authentication successful:", authData.user);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Authentication failed";
        setError(errorMessage);
        console.error("Google OAuth error:", err);
      } finally {
        setIsLoading(false);
      }
    },
    onError: (error) => {
      setError("Google authentication failed");
      console.error("Google OAuth error:", error);
      setIsLoading(false);
    },
  });

  const signIn = useCallback(() => {
    googleLogin();
  }, [googleLogin]);

  const signOut = useCallback(() => {
    localStorage.removeItem("jwt_token");
    localStorage.removeItem("user");
    setUser(null);
    setError(null);
    console.log("User signed out");
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (err) {
        console.error("Failed to parse stored user:", err);
        localStorage.removeItem("user");
        localStorage.removeItem("jwt_token");
      }
    }
  }, []);

  return {
    isLoading,
    error,
    user,
    isAuthenticated,
    signIn,
    signOut,
    clearError,
  };
};
