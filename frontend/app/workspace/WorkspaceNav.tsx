"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function WorkspaceNav() {
  const pathname = usePathname();

  const isActive = (href: string, exact = true) => exact ? pathname === href : pathname.startsWith(href);

  return (
    <nav>
      <Link href="/workspace/overview" aria-current={isActive("/workspace/overview") ? "page" : undefined}>
        <NavIcon name="home" />
        <span className="workspace-nav-label">Overview</span>
      </Link>
      <Link href="/workspace/scenario/new" aria-current={isActive("/workspace/scenario/new") ? "page" : undefined}>
        <NavIcon name="calculator" />
        <span className="workspace-nav-label">ROI Calculator</span>
      </Link>

      <Link href="/workspace/scenarios" aria-current={isActive("/workspace/scenarios", false) ? "page" : undefined}>
        <NavIcon name="bookmark" />
        <span className="workspace-nav-label">Saved Scenarios</span>
      </Link>
      <Link href="/workspace/compare" aria-current={isActive("/workspace/compare") ? "page" : undefined}>
        <NavIcon name="compare" />
        <span className="workspace-nav-label">Compare Universities</span>
      </Link>

      <Link href="/workspace/roadmap" className="ws-nav-group-parent" aria-current={isActive("/workspace/roadmap") ? "page" : undefined}>
        <NavIcon name="map" />
        <span className="workspace-nav-label">Roadmap</span>
      </Link>
      <div className="ws-nav-group" aria-label="Roadmap sub-items">
        <Link href="/workspace/roadmap" className="ws-nav-sub" aria-current={isActive("/workspace/roadmap") ? "page" : undefined}>
          <span className="workspace-nav-label">Dashboard</span>
        </Link>
        <Link href="/workspace/roadmap/simulation" className="ws-nav-sub" aria-current={isActive("/workspace/roadmap/simulation") ? "page" : undefined}>
          <span className="workspace-nav-label">Simulation</span>
        </Link>
        <Link href="/workspace/roadmap/plan" className="ws-nav-sub" aria-current={isActive("/workspace/roadmap/plan") ? "page" : undefined}>
          <span className="workspace-nav-label">My plan</span>
        </Link>
      </div>

      <Link href="/workspace/courses" aria-current={isActive("/workspace/courses") ? "page" : undefined}>
        <NavIcon name="search" />
        <span className="workspace-nav-label">Course search</span>
      </Link>
    </nav>
  );
}

function NavIcon({ name }: { name: string }) {
  if (name === "home") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 10.5 12 3l8.5 7.5M5.5 9.5v10h13v-10M9.5 19.5v-6h5v6" /></svg>;
  if (name === "calculator") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M7.5 6.5h9v3h-9zM8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01M16 17h.01" /></svg>;
  if (name === "bookmark") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h14a1 1 0 0 1 1 1v17l-8-4-8 4V4a1 1 0 0 1 1-1z" /></svg>;
  if (name === "compare") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 20H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5M18 20a2 2 0 0 0 2-2V9m-2 11 2-2m-2 2-2-2M13 4h6a1 1 0 0 1 1 1v4" /></svg>;
  if (name === "map") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" /></svg>;
  if (name === "search") return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.35-4.35" /></svg>;
  return <svg className="workspace-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /></svg>;
}
