import type { Metadata } from "next";
import PlanClient from "./PlanClient";

export const metadata: Metadata = { title: "My career plan" };
export default function MyPlanPage() { return <PlanClient />; }
