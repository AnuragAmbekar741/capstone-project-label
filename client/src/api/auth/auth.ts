import { get, post } from "../request";

export interface GoogleLoginRequest {
  id_token: string;
}

export interface GoogleAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  google_id: string;
  created_at: string;
  updated_at: string;
}

export const googleLogin = async (
  idToken: string
): Promise<GoogleAuthResponse> => {
  return await post<GoogleAuthResponse, GoogleLoginRequest>(
    "/auth/google",
    { id_token: idToken },
    { sendToken: false }
  );
};

export const getCurrentUser = async (): Promise<UserProfile> => {
  return await get<UserProfile>("/auth/me");
};
