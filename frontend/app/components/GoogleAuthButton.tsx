"use client";

import { useEffect, useState } from "react";

type ProviderState = "loading" | "ready" | "unconfigured" | "unavailable";

export const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  cancelled: "Google sign-in was cancelled.",
  google_failed: "Google sign-in failed. Try again or use email and password.",
  email_unverified: "Your Google email is not verified. Verify it with Google or sign in with email.",
  account_disabled: "This account is disabled. Contact support.",
  unavailable: "Sign-in is temporarily unavailable. Try again in a moment.",
};

/** Reads ?next from the current URL and only forwards same-site workspace/payment paths. */
function safeNextPath(): string | null {
  const next = new URLSearchParams(window.location.search).get("next");
  if (!next || !next.startsWith("/") || next.startsWith("//")) return null;
  return next.startsWith("/workspace/") || next.startsWith("/payment") ? next : null;
}

export default function GoogleAuthButton({ label }: { label: string }) {
  const [state, setState] = useState<ProviderState>("loading");
  const [href, setHref] = useState("/api/auth/login/google");

  useEffect(() => {
    const next = safeNextPath();
    if (next) setHref(`/api/auth/login/google?next=${encodeURIComponent(next)}`);
    fetch("/api/auth/providers", { headers: { Accept: "application/json" }, credentials: "include" })
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(String(res.status)))))
      .then((body: { google?: { configured?: boolean } }) => setState(body.google?.configured ? "ready" : "unconfigured"))
      .catch(() => setState("unavailable"));
  }, []);

  const content = (
    <>
      <svg className="auth-google-mark" viewBox="0 0 18 18" width="18" height="18" aria-hidden="true">
        <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62Z" />
        <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18Z" />
        <path fill="#FBBC05" d="M3.97 10.72A5.4 5.4 0 0 1 3.68 9c0-.6.1-1.18.29-1.72V4.95H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.05l3.01-2.33Z" />
        <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58Z" />
      </svg>
      <span>{label}</span>
    </>
  );

  if (state === "ready") {
    return <a className="auth-google" href={href}>{content}</a>;
  }

  const hint = state === "loading"
    ? "Checking Google sign-in…"
    : state === "unconfigured"
      ? "Google sign-in is not configured on this environment yet."
      : "Google sign-in status is unavailable right now.";
  return (
    <div className="auth-google-wrap">
      <button className="auth-google" type="button" disabled aria-disabled="true" aria-describedby="auth-google-hint">{content}</button>
      <p className="auth-google-hint" id="auth-google-hint">{hint}</p>
    </div>
  );
}
