// New utility file
import { jwtDecode } from "jwt-decode";

interface JWTPayload {
  exp: number; // Expiration timestamp
  sub: string;
  email: string;
  type: string;
}

export const isTokenExpiringSoon = (
  token: string,
  bufferSeconds: number = 60
): boolean => {
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    const expirationTime = decoded.exp * 1000;
    const now = Date.now();
    const timeUntilExpiry = expirationTime - now;
    return timeUntilExpiry <= bufferSeconds * 1000;
  } catch {
    return true;
  }
};

export const isTokenExpired = (token: string): boolean => {
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    const expirationTime = decoded.exp * 1000;
    return Date.now() >= expirationTime;
  } catch {
    return true;
  }
};
