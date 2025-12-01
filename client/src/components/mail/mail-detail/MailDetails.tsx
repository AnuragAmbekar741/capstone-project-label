import * as React from "react";
import { Trash2, MoreVertical, Sparkles, Tag } from "lucide-react";
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
  // EMAIL_SANITIZE_CONFIG,
  EMAIL_CONTENT_CLASSES,
  EMAIL_CONTENT_STYLES,
  EMAIL_DROPDOWN_ITEMS,
  EMAIL_CONSTANTS,
  sanitizeEmailContent,
} from "./mailDetails.config";
import { useDeleteEmail } from "@/hooks/imap/useDeleteEmail";
import { useRouterState } from "@tanstack/react-router";
import { getFolderNameFromRoute } from "@/utils/folderMapper";
import { useGetFolder } from "@/hooks/imap/useFolders";
import { toast } from "sonner";
import { DeleteEmailModal } from "@/components/modals/DeleteEmailModal";
import { useCreateLabel } from "@/hooks/imap/useCreateLabel";
import { CreateLabelModal } from "@/components/modals/CreateLabelModal";
import { useSuggestLabel } from "@/hooks/imap/useSuggestLabel";
import { type SuggestLabelResponse } from "@/api/imap/imap";
import { useAddLabelToEmail } from "@/hooks/imap/useAddLabelToEmail";
import { AutoLabelModal } from "@/components/modals/AutoLabelModal";
import { AxiosError } from "axios";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";

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

  // Delete confirmation modal state
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);

  // Delete email mutation hook
  const deleteEmailMutation = useDeleteEmail();

  const createLabelMutation = useCreateLabel();
  const [showCreateLabelModal, setShowCreateLabelModal] = React.useState(false);

  const suggestLabelMutation = useSuggestLabel();
  const addLabelMutation = useAddLabelToEmail(() => {
    // Close modal on successful label application
    setShowAutoLabelModal(false);
    setLabelResult(null);
  });
  const [showAutoLabelModal, setShowAutoLabelModal] = React.useState(false);
  const [labelResult, setLabelResult] =
    React.useState<SuggestLabelResponse | null>(null);
  const [isLabeling, setIsLabeling] = React.useState(false);

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

  // Get HTML content if available, otherwise use text
  const emailContent = React.useMemo(() => {
    if (mail.bodyHtml) {
      return sanitizeEmailContent(mail.bodyHtml);
    }

    if (mail.bodyText) {
      const textWithBreaks = mail.bodyText.replace(
        /\n/g,
        EMAIL_CONSTANTS.LINE_BREAK_REPLACEMENT
      );
      return DOMPurify.sanitize(textWithBreaks);
    }

    return EMAIL_CONSTANTS.EMPTY_CONTENT;
  }, [mail.bodyHtml, mail.bodyText]);

  // Get user labels (filtered from mail.labels which already excludes system labels)
  const userLabels = React.useMemo(() => {
    return mail.labels || [];
  }, [mail.labels]);

  const handleDropdownAction = (action: string) => {
    if (action === "add-label") {
      setShowCreateLabelModal(true);
    }
    // Handle other actions...
  };

  // Add this helper function before the component or inside it
  const getEmailBodyText = (email: Mail): string => {
    // Prefer text body
    let body = email.bodyText || "";

    // If no text body, extract text from HTML
    if (!body || !body.trim()) {
      if (email.bodyHtml) {
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = email.bodyHtml;
        body = tempDiv.textContent || tempDiv.innerText || "";
      }
    }

    return body.trim();
  };

  // Handle Auto Label button click
  const handleAutoLabel = async () => {
    if (!accountId) {
      toast.error("No Gmail account connected");
      return;
    }

    const emailBody = getEmailBodyText(mail);

    // Skip if no body content
    if (!emailBody) {
      toast.error("Email has no body content to analyze");
      return;
    }

    setIsLabeling(true);
    setShowAutoLabelModal(true);

    try {
      const response = await suggestLabelMutation.mutateAsync({
        accountId,
        request: {
          email_id: mail.id,
          subject: mail.subject || "",
          body: emailBody,
        },
      });

      // Convert single response to array format for modal (if modal expects array)
      setLabelResult(response);
    } catch (error) {
      const axiosError = error as AxiosError<{
        detail?: string;
        message?: string;
      }>;
      console.error("Error suggesting label:", {
        message: axiosError.message,
        response: axiosError.response?.data,
        status: axiosError.response?.status,
      });
      setShowAutoLabelModal(false);
    } finally {
      setIsLabeling(false);
    }
  };

  // Handle applying labels
  const handleApplyLabels = async () => {
    if (!accountId || !labelResult || !mail) return;

    const uid = parseInt(mail.id);
    if (isNaN(uid)) {
      toast.error("Invalid email ID");
      return;
    }

    try {
      await addLabelMutation.mutateAsync({
        accountId,
        uid: uid,
        label: labelResult.label,
        folder: "INBOX",
      });
      // Modal closing is handled by hook's onSuccess callback
    } catch (error) {
      const axiosError = error as AxiosError<{
        detail?: string;
        message?: string;
      }>;
      console.error("Error suggesting label:", {
        message: axiosError.message,
        response: axiosError.response?.data,
        status: axiosError.response?.status,
      });
    }
  };

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
                <Button
                  variant="default"
                  size="sm"
                  className="text-xs px-4 py-1.5 h-auto bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 active:scale-95 font-semibold"
                  title="Auto label this email"
                  onClick={handleAutoLabel}
                  disabled={isLabeling || !accountId}
                >
                  <Sparkles
                    className={`h-3 w-3 ${isLabeling ? "animate-spin" : ""}`}
                  />
                  {isLabeling ? "Labeling..." : "Auto Label"}
                </Button>
              )}
            </div>

            <Separator orientation="vertical" className="h-6" />
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
                <DropdownMenuItem
                  key={item.action}
                  onClick={() => handleDropdownAction(item.action)}
                >
                  {item.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Mail Content */}
        <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] min-w-0">
          <div className="flex flex-col gap-4 p-6 max-w-full">
            <div className="flex items-start justify-between min-w-0">
              <div className="flex items-start gap-4 min-w-0 flex-1">
                <Avatar className="shrink-0">
                  <AvatarFallback>
                    {mail.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="grid gap-1 min-w-0 flex-1">
                  <div className="font-semibold break-words">
                    {mail.subject}
                  </div>
                  <div className="text-sm text-muted-foreground break-words">
                    Reply-To: {mail.email}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {mail.date}
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
                key={mail.id}
                style={EMAIL_CONTENT_STYLES.content}
              />
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

      <CreateLabelModal
        open={showCreateLabelModal}
        onOpenChange={setShowCreateLabelModal}
        onCreate={(name) => {
          if (!accountId) return;
          createLabelMutation.mutate(
            {
              accountId,
              request: {
                name,
                label_list_visibility: "labelShow",
                message_list_visibility: "show",
              },
            },
            {
              onSuccess: () => {
                setShowCreateLabelModal(false);
              },
            }
          );
        }}
        isCreating={createLabelMutation.isPending}
      />

      <AutoLabelModal
        open={showAutoLabelModal}
        onOpenChange={setShowAutoLabelModal}
        results={labelResult ? [labelResult] : null}
        isLoading={isLabeling}
        onApplyLabels={handleApplyLabels}
        onCancel={() => {
          setShowAutoLabelModal(false);
          setLabelResult(null);
        }}
        isApplying={addLabelMutation.isPending}
      />
    </>
  );
};
