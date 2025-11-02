import { useMutation } from "@tanstack/react-query";
import { getGmailAuthUrl, type ConnectGmailResponse } from "@/api/gmail/gmail";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface ConnectGmailError {
  message?: string;
  detail?: string;
}

/**
 * React Query mutation hook for connecting Gmail account
 *
 * On success:
 * - Redirects user to Google OAuth authorization page
 * - After authorization, user is redirected back to /dashboard?gmail_connected=...
 *
 * Usage:
 * ```tsx
 * const connectGmail = useConnectGmail();
 *
 * const handleConnect = () => {
 *   connectGmail.mutate();
 * };
 * ```
 */
export const useConnectGmail = () => {
  return useMutation<ConnectGmailResponse, AxiosError<ConnectGmailError>, void>(
    {
      mutationFn: async () => {
        return await getGmailAuthUrl();
      },
      onSuccess: (data) => {
        // Redirect user to Google OAuth page
        window.location.href = data.authorization_url;
        // 1. User authorizes → Google redirects to /api/gmail/callback
        // 2. Backend processes → Redirects to /dashboard?gmail_connected=...
        // 3. Frontend detects query param → Refetches accounts → Modal closes
      },
      onError: (error) => {
        console.error("Failed to get Gmail auth URL:", error);
        const errorMessage =
          error.response?.data?.detail ||
          error.message ||
          "Failed to connect Gmail account. Please try again.";

        toast.error(errorMessage);
      },
      // Invalidate accounts query after successful connection
      // This will be triggered when user returns from OAuth
      onSettled: () => {
        // We don't invalidate here because redirect happens immediately
        // Instead, we invalidate in DashboardLayout when gmail_connected param is detected
      },
    }
  );
};
