"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import WorkspaceNav from "./WorkspaceNav";

export default function WorkspaceSidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
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
    </>
  );
}
