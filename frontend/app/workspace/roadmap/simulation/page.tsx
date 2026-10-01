import type { Metadata } from "next";
import SimulationClient from "./SimulationClient";

export const metadata: Metadata = { title: "Roadmap simulation" };
export default function RoadmapSimulationPage() { return <SimulationClient />; }
