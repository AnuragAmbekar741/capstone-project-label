import React, { type PropsWithChildren } from "react";
import { SidebarProvider } from "../ui/sidebar";
import { AppSidebar } from "../app-bar/AppSidebar";
import { AppBar } from "../app-bar/AppBar";

const DashboardLayout: React.FC<PropsWithChildren> = ({ children }) => {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar />

        <div className="flex-1 flex flex-col">
          <AppBar />

          {/* Child routes render here */}
          <div className="flex-1 overflow-hidden">{children}</div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default DashboardLayout;
