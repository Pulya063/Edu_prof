// The left workspace rail: the person's own choice is remembered; some pages fold it while they are open.
const STORAGE_KEY = "fence.workspace-rail";

function savedCollapsed(): boolean {
  try { return window.localStorage.getItem(STORAGE_KEY) === "collapsed"; } catch { return false; }
}

function show(collapsed: boolean) {
  const root = document.documentElement;
  if (collapsed) root.dataset.wsRail = "collapsed"; else delete root.dataset.wsRail;
}

/** On first load: never unfolds, because a page may already have folded the rail. */
export function restoreRail() {
  if (savedCollapsed()) show(true);
}

export function setRailCollapsed(collapsed: boolean) {
  show(collapsed);
  try { window.localStorage.setItem(STORAGE_KEY, collapsed ? "collapsed" : "expanded"); } catch { /* the choice lasts until reload */ }
}

/** Fold the rail for a split view; the returned function goes back to what the person chose. */
export function foldRail(): () => void {
  show(true);
  return () => show(savedCollapsed());
}
