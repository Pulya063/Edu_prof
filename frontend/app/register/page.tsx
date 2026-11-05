"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { clearSessionCache } from "@/lib/auth/session";
import GoogleAuthButton from "../components/GoogleAuthButton";
import { readApiError } from "@/lib/api/client";
import "../styles/auth.css";

import AuthBrandArt from "../components/AuthBrandArt";
type RegisterField = "email" | "password" | "confirm";
type RegisterErrors = Partial<Record<RegisterField, string>>;

async function parseError(res: Response): Promise<{ message: string; fields: RegisterErrors }> {
  if (res.status === 409) return { message: "", fields: { email: "An account with this email already exists. Sign in instead." } };
  if (res.status === 429) return { message: "Too many attempts. Wait a moment before trying again.", fields: {} };
  const error = await readApiError(res, "Could not create your account right now. Try again in a moment.");
  const fields: RegisterErrors = {};
  if (error.fieldErrors.email) fields.email = "Enter a valid email address.";
  if (error.fieldErrors.password) fields.password = error.fieldErrors.password;
  return { message: Object.keys(fields).length ? "" : error.message, fields };
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
  const [fieldErrors, setFieldErrors] = useState<RegisterErrors>({});

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setFieldErrors({});

    const localErrors: RegisterErrors = {};
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) localErrors.email = "Enter a valid email address.";
    const pwError = validatePassword(password);
    if (pwError) localErrors.password = pwError;
    else if (password !== confirm) localErrors.confirm = "Passwords do not match.";
    if (Object.keys(localErrors).length) { setFieldErrors(localErrors); return; }

    setBusy(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const failure = await parseError(res);
        setFieldErrors(failure.fields);
        setError(failure.message);
        return;
      }

      clearSessionCache();
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

        <AuthBrandArt />
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
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? "reg-email-error" : undefined}
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={busy}
            />
            {fieldErrors.email && <span className="auth-field-error" id="reg-email-error" role="alert">{fieldErrors.email}</span>}
          </div>

          <div className="auth-field">
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={fieldErrors.password ? "reg-password-error" : undefined}
              type="password"
              autoComplete="new-password"
              placeholder="At least 8 characters"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={busy}
            />
            {fieldErrors.password && <span className="auth-field-error" id="reg-password-error" role="alert">{fieldErrors.password}</span>}
            <span className="auth-field-hint">
              Minimum 8 characters · uppercase · lowercase · digit
            </span>
          </div>

          <div className="auth-field">
            <label htmlFor="reg-confirm">Confirm password</label>
            <input
              id="reg-confirm"
              aria-invalid={Boolean(fieldErrors.confirm)}
              aria-describedby={fieldErrors.confirm ? "reg-confirm-error" : undefined}
              type="password"
              autoComplete="new-password"
              placeholder="Repeat your password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              disabled={busy}
            />
            {fieldErrors.confirm && <span className="auth-field-error" id="reg-confirm-error" role="alert">{fieldErrors.confirm}</span>}
          </div>

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
            <span aria-hidden="true">→</span>
          </button>

          <p className="auth-trust">
            Deterministic calculation · no AI-generated financial values
          </p>
        </form>

        <div className="auth-divider" style={{ marginTop: 28 }}>or</div>

        <GoogleAuthButton label="Sign up with Google" />

        <div className="auth-divider" style={{ marginTop: 28 }}>already have an account?</div>

        <p className="auth-alt-link" style={{ marginTop: 18 }}>
          <Link href="/login">Sign in to your workspace</Link>
        </p>
      </div>
    </div>
  );
}
