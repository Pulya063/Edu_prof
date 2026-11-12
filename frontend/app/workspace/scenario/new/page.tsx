import type { Metadata } from "next";
import ScenarioBuilder from "./ScenarioBuilder";

export const metadata: Metadata = {
  title: "Build a decision scenario",
  description: "Create a private education-to-career scenario and calculate its deterministic financial outlook.",
  robots: { index: false, follow: false },
};

export default function NewScenarioPage() {
  return <ScenarioBuilder />;
}
