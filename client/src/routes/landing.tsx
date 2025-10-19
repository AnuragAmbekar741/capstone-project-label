import { createFileRoute } from "@tanstack/react-router";
import { requireGuest } from "@/utils/route-guards";
import { LandingPage } from "@/views/landing-page/LandingPage";

export const Route = createFileRoute("/landing")({
  beforeLoad: requireGuest,
  component: LandingPage,
});
