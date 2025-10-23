import { createFileRoute } from "@tanstack/react-router";
import { Junk } from "@/components/dashboard/junk/Junk";

export const Route = createFileRoute("/dashboard/junk")({
  component: Junk,
});
