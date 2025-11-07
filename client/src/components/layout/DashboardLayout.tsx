import React, { type PropsWithChildren, useState } from "react";
import { SidebarProvider } from "../ui/sidebar";
import { AppSidebar } from "../app-bar/AppSidebar";
import { AppBar } from "../app-bar/AppBar";
import { ConnectGmailModal } from "../modals/ConnectGmailModal";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
const DashboardLayout: React.FC<PropsWithChildren> = ({ children }) => {
  // Use hook to get Gmail accounts
  const { data: gmailAccountsData } = useGmailAccounts();

  // Check if user has connected Gmail accounts
  const hasConnectedAccounts =
    gmailAccountsData?.accounts && gmailAccountsData.accounts.length > 0;

  const [showModal, setShowModal] = useState(!hasConnectedAccounts);

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col">
          <AppBar />
          <div className="flex-1 overflow-hidden">{children}</div>
        </div>
      </div>

      {/* Gmail Connection Modal */}
      <ConnectGmailModal open={showModal} onOpenChange={setShowModal} />
    </SidebarProvider>
  );
};

export default DashboardLayout;
