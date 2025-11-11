import type { EmailResponse } from "@/api/imap/imap";
import { cleanEmailPreview } from "@/utils/emailCleaner";

export interface Mail {
  id: string;
  name: string;
  email: string;
  subject: string;
  text: string;
  date: string;
  read: boolean;
  labels: string[];
  // Optional fields for full email data
  bodyHtml?: string | null;
  bodyText?: string | null;
  attachments?: Array<{
    filename: string;
    content_type: string;
    size: number;
  }>;
  toAddresses?: string[];
}

/**
 * Parse email address to extract name and email
 */
export const parseEmailAddress = (
  address: string
): { name: string; email: string } => {
  if (!address) {
    return { name: "", email: "" };
  }

  // Try to match "Name <email@domain.com>" format
  const match = address.match(/^(.+?)\s*<(.+?)>$/);
  if (match) {
    return {
      name: match[1].trim().replace(/['"]/g, ""),
      email: match[2].trim(),
    };
  }

  // If it's just an email address
  if (address.includes("@")) {
    return {
      name: address.split("@")[0],
      email: address,
    };
  }

  // Otherwise, treat as name
  return {
    name: address,
    email: "",
  };
};

/**
 * Format date string to relative time
 */
export const formatRelativeDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    const diffWeeks = Math.floor(diffDays / 7);
    const diffMonths = Math.floor(diffDays / 30);
    const diffYears = Math.floor(diffDays / 365);

    if (diffMins < 1) return "just now";
    if (diffMins < 60)
      return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24)
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
    if (diffWeeks < 4)
      return `${diffWeeks} week${diffWeeks > 1 ? "s" : ""} ago`;
    if (diffMonths < 12)
      return `${diffMonths} month${diffMonths > 1 ? "s" : ""} ago`;
    if (diffYears < 1)
      return `${diffYears} year${diffYears > 1 ? "s" : ""} ago`;

    return date.toLocaleDateString();
  } catch {
    return dateString;
  }
};

/**
 * Check if email is unread based on labels
 */
export const isUnread = (labels: string[]): boolean => {
  if (!labels || labels.length === 0) {
    return true; // If no labels, assume unread
  }

  // Check if \Seen flag is present (means email is read)
  const hasSeenFlag = labels.some(
    (label) => label.toUpperCase() === "\\SEEN" || label === "\\Seen"
  );

  // Check if \Unseen flag is present (means email is unread)
  const hasUnseenFlag = labels.some(
    (label) =>
      label.toUpperCase() === "\\UNSEEN" || label.toUpperCase() === "UNSEEN"
  );

  // Email is unread if it has \Unseen flag OR doesn't have \Seen flag
  return hasUnseenFlag || !hasSeenFlag;
};

/**
 * Filter out system labels that start with \
 */
export const filterUserLabels = (labels: string[]): string[] => {
  return labels.filter(
    (label) => !label.startsWith("\\") && label.toUpperCase() !== "UNSEEN"
  );
};

/**
 * Convert EmailResponse from API to Mail format for UI
 */
export const emailToMail = (email: EmailResponse): Mail => {
  const { name, email: emailAddr } = parseEmailAddress(email.from_address);

  // Use cleaned preview text
  const textPreview = cleanEmailPreview(email.body_text, email.body_html, 200);

  return {
    id: email.uid.toString(),
    name: name || emailAddr,
    email: emailAddr || email.from_address,
    subject: email.subject || "(No subject)",
    text: textPreview,
    date: formatRelativeDate(email.date),
    read: !isUnread(email.labels),
    labels: filterUserLabels(email.labels),
    bodyHtml: email.body_html,
    bodyText: email.body_text,
    attachments: email.attachments,
    toAddresses: email.to_addresses,
  };
};

// Keep dummy data for fallback
export const mails: Mail[] = [
  {
    id: "1",
    name: "William Smith",
    email: "williamsmith@example.com",
    subject: "Meeting Tomorrow",
    text: "Hi, let's have a meeting tomorrow to discuss the project. I've been reviewing the project details and have some ideas I'd like to share. It's crucial that we align on our next steps to ensure the project's success...",
    date: "almost 2 years ago",
    read: false,
    labels: ["meeting", "work", "important"],
  },
  {
    id: "2",
    name: "Alice Smith",
    email: "alicesmith@example.com",
    subject: "Re: Project Update",
    text: "Thank you for the project update. It looks great! I've gone through the report, and the progress is impressive. The team has done a fantastic job...",
    date: "almost 2 years ago",
    read: true,
    labels: ["work", "important"],
  },
  {
    id: "3",
    name: "Bob Johnson",
    email: "bobjohnson@example.com",
    subject: "Weekend Plans",
    text: "Any plans for the weekend? I was thinking of going hiking in the nearby mountains. It's been a while since we had some outdoor fun...",
    date: "over 2 years ago",
    read: true,
    labels: ["personal"],
  },
];
