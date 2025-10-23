import { createFileRoute, Outlet } from "@tanstack/react-router";
import { requireAuth } from "@/utils/route-guards";
import DashboardLayout from "@/components/layout/DashboardLayout";

function Dashboard() {
  return (
    <DashboardLayout>
      <Outlet />
    </DashboardLayout>
  );
}

export const Route = createFileRoute("/dashboard")({
  beforeLoad: requireAuth,
  component: Dashboard,
});
