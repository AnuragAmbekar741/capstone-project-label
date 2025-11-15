import * as React from "react";
import { Tag, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface CreateLabelModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (name: string) => void;
  isCreating?: boolean;
}

export const CreateLabelModal: React.FC<CreateLabelModalProps> = ({
  open,
  onOpenChange,
  onCreate,
  isCreating = false,
}) => {
  const [labelName, setLabelName] = React.useState("");

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (!open) {
      setLabelName("");
    }
  }, [open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (labelName.trim()) {
      onCreate(labelName.trim());
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-primary/10 p-2 shrink-0">
              <Tag className="h-5 w-5 text-primary" />
            </div>
            <DialogTitle>Create New Label</DialogTitle>
          </div>
          <DialogDescription className="pt-2">
            Create a new label to organize your emails.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="label-name">Label Name</Label>
              <Input
                id="label-name"
                type="text"
                placeholder="Enter label name"
                value={labelName}
                onChange={(e) => setLabelName(e.target.value)}
                disabled={isCreating}
                autoFocus
                required
                maxLength={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isCreating || !labelName.trim()}>
              {isCreating ? (
                <>
                  <Plus className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Label
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
