# Fence workspace UX contract

## Live surfaces

- Compare reads universities from `/api/workspace/universities`; illustrative fallback records are labelled and link to official websites.
- Compare opens `/workspace/universities/:id` for the complete university record from `/api/workspace/universities/:id`.
- Saved scenario cards open `/workspace/scenarios/:id` as the full calculation view, combining the scenario revision with its latest persisted projection.
- Simulation previews a deterministic plan through `/api/workspace/roadmap/preview`; Save creates a persisted roadmap through `/api/roadmap/generate`.
- My plan reads the latest roadmap and persists task completion through `/api/workspace/roadmaps/:id/tasks/:taskId`.
- Courses are queried through `/api/workspace/courses`; save and remove actions persist to the user workspace record.
- Overview career resources are queried through `/api/workspace/resources`; source tabs and search are server-backed and each result opens its declared external source.
- Profile and settings read `/api/workspace` and persist through their dedicated PATCH endpoints.
- Password management routes to the existing reset flow, while unsupported email, session, resume, provider, and OAuth actions remain explicitly disabled.

## Shared states

- Reads show a neutral loading notice, then content, an empty state, or a visible error notice.
- Mutations disable their initiating control while pending and report failure without discarding the visible data.
- External integrations and provider actions stay disabled when the backend reports them unavailable.
- Illustrative data is never presented as verified university or provider data.
- English, Ukrainian, and Polish copy is stored as UTF-8 source text; changing language updates the document locale to `en`, `uk-UA`, or `pl-PL` and must never expose mojibake sequences.

## Interaction rules

- Primary lime actions perform the principal mutation or navigation for the panel.
- Violet communicates estimates, active filters, and explanatory information.
- Dark cards summarize persisted outcomes; white cards contain inputs and browsable records.
- Course and university selection is local UI state; save, progress, profile, and preference changes are server state.
- “Open full calculation” always navigates to the saved projection; “Open full university details” always navigates to the selected university record.
- Saved-scenario quick links deep-link to investment, salary trajectory, and evidence sections of the same server-backed calculation.
