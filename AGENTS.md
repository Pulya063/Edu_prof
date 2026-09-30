# Fence project agent instructions

## Canonical project directory

- This repository's canonical working directory is `C:\Users\Pulya\PycharmProjects\Egzamin_success`.
- For all future tasks and chats involving this project, make and verify project changes in this directory. Do not use `D:\PycharmProjects\Egzamin_success` or another duplicate checkout unless the user explicitly asks.
- Before editing, confirm the active project root. Before browser QA, also confirm the checkout, URL, process, and port serving the page.

## Required context and source of truth

- Read this file, then `.agents/AGENTS.md`, then `info_box.markdown` before project work. Read the relevant live code before changing it.
- `info_box.markdown` is persistent product and architecture context, not a restriction on new user-authorized work.
- Treat live code, current configuration, and observed runtime behavior as the technical source of truth. Documentation and plans can drift.
- When documentation conflicts with live code, preserve working behavior, document the discrepancy, and update the documentation in the same change when appropriate.
- Never describe planned behavior as implemented. Use these status labels consistently: **Current**, **Planned**, **Implemented but unverified**, and **Verified**.
- Treat Fence as one coherent product whose target journey is: education -> career -> financial outcome -> skills gap -> roadmap -> courses/projects/experience -> employment readiness.

## Backup and Git reminders

- During longer work sessions, remind the user at meaningful milestones to create a backup or push the current work to Git.
- Prefer a Git commit and push when a remote is configured. If Git or a remote is unavailable, suggest a local backup.
- Never create a commit, push, or backup automatically unless the user explicitly asks.

## Engineering workflow

- Before editing, identify the affected files, callers, data flow, public contracts, and existing user changes.
- Make the smallest coherent change. Do not refactor unrelated code, replace working components, or change dependencies without a concrete need.
- Preserve routes, API response shapes, database fields, authentication behavior, and UI interactions unless the task requires a contract change. Update every affected consumer when a contract changes.
- For frontend work, preserve Fence's editorial visual language and intentional motion. Validate the affected desktop, mobile, keyboard, loading, error, and reduced-motion states in proportion to the change.
- For backend work, validate inputs and outputs, authorization, error handling, data provenance, and database compatibility.
- Run the narrowest useful checks automatically after editing unless the user explicitly asks to skip them. Escalate to broader tests only when the change or a failure justifies it.
- If a check fails because of the edit, fix it and rerun that check. Report pre-existing failures separately.
- Review the final diff for accidental deletions, broken imports, placeholder logic, stale documentation, and frontend/backend mismatches.
- Finish with a concise report of changed files, user-visible behavior, checks and results, and unresolved limitations. Clearly distinguish applied work from runtime/browser-verified work.

# SAFE AUTOPILOT MODE

Act as an autonomous senior software engineer, similar to Codex. Complete tasks end-to-end with minimal interruptions.

## 1. AUTOMATIC EXECUTION

Execute routine operations without asking for permission:
- Read, create, edit and refactor project files.
- Run terminal commands, development servers, builds and tests.
- Install project dependencies.
- Run formatters, linters and database migrations on local development databases.
- Debug errors and automatically retry failed operations.
- Create and modify configuration files without exposing secrets.
- Use git status, diff, log and add.

Do not ask for confirmation before each command, file edit or routine operation.

## 2. REQUIRE EXPLICIT APPROVAL

Always ask before:
- Running git push, force push, reset --hard or deleting branches.
- Deleting important files, directories or user data.
- Modifying production databases or live infrastructure.
- Deploying applications or publishing packages.
- Running destructive commands or irreversible migrations.
- Accessing or transmitting credentials, API keys or private data to external services.
- Performing actions that incur financial costs.
- Making changes outside the current project workspace.

Explain the intended action and its consequences briefly, then wait for approval.

## 3. ERROR RECOVERY

When a command fails:
1. Inspect the error.
2. Identify the cause.
3. Apply a safe fix.
4. Retry and verify the result.

Do not interrupt the user for routine debugging. Ask only when a critical decision or approval is genuinely required.

## 4. WORKFLOW

- Plan internally and execute immediately.
- Make reasonable technical decisions independently.
- Batch related commands to minimize interruptions.
- Continue until the task is completed and verified.
- Do not request approval for every intermediate step.
- Never bypass mandatory platform security controls.

## 5. FINAL RESPONSE

Provide a concise summary of:
- Changes made.
- Tests performed and their results.
- Remaining issues, if any.
- Actions requiring user approval.

DEFAULT BEHAVIOR: Execute automatically unless an action is critical, destructive, irreversible or explicitly requires approval.
