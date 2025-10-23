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
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useCurrentUser } from "@/hooks/auth/useCurrentUser";
import { menuItems, labels } from "@/data/sidebar-config";

export const AppSidebar: React.FC = () => {
  const { data: user } = useCurrentUser();
  const router = useRouterState();
  const currentPath = router.location.pathname;

  return (
    <Sidebar className="border-r">
      {/* Header */}
      <SidebarHeader className="border-b px-6 py-3.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Tag className="h-4 w-4" />
          </div>
          <span className="text-xl leading- font-light">LABEL</span>
        </div>
      </SidebarHeader>

      {/* Content */}
      <SidebarContent>
        {/* Main Menu Items */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPath === item.href;

                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link to={item.href}>
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                        {item.count && (
                          <Badge variant="secondary" className="ml-auto">
                            {item.count}
                          </Badge>
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <Separator className="my-4" />

        {/* Labels Section */}
        <SidebarGroup>
          <div className="px-4 pb-2 text-xs font-semibold text-muted-foreground">
            Labels
          </div>
          <SidebarGroupContent>
            <SidebarMenu>
              {labels.map((label) => (
                <SidebarMenuItem key={label.id}>
                  <SidebarMenuButton>
                    <div className={`h-2 w-2 rounded-full ${label.color}`} />
                    <span>{label.label}</span>
                    <Badge variant="secondary" className="ml-auto">
                      {label.count}
                    </Badge>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
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
