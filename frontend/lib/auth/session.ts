import { apiRequest } from "@/lib/api/client";
import type { AuthMeResponse } from "@/lib/api/generated";

export type AuthenticatedUser = AuthMeResponse;

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
