import { createFileRoute, Outlet } from "@tanstack/react-router";
import { requireAuth } from "@/utils/route-guards";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { gmailAccountsQueryOptions } from "@/hooks/gmail/useGmailAccount";
// Search params type
type DashboardSearch = {
  gmail_connected?: string;
  gmail_error?: string;
};

function Dashboard() {
  return (
    <DashboardLayout>
      <Outlet />
    </DashboardLayout>
  );
}

export const Route = createFileRoute("/dashboard")({
  beforeLoad: () => {
    requireAuth();
    return gmailAccountsQueryOptions;
  },
  validateSearch: (search: Record<string, unknown>): DashboardSearch => {
    return {
      gmail_connected:
        typeof search.gmail_connected === "string"
          ? search.gmail_connected
          : undefined,
      gmail_error:
        typeof search.gmail_error === "string" ? search.gmail_error : undefined,
    };
  },
  component: Dashboard,
});
