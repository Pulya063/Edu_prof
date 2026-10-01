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
  if (res.status === 409) return "An account with this email already exists. Sign in instead.";
  if (res.status === 422) return "Please check the form — some fields are invalid.";
  return "Could not create your account right now. Try again in a moment.";
}

function validatePassword(p: string): string | null {
  if (p.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Z]/.test(p)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(p)) return "Password must contain at least one lowercase letter.";
  if (!/[0-9]/.test(p)) return "Password must contain at least one digit.";
  return null;
}

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    const pwError = validatePassword(password);
    if (pwError) { setError(pwError); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }

    setBusy(true);
    try {
      const res = await fetch("/api/auth/register", {
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
          <p>Create your account</p>
          <h1>
            Start with<br />
            <em>clarity,</em><br />
            not guesswork.
          </h1>
          <span>
            Compare education costs, salary ranges and career paths
            with deterministic projections — no AI-generated numbers.
          </span>
        </div>

        <p className="auth-brand-footer">Education today. A brighter tomorrow.</p>
      </div>

      {/* Right form panel */}
      <div className="auth-form-panel">
        <div className="auth-form-header">
          <p>Get started — it&apos;s free</p>
          <h2>Create your account</h2>
        </div>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {error && (
            <div className="auth-feedback" role="alert">
              {error}
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
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
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              placeholder="At least 8 characters"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={busy}
            />
            <span className="auth-field-hint">
              Minimum 8 characters · uppercase · lowercase · digit
            </span>
          </div>

          <div className="auth-field">
            <label htmlFor="reg-confirm">Confirm password</label>
            <input
              id="reg-confirm"
              type="password"
              autoComplete="new-password"
              placeholder="Repeat your password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              disabled={busy}
            />
          </div>

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
            <span aria-hidden="true">→</span>
          </button>

          <p className="auth-trust">
            Deterministic calculation · no AI-generated financial values
          </p>
        </form>

        <div className="auth-divider" style={{ marginTop: 28 }}>already have an account?</div>

        <p className="auth-alt-link" style={{ marginTop: 18 }}>
          <Link href="/login">Sign in to your workspace</Link>
        </p>
      </div>
    </div>
  );
}
