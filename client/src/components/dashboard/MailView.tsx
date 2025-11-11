import React, { useEffect, useState, useMemo } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/mail-detail/MailDetails";
import { type Mail, emailToMail, mails as dummyMails } from "@/data/mail-data";
import { useEmails } from "@/hooks/imap/useEmails";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { useGetFolder } from "@/hooks/imap/useFolders";
import { getFolderNameFromRoute } from "@/utils/folderMapper";
import { useRouterState } from "@tanstack/react-router";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, RefreshCw, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

export const MailView: React.FC = () => {
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts?.[0]?.id;
  const router = useRouterState();
  const currentPath = router.location.pathname;

  // Fetch folders to map route to folder name
  const { data: folders } = useGetFolder(accountId || "");

  // Get folder name from current route
  const folderName = useMemo(() => {
    return getFolderNameFromRoute(currentPath, folders);
  }, [currentPath, folders]);

  // Fetch emails from API with dynamic folder
  const {
    data: emails,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useEmails({
    accountId: accountId || "",
    folder: folderName,
    limit: 50,
    enabled: !!accountId && !!folderName,
  });

  // Convert EmailResponse[] to Mail[]
  const mails: Mail[] = useMemo(() => {
    if (!emails) return [];
    return emails.map(emailToMail);
  }, [emails]);

  // Use dummy data as fallback if no account connected
  const displayMails = accountId ? mails : dummyMails;

  const [selectedMail, setSelectedMail] = useState<Mail | null>(null);

  // Update selected mail when mails change
  useEffect(() => {
    if (displayMails.length > 0) {
      const existingMail = displayMails.find((m) => m.id === selectedMail?.id);
      if (existingMail) {
        setSelectedMail(existingMail);
      } else {
        setSelectedMail(displayMails[0]);
      }
    }
  }, [displayMails, selectedMail?.id]);

  // Show loading state with skeleton matching the layout
  if (accountId && (isLoading || isRefetching)) {
    return (
      <ResizablePanelGroup direction="horizontal" className="h-full w-full">
        {/* Mail List Panel Skeleton */}
        <ResizablePanel defaultSize={30} minSize={25}>
          <div className="flex flex-col h-full">
            {/* Header skeleton */}
            <div className="p-4 space-y-4 shrink-0">
              <Skeleton className="h-7 w-32" />
              <Skeleton className="h-10 w-full" />
            </div>
            {/* Mail list skeleton */}
            <div className="flex-1 overflow-y-auto min-h-0 p-4 pt-0 scrollbar-hide">
              <div className="flex flex-col gap-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <Skeleton className="h-5 w-32" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Mail Detail Panel Skeleton */}
        <ResizablePanel defaultSize={70}>
          <div className="flex flex-col h-full">
            {/* Toolbar skeleton */}
            <div className="border-b p-4 shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-9 w-9" />
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-9 w-9" />
                  ))}
                </div>
              </div>
            </div>
            {/* Content skeleton */}
            <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                </div>
                <Skeleton className="h-px w-full" />
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-4/5" />
                </div>
              </div>
            </div>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    );
  }

  // Show error state with retry option
  if (accountId && error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4 p-8 max-w-md text-center">
          <div className="rounded-full bg-destructive/10 p-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Failed to load emails</h3>
            <p className="text-sm text-muted-foreground">
              {error.message ||
                "An error occurred while fetching your emails. Please try again."}
            </p>
          </div>
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="gap-2"
            disabled={isRefetching}
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefetching ? "animate-spin" : ""}`}
            />
            {isRefetching ? "Retrying..." : "Try Again"}
          </Button>
        </div>
      </div>
    );
  }

  // Show empty state
  if (accountId && displayMails.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4 p-8 max-w-md text-center">
          <div className="rounded-full bg-muted p-4">
            <Inbox className="h-8 w-8 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">No emails found</h3>
            <p className="text-sm text-muted-foreground">
              This folder is empty. New emails will appear here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Ensure we have a selected mail
  const currentSelectedMail = selectedMail || displayMails[0];

  return (
    <ResizablePanelGroup direction="horizontal" className="h-full w-full">
      {/* Mail List Panel */}
      <ResizablePanel defaultSize={30} minSize={25}>
        <MailList
          mails={displayMails}
          selectedMail={currentSelectedMail}
          onSelectMail={setSelectedMail}
        />
      </ResizablePanel>

      {/* Resizable Handle */}
      <ResizableHandle withHandle />

      {/* Mail Detail Panel */}
      <ResizablePanel defaultSize={70}>
        {currentSelectedMail ? (
          <MailDetail mail={currentSelectedMail} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">Select an email to view</p>
          </div>
        )}
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};
