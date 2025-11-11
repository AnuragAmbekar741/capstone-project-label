import { createFileRoute } from "@tanstack/react-router";
import { DashboardContent } from "@/components/layout/DashboardContent";

export const Route = createFileRoute("/dashboard/inbox")({
  component: DashboardContent,
});
