import { redirect } from "@tanstack/react-router";
import { TokenCookies } from "./cookie";

/**
 * Protect routes that require authentication
 * Redirects to /auth if user is not authenticated
 */
export const requireAuth = async () => {
  if (!TokenCookies.hasTokens()) {
    throw redirect({ to: "/auth" });
  }
};

/**
 * Protect auth pages from authenticated users
 * Redirects to /dashboard if user is already authenticated
 */
export const requireGuest = async () => {
  if (TokenCookies.hasTokens()) {
    throw redirect({ to: "/dashboard" });
  }
};
