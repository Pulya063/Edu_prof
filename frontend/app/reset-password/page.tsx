"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import "../styles/auth.css";

type ApiError = { detail?: string | Array<{ msg?: string }> };
type Step = "request" | "sent" | "reset" | "complete";

async function responseMessage(response: Response) {
  try {
    const body = (await response.json()) as ApiError;
    if (typeof body.detail === "string") return body.detail;
    const message = body.detail?.find((item) => item.msg)?.msg;
    if (message) return message.replace(/^Value error,\s*/i, "");
  } catch {
    // Use the status-aware, user-safe fallback below.
  }
  if (response.status === 400) return "This reset link is invalid or has expired. Request a new one.";
  if (response.status === 429) return "Too many attempts. Please wait before trying again.";
  if (response.status === 503) return "Password recovery is temporarily unavailable. Try again shortly.";
  return "Fence could not complete this request. Please try again.";
}

function passwordIssue(value: string) {
  if (value.length < 8) return "Use at least 8 characters.";
  if (!/[A-Z]/.test(value)) return "Add at least one uppercase letter.";
  if (!/[a-z]/.test(value)) return "Add at least one lowercase letter.";
  if (!/[0-9]/.test(value)) return "Add at least one number.";
  return null;
}

export default function ResetPasswordPage() {
  const [step, setStep] = useState<Step>("request");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const resetToken = new URLSearchParams(window.location.hash.slice(1)).get("token");
    if (!resetToken) return;
    setToken(resetToken);
    setStep("reset");
    window.history.replaceState({}, "", "/reset-password");
  }, []);

  async function requestReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!email.trim() || !email.includes("@")) {
      setMessage("Enter a valid email address.");
      return;
    }

    setBusy(true);
    try {
      const response = await fetch("/api/auth/password-reset-request", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });
      if (!response.ok) {
        setMessage(await responseMessage(response));
        return;
      }
      setStep("sent");
    } catch {
      setMessage("Network error. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  async function applyReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!token.trim()) {
      setMessage("Open the link from your email or paste the reset token.");
      return;
    }
    const issue = passwordIssue(password);
    if (issue) {
      setMessage(issue);
      return;
    }
    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const response = await fetch("/api/auth/password-reset", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ code: token.trim(), new_password: password }),
      });
      if (!response.ok) {
        setMessage(await responseMessage(response));
        return;
      }
      setStep("complete");
      setToken("");
      setPassword("");
      setConfirmPassword("");
    } catch {
      setMessage("Network error. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  const resetting = step === "reset";

  return (
    <div className="auth-shell">
      <div className="auth-brand-panel" aria-hidden="true">
        <Link href="/" className="auth-brand-logo">
          <span>F</span><div><b>Fence</b><small>Education decisions</small></div>
        </Link>
        <div className="auth-brand-body">
          <p>Secure account recovery</p>
          <h1>Return to<br /><em>your plan.</em></h1>
          <span>A short-lived, one-time link keeps password recovery private and controlled.</span>
        </div>
        <p className="auth-brand-footer">Education today. A brighter tomorrow.</p>
      </div>

      <div className="auth-form-panel">
        <div className="auth-form-header">
          <p>{resetting ? "Choose a new password" : "Account recovery"}</p>
          <h2>{step === "complete" ? "Password updated" : resetting ? "Reset your password" : "Forgot your password?"}</h2>
        </div>

        {step === "request" && (
          <form className="auth-form" onSubmit={requestReset} noValidate>
            {message && <div className="auth-feedback" role="alert">{message}</div>}
            <p className="auth-form-copy">Enter the email connected to your Fence account. We will send a link valid for 15 minutes.</p>
            <div className="auth-field">
              <label htmlFor="reset-email">Email</label>
              <input id="reset-email" type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={(event) => setEmail(event.target.value)} disabled={busy} />
            </div>
            <button className="auth-submit" type="submit" disabled={busy}>{busy ? "Sending secure link…" : "Send reset link"}<span aria-hidden="true">→</span></button>
          </form>
        )}

        {step === "sent" && (
          <div className="auth-form auth-result" aria-live="polite">
            <div className="auth-feedback is-success">If an active account exists for that email, a secure reset link has been prepared.</div>
            <p className="auth-form-copy">Check your inbox and spam folder. For privacy, Fence never confirms whether an email is registered.</p>
            <button className="auth-secondary-action" type="button" onClick={() => setStep("reset")}>I already have a reset token</button>
          </div>
        )}

        {step === "reset" && (
          <form className="auth-form" onSubmit={applyReset} noValidate>
            {message && <div className="auth-feedback" role="alert">{message}</div>}
            <div className="auth-field">
              <label htmlFor="reset-token">Reset token</label>
              <input id="reset-token" type="text" autoComplete="one-time-code" placeholder="Token from the email" required value={token} onChange={(event) => setToken(event.target.value)} disabled={busy} />
            </div>
            <div className="auth-field">
              <label htmlFor="new-password">New password</label>
              <input id="new-password" type="password" autoComplete="new-password" placeholder="At least 8 characters" required value={password} onChange={(event) => setPassword(event.target.value)} disabled={busy} />
              <span className="auth-field-hint">Minimum 8 characters · uppercase · lowercase · digit</span>
            </div>
            <div className="auth-field">
              <label htmlFor="confirm-new-password">Confirm new password</label>
              <input id="confirm-new-password" type="password" autoComplete="new-password" placeholder="Repeat your new password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} disabled={busy} />
            </div>
            <button className="auth-submit" type="submit" disabled={busy}>{busy ? "Updating password…" : "Update password"}<span aria-hidden="true">→</span></button>
          </form>
        )}

        {step === "complete" && (
          <div className="auth-form auth-result" aria-live="polite">
            <div className="auth-feedback is-success">Your password has been updated. The reset link cannot be used again.</div>
            <Link className="auth-submit auth-submit-link" href="/login">Return to sign in<span aria-hidden="true">→</span></Link>
          </div>
        )}

        {step !== "complete" && (
          <p className="auth-alt-link auth-return-link"><Link href="/login">Back to sign in</Link></p>
        )}
      </div>
    </div>
  );
}
