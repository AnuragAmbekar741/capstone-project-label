import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { type Mail } from "@/data/mail-data";

interface MailCardProps {
  mail: Mail;
  isSelected: boolean;
  onClick: () => void;
}

export const MailCard: React.FC<MailCardProps> = ({
  mail,
  isSelected,
  onClick,
}) => {
  return (
    <button
      className={cn(
        "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent w-full",
        isSelected && "bg-muted"
      )}
      onClick={onClick}
    >
      {/* Header: Name, Unread indicator, and Date */}
      <div className="flex w-full items-center gap-2 min-w-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="font-semibold truncate">{mail.name}</div>
          {!mail.read && (
            <span className="flex h-2 w-2 rounded-full bg-blue-600 shrink-0" />
          )}
        </div>
        <div className="text-xs text-muted-foreground shrink-0 whitespace-nowrap">
          {mail.date}
        </div>
      </div>

      {/* Subject */}
      <div className="text-xs font-medium truncate w-full">{mail.subject}</div>

      {/* Email preview text */}
      <div className="line-clamp-2 text-xs text-muted-foreground w-full break-words">
        {mail.text}
      </div>

      {/* Labels */}
      {mail.labels.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap w-full">
          {mail.labels.map((label) => (
            <Badge
              key={label}
              variant="secondary"
              className="text-xs truncate max-w-full"
            >
              {label}
            </Badge>
          ))}
        </div>
      )}
    </button>
  );
};
