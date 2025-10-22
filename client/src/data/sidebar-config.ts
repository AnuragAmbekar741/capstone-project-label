import {
  Inbox,
  File,
  Send,
  Trash,
  Trash2,
  Archive,
  type LucideIcon,
} from "lucide-react";

export interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  count?: number;
  isActive?: boolean;
}

export interface Label {
  id: string;
  label: string;
  color: string;
  count: number;
}

export const menuItems: MenuItem[] = [
  { id: "inbox", label: "Inbox", icon: Inbox, count: 128, isActive: true },
  { id: "drafts", label: "Drafts", icon: File, count: 9 },
  { id: "sent", label: "Sent", icon: Send },
  { id: "junk", label: "Junk", icon: Trash, count: 23 },
  { id: "trash", label: "Trash", icon: Trash2 },
  { id: "archive", label: "Archive", icon: Archive },
];

export const labels: Label[] = [
  { id: "social", label: "Social", color: "bg-red-500", count: 972 },
  { id: "updates", label: "Updates", color: "bg-blue-500", count: 342 },
  { id: "forums", label: "Forums", color: "bg-green-500", count: 128 },
  { id: "shopping", label: "Shopping", color: "bg-purple-500", count: 8 },
  { id: "promotions", label: "Promotions", color: "bg-orange-500", count: 21 },
];
