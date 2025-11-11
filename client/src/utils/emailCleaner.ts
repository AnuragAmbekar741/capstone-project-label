/**
 * Utility functions for cleaning email body content
 */

/**
 * Remove email signatures and common footer patterns
 */
const removeSignatures = (text: string): string => {
  // Common signature patterns
  const signaturePatterns = [
    // Common email signatures
    /^--\s*$/m, // Standard email separator
    /^_{3,}$/m, // Underscore separators
    /^Sent from my .+$/im,
    /^Get Outlook for .+$/im,
    /^Sent from Mail for .+$/im,
    /^This email was sent from .+$/im,
    /^You received this email because .+$/im,
    /^Unsubscribe.*$/im,
    /^To unsubscribe.*$/im,
    /^View this email in your browser.*$/im,
    // Common signature blocks (lines starting with dashes)
    /^-{3,}.*$/m,
  ];

  let cleaned = text;
  signaturePatterns.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, "");
  });

  // Remove everything after common signature markers
  const signatureMarkers = [
    /^--\s*$/m,
    /^_{3,}$/m,
    /^Sent from my/i,
    /^Get Outlook/i,
    /^Sent from Mail/i,
  ];

  for (const marker of signatureMarkers) {
    const match = cleaned.search(marker);
    if (match > cleaned.length * 0.5) {
      // Only remove if signature is in the latter half of the email
      cleaned = cleaned.substring(0, match).trim();
    }
  }

  return cleaned;
};

/**
 * Remove quoted/replied content
 */
const removeQuotedContent = (text: string): string => {
  // Remove lines starting with > (quoted text)
  let cleaned = text.replace(/^>+.*$/gm, "");

  // Remove common reply patterns
  const replyPatterns = [
    /^On .+ wrote:.*$/im,
    /^From: .+$/im,
    /^Sent: .+$/im,
    /^To: .+$/im,
    /^Subject: .+$/im,
    /^Date: .+$/im,
    /^On .+ at .+ .+ wrote:.*$/im,
    /^On .+, .+ wrote:.*$/im,
    /^Le .+ a écrit :.*$/im, // French
    /^El .+ escribió:.*$/im, // Spanish
    /^Am .+ schrieb .+:.*$/im, // German
  ];

  replyPatterns.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, "");
  });

  // Remove forwarded message markers
  cleaned = cleaned.replace(/^-+ ?Forwarded Message ?-+$/im, "");
  cleaned = cleaned.replace(/^Begin forwarded message:.*$/im, "");
  cleaned = cleaned.replace(/^End forwarded message:.*$/im, "");

  return cleaned;
};

/**
 * Remove HTML tags and decode entities
 */
const stripHtml = (html: string): string => {
  // Remove script and style tags completely
  let cleaned = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "");
  cleaned = cleaned.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "");

  // Remove HTML tags but preserve line breaks
  cleaned = cleaned.replace(/<br\s*\/?>/gi, "\n");
  cleaned = cleaned.replace(/<\/p>/gi, "\n\n");
  cleaned = cleaned.replace(/<\/div>/gi, "\n");
  cleaned = cleaned.replace(/<\/li>/gi, "\n");
  cleaned = cleaned.replace(/<li>/gi, "• ");

  // Remove all other HTML tags
  cleaned = cleaned.replace(/<[^>]+>/g, "");

  // Decode HTML entities
  const textarea = document.createElement("textarea");
  textarea.innerHTML = cleaned;
  cleaned = textarea.value;

  // Decode common entities manually
  cleaned = cleaned
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'");

  return cleaned;
};

/**
 * Normalize whitespace
 */
const normalizeWhitespace = (text: string): string => {
  // Replace multiple spaces with single space
  let cleaned = text.replace(/[ \t]+/g, " ");

  // Replace multiple newlines (more than 2) with double newline
  cleaned = cleaned.replace(/\n{3,}/g, "\n\n");

  // Remove trailing whitespace from each line
  cleaned = cleaned.replace(/[ \t]+$/gm, "");

  // Remove leading/trailing whitespace
  cleaned = cleaned.trim();

  return cleaned;
};

/**
 * Remove email headers that might appear in body
 */
const removeHeaders = (text: string): string => {
  const headerPatterns = [
    /^Message-ID: .+$/im,
    /^In-Reply-To: .+$/im,
    /^References: .+$/im,
    /^X-Mailer: .+$/im,
    /^X-Original-Sender: .+$/im,
    /^Return-Path: .+$/im,
    /^Received: .+$/im,
    /^MIME-Version: .+$/im,
    /^Content-Type: .+$/im,
    /^Content-Transfer-Encoding: .+$/im,
  ];

  let cleaned = text;
  headerPatterns.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, "");
  });

  return cleaned;
};

/**
 * Main function to clean email body
 */
export const cleanEmailBody = (
  bodyText: string | null | undefined,
  bodyHtml: string | null | undefined
): string => {
  let text = "";

  // Prefer plain text over HTML
  if (bodyText) {
    text = bodyText;
  } else if (bodyHtml) {
    text = stripHtml(bodyHtml);
  } else {
    return "(No content)";
  }

  // Apply cleaning steps
  text = removeHeaders(text);
  text = removeQuotedContent(text);
  text = removeSignatures(text);
  text = normalizeWhitespace(text);

  return text.trim() || "(No content)";
};

/**
 * Clean email body for preview (shorter version)
 */
export const cleanEmailPreview = (
  bodyText: string | null | undefined,
  bodyHtml: string | null | undefined,
  maxLength: number = 200
): string => {
  const cleaned = cleanEmailBody(bodyText, bodyHtml);

  if (cleaned.length <= maxLength) {
    return cleaned;
  }

  // Truncate at word boundary
  const truncated = cleaned.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");

  if (lastSpace > maxLength * 0.8) {
    return truncated.substring(0, lastSpace) + "...";
  }

  return truncated + "...";
};
