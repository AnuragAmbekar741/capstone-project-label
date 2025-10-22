import * as React from "react";
import {
  Search,
  Inbox,
  File,
  Send,
  Trash2,
  Archive,
  MoreVertical,
  Reply,
  ReplyAll,
  Forward,
  Clock,
  ArchiveX,
  Trash,
  PowerOff,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { TokenCookies } from "@/utils/cookie";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
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
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { useCurrentUser } from "@/hooks/auth/useCurrentUser";

interface Mail {
  id: string;
  name: string;
  email: string;
  subject: string;
  text: string;
  date: string;
  read: boolean;
  labels: string[];
}

const mails: Mail[] = [
  {
    id: "1",
    name: "William Smith",
    email: "williamsmith@example.com",
    subject: "Meeting Tomorrow",
    text: "Hi, let's have a meeting tomorrow to discuss the project. I've been reviewing the project details and have some ideas I'd like to share. It's crucial that we align on our next steps to ensure the project's success...",
    date: "almost 2 years ago",
    read: false,
    labels: ["meeting", "work", "important"],
  },
  {
    id: "2",
    name: "Alice Smith",
    email: "alicesmith@example.com",
    subject: "Re: Project Update",
    text: "Thank you for the project update. It looks great! I've gone through the report, and the progress is impressive. The team has done a fantastic job...",
    date: "almost 2 years ago",
    read: true,
    labels: ["work", "important"],
  },
  {
    id: "3",
    name: "Bob Johnson",
    email: "bobjohnson@example.com",
    subject: "Weekend Plans",
    text: "Any plans for the weekend? I was thinking of going hiking in the nearby mountains. It's been a while since we had some outdoor fun...",
    date: "over 2 years ago",
    read: true,
    labels: ["personal"],
  },
  // Add more sample emails as needed
];

export default function MailDashboard() {
  const { data: user } = useCurrentUser();
  const navigate = useNavigate();
  const [selectedMail, setSelectedMail] = React.useState<Mail>(mails[0]);
  const handleLogout = () => {
    TokenCookies.clearTokens();
    toast.success("Logged out successfully");
    navigate({ to: "/auth" });
  };
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        {/* Sidebar */}
        <Sidebar className="border-r">
          <SidebarHeader className="border-b px-6 py-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Inbox className="h-4 w-4" />
              </div>
              <span className="text-lg font-semibold">Mail</span>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton isActive>
                      <Inbox className="h-4 w-4" />
                      <span>Inbox</span>
                      <Badge variant="secondary" className="ml-auto">
                        128
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <File className="h-4 w-4" />
                      <span>Drafts</span>
                      <Badge variant="secondary" className="ml-auto">
                        9
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <Send className="h-4 w-4" />
                      <span>Sent</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <Trash className="h-4 w-4" />
                      <span>Junk</span>
                      <Badge variant="secondary" className="ml-auto">
                        23
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <Trash2 className="h-4 w-4" />
                      <span>Trash</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <Archive className="h-4 w-4" />
                      <span>Archive</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <Separator className="my-4" />

            <SidebarGroup>
              <div className="px-4 pb-2 text-xs font-semibold text-muted-foreground">
                Labels
              </div>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <div className="h-2 w-2 rounded-full bg-red-500" />
                      <span>Social</span>
                      <Badge variant="secondary" className="ml-auto">
                        972
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      <span>Updates</span>
                      <Badge variant="secondary" className="ml-auto">
                        342
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                      <span>Forums</span>
                      <Badge variant="secondary" className="ml-auto">
                        128
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <div className="h-2 w-2 rounded-full bg-purple-500" />
                      <span>Shopping</span>
                      <Badge variant="secondary" className="ml-auto">
                        8
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton>
                      <div className="h-2 w-2 rounded-full bg-orange-500" />
                      <span>Promotions</span>
                      <Badge variant="secondary" className="ml-auto">
                        21
                      </Badge>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="border-t p-4">
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                {/* <AvatarImage src={user?.picture ?? ""} /> */}
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

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          <div className="border-b px-4 py-3 flex items-center gap-2">
            <SidebarTrigger />
            <div className="flex-1" />
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              Logout
              <PowerOff className="h-4 w-4 mr-2" />
            </Button>
          </div>

          <ResizablePanelGroup direction="horizontal" className="flex-1">
            {/* Mail List Panel */}
            <ResizablePanel defaultSize={30} minSize={25}>
              <div className="flex flex-col h-full">
                <div className="p-4 space-y-4">
                  <h1 className="text-xl font-bold">Inbox</h1>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input placeholder="Search" className="pl-10" />
                  </div>
                </div>

                <Tabs defaultValue="all" className="px-4">
                  <TabsList>
                    <TabsTrigger value="all">All mail</TabsTrigger>
                    <TabsTrigger value="unread">Unread</TabsTrigger>
                  </TabsList>
                </Tabs>

                <ScrollArea className="flex-1">
                  <div className="flex flex-col gap-2 p-4 pt-0">
                    {mails.map((mail) => (
                      <button
                        key={mail.id}
                        className={cn(
                          "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent",
                          selectedMail.id === mail.id && "bg-muted"
                        )}
                        onClick={() => setSelectedMail(mail)}
                      >
                        <div className="flex w-full flex-col gap-1">
                          <div className="flex items-center">
                            <div className="flex items-center gap-2">
                              <div className="font-semibold">{mail.name}</div>
                              {!mail.read && (
                                <span className="flex h-2 w-2 rounded-full bg-blue-600" />
                              )}
                            </div>
                            <div className="ml-auto text-xs text-muted-foreground">
                              {mail.date}
                            </div>
                          </div>
                          <div className="text-xs font-medium">
                            {mail.subject}
                          </div>
                        </div>
                        <div className="line-clamp-2 text-xs text-muted-foreground">
                          {mail.text}
                        </div>
                        {mail.labels.length > 0 && (
                          <div className="flex items-center gap-2">
                            {mail.labels.map((label) => (
                              <Badge key={label} variant="secondary">
                                {label}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Mail Detail Panel */}
            <ResizablePanel defaultSize={70}>
              <div className="flex h-full flex-col">
                <div className="flex items-center border-b p-4">
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon">
                      <Archive className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <ArchiveX className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    <Separator orientation="vertical" className="h-6" />
                    <Button variant="ghost" size="icon">
                      <Clock className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="ml-auto flex items-center gap-2">
                    <Button variant="ghost" size="icon">
                      <Reply className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <ReplyAll className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Forward className="h-4 w-4" />
                    </Button>
                  </div>
                  <Separator orientation="vertical" className="mx-2 h-6" />
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>Mark as unread</DropdownMenuItem>
                      <DropdownMenuItem>Star thread</DropdownMenuItem>
                      <DropdownMenuItem>Add label</DropdownMenuItem>
                      <DropdownMenuItem>Mute thread</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <ScrollArea className="flex-1">
                  <div className="flex flex-col gap-4 p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <Avatar>
                          <AvatarFallback>
                            {selectedMail.name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </AvatarFallback>
                        </Avatar>
                        <div className="grid gap-1">
                          <div className="font-semibold">
                            {selectedMail.subject}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Reply-To: {selectedMail.email}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {selectedMail.date}
                          </div>
                        </div>
                      </div>
                    </div>
                    <Separator />
                    <div className="text-sm">
                      <p>{selectedMail.text}</p>
                    </div>
                  </div>
                </ScrollArea>
                <Separator />
                <div className="p-4">
                  <div className="grid gap-4">
                    <Button size="sm" className="ml-auto">
                      Send
                    </Button>
                  </div>
                </div>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>
    </SidebarProvider>
  );
}
