// client/src/views/auth/Auth.tsx
import React, { useState } from "react";
// import { Button } from "@/components/ui/button";
import { GoogleLogin } from "@react-oauth/google";

const Auth: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      setIsLoading(true);
      setError(null);

      const credential = credentialResponse?.credential;
      if (!credential) {
        throw new Error("No credential received from Google");
      }

      console.log("Google ID token received:", credential);

      const response = await fetch("http://localhost:8000/auth/google", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id_token: credential }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Backend authentication failed");
      }

      const authData = await response.json();

      // Store JWT token and user data
      localStorage.setItem("jwt_token", authData.jwt_token);
      localStorage.setItem("user", JSON.stringify(authData.user));

      console.log("Authentication successful:", authData.user);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Authentication failed";
      setError(errorMessage);
      console.error("Google OAuth error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError("Google authentication failed");
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Welcome to Label
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to continue to your account
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div className="mt-8">
          <GoogleLogin
            size="large"
            width="360px"
            type="standard"
            theme="outline"
            logo_alignment="left"
            shape="rectangular"
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            ux_mode="popup"
          />
        </div>
      </div>
    </div>
  );
};

export default Auth;
