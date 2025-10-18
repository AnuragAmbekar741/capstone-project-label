import { createFileRoute, redirect } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";
import Dashboard from "@/views/dashboard/Dashboard";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: async () => {
    if (!TokenCookies.hasTokens()) {
      throw redirect({ to: "/auth" });
    }
  },
  component: Dashboard,
});
