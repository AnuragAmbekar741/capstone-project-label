import React, { useEffect, useState, useMemo } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/MailDetails";
import { type Mail, emailToMail, mails as dummyMails } from "@/data/mail-data";
import { useEmails } from "@/hooks/imap/useEmails";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { Skeleton } from "@/components/ui/skeleton";

export const Inbox: React.FC = () => {
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts?.[0]?.id;

  // Fetch emails from API
  const {
    data: emails,
    isLoading,
    error,
  } = useEmails({
    accountId: accountId || "",
    folder: "INBOX",
    limit: 50,
    // sinceDate: todayDate,
    enabled: !!accountId,
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

  // Show loading state
  if (accountId && isLoading) {
    return (
      <div className="flex flex-col gap-4 p-4 h-full">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  // Show error state
  if (accountId && error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">
          Error loading emails: {error.message}
        </p>
      </div>
    );
  }

  // Show empty state
  if (accountId && displayMails.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">No emails found</p>
      </div>
    );
  }

  // Ensure we have a selected mail
  const currentSelectedMail = selectedMail || displayMails[0];

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="h-full lg:max-w-[82vw] 2xl:max-w-[87vw]"
    >
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
