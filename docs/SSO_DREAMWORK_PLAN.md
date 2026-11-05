# SSO Fence → DreamWork (plan, not implemented)

Status: **Planned**. Today Fence talks to DreamWork through one shared service account (`DREAMWORK_USERNAME` / `DREAMWORK_PASSWORD`), so DreamWork does not know which Fence user a roadmap belongs to.

1. Fence acts as the identity provider. A user who is already signed in clicks "Open in DreamWork". Fence signs a short-lived JWT: RS256, 60 s TTL, claims `sub` = Fence user id, `email`, `aud=dreamwork`, `iss=fence`, a one-time `jti`.
2. The private key exists only on Fence, in `.env` / Secret Manager. DreamWork gets the public key through `GET /.well-known/jwks.json` on Fence, so no secret is shared.
3. The browser goes to `DREAMWORK_URL/sso/fence?token=…` with a POST form, so the token does not end up in history or logs.
4. DreamWork checks the signature, `aud`, `iss` and `exp`, and keeps the `jti` in Redis until it expires to block replays. It then finds or creates a local user linked by `fence_user_id` (never by email alone) and starts its own session.
5. Server-to-server calls (roadmap generation) move from the shared account to a per-user token minted the same way. The service account stays only for health checks.
6. Fence gets an additive Alembic migration: `user_external_links(user_id, provider, external_id)`. No existing fields change.
7. Logout stays per app. Fence sends a best-effort webhook `POST /sso/fence/logout` with `sub`, and DreamWork ends that user's sessions.
8. Before turning it on: a feature flag `FENCE_DREAMWORK_SSO=false`, tests for expired, replayed, wrong-audience and tampered tokens, and the roadmap remains admin-only until this ships.
