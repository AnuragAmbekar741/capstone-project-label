import React from "react";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/MailDetails";
import { type Mail, emailToMail, mails as dummyMails } from "@/data/mail-data";
import { useEmails } from "@/hooks/imap/useEmails";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Sparkles } from "lucide-react";

export const DashboardContent: React.FC = () => {
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
    enabled: !!accountId,
  });

  // Convert EmailResponse[] to Mail[]
  const mails: Mail[] = React.useMemo(() => {
    if (!emails) return [];
    return emails.map(emailToMail);
  }, [emails]);

  // Use dummy data as fallback if no account connected
  const displayMails = accountId ? mails : dummyMails;

  const [selectedMail, setSelectedMail] = React.useState<Mail | null>(null);
  const [isAiOpen, setIsAiOpen] = React.useState(false);

  // Update selected mail when mails change
  React.useEffect(() => {
    if (displayMails.length > 0) {
      // If current selected mail exists in new list, keep it
      const existingMail = displayMails.find((m) => m.id === selectedMail?.id);
      if (existingMail) {
        setSelectedMail(existingMail);
      } else {
        // Otherwise, select first mail
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
    <div className="flex h-full w-full overflow-hidden">
      {/* Part 1: Email List - Fixed Width */}
      <div className="w-[350px] border-r flex-shrink-0 overflow-hidden flex flex-col">
        <MailList
          mails={displayMails}
          selectedMail={currentSelectedMail}
          onSelectMail={setSelectedMail}
        />
      </div>

      {/* Part 2: Email Details - Flexible Width */}
      <div className="flex-1 min-w-0 overflow-hidden flex flex-col">
        {currentSelectedMail ? (
          <MailDetail mail={currentSelectedMail} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">Select an email to view</p>
          </div>
        )}
      </div>

      {/* Part 3: AI Section - Collapsible */}
      <Collapsible open={isAiOpen} onOpenChange={setIsAiOpen}>
        <div className="flex border-l">
          {/* Collapsible Trigger Button */}
          <div className="flex items-center">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-full rounded-none border-r"
                aria-label={isAiOpen ? "Close AI panel" : "Open AI panel"}
              >
                {isAiOpen ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
          </div>

          {/* AI Panel Content */}
          <CollapsibleContent className="w-[400px] flex-shrink-0 border-l">
            <div className="h-full flex flex-col">
              {/* AI Header */}
              <div className="border-b p-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <h2 className="font-semibold text-lg">AI Assistant</h2>
              </div>

              {/* AI Content Area */}
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    AI features will appear here. This section can help with:
                  </p>
                  <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
                    <li>Email summarization</li>
                    <li>Smart replies</li>
                    <li>Email categorization</li>
                    <li>Action items extraction</li>
                  </ul>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </div>
      </Collapsible>
    </div>
  );
};
