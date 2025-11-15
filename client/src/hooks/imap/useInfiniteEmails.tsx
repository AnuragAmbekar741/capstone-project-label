import { useInfiniteQuery } from "@tanstack/react-query";
import { getEmails, type EmailResponse } from "@/api/imap/imap";
import { AxiosError } from "axios";

interface UseInfiniteEmailsParams {
  accountId: string;
  folder?: string;
  limit?: number;
  sinceDate?: string;
  enabled?: boolean;
}

export const useInfiniteEmails = (params: UseInfiniteEmailsParams) => {
  const limit = params.limit || 50;

  return useInfiniteQuery<EmailResponse[], AxiosError>({
    queryKey: [
      "emails",
      "infinite",
      params.accountId,
      params.folder || "INBOX",
      limit,
      params.sinceDate,
    ],
    queryFn: ({ pageParam = 0 }) =>
      getEmails(
        params.accountId,
        params.folder || "INBOX",
        limit,
        pageParam as number,
        params.sinceDate
      ),
    getNextPageParam: (lastPage, allPages) => {
      // Limit to 20 pages (1000 emails if limit=50)
      const MAX_PAGES = 20;
      if (allPages.length >= MAX_PAGES) {
        return undefined;
      }
      // If last page has fewer emails than limit, we've reached the end
      if (lastPage.length < limit) {
        return undefined;
      }
      // Return the next offset
      return allPages.length * limit;
    },
    initialPageParam: 0,
    enabled: params.enabled !== false && !!params.accountId,
    retry: 1,
  });
};
