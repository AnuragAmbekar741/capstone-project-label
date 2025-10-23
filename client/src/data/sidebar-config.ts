import { Inbox, File, Send, Trash, type LucideIcon } from "lucide-react";

export interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  count?: number;
  href: string;
}

export interface Label {
  id: string;
  label: string;
  color: string;
  count: number;
}

export const menuItems: MenuItem[] = [
  {
    id: "inbox",
    label: "Inbox",
    icon: Inbox,
    count: 128,
    href: "/dashboard/inbox",
  },
  {
    id: "drafts",
    label: "Drafts",
    icon: File,
    count: 9,
    href: "/dashboard/draft",
  },
  { id: "sent", label: "Sent", icon: Send, href: "/dashboard/sent" },
  {
    id: "junk",
    label: "Junk",
    icon: Trash,
    count: 23,
    href: "/dashboard/junk",
  },
  // { id: "trash", label: "Trash", icon: Trash2, href: "/dashboard/trash" },
  // {
  //   id: "archive",
  //   label: "Archive",
  //   icon: Archive,
  //   href: "/dashboard/archive",
  // },
];

export const labels: Label[] = [
  { id: "social", label: "Social", color: "bg-red-500", count: 972 },
  { id: "updates", label: "Updates", color: "bg-blue-500", count: 342 },
  { id: "forums", label: "Forums", color: "bg-green-500", count: 128 },
  { id: "shopping", label: "Shopping", color: "bg-purple-500", count: 8 },
  { id: "promotions", label: "Promotions", color: "bg-orange-500", count: 21 },
];
