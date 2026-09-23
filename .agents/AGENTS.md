# Agent Rules for "Education ROI Calculator" Project

This file contains specific Customizations (rules) for the AI agent to better understand the context, constraints, and technology stack of this project. 

## Technology Stack & Core Tools
1. **Backend**: Python 3.13, Flask, SQLAlchemy 2.0 (Core/ORM).
2. **Database**: PostgreSQL, database migrations via Alembic.
3. **Frontend**: Jinja2 templates, HTMX (for dynamic partial page updates without full reloads), TailwindCSS (for styling).
4. **Testing**: Pytest (for unit and integration tests).
5. **Logging**: Standard Python `logging` module.

## Backend Development Rules
- **Architecture**: Strictly adhere to the existing project structure:
  - `app/api/`: Route handlers and Blueprints.
  - `app/services/`: Business logic and database interactions.
  - `app/models.py`: Database schemas.
- **Dependency Injection & Separation of Concerns**: Use the service layer (`app/services`) for data processing. Route handlers (Blueprints) should only handle request parsing, calling the service layer, and returning the response or rendering templates.
- **Security & Auth**: Always protect private routes using the `@get_current_user` decorator (or similar). Validate all incoming data (e.g., using Pydantic schemas) before processing it.
- **Logging**: Never use `print()`. Always use the `logging` module (`logger.info`, `logger.error`, etc.) for debugging and audit trails.

## Database & SQLAlchemy 2.0 Rules
- **Modern SQLAlchemy**: Use SQLAlchemy 2.0 syntax. Always use `db.session.execute(select(Model))` instead of the legacy `Model.query`.
- **Eager Loading**: Prevent N+1 query problems by proactively using `joinedload` or `selectinload` when querying models with relationships (e.g., fetching a `User` and their `ROICalculation` history).
- **Migrations**: Any changes made to `models.py` must ALWAYS be followed by creating a new Alembic migration (`alembic revision --autogenerate`). Never modify the database schema without a migration file.
- **Indexing**: Ensure heavily queried fields (like `email`, `university_name`) have `index=True`.

## Frontend (UI/UX) Development Rules
- **Modern Aesthetics**: The user interface must look premium and modern. Utilize smooth gradients, micro-animations, modern typography (Google Fonts, e.g., Inter), and harmonious color palettes. Avoid generic basic colors.
- **No Heavy JS Frameworks**: Do not suggest or use React, Vue, Angular, or similar frameworks. For interactivity, rely strictly on **HTMX** (`hx-get`, `hx-post`, `hx-swap`, `hx-target`) combined with Jinja2 templates.
- **TailwindCSS**: Write all new styles using TailwindCSS utility classes. Maintain consistent spacing (e.g., using `gap-4`, `p-6`) and standard focus rings for inputs (`focus:ring-2 focus:ring-blue-500`).
- **Responsiveness**: All interfaces must be fully responsive (using Flexbox/Grid) and display correctly on mobile devices down to 320px width.
- **Accessibility (a11y)**: Ensure forms have proper `<label>` tags, inputs have `aria-` attributes where necessary, and the contrast ratio is sufficient.

## HTMX Specific Rules
- **Request Detection**: Use `request.headers.get("HX-Request") == "true"` to determine if a request came from HTMX.
- **Responses**: If it's an HTMX request, return rendered HTML partials (`render_template("partials/...html")`). If it's a standard API request, return JSON.
- **Redirects**: To redirect a user during an HTMX request (e.g., after successful login), use the `HX-Redirect` response header instead of a standard 302 redirect.
- **Form Handling**: Always use `hx-indicator` on forms to show a loading spinner while waiting for the server response.

## Error Handling & UI States
- **Empty States**: Always anticipate and design for "Empty States" (when no data is present, e.g., no calculations saved). Provide clear call-to-action buttons in these states with an appealing illustration or icon.
- **Loading States**: Always use loading states and spinners (`hx-indicator`) during HTMX requests to provide visual feedback to the user.
- **Error Messages**: Display user-friendly, localized error messages (flash messages or inline alerts) rather than raw backend exceptions. Ensure 400 and 500 level errors are caught and rendered beautifully in the UI.

## Testing Rules
- **Coverage**: Whenever adding a new feature or complex logic (e.g., ROI math), write accompanying Pytest tests.
- **Mocking**: External API calls (like Hipolabs or College Scorecard) must be mocked using `unittest.mock` during testing to prevent flaky tests.
- **Final Checks**: Do not run final build, test, lint, or type-check commands unless the user explicitly asks for them.

## Git, Environment, and Documentation Workflow
- **Commits**: Write clear, descriptive, and atomic commits using Conventional Commits format (e.g., `feat: add history table`, `fix: correct ROI math`).
- **Dependencies**: Whenever a new Python package is used, immediately update `requirements.txt`.
- **Environment Variables**: If a new configuration or secret is introduced, use `os.getenv()` with a fallback or raise an error on startup. Instruct the user to update their `.env` file.
- **Continuous Documentation**: Whenever completing a new user story or feature, automatically propose updates to the `README.md` to keep the project documentation (Problem analysis, User stories, Tech Spec) strictly aligned with the actual codebase.
