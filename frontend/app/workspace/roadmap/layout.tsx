"use client";

import Link from "next/link";
import { useWorkspaceAuth } from "@/components/auth/WorkspaceAuthGuard";
import { WorkspacePageHeader } from "../WorkspaceUI";

// Roadmap is admin-only for now; the API answers 403 to everyone else, so the pages are not rendered at all.
export default function RoadmapLayout({ children }: { children: React.ReactNode }) {
  const { user } = useWorkspaceAuth();
  if (user.is_admin) return <>{children}</>;
  return (
    <main className="sketch-page">
      <WorkspacePageHeader section="Roadmap" title="Roadmap is not available yet" highlight="not available" description="Career roadmaps are being prepared and are open to administrators only for now." />
      <div className="workspace-status" role="status">Your calculations and university comparisons work as usual. <Link href="/workspace/overview">Back to overview</Link></div>
    </main>
  );
}
