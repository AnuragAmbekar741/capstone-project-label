import { createFileRoute, Outlet } from "@tanstack/react-router";
import { requireAuth } from "@/utils/route-guards";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-bar/AppSidebar";
import { AppBar } from "@/components/app-bar/AppBar";

function DashboardLayout() {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar />

        <div className="flex-1 flex flex-col">
          <AppBar />

          {/* Child routes render here */}
          <div className="flex-1 overflow-hidden">
            <Outlet />
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
}

export const Route = createFileRoute("/dashboard/")({
  beforeLoad: requireAuth,
  component: DashboardLayout,
});
