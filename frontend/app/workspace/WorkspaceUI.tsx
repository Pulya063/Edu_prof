import type { ReactNode } from "react";

type IconName =
  | "arrow" | "book" | "briefcase" | "check" | "clock" | "code"
  | "database" | "document" | "globe" | "graduation" | "info" | "laptop"
  | "map" | "pin" | "search" | "settings" | "spark" | "target" | "tasks"
  | "user" | "video";

export function Icon({ name, size = 22 }: { name: IconName; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  if (name === "arrow") return <svg {...common}><path d="M5 12h14M14 7l5 5-5 5" /></svg>;
  if (name === "book") return <svg {...common}><path d="M3 5.5A3.5 3.5 0 0 1 6.5 2H11v18H6.5A3.5 3.5 0 0 0 3 23V5.5ZM21 5.5A3.5 3.5 0 0 0 17.5 2H13v18h4.5A3.5 3.5 0 0 1 21 23V5.5Z" /></svg>;
  if (name === "briefcase") return <svg {...common}><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V4h8v3M3 12h18"/></svg>;
  if (name === "check") return <svg {...common}><path d="m5 12 4 4L19 6" /></svg>;
  if (name === "clock") return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>;
  if (name === "code") return <svg {...common}><path d="m8 9-3 3 3 3m8-6 3 3-3 3m-2-9-4 12"/></svg>;
  if (name === "database") return <svg {...common}><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>;
  if (name === "document") return <svg {...common}><path d="M6 2h8l4 4v16H6zM14 2v5h5M9 12h6M9 16h6"/></svg>;
  if (name === "globe") return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.4 4 5.4 4 9s-1.5 6.6-4 9c-2.5-2.4-4-5.4-4-9s1.5-6.6 4-9Z"/></svg>;
  if (name === "graduation") return <svg {...common}><path d="m2 9 10-5 10 5-10 5L2 9Z"/><path d="M6 11.5V17c3.7 2.8 8.3 2.8 12 0v-5.5M22 9v6"/></svg>;
  if (name === "info") return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></svg>;
  if (name === "laptop") return <svg {...common}><rect x="4" y="4" width="16" height="12" rx="1.5"/><path d="M2 20h20M8 20l1-4h6l1 4"/></svg>;
  if (name === "map") return <svg {...common}><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15"/></svg>;
  if (name === "pin") return <svg {...common}><path d="M20 10c0 5.5-8 12-8 12S4 15.5 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>;
  if (name === "search") return <svg {...common}><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>;
  if (name === "settings") return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></svg>;
  if (name === "spark") return <svg {...common}><path d="m12 2 1.7 5.3L19 9l-5.3 1.7L12 16l-1.7-5.3L5 9l5.3-1.7L12 2ZM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/></svg>;
  if (name === "target") return <svg {...common}><circle cx="11" cy="13" r="8"/><circle cx="11" cy="13" r="4"/><path d="m14 10 7-7M17 3h4v4"/></svg>;
  if (name === "tasks") return <svg {...common}><path d="m4 6 2 2 3-4M11 6h9M4 13l2 2 3-4M11 13h9M4 20l2 2 3-4M11 20h9"/></svg>;
  if (name === "user") return <svg {...common}><circle cx="12" cy="7" r="4"/><path d="M4 21c0-4.5 3.6-8 8-8s8 3.5 8 8"/></svg>;
  return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m10 9 5 3-5 3V9Z"/></svg>;
}

export function WorkspacePageHeader({
  section,
  title,
  highlight,
  description,
  children,
}: {
  section: string;
  title: string;
  highlight?: string;
  description: string;
  children?: ReactNode;
}) {
  const parts = highlight ? title.split(highlight) : [title];
  return (
    <header className="sketch-page-header">
      <p className="sketch-breadcrumb">Workspace <i>/</i> {section}</p>
      <div className="sketch-heading-row">
        <div>
          <h1>
            {highlight && parts.length > 1 ? <>{parts[0]}<span>{highlight}</span>{parts.slice(1).join(highlight)}</> : title}
          </h1>
          <p>{description}</p>
        </div>
        <span className="sketch-demo-badge">Demo data</span>
      </div>
      {children}
    </header>
  );
}

export function Topography() {
  return <span className="sketch-topography" aria-hidden="true" />;
}

