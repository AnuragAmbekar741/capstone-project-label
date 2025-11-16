import * as React from "react";
import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { type Mail } from "@/data/mail-data";

interface DeleteEmailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mail: Mail | null;
  onConfirm: () => void;
  isDeleting?: boolean;
}

export const DeleteEmailModal: React.FC<DeleteEmailModalProps> = ({
  open,
  onOpenChange,
  mail,
  onConfirm,
  isDeleting = false,
}) => {
  if (!mail) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-destructive/10 p-2 shrink-0">
              <AlertTriangle className="h-5 w-5 text-destructive" />
            </div>
            <DialogTitle>Delete Email</DialogTitle>
          </div>
          <DialogDescription className="pt-2">
            Are you sure you want to delete this email? This action cannot be
            undone.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <div className="rounded-lg border bg-muted/50 p-3">
            <p className="text-sm font-medium">{mail.subject}</p>
            <p className="text-xs text-muted-foreground mt-1">
              From: {mail.email}
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
