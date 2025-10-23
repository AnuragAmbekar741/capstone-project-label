import React from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/MailDetails";
import { mails, type Mail } from "@/data/mail-data";

export const Inbox: React.FC = () => {
  const [selectedMail, setSelectedMail] = React.useState<Mail>(mails[0]);

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
