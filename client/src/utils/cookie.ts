import Cookies from "js-cookie";

const COOKIE_OPTIONS = {
  secure: true, // Only sent over HTTPS (set to false in dev if needed)
  sameSite: "strict" as const, // CSRF protection
  expires: 7, // 7 days
};

export const TokenCookies = {
  setAccessToken: (token: string) => {
    Cookies.set("access_token", token, {
      ...COOKIE_OPTIONS,
      expires: 1 / 48, // 30 minutes (1/48 of a day)
    });
  },

  setRefreshToken: (token: string) => {
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
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
  },

  hasTokens: (): boolean => {
    return !!Cookies.get("access_token");
  },
};
