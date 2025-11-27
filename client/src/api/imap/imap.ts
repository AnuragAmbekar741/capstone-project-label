import { get } from "../request";
import { del } from "../request";
import { post } from "../request";

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

export interface CreateLabelRequest {
  name: string;
  label_list_visibility?: "labelShow" | "labelHide";
  message_list_visibility?: "show" | "hide";
}

export interface LabelResponse {
  id: string;
  name: string;
  label_list_visibility: string;
  message_list_visibility: string;
  type: string;
}

export interface EmailForLabeling {
  id: string;
  subject: string;
  body: string;
}

export interface BatchLabelEmailsRequest {
  emails: EmailForLabeling[];
  apply_labels?: boolean;
}

export interface EmailLabelResult {
  id: string;
  label: string;
  reason: string;
}

export interface BatchLabelEmailsResponse {
  results: EmailLabelResult[];
  total_processed: number;
  successful: number;
  failed: number;
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

// Create a new label
export const createLabel = async (
  accountId: string,
  request: CreateLabelRequest
): Promise<LabelResponse> => {
  return await post<LabelResponse, CreateLabelRequest>(
    `/api/gmail/accounts/${accountId}/labels`,
    request
  );
};

// Batch label emails using AI
export const batchLabelEmails = async (
  accountId: string,
  request: BatchLabelEmailsRequest
): Promise<BatchLabelEmailsResponse> => {
  return await post<BatchLabelEmailsResponse, BatchLabelEmailsRequest>(
    `/api/gmail/accounts/${accountId}/emails/batch-label`,
    request
  );
};

// Delete an email
export const deleteEmail = async (
  accountId: string,
  uid: number,
  folder: string = "INBOX"
): Promise<{ message: string }> => {
  const params = new URLSearchParams({
    folder,
  });
  return await del<{ message: string }>(
    `/api/gmail/accounts/${accountId}/emails/${uid}?${params.toString()}`
  );
};
