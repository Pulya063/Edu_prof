import type { Metadata } from "next";
import SettingsClient from "./SettingsClient";

export const metadata: Metadata = { title: "Workspace settings" };
export default function SettingsPage() { return <SettingsClient />; }
