import { createFileRoute } from "@tanstack/react-router";
import { LandingPage } from "@/views/landing-page/LandingPage";

export const Route = createFileRoute("/landing")({
  component: LandingPage,
});
