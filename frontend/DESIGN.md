---
version: alpha
colors:
  deepBlack: "#050505"
  charcoal: "#171819"
  warmWhite: "#F7F7F3"
  limeJourney: "#B7FF2A"
  paleViolet: "#D7C7FF"
  muted: "#85898F"
typography:
  display:
    fontFamily: "Manrope, Segoe UI, Arial, sans-serif"
  body:
    fontFamily: "DM Sans, Manrope, Segoe UI, Arial, sans-serif"
rounded:
  card: "18px"
  control: "999px"
spacing:
  sectionInline: "4.2vw"
  sectionBlock: "clamp(96px, 12vw, 180px)"
components:
  journeyThread:
    owner: "app/hooks/useScrollMotion.tsx"
    role: "single scroll-revealed editorial route"
  previewAction:
    owner: "app/styles/responsive.css"
    role: "truthful non-interactive state for unfinished product flows"
  workspaceShell:
    owner: "app/workspace/layout.tsx + app/styles/workspace-panels.css"
    role: "shared navigation, application canvas, focus and responsive behavior"
  workspacePanel:
    owner: "app/styles/workspace-panels.css"
    role: "canonical light, dark and violet analytical surfaces"
---

## Overview

Fence is a brand-led education-decision journey for students comparing cost, outcomes, and career direction. The public landing page is editorial rather than dashboard-like: one clear route through uncertainty, evidence, and a next step.

The authenticated workspace is the product register of the same identity. It uses a fixed dark navigation rail, a cool light-grey analytical canvas, strong Manrope headings, compact DM Sans utility text, and alternating light/dark evidence panels. It should feel like a connected education planning desk, not a generic equal-card SaaS dashboard.

The visual signature is the lime journey thread. It runs behind the content, changes direction at each chapter, and is only fully drawn by the end of the page. Thin, dim companion lines provide atmosphere; they never become a grid, a chart, or a competing focal point.

This is the single canonical visual-design document for the frontend. `UX-CONTRACT.md` remains the companion source for navigation, persistence, loading, error, and feedback behavior. Live components and runtime tokens remain the implementation source of truth; when this document and code diverge, reconcile both deliberately rather than treating an old mockup or handoff as current behavior.

The current direction supersedes the earlier three-panel demo treatment. Do not revive its Inter-led type system, alternate lime token, fixed presentation-panel composition, or decorative plus marks unless a new product decision explicitly reintroduces them.

### Visual reference hierarchy

The reference images are local design inputs outside the repository. Use them as visual evidence, never as proof that a route or feature is implemented.

| Reference | Primary use |
|---|---|
| `D:\Fence Design\roi calculator.png` | ROI calculator composition, control rhythm, forecast hierarchy |
| `D:\Fence Design\simulation.png` | Dark analytical panels, metrics, progress and learning groups |
| `D:\Fence Design\Overview.png` | Workspace shell, sidebar density and content width |
| `D:\Fence Design\compare.png` | Comparison cards, filters and detail drawer |
| `D:\Fence Design\cource search.png` | Course search, filters and detail drawer |
| `D:\Fence Design\more about university.png` | University-detail information hierarchy |
| `D:\Fence Design\My plan.png` | Roadmap phases, tasks and selected-task detail |
| `D:\Fence Design\Roadmap dashboard.png` | Roadmap empty state and summary |
| `D:\Fence Design\saved.png` | Scenario collection and detail drawer |
| `D:\Fence Design\settings.png` | Settings groups and connected-source panel |
| `D:\Fence Design\user profile.png` | Profile, plan usage and skills layout |

For the calculator, prioritize `roi calculator.png`, then `simulation.png`, then `Overview.png`. The older compact-navigation screenshot is only a secondary cue; full mockups and live shared components take precedence.

## Colors

Deep black and charcoal establish the analytical chapters. Warm white gives decision tools breathing space. Lime is not a surface treatment: reserve it for the journey line, an active state, or the primary action. Pale violet marks a single editorial word-level emphasis. Avoid blue, glossy gradients, and full-panel glow.

Runtime tokens live in `app/globals.css`; this file documents their intended roles rather than generating a second token source.

Within the workspace, blue-grey is reserved for explanatory copy and borders. Lime remains the primary action/progress color, violet marks planning, prediction, or the active learning state, and charcoal holds forecasts and evidence-heavy views.

## Typography

Manrope carries high-impact editorial headings and numerical emphasis. DM Sans is used for supporting copy, labels, and controls, with Manrope and Segoe UI as Unicode-capable fallbacks. Ukrainian pages use Manrope for the full body so Cyrillic glyphs remain visually consistent; Polish keeps DM Sans with its Latin Extended forms. Headline breaks express a sequence; utility text remains compact, well-spaced, and calm.

