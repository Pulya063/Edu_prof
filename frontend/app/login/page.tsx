"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import "../styles/auth.css";

type ApiError = {
  detail?: string | Array<{ msg?: string }>;
};

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiError;
    if (typeof body.detail === "string") return body.detail;
    const msg = body.detail?.find((d) => d.msg)?.msg;
    if (msg) return msg.replace(/^Value error,\s*/i, "");
  } catch {
    /* ignore */
  }
  if (res.status === 401) return "Incorrect email or password. Try again.";
  if (res.status === 429) return "Too many attempts. Wait a moment before trying again.";
  return "Could not sign in right now. Check your connection and try again.";
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        setError(await parseError(res));
        return;
      }

      router.push("/workspace/overview");
      router.refresh();
    } catch {
      setError("Network error. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      {/* Left brand panel */}
      <div className="auth-brand-panel" aria-hidden="true">
        <Link href="/workspace/overview" className="auth-brand-logo">
          <span>F</span>
          <div>
            <b>Fence</b>
            <small>Education decisions</small>
          </div>
        </Link>

        <div className="auth-brand-body">
          <p>Sign in to your workspace</p>
          <h1>
            Your next<br />
            <em>education</em><br />
            decision.
          </h1>
          <span>
            Model education costs, salary assumptions, payback periods
            and career paths — all in one connected view.
          </span>
        </div>

        <p className="auth-brand-footer">Education today. A brighter tomorrow.</p>
      </div>

      {/* Right form panel */}
      <div className="auth-form-panel">
        <div className="auth-form-header">
          <p>Welcome back</p>
          <h2>Sign in to Fence</h2>
        </div>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {error && (
            <div className="auth-feedback" role="alert">
              {error}
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={busy}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="Your password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={busy}
            />
          </div>

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
            <span aria-hidden="true">→</span>
          </button>

          <p className="auth-trust">
            Deterministic calculation · no AI-generated financial values
          </p>
        </form>

        <div className="auth-divider" style={{ marginTop: 28 }}>or</div>

        <p className="auth-alt-link" style={{ marginTop: 18 }}>
          Don&apos;t have an account?{" "}
          <Link href="/register">Create one</Link>
        </p>

        <p className="auth-alt-link" style={{ marginTop: 12 }}>
          <Link href="/reset-password">Forgot your password?</Link>
        </p>
      </div>
    </div>
  );
}
