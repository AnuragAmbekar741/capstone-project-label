// import { useState, useCallback, useEffect } from "react";
// import { GoogleLogin } from "@react-oauth/google";

// interface User {
//   id: number;
//   google_id: string;
//   email: string;
//   name: string;
//   picture?: string;
//   is_active: boolean;
//   created_at: string;
//   updated_at: string;
// }

// interface AuthResponse {
//   jwt_token: string;
//   user: User;
// }

// interface UseGoogleAuthReturn {
//   isLoading: boolean;
//   error: string | null;
//   user: User | null;
//   isAuthenticated: boolean;
//   signIn: () => void;
//   signOut: () => void;
//   clearError: () => void;
//   GoogleLoginComponent: () => JSX.Element;
// }

// export const useGoogleAuth = (): UseGoogleAuthReturn => {
//   const [isLoading, setIsLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [user, setUser] = useState<User | null>(null);

//   const isAuthenticated = !!user || !!localStorage.getItem("jwt_token");

//   const handleGoogleSuccess = async (credentialResponse: any) => {
//     try {
//       setIsLoading(true);
//       setError(null);

//       const credential = credentialResponse?.credential;
//       if (!credential) {
//         throw new Error("No credential received from Google");
//       }

//       console.log("Google ID token received:", credential);

//       const response = await fetch("http://localhost:8000/auth/google", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ id_token: credential }),
//       });

//       if (!response.ok) {
//         const errorData = await response.json();
//         throw new Error(errorData.detail || "Backend authentication failed");
//       }

//       const authData: AuthResponse = await response.json();

//       // Store JWT token and user data
//       localStorage.setItem("jwt_token", authData.jwt_token);
//       localStorage.setItem("user", JSON.stringify(authData.user));

//       // Update state
//       setUser(authData.user);

//       console.log("Authentication successful:", authData.user);
//     } catch (err) {
//       const errorMessage =
//         err instanceof Error ? err.message : "Authentication failed";
//       setError(errorMessage);
//       console.error("Google OAuth error:", err);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const handleGoogleError = () => {
//     setError("Google authentication failed");
//     setIsLoading(false);
//   };

//   const signIn = useCallback(() => {
//     // This will be handled by the GoogleLogin component
//   }, []);

//   const signOut = useCallback(() => {
//     localStorage.removeItem("jwt_token");
//     localStorage.removeItem("user");
//     setUser(null);
//     setError(null);
//     console.log("User signed out");
//   }, []);

//   const clearError = useCallback(() => {
//     setError(null);
//   }, []);

// const GoogleLoginComponent = useCallback(() => {
//   return (
//     <GoogleLogin
//       size="large"
//       width="360px"
//       type="standard"
//       theme="outline"
//       logo_alignment="left"
//       shape="rectangular"
//       onSuccess={handleGoogleSuccess}
//       onError={handleGoogleError}
//       ux_mode="popup"
//     />
//   );
// }, []);

//   useEffect(() => {
//     const storedUser = localStorage.getItem("user");
//     if (storedUser) {
//       try {
//         setUser(JSON.parse(storedUser));
//       } catch (err) {
//         console.error("Failed to parse stored user:", err);
//         localStorage.removeItem("user");
//         localStorage.removeItem("jwt_token");
//       }
//     }
//   }, []);

//   return {
//     isLoading,
//     error,
//     user,
//     isAuthenticated,
//     signIn,
//     signOut,
//     clearError,
//     GoogleLoginComponent,
//   };
// };
