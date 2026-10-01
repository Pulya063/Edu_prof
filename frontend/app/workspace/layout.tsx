import type { Metadata } from "next";
import Link from "next/link";
import "../styles/workspace.css";
import "../styles/workspace-panels.css";
import WorkspaceNav from "./WorkspaceNav";
import AvatarDropdown from "./AvatarDropdown";

export const metadata: Metadata = {
  title: "Workspace",
  description: "A private Fence report connecting an education path with career and financial outcomes.",
  robots: { index: false, follow: false },
};

export default function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="workspace-shell">
      <aside className="workspace-rail" aria-label="Workspace navigation">
        <Link href="/workspace/overview" className="workspace-brand" aria-label="Fence workspace">
          <span aria-hidden="true"><i />F</span><b>Fence</b>
        </Link>
        <WorkspaceNav />
        <div className="workspace-rail-foot">
          <Link href="/contact" className="workspace-help-link">
            <span aria-hidden="true">?</span> Help
          </Link>
          <p>Education today.<br />A brighter tomorrow.</p>
        </div>
      </aside>
      <main className="workspace-main" id="report">
        <header className="workspace-topbar" aria-label="Workspace header">
          <div className="workspace-topbar-end">
            <AvatarDropdown />
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
