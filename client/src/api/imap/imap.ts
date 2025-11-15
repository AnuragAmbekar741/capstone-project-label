import { get } from "../request";

export interface EmailAttachment {
  filename: string;
  content_type: string;
  size: number;
}

export interface EmailResponse {
  uid: number;
  subject: string;
  from_address: string;
  to_addresses: string[];
  date: string;
  body_text: string | null;
  body_html: string | null;
  labels: string[];
  attachments: EmailAttachment[];
  // Thread identification fields
  message_id?: string | null;
  in_reply_to?: string | null;
  references?: string | null;
  is_thread?: boolean;
}

export interface FolderResponse {
  name: string;
  flags: string[];
}

// Fetch emails from a Gmail account
export const getEmails = async (
  accountId: string,
  folder: string = "INBOX",
  limit: number = 50,
  offset: number = 0,
  sinceDate?: string
): Promise<EmailResponse[]> => {
  const params = new URLSearchParams({
    folder,
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (sinceDate) {
    params.append("since_date", sinceDate);
  }
  return await get<EmailResponse[]>(
    `/api/gmail/accounts/${accountId}/emails?${params.toString()}`
  );
};

// Search emails
export const searchEmails = async (
  accountId: string,
  query: string,
  folder: string = "INBOX",
  limit: number = 50
): Promise<EmailResponse[]> => {
  const params = new URLSearchParams({
    query,
    folder,
    limit: limit.toString(),
  });
  return await get<EmailResponse[]>(
    `/api/gmail/accounts/${accountId}/search?${params.toString()}`
  );
};

// List folders
export const getFolders = async (
  accountId: string
): Promise<FolderResponse[]> => {
  return await get<FolderResponse[]>(
    `/api/gmail/accounts/${accountId}/folders`
  );
};
