import { createFileRoute, redirect } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";
import { LandingPage } from "@/views/landing-page/LandingPage";

export const Route = createFileRoute("/landing")({
  beforeLoad: async () => {
    if (TokenCookies.hasTokens()) {
      throw redirect({ to: "/dashboard" });
    }
  },
  component: LandingPage,
});
