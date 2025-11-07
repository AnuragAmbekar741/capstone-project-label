import React from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/MailDetails";
import { mails, type Mail } from "@/data/mail-data";
import { useEmails } from "@/hooks/imap/useEmails";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";

export const Inbox: React.FC = () => {
  const [selectedMail, setSelectedMail] = React.useState<Mail>(mails[0]);
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts[0]?.id;
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
  console.log("Emails:", emails);
  console.log("Is Loading:", isLoading);
  console.log("Error:", error);
  return (
    <ResizablePanelGroup direction="horizontal" className="h-full">
      {/* Mail List Panel */}
      <ResizablePanel defaultSize={30} minSize={25}>
        <MailList
          mails={mails}
          selectedMail={selectedMail}
          onSelectMail={setSelectedMail}
        />
      </ResizablePanel>

      {/* Resizable Handle */}
      <ResizableHandle withHandle />

      {/* Mail Detail Panel */}
      <ResizablePanel defaultSize={70}>
        <MailDetail mail={selectedMail} />
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};
