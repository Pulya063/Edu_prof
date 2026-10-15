import type { Metadata } from "next";
import { Suspense } from "react";
import SimulationClient from "./SimulationClient";

export const metadata: Metadata = { title: "Roadmap simulation" };
export default function RoadmapSimulationPage() {
  return <Suspense fallback={<main className="sketch-page"><div className="workspace-status">Loading simulation…</div></main>}><SimulationClient /></Suspense>;
}
