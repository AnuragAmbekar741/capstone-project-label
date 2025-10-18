import { createFileRoute, redirect } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";
import Auth from "@/views/auth/Auth";

export const Route = createFileRoute("/auth")({
  beforeLoad: async () => {
    if (TokenCookies.hasTokens()) {
      throw redirect({ to: "/dashboard" });
    }
  },
  component: Auth,
});
