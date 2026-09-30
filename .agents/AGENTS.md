# Fence repository engineering rules

This file defines the current project stack and implementation rules. It supplements the repository-level `AGENTS.md`; it does not duplicate the safe-autopilot policy.

## Status language

- **Current**: present in the live code now.
- **Planned**: approved direction that is not implemented yet.
- **Implemented but unverified**: code exists, but the relevant runtime or browser check has not passed.
- **Verified**: the relevant automated and/or rendered check has passed in the current checkout.
- Never infer implementation from a roadmap, mockup, screenshot, or documentation entry. Inspect the live code.

## Current technology stack

- **Frontend**: Next.js 14 App Router, React 18, TypeScript, and the existing CSS/Tailwind toolchain under `frontend/`. Next.js is the primary product UI.
- **Legacy UI**: Flask/Jinja/HTMX remains only where the live backend still renders templates. Do not build a new primary product surface there unless the user explicitly asks.
- **Backend**: Python 3.13, Flask, Pydantic, SQLAlchemy 2, and Alembic, organized as a modular monolith.
- **Data and jobs**: PostgreSQL, Redis, RabbitMQ, and Celery.
- **AI/data integrations**: Ollama/LangChain/Chroma experiments, DreamWork, College Scorecard, Hipolabs, and O*NET where configured.
- **Testing**: Pytest for backend work; the frontend's configured lint, type-check, build, and browser tooling for UI work.

## Backend rules

- Keep transport in `app/api/`, business logic in `app/services/`, persistence in `app/models.py`, validation in Pydantic schemas, and infrastructure adapters under `app/core/` or dedicated services.
- Use SQLAlchemy 2 syntax (`select`, `db.session.execute`) and avoid legacy `Model.query`.
- Protect private routes with the established authentication dependency and validate both request data and service/API output.
- Preserve public routes and response shapes unless the task requires a contract change; update every affected consumer and test when a contract changes.
- Use structured, user-safe errors and Python logging. Never log credentials, session tokens, password-reset tokens, or private payloads.
- Prevent N+1 queries with appropriate eager loading when a relationship is actually consumed.

## Database and migrations

- Every database-schema change requires a new Alembic revision. Do not edit an already-applied migration to represent a new change.
- Inspect the current revision graph and existing user changes before generating a migration.
- Never upgrade a production database or run an irreversible migration without explicit approval.
- Add indexes and constraints from demonstrated query/integrity needs, not speculation.

## Frontend and design rules

- Use Next.js/React for the current product frontend. Prefer server components for static/data-rendered shells and client components only for interaction, browser APIs, forms, charts, or local state.
- Do not require Tailwind for every change. Follow the local styling approach of the affected component and avoid adding another global override layer without a concrete need.
- Preserve Fence's editorial identity: black/white contrast, `#171819` dark surfaces, lime `#B7FF2A` action/progress accents, violet `#D7C7FF` AI/prediction accents, restrained corners, strong typography, subtle texture, and purposeful motion.
- Do not turn the product into a generic equal-card SaaS dashboard. Prefer an analytical-report hierarchy.
- Provide loading, empty, error, stale-data, keyboard, focus, and reduced-motion states where the affected flow needs them.
- For explicit responsive work, validate 320, 375, 768, 1024, 1440, and 1920 px, 200% zoom, resize/orientation, keyboard navigation, and `prefers-reduced-motion`.
- Confirm the active checkout, server process, URL, and port before rendered QA. Source inspection is not browser verification.

## Product and simulation direction

- Fence's target journey is education -> career -> financial outcome -> skills gap -> roadmap -> courses/projects/experience -> employment readiness.
- **Planned**: a versioned Simulation Scenario will eventually connect education, career, finance, skills, roadmap, and evidence. Do not describe it as Current until implemented.
- Roadmap progress should eventually update skill evidence and readiness. Completing a task must not directly or silently increase a salary estimate.
- Do not implement a later roadmap phase merely because it is documented; stay within the user's current scope.

## Prediction, provenance, and AI

- Tuition, investment, salary ranges, projections, ROI, payback, inflation, market indexes, and financial comparisons must come from deterministic, versioned, testable code backed by structured data.
- LLMs may classify, map careers, extract skills, draft roadmaps, explain deterministic results, summarize, and support natural-language interaction.
- Validate AI output with structured schemas. Do not accept LLM-generated values into core financial fields.
- Important estimates should carry source, source reference, acquisition date, geography, role/seniority, sample size when available, confidence/data strength, and methodology version.
- Prefer simple services and bounded LLM calls. Do not create a mega-agent, add LangGraph, split microservices, or introduce a separate vector database without a concrete measured need.
- For retrieval, evaluate PostgreSQL/pgvector before adding separate vector infrastructure.

## Testing and verification

- Add or update focused tests for changed business logic and contracts. Mock external APIs, SMTP, queues, Redis, and LLMs where the test is not specifically an integration test.
- Run the narrowest relevant checks after editing unless the user explicitly asks not to. Run broader checks when the change is cross-cutting or a focused check reveals wider risk.
- Report pre-existing failures separately. Never present an unrun check as passing.
- Distinguish source-applied, automated-test verified, runtime verified, and browser verified work.

## Documentation and environment

- Keep `info_box.markdown` aligned with the live implementation and explicitly separate Current from Planned behavior.
- A user-authorized feature is not prohibited merely because it is absent from the documentation. Inspect the code, implement within scope, and update documentation when public behavior changes.
- Add new dependencies only for a concrete need and update every authoritative dependency manifest in the same change.
- Add new configuration through environment variables with safe local defaults or production startup validation. Never expose secrets.
