import type { Metadata } from "next";
import "../styles/workspace.css";
import "../styles/workspace-panels.css";
import AvatarDropdown from "./AvatarDropdown";
import WorkspaceAuthGuard from "@/components/auth/WorkspaceAuthGuard";
import WorkspaceSidebar from "./WorkspaceSidebar";

export const metadata: Metadata = {
  title: "Workspace",
  description: "A private Fence report connecting an education path with career and financial outcomes.",
  robots: { index: false, follow: false },
};

export default function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <WorkspaceAuthGuard>
      <div className="workspace-shell">
        <WorkspaceSidebar />
        <main className="workspace-main" id="report">
          <header className="workspace-topbar" aria-label="Workspace header">
            <div className="workspace-topbar-end">
              <AvatarDropdown />
            </div>
          </header>
          {children}
        </main>
      </div>
    </WorkspaceAuthGuard>
  );
}
