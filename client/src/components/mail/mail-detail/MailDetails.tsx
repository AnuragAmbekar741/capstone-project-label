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
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { type Mail } from "@/data/mail-data";
import DOMPurify from "dompurify";
import {
  EMAIL_SANITIZE_CONFIG,
  EMAIL_CONTENT_CLASSES,
  EMAIL_CONTENT_STYLES,
  EMAIL_DROPDOWN_ITEMS,
  EMAIL_CONSTANTS,
} from "./mailDetails.config";
import { useThreadEmails } from "@/hooks/imap/useThreadEmails";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { ThreadEmailItem } from "./ThreadEmailItem";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

interface MailDetailProps {
  mail: Mail;
}

export const MailDetail: React.FC<MailDetailProps> = ({ mail }) => {
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts?.[0]?.id;
  const [showThread, setShowThread] = React.useState(true);
  const [activeThreadEmailId, setActiveThreadEmailId] = React.useState<
    string | null
  >(mail.id);

  // Fetch thread emails if this email is part of a thread
  const { data: threadEmails, isLoading: threadLoading } = useThreadEmails({
    accountId: accountId || "",
    mail,
    enabled: !!accountId && (mail.isThread || !!mail.messageId),
  });

  // Get the active email (either current mail or selected thread email)
  const activeEmail = React.useMemo(() => {
    if (threadEmails && activeThreadEmailId) {
      return threadEmails.find((e) => e.id === activeThreadEmailId) || mail;
    }
    return mail;
  }, [threadEmails, activeThreadEmailId, mail]);

  // Get HTML content if available, otherwise use text
  const emailContent = React.useMemo(() => {
    if (activeEmail.bodyHtml) {
      return DOMPurify.sanitize(activeEmail.bodyHtml, EMAIL_SANITIZE_CONFIG);
    }

    if (activeEmail.bodyText) {
      const textWithBreaks = activeEmail.bodyText.replace(
        /\n/g,
        EMAIL_CONSTANTS.LINE_BREAK_REPLACEMENT
      );
      return DOMPurify.sanitize(textWithBreaks);
    }

    return EMAIL_CONSTANTS.EMPTY_CONTENT;
  }, [activeEmail.bodyHtml, activeEmail.bodyText]);

  const hasThread = threadEmails && threadEmails.length > 1;

  return (
    <div className="flex h-full flex-col">
      {/* Action Toolbar */}
      <div className="flex items-center border-b p-4 shrink-0">
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
          {hasThread && (
            <>
              <Separator orientation="vertical" className="h-6" />
              <Button
                variant={showThread ? "secondary" : "ghost"}
                size="icon"
                onClick={() => setShowThread(!showThread)}
                title={showThread ? "Hide thread" : "Show thread"}
              >
                <MessageSquare className="h-4 w-4" />
              </Button>
            </>
          )}
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
            {EMAIL_DROPDOWN_ITEMS.map((item) => (
              <DropdownMenuItem key={item.action}>
                {item.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Mail Content - scrollbar hidden */}
      <div className="flex-1 overflow-hidden min-w-0 flex">
        {/* Thread Sidebar */}
        {hasThread && showThread && (
          <>
            <div className="w-80 border-r shrink-0 flex flex-col">
              <div className="p-3 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">
                    Thread ({threadEmails.length})
                  </h3>
                  {threadLoading && <Skeleton className="h-4 w-16" />}
                </div>
              </div>
              <ScrollArea className="flex-1">
                <div className="divide-y">
                  {threadEmails.map((threadMail) => (
                    <ThreadEmailItem
                      key={threadMail.id}
                      mail={threadMail}
                      isActive={threadMail.id === activeThreadEmailId}
                      onClick={() => setActiveThreadEmailId(threadMail.id)}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>
            <Separator orientation="vertical" />
          </>
        )}

        {/* Main Email Content */}
        <div className="flex-1 overflow-y-auto scrollbar-hide min-w-0">
          <div className="flex flex-col gap-4 p-6 max-w-full">
            <div className="flex items-start justify-between min-w-0">
              <div className="flex items-start gap-4 min-w-0 flex-1">
                <Avatar className="shrink-0">
                  <AvatarFallback>
                    {activeEmail.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="grid gap-1 min-w-0 flex-1">
                  <div className="font-semibold break-words">
                    {activeEmail.subject}
                  </div>
                  <div className="text-sm text-muted-foreground break-words">
                    Reply-To: {activeEmail.email}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {activeEmail.date}
                  </div>
                </div>
              </div>
            </div>
            <Separator />
            {/* Email content isolated in a scoped container */}
            <div
              className={EMAIL_CONTENT_CLASSES.wrapper}
              style={EMAIL_CONTENT_STYLES.wrapper}
            >
              <div
                className={EMAIL_CONTENT_CLASSES.content}
                dangerouslySetInnerHTML={{ __html: emailContent }}
                key={activeEmail.id}
                style={EMAIL_CONTENT_STYLES.content}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Reply Footer */}
      <Separator />
      <div className="p-4 shrink-0">
        <div className="grid gap-4">
          <Button size="sm" className="ml-auto">
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};
