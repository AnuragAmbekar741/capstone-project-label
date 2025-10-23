import { createFileRoute } from "@tanstack/react-router";
import { Inbox } from "@/components/dashboard/inbox/Inbox";

export const Route = createFileRoute("/dashboard/inbox")({
  component: Inbox,
});
