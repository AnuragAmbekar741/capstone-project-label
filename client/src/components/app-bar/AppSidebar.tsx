import * as React from "react";
import { Tag } from "lucide-react";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useCurrentUser } from "@/hooks/auth/useCurrentUser";
import { useGmailAccounts } from "@/hooks/gmail/useGmailAccount";
import { useGetFolder } from "@/hooks/imap/useFolders";
import { mapFoldersToMenuItems } from "@/utils/folderMapper";
import { Skeleton } from "@/components/ui/skeleton";

export const AppSidebar: React.FC = () => {
  const { data: user } = useCurrentUser();
  const router = useRouterState();
  const currentPath = router.location.pathname;
  const { data: gmailAccountsData } = useGmailAccounts();
  const accountId = gmailAccountsData?.accounts?.[0]?.id;

  // Fetch folders from API
  const { data: folders, isLoading: foldersLoading } = useGetFolder(
    accountId || ""
  );

  // Map folders to menu items
  const { systemFolders, customLabels } = React.useMemo(() => {
    if (!folders) return { systemFolders: [], customLabels: [] };
    return mapFoldersToMenuItems(folders);
  }, [folders]);

  return (
    <Sidebar className="border-r">
      {/* Header */}
      <SidebarHeader className="border-b px-6 py-3.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-primary text-primary-foreground">
            <Tag className="h-3 w-3" />
          </div>
          <span className="text-xl leading- font-light">LABEL</span>
        </div>
      </SidebarHeader>

      {/* Content */}
      <SidebarContent>
        {/* Main Menu Items - System Folders */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {foldersLoading
                ? // Loading state
                  Array.from({ length: 4 }).map((_, i) => (
                    <SidebarMenuItem key={i}>
                      <Skeleton className="h-8 w-full" />
                    </SidebarMenuItem>
                  ))
                : systemFolders.map((folder) => {
                    const Icon = folder.icon;
                    const isActive = currentPath === folder.href;

                    return (
                      <SidebarMenuItem key={folder.id}>
                        <SidebarMenuButton asChild isActive={isActive}>
                          <Link to={folder.href}>
                            <Icon className="h-4 w-4" />
                            <span>{folder.displayName}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    );
                  })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <Separator className="my-4" />

        {/* Labels Section - Custom Folders */}
        {customLabels.length > 0 && (
          <SidebarGroup>
            <div className="px-4 pb-2 text-xs font-semibold text-muted-foreground">
              Labels
            </div>
            <SidebarGroupContent>
              <SidebarMenu>
                {customLabels.map((label) => {
                  const Icon = label.icon;
                  const isActive = currentPath === label.href;

                  return (
                    <SidebarMenuItem key={label.id}>
                      <SidebarMenuButton asChild isActive={isActive}>
                        <Link to={label.href}>
                          <Icon className="h-4 w-4" />
                          <span className="truncate">{label.displayName}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="border-t p-4">
        <div className="flex items-center gap-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback>
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground truncate">
              {user?.email}
            </p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
};