## Layout

Use wide asymmetrical editorial compositions at desktop, a 5vw mobile gutter, and no horizontal document overflow. The route moves along outer compositional lanes so it can connect chapters without touching text, controls, or cards.

Workspace pages use a 232px navigation rail and a content width capped near 1280px. Dense comparison and planning views may use split panels; on narrow screens they become a single readable document without hiding actions or values.

The workspace responsive contract is:

| Viewport | Expected composition |
|---:|---|
| 320px | One readable column, roughly 16px safe edge, no clipped labels or metrics |
| 375px | One column with visible hierarchy and at least 44px touch targets |
| 768px | Top navigation; two-column fields only where labels stay readable; main panels stacked |
| 1024px | Compact rail; form and forecast stack without compressed controls |
| 1440px | Balanced two-panel composition beside the rail |
| 1920px | Centered content; panels do not stretch across the full window |

At every width, long university, specialization, and role names wrap safely. The document must tolerate 200% zoom, portrait/landscape resizing, persistent error copy, keyboard focus, and reduced motion without horizontal page scrolling or a sticky-panel scroll trap.

## Elevation & Depth

Surfaces are mostly flat. Elevation is reserved for an active card, hero device, or an action the user can move toward. Ambient lines sit behind all interaction layers and cannot obscure focus rings.

## Shapes

Cards use restrained 17–24px corners. Pill shapes are for compact labels and main actions only. Circular controls are reserved for directional actions and icons.

## Components

`JourneyThread` is the canonical landing-page connective treatment. It uses a normalized SVG route in the outer composition lane and the existing `--journey-progress` motion value for scroll reveal. The route remains uninterrupted through the footer while preserving a quiet reading zone around every card and headline.

Workspace dark panels use restrained topographic contour texture as their shared signature. The contour is atmospheric, never an information graphic, and must remain behind readable content. `WorkspacePageHeader`, `Icon`, and `Topography` in `app/workspace/WorkspaceUI.tsx` are shared owners for the new product screens.

The workspace surface grammar is intentionally small:

- white or cool-grey panels hold inputs, filters, browsable records, and editable settings;
- charcoal panels summarize persisted outcomes, forecasts, or roadmap progress;
- violet callouts explain evidence, prediction, blocked data, or the active learning state;
- lime actions identify the single principal mutation or navigation within a panel;
- detail drawers and split panels preserve the parent list context rather than feeling like a separate product.

The ROI calculator uses one white education-input panel paired with one dark forecast panel. Its hierarchy must answer, in order: the education path, career target, investment, available outputs, missing evidence, and next action. Financial values remain deterministic; visual polish must never imply confidence that the evidence layer does not provide.

Overview, saved scenarios, comparison, university details, roadmap, simulation, plan, courses, profile, and settings reuse the same shell and surface grammar. Extract a new primitive only after at least two live screens demonstrate the same need; do not pre-build a broad component library from mockups alone.

The public product is currently a preview. Pricing is the only active commercial route. Unfinished sign-in, checkout, matching, forecast, legal, social, and contact actions use a visible non-interactive state with plain-language status copy; they must not contain placeholder redirects or deep links.

## Do's and Don'ts

Do keep motion purposeful: `transform`, opacity, and SVG stroke reveal only. Disclosure height may use a layout-safe `grid-template-rows` transition when content size is unknown. Menus and contextual detail panels use the shared short reveal language; completion checks may use one restrained appear motion. Do preserve a quiet reading zone around every headline and control. Do support reduced motion with a static, low-contrast line.

Do not add a separate neon flourish per section. Do not use celebration particles, casino-style counters, pointer-driven 3D tilt, or autonomous AI-stream motion unless a real product flow explicitly requires it. Do not use a generic gradient band to hide a transition. Do not place the journey thread above content or turn its companion lines into a decorative mesh.

Do not activate a control merely because it appears in a mockup. Do not use glass effects, thick shadows, equal-card dashboards, AI-generated financial numbers, or decorative motion that competes with the forecast. Do not copy a reference brand name, logo, presenter photo, certification mark, or proprietary wording.

## Verification contract

Design status must use one of four labels: **Current**, **Planned**, **Implemented but unverified**, or **Verified**. A mockup, Markdown plan, or successful build does not make a screen **Verified**.

For meaningful frontend changes, check the affected desktop and narrow-mobile states, keyboard focus, long content, loading/error/empty states, and reduced motion in proportion to the change. For workspace layout work, use the viewport matrix above and confirm the canonical checkout, URL, process, and port before drawing browser conclusions.

Keep implementation history out of this file. Temporary QA observations belong in the task report; durable visual rules belong here, and shared behavioral rules belong in `UX-CONTRACT.md`.
