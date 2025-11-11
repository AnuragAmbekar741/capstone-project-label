import { type Config } from "dompurify";

/**
 * Configuration for email content sanitization
 */
export const EMAIL_SANITIZE_CONFIG: Config = {
  ALLOWED_TAGS: [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "b",
    "i",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "td",
    "th",
    "div",
    "span",
    "blockquote",
    "pre",
    "code",
    "hr",
    "br",
  ],
  ALLOWED_ATTR: ["href", "src", "alt", "title"],
  ALLOW_DATA_ATTR: false,
  FORBID_ATTR: ["style", "class", "id"],
  FORBID_TAGS: ["style", "script", "link", "meta"],
};

/**
 * CSS classes for email content wrapper
 */
export const EMAIL_CONTENT_CLASSES = {
  wrapper:
    "email-content-wrapper text-sm max-w-full [&_*]:max-w-full [&_img]:max-w-full [&_pre]:overflow-x-auto [&_table]:overflow-x-auto [&_a]:text-primary [&_a]:underline",
  content: "email-content",
};

/**
 * Inline styles for email content isolation
 */
export const EMAIL_CONTENT_STYLES = {
  wrapper: {
    isolation: "isolate" as const,
    contain: "layout style paint" as const,
  },
  content: {
    all: "initial" as const,
    display: "block" as const,
    fontFamily: "inherit",
    fontSize: "inherit",
    color: "inherit",
    lineHeight: "inherit",
  },
};

/**
 * Dropdown menu items for email actions
 */
export const EMAIL_DROPDOWN_ITEMS = [
  { label: "Mark as unread", action: "mark-unread" },
  { label: "Star thread", action: "star" },
  { label: "Add label", action: "add-label" },
  { label: "Mute thread", action: "mute" },
] as const;

/**
 * Constants
 */
export const EMAIL_CONSTANTS = {
  EMPTY_CONTENT: "(No content)",
  LINE_BREAK_REPLACEMENT: "<br />",
} as const;
