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
    fontFamily: "Manrope, Arial, sans-serif"
  body:
    fontFamily: "DM Sans, Arial, sans-serif"
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

## Colors

Deep black and charcoal establish the analytical chapters. Warm white gives decision tools breathing space. Lime is not a surface treatment: reserve it for the journey line, an active state, or the primary action. Pale violet marks a single editorial word-level emphasis. Avoid blue, glossy gradients, and full-panel glow.

Runtime tokens live in `app/globals.css`; this file documents their intended roles rather than generating a second token source.

Within the workspace, blue-grey is reserved for explanatory copy and borders. Lime remains the primary action/progress color, violet marks planning, prediction, or the active learning state, and charcoal holds forecasts and evidence-heavy views.

## Typography

Manrope carries high-impact editorial headings and numerical emphasis. DM Sans is used for supporting copy, labels, and controls. Headline breaks express a sequence; utility text remains compact, well-spaced, and calm.

## Layout

Use wide asymmetrical editorial compositions at desktop, a 5vw mobile gutter, and no horizontal document overflow. The route moves along outer compositional lanes so it can connect chapters without touching text, controls, or cards.

Workspace pages use a 232px navigation rail and a content width capped near 1280px. Dense comparison and planning views may use split panels; on narrow screens they become a single readable document without hiding actions or values.

## Elevation & Depth

Surfaces are mostly flat. Elevation is reserved for an active card, hero device, or an action the user can move toward. Ambient lines sit behind all interaction layers and cannot obscure focus rings.

## Shapes

Cards use restrained 17–24px corners. Pill shapes are for compact labels and main actions only. Circular controls are reserved for directional actions and icons.

## Components

`JourneyThread` is the canonical landing-page connective treatment. It uses a normalized SVG route in the outer composition lane and the existing `--journey-progress` motion value for scroll reveal. The route remains uninterrupted through the footer while preserving a quiet reading zone around every card and headline.

Workspace dark panels use restrained topographic contour texture as their shared signature. The contour is atmospheric, never an information graphic, and must remain behind readable content. `WorkspacePageHeader`, `Icon`, and `Topography` in `app/workspace/WorkspaceUI.tsx` are shared owners for the new product screens.

The public product is currently a preview. Pricing is the only active commercial route. Unfinished sign-in, checkout, matching, forecast, legal, social, and contact actions use a visible non-interactive state with plain-language status copy; they must not contain placeholder redirects or deep links.

## Do's and Don'ts

Do keep motion purposeful: `transform`, opacity, and SVG stroke reveal only. Do preserve a quiet reading zone around every headline and control. Do support reduced motion with a static, low-contrast line.

Do not add a separate neon flourish per section. Do not use a generic gradient band to hide a transition. Do not place the journey thread above content or turn its companion lines into a decorative mesh.
