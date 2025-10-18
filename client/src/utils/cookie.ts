import Cookies from "js-cookie";

// Only use secure cookies in production (HTTPS)
const isProduction = import.meta.env.PROD;

const COOKIE_OPTIONS = {
  secure: isProduction, // false in dev, true in production
  sameSite: "strict" as const,
  expires: 7,
};

export const TokenCookies = {
  setAccessToken: (token: string) => {
    console.log("🍪 Setting access token");
    Cookies.set("access_token", token, {
      ...COOKIE_OPTIONS,
      expires: 1 / 48, // 30 minutes
    });
  },

  setRefreshToken: (token: string) => {
    console.log("🍪 Setting refresh token");
    Cookies.set("refresh_token", token, {
      ...COOKIE_OPTIONS,
      expires: 7, // 7 days
    });
  },

  getAccessToken: (): string | undefined => {
    return Cookies.get("access_token");
  },

  getRefreshToken: (): string | undefined => {
    return Cookies.get("refresh_token");
  },

  clearTokens: () => {
    console.log("🍪 Clearing tokens");
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
  },

  hasTokens: (): boolean => {
    const hasToken = !!Cookies.get("access_token");
    console.log("🍪 Has tokens:", hasToken);
    return hasToken;
  },
};
