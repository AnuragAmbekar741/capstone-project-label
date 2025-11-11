import { createFileRoute } from "@tanstack/react-router";
import { MailView } from "@/components/dashboard/MailView";

export const Route = createFileRoute("/dashboard/sent")({
  component: MailView,
});
