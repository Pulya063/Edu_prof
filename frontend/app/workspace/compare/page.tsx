import type { Metadata } from "next";
import CompareClient from "./CompareClient";

export const metadata: Metadata = { title: "Compare universities" };
export default function CompareUniversitiesPage() { return <CompareClient />; }
