import { type Config } from "dompurify";
import DOMPurify from "dompurify";

/**
 * Image-specific CSS properties allowed
 */
const ALLOWED_IMAGE_CSS_PROPERTIES = new Set([
  "width",
  "height",
  "max-width",
  "max-height",
  "min-width",
  "min-height",
  "display",
  "object-fit",
  "object-position",
  "border",
  "border-radius",
  "margin",
  "margin-top",
  "margin-right",
  "margin-bottom",
  "margin-left",
  "padding",
  "padding-top",
  "padding-right",
  "padding-bottom",
  "padding-left",
]);

/**
 * Sanitize CSS style attribute for images only
 */
const sanitizeImageStyleAttribute = (style: string): string => {
  if (!style || typeof style !== "string") return "";

  // Parse style string into property-value pairs
  const declarations = style
    .split(";")
    .map((decl) => decl.trim())
    .filter(Boolean)
    .map((decl) => {
      const colonIndex = decl.indexOf(":");
      if (colonIndex === -1) return null;

      const property = decl.slice(0, colonIndex).trim().toLowerCase();
      const value = decl.slice(colonIndex + 1).trim();

      return { property, value };
    })
    .filter(
      (decl): decl is { property: string; value: string } => decl !== null
    );

  // Filter and rebuild safe styles for images
  const safeDeclarations = declarations
    .filter(({ property, value }) => {
      // Check if property is allowed for images
      if (!ALLOWED_IMAGE_CSS_PROPERTIES.has(property)) {
        return false;
      }

      // Block any value containing url() or expression() (can execute code)
      if (
        value.includes("url(") ||
        value.includes("expression(") ||
        value.includes("javascript:")
      ) {
        return false;
      }

      return true;
    })
    .map(({ property, value }) => `${property}: ${value}`)
    .join("; ");

  return safeDeclarations;
};

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
  ALLOWED_ATTR: ["href", "src", "alt", "title", "style"],
  ALLOW_DATA_ATTR: false,
  FORBID_ATTR: ["class", "id"],
  FORBID_TAGS: ["style", "script", "link", "meta"],
  // Hook to sanitize style attributes
  ADD_ATTR: ["style"],
};

/**
 * Enhanced sanitize function that removes all style attributes except for images
 */
export const sanitizeEmailContent = (dirty: string): string => {
  // First, sanitize HTML structure
  const clean = DOMPurify.sanitize(dirty, EMAIL_SANITIZE_CONFIG);

  // Then, create a temporary DOM to sanitize style attributes
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = clean;

  // Remove all style attributes except for images
  const elements = tempDiv.querySelectorAll("[style]");
  elements.forEach((element) => {
    if (element.tagName.toLowerCase() === "img") {
      // For images, sanitize and keep only image-specific styles
      const styleAttr = element.getAttribute("style");
      if (styleAttr) {
        const sanitized = sanitizeImageStyleAttribute(styleAttr);
        if (sanitized) {
          element.setAttribute("style", sanitized);
        } else {
          element.removeAttribute("style");
        }
      }
    } else {
      // For all other elements, remove style attribute completely
      element.removeAttribute("style");
    }
  });

  return tempDiv.innerHTML;
};

/**
 * CSS classes for email content wrapper
 */
export const EMAIL_CONTENT_CLASSES = {
  wrapper:
    "email-content-wrapper text-sm max-w-full [&_*]:max-w-full [&_img]:max-w-full [&_pre]:overflow-x-auto [&_table]:overflow-x-auto [&_a]:text-white [&_a]:underline [&_*]:text-white [&_img]:!text-inherit",
  content: "email-content text-white",
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
    color: "white",
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
