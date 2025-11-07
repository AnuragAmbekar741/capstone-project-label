import * as React from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { type Mail } from "@/data/mail-data";
import { MailCard } from "./MailCard";

interface MailListProps {
  mails: Mail[];
  selectedMail: Mail;
  onSelectMail: (mail: Mail) => void;
}

export const MailList: React.FC<MailListProps> = ({
  mails,
  selectedMail,
  onSelectMail,
}) => {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 space-y-4 shrink-0">
        <h1 className="text-xl font-bold">Inbox</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search" className="pl-10" />
        </div>
      </div>

      <Tabs defaultValue="all" className="px-4 shrink-0">
        <TabsList>
          <TabsTrigger value="all">All mail</TabsTrigger>
          <TabsTrigger value="unread">Unread</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Scrollable mail list */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="flex flex-col gap-2 p-4 pt-0">
          {mails.map((mail) => (
            <MailCard
              key={mail.id}
              mail={mail}
              isSelected={selectedMail.id === mail.id}
              onClick={() => onSelectMail(mail)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
