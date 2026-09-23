# Fence project agent instructions

## Canonical project directory

- This repository's canonical working directory is `C:\Users\Pulya\PycharmProjects\Egzamin_success`.
- For all future tasks and chats involving this project, make and verify project changes in this directory. Do not use `D:\PycharmProjects\Egzamin_success` or another duplicate checkout unless the user explicitly asks.
- Before editing, confirm the active project root is the canonical directory above; if the current workspace points elsewhere, switch to or open the canonical directory before making changes.

## Existing project guidance

- Before changing the project, read `.agents/AGENTS.md` in full and follow its repository-specific engineering rules.
- Before any project work, read `info_box.markdown` in full. Treat its entire contents as persistent project context for the product purpose, architecture, routes, user flows, API behavior, calculations, integrations, configuration, limitations, and planned development.
- Re-read `info_box.markdown` whenever it changes. When its description conflicts with the live code, inspect the implementation, preserve working behavior, and explicitly flag the discrepancy instead of silently guessing.
- Treat Fence as one coherent product whose core journey is education -> skills -> career -> financial outcome.

## Backup and Git reminders

- During longer work sessions, periodically remind the user to create a backup or push the current work to Git.
- Give a reminder at meaningful checkpoints, especially after a substantial feature, refactor, migration, or verified milestone, and when there is a meaningful amount of uncommitted work.
- Keep reminders brief and occasional; do not repeat them in every message or interrupt focused work without a useful checkpoint.
- Prefer a Git commit and push when a remote is configured. If Git or a remote is unavailable, suggest making a local backup instead.
- Never create a commit, push, or backup automatically unless the user explicitly asks for it.

## Engineering workflow

- Before editing, identify the files involved, their callers, and the existing data flow. Read only the relevant code after reading the required project guidance.
- Define the expected behavior and a short list of affected scenarios before making changes. If the request is clear, proceed without asking for confirmation.
- Make the smallest coherent change. Do not refactor unrelated code, replace working components, or change dependencies without a concrete need.
- Preserve existing routes, API response shapes, database fields, authentication behavior, and UI interactions unless the task requires a change. When a contract must change, update every affected consumer.
- For frontend changes, check desktop and mobile layouts and the interaction states affected by the change. Preserve Fence’s established visual language and motion behavior.
- For backend changes, check validation, authorization, error handling, and database compatibility in the affected flow.
- Run the narrowest useful checks after editing. For example: relevant tests, typecheck, lint, or build. Do not repeatedly run the full suite unless a failure or broad change justifies it.
- If a check fails because of the edit, fix the cause and rerun that check. Report pre-existing failures separately.
- Review the final diff for accidental deletions, broken imports, placeholder logic, and mismatches between frontend and backend.
- Finish with a concise report: changed files, user-visible result, checks run and their results, and any unresolved limitation.
