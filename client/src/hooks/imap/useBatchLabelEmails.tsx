import { useMutation } from "@tanstack/react-query";
import {
  batchLabelEmails,
  type BatchLabelEmailsRequest,
  type BatchLabelEmailsResponse,
} from "@/api/imap/imap";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface BatchLabelError {
  detail?: string;
  message?: string;
}

export const useBatchLabelEmails = () => {
  return useMutation<
    BatchLabelEmailsResponse,
    AxiosError<BatchLabelError>,
    { accountId: string; request: BatchLabelEmailsRequest }
  >({
    mutationFn: ({ accountId, request }) =>
      batchLabelEmails(accountId, request),
    onSuccess: (data) => {
      if (data.successful > 0) {
        toast.success(
          `Successfully labeled ${data.successful} email${data.successful > 1 ? "s" : ""}`
        );
      }
      if (data.failed > 0) {
        toast.warning(
          `Failed to label ${data.failed} email${data.failed > 1 ? "s" : ""}`
        );
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to label emails");
    },
  });
};
