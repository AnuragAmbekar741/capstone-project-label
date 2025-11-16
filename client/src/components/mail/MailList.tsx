import * as React from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { type Mail } from "@/data/mail-data";
import { MailCard } from "./MailCard";
import InfiniteScroll from "react-infinite-scroll-component";

interface MailListProps {
  mails: Mail[];
  selectedMail: Mail;
  onSelectMail: (mail: Mail) => void;
  onLoadMore?: () => void;
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
}

export const MailList: React.FC<MailListProps> = ({
  mails,
  selectedMail,
  onSelectMail,
  onLoadMore,
  hasNextPage = false,
}) => {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 space-y-4 shrink-0">
        <h1 className="text-xl font-bold">Inbox</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search" className="pl-10" />
        </div>
      </div>

      {/* Scrollable mail list with infinite scroll */}
      <div
        id="scrollableDiv"
        className="flex-1 overflow-y-auto min-h-0 scrollbar-hide"
        style={{ height: "100%" }}
      >
        <InfiniteScroll
          dataLength={mails.length}
          next={onLoadMore || (() => {})}
          hasMore={hasNextPage}
          loader={
            <div className="flex items-center justify-center py-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading more emails...</span>
              </div>
            </div>
          }
          endMessage={
            mails.length > 0 && !hasNextPage ? (
              <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
                No more emails to load
              </div>
            ) : null
          }
          scrollableTarget="scrollableDiv"
        >
          <div className="flex flex-col gap-2 p-4 pt-0">
            {mails.map((mail) => (
              <MailCard
                key={mail.id}
                mail={mail}
                isSelected={selectedMail.id === mail.id}
                onClick={() => onSelectMail(mail)}
              />
            ))}
          </div>
        </InfiniteScroll>
      </div>
    </div>
  );
};
