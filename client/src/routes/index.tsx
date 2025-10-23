import { createFileRoute, redirect } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    // If user has tokens, go to dashboard, otherwise to landing
    if (TokenCookies.hasTokens()) {
      throw redirect({ to: "/dashboard/inbox" });
    } else {
      throw redirect({ to: "/landing" });
    }
  },
});
