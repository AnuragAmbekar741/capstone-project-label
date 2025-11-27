import { useQuery } from "@tanstack/react-query";
import { getFolders, type FolderResponse } from "@/api/imap/imap";
import { AxiosError } from "axios";

export const useGetFolder = (accountId: string) => {
  return useQuery<FolderResponse[], AxiosError>({
    queryKey: ["userFolders", accountId], // ← Add accountId to match invalidation
    queryFn: () => getFolders(accountId),
    enabled: !!accountId,
    retry: 1,
  });
};
