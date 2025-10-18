import { post } from "../request";

export interface GoogleLoginRequest {
  id_token: string;
}

export interface GoogleAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
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
