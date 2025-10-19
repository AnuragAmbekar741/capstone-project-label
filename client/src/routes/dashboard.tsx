import { createFileRoute } from "@tanstack/react-router";
import { requireAuth } from "@/utils/route-guards";
import Dashboard from "@/views/dashboard/Dashboard";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: requireAuth,
  component: Dashboard,
});
