import { createFileRoute } from "@tanstack/react-router";
import { Draft } from "@/components/dashboard/draft/Draft";

export const Route = createFileRoute("/dashboard/draft")({
  component: Draft,
});
