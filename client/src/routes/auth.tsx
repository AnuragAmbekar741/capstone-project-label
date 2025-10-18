import { createFileRoute } from "@tanstack/react-router";
import Auth from "@/views/auth/Auth";

export const Route = createFileRoute("/auth")({
  component: Auth,
});
