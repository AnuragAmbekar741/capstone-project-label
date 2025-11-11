import * as React from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { AppSidebar } from "@/components/app-bar/AppSidebar";
import { AppBar } from "@/components/app-bar/AppBar";
import { MailList } from "@/components/mail/MailList";
import { MailDetail } from "@/components/mail/mail-detail/MailDetails";
import { mails } from "@/data/mail-data";

export default function Dashboard() {
  const [selectedMail, setSelectedMail] = React.useState(mails[0]);

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar />

        <div className="flex-1 flex flex-col">
          <AppBar />

          <ResizablePanelGroup direction="horizontal" className="flex-1">
            <ResizablePanel defaultSize={30} minSize={25}>
              <MailList
                mails={mails}
                selectedMail={selectedMail}
                onSelectMail={setSelectedMail}
              />
            </ResizablePanel>

            <ResizableHandle withHandle />

            <ResizablePanel defaultSize={70}>
              <MailDetail mail={selectedMail} />
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>
    </SidebarProvider>
  );
}
