import { createFileRoute, redirect } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";

export const Route = createFileRoute("/$")({
  beforeLoad: () => {
    if (TokenCookies.hasTokens()) {
      throw redirect({
        to: "/dashboard/inbox",
        replace: true,
      });
    } else {
      throw redirect({
        to: "/auth",
        replace: true,
      });
    }
  },
});
