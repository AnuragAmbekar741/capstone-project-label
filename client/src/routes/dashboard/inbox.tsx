import { createFileRoute } from "@tanstack/react-router";
import { MailView } from "@/components/dashboard/MailView";

export const Route = createFileRoute("/dashboard/inbox")({
  component: MailView,
});
