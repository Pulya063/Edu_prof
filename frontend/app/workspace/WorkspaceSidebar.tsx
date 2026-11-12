"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import WorkspaceNav from "./WorkspaceNav";
import { restoreRail, setRailCollapsed } from "@/lib/railState";
import "../styles/workspace-rail.css";

export default function WorkspaceSidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Pages fold the rail too, so the button reads the actual state.
  useEffect(() => {
    restoreRail();
    const root = document.documentElement;
    const sync = () => setCollapsed(root.dataset.wsRail === "collapsed");
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ["data-ws-rail"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setOpen(false);
    // Desktop scrolls inside .workspace-main, so a new page must start at its top.
    document.querySelector(".workspace-main")?.scrollTo({ top: 0 });
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <>
      <button
        className="workspace-menu-toggle"
        type="button"
        aria-label={open ? "Close workspace navigation" : "Open workspace navigation"}
        aria-controls="workspace-navigation"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span aria-hidden="true" />
        <span aria-hidden="true" />
        <span aria-hidden="true" />
      </button>
      <button
        className="workspace-sidebar-backdrop"
        type="button"
        aria-label="Close workspace navigation"
        data-open={open}
        onClick={() => setOpen(false)}
      />
      <aside id="workspace-navigation" className="workspace-rail" aria-label="Workspace navigation" data-open={open}>
        <div className="workspace-rail-head">
          <Link href="/workspace/overview" className="workspace-brand" aria-label="Fence workspace">
            <span aria-hidden="true"><i />F</span><b>Fence</b>
          </Link>
          {/* Sits on the rail's edge next to the logo, so it is in the same place folded or not. */}
          <button type="button" className="workspace-rail-toggle" aria-pressed={collapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => setRailCollapsed(!collapsed)}>
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="m15 6-6 6 6 6" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        </div>
        <WorkspaceNav />
        <div className="workspace-rail-foot">
          <Link href="/contact" className="workspace-help-link" title="Help">
            <span className="workspace-help-icon" aria-hidden="true">?</span><span className="workspace-nav-label">Help</span>
          </Link>
          <p>Education today.<br />A brighter tomorrow.</p>
        </div>
      </aside>
    </>
  );
}
