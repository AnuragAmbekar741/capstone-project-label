import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteEmail, type EmailResponse } from "@/api/imap/imap";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface DeleteEmailParams {
  accountId: string;
  uid: number;
  folder?: string;
}

interface DeleteEmailError {
  detail?: string;
  message?: string;
}

export const useDeleteEmail = () => {
  const queryClient = useQueryClient();

  return useMutation<
    { message: string },
    AxiosError<DeleteEmailError>,
    DeleteEmailParams
  >({
    mutationFn: ({ accountId, uid, folder = "INBOX" }) =>
      deleteEmail(accountId, uid, folder),
    onSuccess: (_, variables) => {
      const { accountId, uid } = variables;

      // Remove email from infinite query cache
      queryClient.setQueriesData<{
        pages: EmailResponse[][];
        pageParams: number[];
      }>(
        {
          queryKey: ["emails", "infinite", accountId],
        },
        (oldData) => {
          if (!oldData) return oldData;

          // Filter out the deleted email from all pages
          const updatedPages = oldData.pages.map((page) =>
            page.filter((email) => email.uid !== uid)
          );

          return {
            ...oldData,
            pages: updatedPages,
          };
        }
      );

      // Also remove from regular emails query cache (if it exists)
      queryClient.setQueriesData<EmailResponse[]>(
        {
          queryKey: ["emails", accountId],
        },
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.filter((email) => email.uid !== uid);
        }
      );

      // Invalidate queries as a fallback to ensure consistency
      queryClient.invalidateQueries({
        queryKey: ["emails", accountId],
      });

      toast.success("Email deleted successfully");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete email");
    },
  });
};
