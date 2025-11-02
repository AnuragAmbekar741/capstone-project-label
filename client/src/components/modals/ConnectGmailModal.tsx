import * as React from "react";
import { Mail, Loader2, Shield, CheckCircle2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useConnectGmail } from "@/hooks/gmail/useConnectGmail";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";

interface ConnectGmailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Google Logo SVG Component
const GoogleIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      fill="#EA4335"
    />
  </svg>
);

export const ConnectGmailModal: React.FC<ConnectGmailModalProps> = ({
  open,
  onOpenChange,
}) => {
  const { data: gmailAccountsData } = useGmailAccounts();
  const connectGmail = useConnectGmail();

  const hasConnectedAccounts =
    gmailAccountsData?.accounts && gmailAccountsData.accounts.length > 0;

  React.useEffect(() => {
    if (hasConnectedAccounts && open) {
      onOpenChange(false);
    }
  }, [hasConnectedAccounts, open, onOpenChange]);

  const handleConnectGmail = () => {
    connectGmail.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton={false} className="sm:max-w-[500px]">
        <DialogHeader className="space-y-4">
          {/* Google Logo Section */}
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/20 via-yellow-500/20 to-green-500/20 blur-2xl rounded-full" />
              <div className="relative rounded-full bg-background p-4 border-2 border-border shadow-lg">
                <div className="flex items-center justify-center w-7 h-7">
                  <GoogleIcon className="w-8 h-8" />
                </div>
              </div>
            </div>

            <div className="text-center space-y-2">
              <DialogTitle className="text-2xl font-semibold">
                Connect Your Gmail Account
              </DialogTitle>
              <DialogDescription className="text-base text-muted-foreground max-w-md">
                Get started by connecting your Gmail account to organize and
                manage your emails efficiently.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Features Section */}
        <div className="py-6 space-y-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors">
              <div className="mt-0.5 rounded-full bg-primary/10 p-1.5">
                <Mail className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Read and manage emails</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Access your inbox, read messages, and stay organized
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors">
              <div className="mt-0.5 rounded-full bg-primary/10 p-1.5">
                <CheckCircle2 className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Organize with labels</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Create and manage labels to categorize your emails
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors">
              <div className="mt-0.5 rounded-full bg-primary/10 p-1.5">
                <Shield className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Secure and private</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Your data is encrypted and never shared with third parties
                </p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            onClick={handleConnectGmail}
            disabled={connectGmail.isPending}
            className="flex-1 sm:flex-initial w-full"
          >
            {connectGmail.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <GoogleIcon className="mr-2 h-4 w-4" />
                Connect with Google
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
