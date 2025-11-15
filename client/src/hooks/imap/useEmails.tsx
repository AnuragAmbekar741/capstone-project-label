import { useQuery, queryOptions } from "@tanstack/react-query";
import { getEmails, type EmailResponse } from "@/api/imap/imap";
import { AxiosError } from "axios";

interface UseEmailsParams {
  accountId: string;
  folder?: string;
  limit?: number;
  offset?: number;
  sinceDate?: string;
  enabled?: boolean;
}

export const emailsQueryOptions = (params: UseEmailsParams) =>
  queryOptions<EmailResponse[], AxiosError>({
    queryKey: [
      "emails",
      params.accountId,
      params.folder || "INBOX",
      params.limit || 50,
      params.offset || 0,
      params.sinceDate,
    ],
    queryFn: () =>
      getEmails(
        params.accountId,
        params.folder || "INBOX",
        params.limit || 50,
        params.offset || 0,
        params.sinceDate
      ),
    enabled: params.enabled !== false && !!params.accountId,
    retry: 1,
  });

export const useEmails = (params: UseEmailsParams) => {
  return useQuery<EmailResponse[], AxiosError>(emailsQueryOptions(params));
};
