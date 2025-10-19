import { createFileRoute } from "@tanstack/react-router";
import { requireGuest } from "@/utils/route-guards";
import Auth from "@/views/auth/Auth";

export const Route = createFileRoute("/auth")({
  beforeLoad: requireGuest,
  component: Auth,
});
