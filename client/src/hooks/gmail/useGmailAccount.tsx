import { useQuery, queryOptions } from "@tanstack/react-query";
import {
  getGmailAccounts,
  type GmailAccountsResponse,
} from "@/api/gmail/gmail";
import { AxiosError } from "axios";

export const gmailAccountsQueryOptions = queryOptions<
  GmailAccountsResponse,
  AxiosError
>({
  queryKey: ["gmailAccounts"],
  queryFn: getGmailAccounts,
  retry: 1,
});

export const useGmailAccounts = () => {
  return useQuery<GmailAccountsResponse, AxiosError>(gmailAccountsQueryOptions);
};
