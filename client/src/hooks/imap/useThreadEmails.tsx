import { useQuery, queryOptions } from "@tanstack/react-query";
import { searchEmails } from "@/api/imap/imap";
import { AxiosError } from "axios";
import { type Mail, emailToMail } from "@/data/mail-data";

interface UseThreadEmailsParams {
  accountId: string;
  mail: Mail;
  enabled?: boolean;
}

/**
 * Build Gmail search query to find emails in the same thread
 */
const buildThreadQuery = (mail: Mail): string => {
  // If email has references, search for emails with those message IDs
  if (mail.references) {
    // Extract message IDs from references (space-separated)
    const messageIds = mail.references.split(/\s+/).filter(Boolean);
    if (messageIds.length > 0) {
      // Search for emails with any of these message IDs in references
      return messageIds.map((id) => `rfc822msgid:${id}`).join(" OR ");
    }
  }

  // If email is a reply, search for the original message
  if (mail.inReplyTo) {
    return `rfc822msgid:${mail.inReplyTo}`;
  }

  // If email has message ID, search for replies to it
  if (mail.messageId) {
    return `rfc822msgid:${mail.messageId}`;
  }

  // Fallback: search by subject (less accurate)
  return `subject:"${mail.subject}"`;
};

export const threadEmailsQueryOptions = (params: UseThreadEmailsParams) =>
  queryOptions<Mail[], AxiosError>({
    queryKey: [
      "threadEmails",
      params.accountId,
      params.mail.id,
      params.mail.messageId,
    ],
    queryFn: async () => {
      if (
        !params.mail.isThread &&
        !params.mail.messageId &&
        !params.mail.inReplyTo
      ) {
        // If not part of a thread, return just this email
        return [params.mail];
      }

      const query = buildThreadQuery(params.mail);
      const emails = await searchEmails(
        params.accountId,
        query,
        "INBOX", // Could be made dynamic
        100 // Get more emails to find all in thread
      );

      // Convert to Mail format
      const mails = emails.map(emailToMail);

      // Add current mail if not in results
      const currentMailInResults = mails.find((m) => m.id === params.mail.id);
      if (!currentMailInResults) {
        mails.push(params.mail);
      }

      // Sort by date (oldest first for thread view)
      return mails.sort((a, b) => {
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        return dateA - dateB;
      });
    },
    enabled: params.enabled !== false && !!params.accountId && !!params.mail,
    retry: 1,
  });

export const useThreadEmails = (params: UseThreadEmailsParams) => {
  return useQuery<Mail[], AxiosError>(threadEmailsQueryOptions(params));
};
