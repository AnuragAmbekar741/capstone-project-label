import * as React from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { type Mail } from "@/data/mail-data";
import DOMPurify from "dompurify";
import {
  EMAIL_SANITIZE_CONFIG,
  EMAIL_CONTENT_CLASSES,
  EMAIL_CONTENT_STYLES,
  EMAIL_CONSTANTS,
} from "./mailDetails.config";

interface ThreadEmailItemProps {
  mail: Mail;
  isActive?: boolean;
  onClick?: () => void;
}

export const ThreadEmailItem: React.FC<ThreadEmailItemProps> = ({
  mail,
  isActive = false,
  onClick,
}) => {
  // Get HTML content if available, otherwise use text
  const emailContent = React.useMemo(() => {
    if (mail.bodyHtml) {
      return DOMPurify.sanitize(mail.bodyHtml, EMAIL_SANITIZE_CONFIG);
    }

    if (mail.bodyText) {
      const textWithBreaks = mail.bodyText.replace(
        /\n/g,
        EMAIL_CONSTANTS.LINE_BREAK_REPLACEMENT
      );
      return DOMPurify.sanitize(textWithBreaks);
    }

    return EMAIL_CONSTANTS.EMPTY_CONTENT;
  }, [mail.bodyHtml, mail.bodyText]);

  return (
    <div
      className={`border-b last:border-b-0 ${
        isActive ? "bg-muted/50" : ""
      } transition-colors ${onClick ? "cursor-pointer hover:bg-muted/30" : ""}`}
      onClick={onClick}
    >
      <div className="p-4 space-y-3">
        {/* Email Header */}
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className="text-xs">
              {mail.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-medium text-sm truncate">
                  {mail.name}
                </span>
                <span className="text-xs text-muted-foreground truncate">
                  {mail.email}
                </span>
              </div>
              <span className="text-xs text-muted-foreground shrink-0">
                {mail.date}
              </span>
            </div>
            {mail.subject && (
              <div className="text-sm font-medium mt-1 truncate">
                {mail.subject}
              </div>
            )}
          </div>
        </div>

        {/* Email Content Preview */}
        <div
          className={EMAIL_CONTENT_CLASSES.wrapper}
          style={EMAIL_CONTENT_STYLES.wrapper}
        >
          <div
            className={`${EMAIL_CONTENT_CLASSES.content} text-sm line-clamp-3`}
            dangerouslySetInnerHTML={{ __html: emailContent }}
            style={EMAIL_CONTENT_STYLES.content}
          />
        </div>
      </div>
    </div>
  );
};
