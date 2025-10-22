import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";
import { toast } from "sonner";

export function AppBar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    TokenCookies.clearTokens();
    toast.success("Logged out successfully");
    navigate({ to: "/auth" });
  };

  return (
    <div className="border-b px-4 py-3 flex items-center gap-2">
      <SidebarTrigger />
      <div className="flex-1" />
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        <LogOut className="h-4 w-4 mr-2" />
        Logout
      </Button>
    </div>
  );
}
