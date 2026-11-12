/** Visible "the page is working" state, so nobody clicks around while data loads. */
export default function PageLoading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="ws-loading" role="status" aria-live="polite">
      <span className="ws-loading-bar" aria-hidden="true"><i /></span>
      <span className="ws-loading-spinner" aria-hidden="true" />
      <p>{label}…</p>
    </div>
  );
}
