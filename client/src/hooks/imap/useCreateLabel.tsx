import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createLabel,
  type CreateLabelRequest,
  type LabelResponse,
} from "@/api/imap/imap";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface CreateLabelError {
  detail?: string;
  message?: string;
}

export const useCreateLabel = () => {
  const queryClient = useQueryClient();

  return useMutation<
    LabelResponse,
    AxiosError<CreateLabelError>,
    { accountId: string; request: CreateLabelRequest }
  >({
    mutationFn: ({ accountId, request }) => createLabel(accountId, request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["userFolders"],
      });

      toast.success(`Label "${data.name}" created successfully`);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to create label");
    },
  });
};
