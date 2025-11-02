import React, { type PropsWithChildren, useEffect, useState } from "react";
import { SidebarProvider } from "../ui/sidebar";
import { AppSidebar } from "../app-bar/AppSidebar";
import { AppBar } from "../app-bar/AppBar";
import { ConnectGmailModal } from "../modals/ConnectGmailModal";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { useRouterState, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const DashboardLayout: React.FC<PropsWithChildren> = ({ children }) => {
  const router = useRouterState();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const search = router.location.search as {
    gmail_connected?: string;
    gmail_error?: string;
  };

  // Use hook to get Gmail accounts
  const { data: gmailAccountsData, isLoading, refetch } = useGmailAccounts();
  const [showModal, setShowModal] = useState(false);

  // Check if user has connected Gmail accounts
  const hasConnectedAccounts =
    gmailAccountsData?.accounts && gmailAccountsData.accounts.length > 0;

  // Show modal if no Gmail accounts connected (after data loads)
  useEffect(() => {
    if (!isLoading && !hasConnectedAccounts && !showModal) {
      // Small delay for smooth transition after login
      const timer = setTimeout(() => {
        setShowModal(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isLoading, hasConnectedAccounts, showModal]);

  // Handle OAuth callback success/error messages
  useEffect(() => {
    if (search.gmail_connected) {
      // Invalidate and refetch accounts
      queryClient.invalidateQueries({ queryKey: ["gmailAccounts"] });
      refetch();

      toast.success("Gmail account connected successfully!");
      setShowModal(false);

      // Clean up URL after a short delay
      setTimeout(() => {
        navigate({
          to: "/dashboard",
          search: {},
          replace: true,
        });
      }, 100);
    }

    if (search.gmail_error) {
      const errorMsg =
        search.gmail_error === "invalid_state"
          ? "Invalid connection request. Please try again."
          : search.gmail_error === "missing_code"
            ? "Authorization failed. Please try again."
            : "Failed to connect Gmail account. Please try again.";

      toast.error(errorMsg);

      // Clean up URL
      setTimeout(() => {
        navigate({
          to: "/dashboard",
          search: {},
          replace: true,
        });
      }, 100);
    }
  }, [
    search.gmail_connected,
    search.gmail_error,
    queryClient,
    refetch,
    navigate,
  ]);

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
