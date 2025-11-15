import * as React from "react";
import { Trash2, MoreVertical, MessageSquare, Plus, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
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
import { useDeleteEmail } from "@/hooks/imap/useDeleteEmail";
import { useRouterState } from "@tanstack/react-router";
import { getFolderNameFromRoute } from "@/utils/folderMapper";
import { useGetFolder } from "@/hooks/imap/useFolders";
import { toast } from "sonner";
import { DeleteEmailModal } from "@/components/modals/DeleteEmailModal";

interface MailDetailProps {
  mail: Mail;
}

export const MailDetail: React.FC<MailDetailProps> = ({ mail }) => {
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts?.[0]?.id;
  const router = useRouterState();
  const currentPath = router.location.pathname;

  // Get folder name for delete operation
  const { data: folders } = useGetFolder(accountId || "");
  const folderName = React.useMemo(() => {
    return getFolderNameFromRoute(currentPath, folders) || "INBOX";
  }, [currentPath, folders]);

  const [showThread, setShowThread] = React.useState(true);
  const [activeThreadEmailId, setActiveThreadEmailId] = React.useState<
    string | null
  >(mail.id);

  // Delete confirmation modal state
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);

  // Delete email mutation hook
  const deleteEmailMutation = useDeleteEmail();

  // Handle delete email - open confirmation dialog
  const handleDeleteClick = () => {
    if (!accountId) {
      toast.error("No Gmail account connected");
      return;
    }

    const uid = parseInt(mail.id);
    if (isNaN(uid)) {
      toast.error("Invalid email ID");
      return;
    }

    setShowDeleteDialog(true);
  };

  // Confirm and delete email
  const handleConfirmDelete = () => {
    if (!accountId) return;

    const uid = parseInt(mail.id);
    if (isNaN(uid)) return;

    // Use the mutation hook - errors are handled by onError callback
    deleteEmailMutation.mutate(
      {
        accountId,
        uid,
        folder: folderName,
      },
      {
        onSuccess: () => {
          setShowDeleteDialog(false);
        },
      }
    );
  };

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

  // Get user labels (filtered from mail.labels which already excludes system labels)
  const userLabels = React.useMemo(() => {
    return activeEmail.labels || [];
  }, [activeEmail.labels]);

  return (
    <>
      <div className="flex h-full flex-col">
        {/* Action Toolbar */}
        <div className="flex items-center border-b p-4 shrink-0">
          <div className="flex items-center gap-2">
            {/* Labels Section */}
            <div className="flex items-center gap-1.5 ml-1">
              {userLabels.length > 0 ? (
                userLabels.map((label) => (
                  <Badge
                    key={label}
                    variant="secondary"
                    className="text-xs flex items-center gap-1"
                  >
                    <Tag className="h-3 w-3" />
                    {label}
                  </Badge>
                ))
              ) : (
                <Badge
                  variant="outline"
                  className="text-xs px-4 py-1.5 flex items-center gap-1 cursor-pointer hover:bg-accent"
                  title="Add label to this email"
                >
                  <Plus className="h-3 w-3" />
                  Add Label
                </Badge>
              )}
            </div>

            <Separator orientation="vertical" className="h-6" />
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
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDeleteClick}
              disabled={!accountId || deleteEmailMutation.isPending}
              title="Delete email"
            >
              <Trash2 className="h-4 w-4" />
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

      {/* Delete Confirmation Modal */}
      <DeleteEmailModal
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        mail={mail}
        onConfirm={handleConfirmDelete}
        isDeleting={deleteEmailMutation.isPending}
      />
    </>
  );
};
