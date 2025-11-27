import { useMutation, useQueryClient } from "@tanstack/react-query";
import { addLabelToEmail } from "@/api/imap/imap";
import { AxiosError } from "axios";
import { toast } from "sonner";
import type { EmailResponse } from "@/api/imap/imap";
import type { Mail } from "@/data/mail-data";

interface AddLabelToEmailParams {
  accountId: string;
  uid: number;
  label: string;
  folder?: string;
}

interface AddLabelToEmailError {
  detail?: string;
  message?: string;
}

export const useAddLabelToEmail = (onSuccessCallback?: () => void) => {
  const queryClient = useQueryClient();

  return useMutation<
    { message: string },
    AxiosError<AddLabelToEmailError>,
    AddLabelToEmailParams
  >({
    mutationFn: ({ accountId, uid, label, folder = "INBOX" }) =>
      addLabelToEmail(accountId, uid, label, folder),
    onSuccess: (_, variables) => {
      const { accountId, uid, label } = variables;

      // Helper function to add label to EmailResponse
      const addLabelToEmailResponse = (email: EmailResponse): EmailResponse => {
        const currentLabels = email.labels || [];
        const labelLower = label.toLowerCase();
        const hasLabel = currentLabels.some(
          (existingLabel) => existingLabel.toLowerCase() === labelLower
        );
        if (!hasLabel) {
          return {
            ...email,
            labels: [...currentLabels, label],
          };
        }
        return email;
      };

      // Helper function to add label to Mail
      const addLabelToMail = (email: Mail): Mail => {
        const currentLabels = email.labels || [];
        const labelLower = label.toLowerCase();
        const hasLabel = currentLabels.some(
          (existingLabel) => existingLabel.toLowerCase() === labelLower
        );
        if (!hasLabel) {
          return {
            ...email,
            labels: [...currentLabels, label],
          };
        }
        return email;
      };

      // Update infinite emails query cache
      queryClient.setQueriesData<{
        pages: EmailResponse[][];
        pageParams: number[];
      }>(
        {
          queryKey: ["emails", "infinite", accountId],
        },
        (oldData) => {
          if (!oldData) return oldData;

          // Update the email in all pages
          const updatedPages = oldData.pages.map((page) =>
            page.map((email) =>
              email.uid === uid ? addLabelToEmailResponse(email) : email
            )
          );

          return {
            ...oldData,
            pages: updatedPages,
          };
        }
      );

      // Update regular emails query cache (all variations with different params)
      queryClient.setQueriesData<EmailResponse[]>(
        {
          queryKey: ["emails", accountId],
        },
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.map((email) =>
            email.uid === uid ? addLabelToEmailResponse(email) : email
          );
        }
      );

      // Update thread emails cache if the email exists there
      queryClient.setQueriesData<Mail[]>(
        {
          queryKey: ["threadEmails", accountId],
        },
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.map((email) => {
            // Thread emails use string id, need to convert uid to string for comparison
            if (email.id === uid.toString()) {
              return addLabelToMail(email);
            }
            return email;
          });
        }
      );

      toast.success("Label applied successfully");

      // Call optional callback (e.g., to close modal)
      onSuccessCallback?.();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to apply label");
    },
  });
};
