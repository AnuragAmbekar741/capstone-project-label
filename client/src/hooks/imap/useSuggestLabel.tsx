import { useMutation } from "@tanstack/react-query";
import {
  suggestLabel,
  type SuggestLabelRequest,
  type SuggestLabelResponse,
} from "@/api/imap/imap";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface SuggestLabelError {
  detail?: string;
  message?: string;
}

export const useSuggestLabel = () => {
  return useMutation<
    SuggestLabelResponse,
    AxiosError<SuggestLabelError>,
    { accountId: string; request: SuggestLabelRequest }
  >({
    mutationFn: ({ accountId, request }) => suggestLabel(accountId, request),
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to suggest label");
    },
    // No success toast - just returns suggestion, doesn't apply anything
  });
};
