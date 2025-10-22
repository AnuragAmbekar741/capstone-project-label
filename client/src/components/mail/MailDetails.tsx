import * as React from "react";
import {
  Archive,
  ArchiveX,
  Trash2,
  Clock,
  Reply,
  ReplyAll,
  Forward,
  MoreVertical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { type Mail } from "@/data/mail-data";

interface MailDetailProps {
  mail: Mail;
}

export const MailDetail: React.FC<MailDetailProps> = ({ mail }) => {
  return (
    <div className="flex h-full flex-col">
      {/* Action Toolbar */}
      <div className="flex items-center border-b p-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Archive className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <ArchiveX className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <Trash2 className="h-4 w-4" />
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <Button variant="ghost" size="icon">
            <Clock className="h-4 w-4" />
          </Button>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Reply className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <ReplyAll className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <Forward className="h-4 w-4" />
          </Button>
        </div>
        <Separator orientation="vertical" className="mx-2 h-6" />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Mark as unread</DropdownMenuItem>
            <DropdownMenuItem>Star thread</DropdownMenuItem>
            <DropdownMenuItem>Add label</DropdownMenuItem>
            <DropdownMenuItem>Mute thread</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Mail Content */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <Avatar>
                <AvatarFallback>
                  {mail.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
              <div className="grid gap-1">
                <div className="font-semibold">{mail.subject}</div>
                <div className="text-sm text-muted-foreground">
                  Reply-To: {mail.email}
                </div>
                <div className="text-sm text-muted-foreground">{mail.date}</div>
              </div>
            </div>
          </div>
          <Separator />
          <div className="text-sm">
            <p>{mail.text}</p>
          </div>
        </div>
      </ScrollArea>

      {/* Reply Footer */}
      <Separator />
      <div className="p-4">
        <div className="grid gap-4">
          <Button size="sm" className="ml-auto">
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};
