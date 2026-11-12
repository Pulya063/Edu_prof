import PageLoading from "./PageLoading";

// Shown by Next.js while a workspace page loads after a click, so the person sees it is working.
export default function WorkspaceLoading() {
  return <PageLoading label="Opening the page" />;
}
