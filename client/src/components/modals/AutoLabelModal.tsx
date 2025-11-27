import * as React from "react";
import { Sparkles, Tag, Check, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import type { SuggestLabelResponse } from "@/api/imap/imap";

interface AutoLabelModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  results: SuggestLabelResponse[] | null;
  isLoading: boolean;
  onApplyLabels: () => void;
  onCancel: () => void;
  isApplying?: boolean;
}

export const AutoLabelModal: React.FC<AutoLabelModalProps> = ({
  open,
  onOpenChange,
  results,
  isLoading,
  onApplyLabels,
  onCancel,
  isApplying = false,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 p-2 shrink-0">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <DialogTitle>AI Suggested Labels</DialogTitle>
          </div>
          <DialogDescription className="pt-2">
            Review the AI-suggested labels for your email. You can apply them or
            cancel.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ))}
            </div>
          ) : results && results.length > 0 ? (
            <ScrollArea className="max-h-[400px] pr-4">
              <div className="space-y-4">
                {results.map((result) => (
                  <div
                    key={result.id}
                    className="border rounded-lg p-4 space-y-2 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <Badge
                          variant="secondary"
                          className="text-xs flex items-center gap-1 shrink-0"
                        >
                          <Tag className="h-3 w-3" />
                          {result.label}
                        </Badge>
                        <span className="text-xs text-muted-foreground truncate">
                          Email ID: {result.id}
                        </span>
                      </div>
                    </div>
                    {result.reason && (
                      <p className="text-sm text-muted-foreground">
                        {result.reason}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>No labels suggested.</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isApplying || isLoading}
          >
            <X className="mr-2 h-4 w-4" />
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onApplyLabels}
            disabled={
              isApplying || isLoading || !results || results.length === 0
            }
          >
            {isApplying ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Apply Labels
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
