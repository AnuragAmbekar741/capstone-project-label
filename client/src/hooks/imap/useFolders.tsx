import { useQuery } from "@tanstack/react-query";
import { getFolders, type FolderResponse } from "@/api/imap/imap";
import { AxiosError } from "axios";

export const useGetFolder = (accountId: string) => {
  return useQuery<FolderResponse[], AxiosError>({
    queryKey: ["userFolders"],
    queryFn: () => getFolders(accountId),
    enabled: !!accountId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
};
