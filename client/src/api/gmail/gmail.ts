import { get } from "../request";

export interface GmailAccount {
  id: string;
  email_address: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GmailAccountsResponse {
  accounts: GmailAccount[];
}

export interface ConnectGmailResponse {
  authorization_url: string;
  state: string;
}

// Get authorization URL to connect Gmail
export const getGmailAuthUrl = async (): Promise<ConnectGmailResponse> => {
  return await get<ConnectGmailResponse>("/api/gmail/connect");
};

// Get user's connected Gmail accounts
export const getGmailAccounts = async (): Promise<GmailAccountsResponse> => {
  return await get<GmailAccountsResponse>("/api/gmail/accounts");
};
