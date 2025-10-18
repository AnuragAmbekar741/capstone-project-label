import { useMutation } from "@tanstack/react-query";
import { googleLogin, type GoogleAuthResponse } from "@/api/auth/auth";
import { TokenCookies } from "@/utils/cookie";
import { setAuthToken } from "@/api/global.client";
import { AxiosError } from "axios";

interface GoogleLoginVariables {
  idToken: string;
}

interface GoogleLoginError {
  message: string;
  detail?: string;
}

/**
 * React Query mutation hook for Google OAuth login
 *
 * On success:
 * - Stores access and refresh tokens in cookies
 * - Sets the access token in the global API client
 */
export const useGoogleLogin = () => {
  return useMutation<
    GoogleAuthResponse,
    AxiosError<GoogleLoginError>,
    GoogleLoginVariables
  >({
    mutationFn: async ({ idToken }) => {
      return await googleLogin(idToken);
    },
    onSuccess: (data) => {
      // Store tokens in cookies
      TokenCookies.setAccessToken(data.access_token);
      TokenCookies.setRefreshToken(data.refresh_token);

      // Set token in global API client
      setAuthToken(data.access_token);

      console.log("Authentication successful, tokens stored");
    },
    onError: (error) => {
      console.error("Google login failed:", error);
      // Clear any existing tokens on error
      TokenCookies.clearTokens();
    },
  });
};
