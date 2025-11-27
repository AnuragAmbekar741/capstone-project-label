import { type Config } from "dompurify";
import DOMPurify from "dompurify";

/**
 * Safe CSS properties allowed in email styles
 * Blocks dangerous properties like background, position, z-index, etc.
 */
const ALLOWED_CSS_PROPERTIES = new Set([
  // Typography
  "color",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "font-variant",
  "line-height",
  "text-align",
  "text-decoration",
  "text-transform",
  "letter-spacing",
  "word-spacing",

  // Layout (safe ones only)
  "width",
  "height",
  "max-width",
  "max-height",
  "min-width",
  "min-height",
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
  "border",
  "border-top",
  "border-right",
  "border-bottom",
  "border-left",
  "border-width",
  "border-style",
  "border-color",
  "border-radius",

  // Display (safe values only)
  "display", // Will filter out 'none' values
  "visibility", // Will filter out 'hidden' values
  "overflow",
  "overflow-x",
  "overflow-y",

  // List
  "list-style",
  "list-style-type",
  "list-style-position",

  // Table
  "border-collapse",
  "border-spacing",
  "vertical-align",

  // Other safe properties
  "white-space",
  "word-wrap",
  "word-break",
  "text-overflow",
]);

/**
 * Dangerous CSS property values that should be blocked
 */
const FORBIDDEN_CSS_VALUES = {
  display: ["none"],
  visibility: ["hidden"],
  position: ["fixed", "absolute", "sticky"],
  opacity: ["0", "0.0"],
};

/**
 * Sanitize CSS style attribute - allows safe properties, blocks dangerous ones
 */
const sanitizeStyleAttribute = (style: string): string => {
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

  // Filter and rebuild safe styles
  const safeDeclarations = declarations
    .filter(({ property, value }) => {
      // Block background-related properties
      if (property.startsWith("background")) {
        return false;
      }

      // Block position-related properties that can overlay content
      if (
        property === "position" ||
        property === "z-index" ||
        property === "top" ||
        property === "right" ||
        property === "bottom" ||
        property === "left"
      ) {
        return false;
      }

      // Check if property is allowed
      if (!ALLOWED_CSS_PROPERTIES.has(property)) {
        return false;
      }

      // Check for forbidden values
      const forbiddenValues =
        FORBIDDEN_CSS_VALUES[property as keyof typeof FORBIDDEN_CSS_VALUES];
      if (forbiddenValues && forbiddenValues.includes(value.toLowerCase())) {
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
 * Enhanced sanitize function that also sanitizes style attributes
 */
export const sanitizeEmailContent = (dirty: string): string => {
  // First, sanitize HTML structure
  const clean = DOMPurify.sanitize(dirty, EMAIL_SANITIZE_CONFIG);

  // Then, create a temporary DOM to sanitize style attributes
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = clean;

  // Sanitize all style attributes
  const elements = tempDiv.querySelectorAll("[style]");
  elements.forEach((element) => {
    const styleAttr = element.getAttribute("style");
    if (styleAttr) {
      const sanitized = sanitizeStyleAttribute(styleAttr);
      if (sanitized) {
        element.setAttribute("style", sanitized);
      } else {
        element.removeAttribute("style");
      }
    }
  });

  return tempDiv.innerHTML;
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
