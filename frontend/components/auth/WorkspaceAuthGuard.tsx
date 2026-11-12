"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { AUTH_EXPIRED_EVENT, ApiRequestError } from "@/lib/api/client";
import { AuthenticatedUser, clearSessionCache, getCurrentUser } from "@/lib/auth/session";

type WorkspaceAuthValue = {
  user: AuthenticatedUser;
  verifySession: () => Promise<void>;
};

const WorkspaceAuthContext = createContext<WorkspaceAuthValue | null>(null);

export function useWorkspaceAuth(): WorkspaceAuthValue {
  const value = useContext(WorkspaceAuthContext);
  if (!value) throw new Error("useWorkspaceAuth must be used inside WorkspaceAuthGuard");
  return value;
}

export default function WorkspaceAuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [state, setState] = useState<"checking" | "ready" | "error">("checking");
  const [message, setMessage] = useState("");

  const goToLogin = useCallback(() => {
    const next = pathname.startsWith("/workspace") ? pathname : "/workspace/overview";
    router.replace(`/login?next=${encodeURIComponent(next)}`);
    router.refresh();
  }, [pathname, router]);

  const handleExpiredSession = useCallback(() => {
    clearSessionCache();
    goToLogin();
  }, [goToLogin]);

  const verifySession = useCallback(async () => {
    setState("checking");
    setMessage("");
    try {
      const currentUser = await getCurrentUser(true);
      setUser(currentUser);
      setState("ready");
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        goToLogin();
        return;
      }
      setUser(null);
      setMessage(error instanceof Error ? error.message : "Fence could not verify your session.");
      setState("error");
    }
  }, [goToLogin]);

  useEffect(() => {
    let active = true;
    setState("checking");
    getCurrentUser()
      .then((currentUser) => {
        if (!active) return;
        setUser(currentUser);
        setState("ready");
      })
      .catch((error) => {
        if (!active) return;
        if (error instanceof ApiRequestError && error.status === 401) {
          goToLogin();
          return;
        }
        setMessage(error instanceof Error ? error.message : "Fence could not verify your session.");
        setState("error");
      });
    return () => { active = false; };
  }, [goToLogin]);

  useEffect(() => {
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpiredSession);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpiredSession);
  }, [handleExpiredSession]);

  const value = useMemo(() => user ? { user, verifySession } : null, [user, verifySession]);

  if (state === "checking") {
    return <div className="workspace-auth-state" role="status"><span>Checking secure session</span><i /><i /><i /></div>;
  }
  if (state === "error" || !value) {
    return <main className="workspace-auth-state is-error"><span>{message || "Your session could not be verified."}</span><button type="button" onClick={() => void verifySession()}>Try again</button><button type="button" className="is-secondary" onClick={goToLogin}>Sign in</button></main>;
  }

  return <WorkspaceAuthContext.Provider value={value}>{children}</WorkspaceAuthContext.Provider>;
}
