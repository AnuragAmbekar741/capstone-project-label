import * as React from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { type Mail } from "@/data/mail-data";

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
      <div className="p-4 space-y-4">
        <h1 className="text-xl font-bold">Inbox</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search" className="pl-10" />
        </div>
      </div>

      <Tabs defaultValue="all" className="px-4">
        <TabsList>
          <TabsTrigger value="all">All mail</TabsTrigger>
          <TabsTrigger value="unread">Unread</TabsTrigger>
        </TabsList>
      </Tabs>

      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-2 p-4 pt-0">
          {mails.map((mail) => (
            <button
              key={mail.id}
              className={cn(
                "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent",
                selectedMail.id === mail.id && "bg-muted"
              )}
              onClick={() => onSelectMail(mail)}
            >
              <div className="flex w-full flex-col gap-1">
                <div className="flex items-center">
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">{mail.name}</div>
                    {!mail.read && (
                      <span className="flex h-2 w-2 rounded-full bg-blue-600" />
                    )}
                  </div>
                  <div className="ml-auto text-xs text-muted-foreground">
                    {mail.date}
                  </div>
                </div>
                <div className="text-xs font-medium">{mail.subject}</div>
              </div>
              <div className="line-clamp-2 text-xs text-muted-foreground">
                {mail.text}
              </div>
              {mail.labels.length > 0 && (
                <div className="flex items-center gap-2">
                  {mail.labels.map((label) => (
                    <Badge key={label} variant="secondary">
                      {label}
                    </Badge>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};
