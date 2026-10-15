import { apiRequest } from "@/lib/api/client";

export type AuthenticatedUser = {
  id: number;
  email: string;
  username: string;
  created_at: string;
  plan: string;
  plan_limits: { roi_calculations: number | null; roadmaps: number | null };
  plan_features: string[];
  usage: { roi_calculations: number; roadmaps: number };
  calculations_remaining: number | null;
};

let cachedUser: AuthenticatedUser | null = null;
let sessionRequest: Promise<AuthenticatedUser> | null = null;

export function clearSessionCache(): void {
  cachedUser = null;
  sessionRequest = null;
}

export function getCurrentUser(force = false): Promise<AuthenticatedUser> {
  if (!force && cachedUser) return Promise.resolve(cachedUser);
  if (!force && sessionRequest) return sessionRequest;

  sessionRequest = apiRequest<AuthenticatedUser>("/api/auth/me", {
    fallbackMessage: "Fence could not verify your session.",
  }).then((user) => {
    cachedUser = user;
    return user;
  }).finally(() => {
    sessionRequest = null;
  });
  return sessionRequest;
}

export async function logoutCurrentUser(): Promise<{ message: string }> {
  const response = await apiRequest<{ message: string }>("/api/auth/logout", {
    method: "POST",
    fallbackMessage: "Fence could not sign you out.",
  });
  clearSessionCache();
  return response;
}
