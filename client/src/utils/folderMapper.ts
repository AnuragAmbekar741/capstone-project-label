import { type FolderResponse } from "@/api/imap/imap";
import {
  Inbox,
  File,
  Send,
  Trash,
  Star,
  Archive,
  AlertCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface MappedFolder {
  id: string;
  name: string;
  displayName: string;
  icon: LucideIcon;
  href: string;
  flags: string[];
  isSystemFolder: boolean;
}

/**
 * Map folder flags to icon and route
 */
const getFolderConfig = (
  name: string,
  flags: string[]
): {
  icon: LucideIcon;
  href: string;
  displayName: string;
} | null => {
  const upperFlags = flags.map((f) => f.toUpperCase());

  // System folders based on flags
  if (upperFlags.includes("\\DRAFTS")) {
    return { icon: File, href: "/dashboard/draft", displayName: "Drafts" };
  }
  if (upperFlags.includes("\\SENT")) {
    return { icon: Send, href: "/dashboard/sent", displayName: "Sent" };
  }
  if (upperFlags.includes("\\TRASH")) {
    return { icon: Trash, href: "/dashboard/trash", displayName: "Trash" };
  }
  if (upperFlags.includes("\\JUNK") || upperFlags.includes("\\SPAM")) {
    return { icon: AlertCircle, href: "/dashboard/junk", displayName: "Spam" };
  }
  if (upperFlags.includes("\\FLAGGED") || name.includes("Starred")) {
    return { icon: Star, href: "/dashboard/starred", displayName: "Starred" };
  }
  if (upperFlags.includes("\\ALL") || name.includes("All Mail")) {
    return { icon: Archive, href: "/dashboard/all", displayName: "All Mail" };
  }
  if (name === "INBOX" || upperFlags.includes("\\INBOX")) {
    return { icon: Inbox, href: "/dashboard/inbox", displayName: "Inbox" };
  }

  return null;
};

/**
 * Map folders from API to sidebar menu items
 */
export const mapFoldersToMenuItems = (
  folders: FolderResponse[]
): {
  systemFolders: MappedFolder[];
  customLabels: MappedFolder[];
} => {
  const systemFolders: MappedFolder[] = [];
  const customLabels: MappedFolder[] = [];

  folders.forEach((folder) => {
    const config = getFolderConfig(folder.name, folder.flags);

    // Skip [Gmail] parent folder (it's just a container)
    if (folder.name === "[Gmail]" && folder.flags.includes("\\Noselect")) {
      return;
    }

    if (config) {
      // System folder
      systemFolders.push({
        id: folder.name.toLowerCase().replace(/[^a-z0-9]/g, "-"),
        name: folder.name,
        displayName: config.displayName,
        icon: config.icon,
        href: config.href,
        flags: folder.flags,
        isSystemFolder: true,
      });
    } else {
      // Custom label/folder
      customLabels.push({
        id: folder.name.toLowerCase().replace(/[^a-z0-9]/g, "-"),
        name: folder.name,
        displayName: folder.name,
        icon: File, // Default icon for custom labels
        href: `/dashboard/folder/${encodeURIComponent(folder.name)}`,
        flags: folder.flags,
        isSystemFolder: false,
      });
    }
  });

  // Sort system folders in a specific order
  const folderOrder = [
    "inbox",
    "drafts",
    "sent",
    "starred",
    "all",
    "trash",
    "spam",
    "junk",
  ];
  systemFolders.sort((a, b) => {
    const aIndex = folderOrder.findIndex((order) => a.href.includes(order));
    const bIndex = folderOrder.findIndex((order) => b.href.includes(order));
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  return { systemFolders, customLabels };
};

/**
 * Get folder name from route path
 */
export const getFolderNameFromRoute = (
  routePath: string,
  folders: FolderResponse[] | undefined
): string => {
  if (!folders) {
    // Default fallback based on route
    if (routePath.includes("/draft")) return "[Gmail]/Drafts";
    if (routePath.includes("/sent")) return "[Gmail]/Sent Mail";
    if (routePath.includes("/junk") || routePath.includes("/spam"))
      return "[Gmail]/Spam";
    if (routePath.includes("/trash")) return "[Gmail]/Trash";
    if (routePath.includes("/starred")) return "[Gmail]/Starred";
    if (routePath.includes("/all")) return "[Gmail]/All Mail";
    return "INBOX"; // Default
  }

  // Check if it's a custom folder route
  if (routePath.includes("/folder/")) {
    const folderName = decodeURIComponent(routePath.split("/folder/")[1]);
    return folderName;
  }

  // Map system routes to folder names
  const { systemFolders, customLabels } = mapFoldersToMenuItems(folders);
  const allFolders = [...systemFolders, ...customLabels];

  const matchedFolder = allFolders.find((folder) => folder.href === routePath);

  if (matchedFolder) {
    return matchedFolder.name;
  }

  // Fallback based on route path
  if (routePath.includes("/draft")) return "[Gmail]/Drafts";
  if (routePath.includes("/sent")) return "[Gmail]/Sent Mail";
  if (routePath.includes("/junk") || routePath.includes("/spam"))
    return "[Gmail]/Spam";
  if (routePath.includes("/trash")) return "[Gmail]/Trash";
  if (routePath.includes("/starred")) return "[Gmail]/Starred";
  if (routePath.includes("/all")) return "[Gmail]/All Mail";

  return "INBOX"; // Default
};
