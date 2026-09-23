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
    owner: "app/components/motion.tsx"
    role: "single scroll-revealed editorial route"
---

## Overview

Fence is a brand-led education-decision journey for students comparing cost, outcomes, and career direction. The public landing page is editorial rather than dashboard-like: one clear route through uncertainty, evidence, and a next step.

The visual signature is the lime journey thread. It runs behind the content, changes direction at each chapter, and is only fully drawn by the end of the page. Thin, dim companion lines provide atmosphere; they never become a grid, a chart, or a competing focal point.

## Colors

Deep black and charcoal establish the analytical chapters. Warm white gives decision tools breathing space. Lime is not a surface treatment: reserve it for the journey line, an active state, or the primary action. Pale violet marks a single editorial word-level emphasis. Avoid blue, glossy gradients, and full-panel glow.

Runtime tokens live in `app/globals.css`; this file documents their intended roles rather than generating a second token source.

## Typography

Manrope carries high-impact editorial headings and numerical emphasis. DM Sans is used for supporting copy, labels, and controls. Headline breaks express a sequence; utility text remains compact, well-spaced, and calm.

## Layout

Use wide asymmetrical editorial compositions at desktop, a 5vw mobile gutter, and no horizontal document overflow. The route moves along outer compositional lanes so it can connect chapters without touching text, controls, or cards.

## Elevation & Depth

Surfaces are mostly flat. Elevation is reserved for an active card, hero device, or an action the user can move toward. Ambient lines sit behind all interaction layers and cannot obscure focus rings.

## Shapes

Cards use restrained 17–24px corners. Pill shapes are for compact labels and main actions only. Circular controls are reserved for directional actions and icons.

## Components

`JourneyThread` is the canonical landing-page connective treatment. It uses a normalized SVG route in the outer composition lane and the existing `--journey-progress` motion value for scroll reveal. The route remains uninterrupted through the footer while preserving a quiet reading zone around every card and headline.

## Do's and Don'ts

Do keep motion purposeful: `transform`, opacity, and SVG stroke reveal only. Do preserve a quiet reading zone around every headline and control. Do support reduced motion with a static, low-contrast line.

Do not add a separate neon flourish per section. Do not use a generic gradient band to hide a transition. Do not place the journey thread above content or turn its companion lines into a decorative mesh.
