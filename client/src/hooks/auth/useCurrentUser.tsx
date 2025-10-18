import { useQuery } from "@tanstack/react-query";
import { getCurrentUser, type UserProfile } from "@/api/auth/auth";
import { AxiosError } from "axios";

export const useCurrentUser = () => {
  return useQuery<UserProfile, AxiosError>({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
};
