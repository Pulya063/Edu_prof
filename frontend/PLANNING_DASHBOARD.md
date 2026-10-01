# Internal Dashboard Design Plan: Fence Workspace

> **Verified 2026-10-01:** `/workspace/overview` реалізовано як read-only analytical report поверх `GET /api/simulations/overview`, а `/workspace/scenario/new` — як authenticated creation flow через наявні scenario та deterministic projection contracts. Нижчий первинний plan з sidebar/card dashboard і `/api/calculate` збережений як історичний напрям та не є описом live implementation. Scenario editing/revisions і roadmap feedback UI залишаються planned.

## 1. Overview & Architecture

The internal application (Workspace) will use a **Sidebar Layout (App Shell)**. The layout will provide a consistent navigation experience across all internal pages, keeping the user context clear.

*   **Tech Stack:** Next.js App Router, React (Client/Server components), TailwindCSS.
*   **Design Language:** Modern, clean, high contrast. Uses dark cards for key metrics/hero elements and white cards for standard lists/inputs. Primary accent color is bright lime/neon green.

## 2. Global Layout (App Shell)

### Sidebar (Left Navigation)
*   **Branding:** "Fence" Logo at the top left.
*   **Primary Links:**
    *   Home / Overview (Active state indicator)
    *   ROI Calculator
    *   Saved Scenarios
    *   Compare Universities
*   **Secondary Group (Roadmap):** Expandable/nested list with "Dashboard", "Simulation", "My plan", "Course search".
*   **Bottom Area:** Help/Support link, and a small typographic branding text ("EDUCATION TODAY. A BRIGHTER TOMORROW.").
*   **Styling:** Dark sidebar with light text, active item highlighted with the lime green accent.

### Topbar
*   **Breadcrumbs:** Shows current path (e.g., `Workspace / Overview`).
*   **Context Badges:** e.g., "DEMO DATA" indicator.
*   **User Menu:** Avatar/Profile icon triggering a dropdown (Profile, Settings).

---

## 3. Page Breakdown

### A. Dashboard Overview (`/workspace/overview`)
The landing page for authenticated users, providing a snapshot of their current active plan and recommended next steps.

**Key Components:**
1.  **Welcome Header:** Large greeting ("Your next move, [Name].") with an elliptical highlight behind "next move". Includes a primary action button `+ New scenario` (Lime green).
2.  **Active Scenario Card (Hero - Dark):**
    *   Displays the currently tracked educational path (e.g., Computer Science at WSiiZ).
    *   Visual flair: Abstract topographic or wave background lines.
    *   Metadata: Field, Location, Study Mode, Target Role.
3.  **Career Insights Card (White):**
    *   Resource recommendation feed (Based on roadmap/backend).
    *   Filter pills: All, YouTube, Public web.
    *   List items: Title, description, source type (tag), external link icon.
4.  **Saved Scenarios Widget (White):**
    *   Mini-table showing recent drafts and active scenarios.
    *   Columns: Scenario name (with icon), Location, Status badge (Active/Draft).
5.  **Career Roadmap Widget (Dark):**
    *   Progress tracker (e.g., "3 of 12 tasks completed") with a visual progress bar.
    *   Task list with status icons (Checkmark for completed, empty circle for upcoming).
6.  **Bottom CTA banner:** "Start small. Move with clarity." prompting users to compare options.

### B. ROI Calculator (`/workspace/calculator`)
An interactive form and results view for estimating education costs and salary potential.

**Key Components:**
1.  **Header:** "Build your education forecast".
2.  **Left Column - Input Form (White Card):**
    *   Title: "Education details".
    *   Inputs: University search (Combobox/Autocomplete), Country, Faculty, Degree, Duration, Annual tuition, Living costs (optional).
    *   Action: Large `Calculate forecast` button (Lime green).
3.  **Right Column - Results Panel (Dark Card):**
    *   Title: "Your education forecast" with context (University, Program).
    *   Top Metrics Grid: Total investment range, Career potential score (x/10), Data confidence percentage.
    *   Alert Banner: Warning state for unverified data (light purple/blue background).
    *   Salary Forecast Table: Rows for Intern/trainee, Junior, Mid, Senior showing expected gross USD ranges.
    *   Bottom Actions: `Save scenario` (Primary), `Compare universities` (Secondary), `Create roadmap` (Secondary).

---

## 4. Implementation Steps & Phasing

### Phase 1: Layout & Foundation
1.  Create the `app/workspace/layout.tsx` for the App Shell (Sidebar + Topbar).
2.  Define Tailwind configuration (colors: lime accent, dark slate for cards, typography scales).
3.  Build basic UI primitives (Button, Input, Select, Card, Badge, Highlight Text).

### Phase 2: Overview Page
1.  Implement `/workspace/overview/page.tsx`.
2.  Build the `ActiveScenarioCard` component.
3.  Build the `CareerInsights` feed component.
4.  Build the `RoadmapProgressWidget`.

### Phase 3: ROI Calculator Page
1.  Implement `/workspace/calculator/page.tsx`.
2.  Build the interactive form with state management (React `useState` or `react-hook-form`).
3.  Build the `ResultsPanel` component to reactively display calculated metrics based on the form input.
4.  Integrate with backend API (`/api/calculate`) to fetch real salary and tuition estimates.

### Phase 4: Polish & Interactions
*   Add hover states, active states for sidebar navigation.
*   Implement custom dropdowns for the form.
*   Ensure responsive design (stacking columns on mobile, hiding sidebar behind a hamburger menu).
