# Fence demo — visual direction

Fence demo is an education ROI presentation surface. The page uses a three-panel editorial rhythm inspired by enterprise presentation systems: light-gray product panels alternate with a near-black closing panel, while a fluorescent lime accent marks action and possibility.

## Visual tokens

| Role | Value |
|---|---|
| Black canvas | `#050505` |
| Dark panel | `#171819` |
| Light panel | `#E8EBEF` |
| White surface | `#F7F8F8` |
| Lime accent | `#C4FF3D` |
| Lavender highlight | `#D8D0FF` |
| Muted text | `#7A7D82` |

## Layout

- Centered presentation width: `1180px` with a black outer canvas.
- Three major panels: hero/product preview, metrics, then path/CTA.
- Panel gutters: `30px` desktop and `20px` mobile.
- Card gaps: `10px`.
- Card radius: `22px`.
- The first panel is a light-gray product canvas with a diagonal Mac/dashboard mockup and two overlapping callout cards.
- The second panel uses one large lime metric card, one image metric card, and a stacked pair of supporting cards.
- The third panel uses three tall rounded cards over a subtle diagonal texture.

## Typography

Use Inter/system grotesk. Headings are heavy, tightly tracked, and set at approximately `0.93` line-height. Utility navigation is uppercase, muted, and small. Body copy is short and concrete. Lavender marker highlights sit behind selected words and never become a full gradient treatment.

## Components

- `PanelNav`: repeated presentation navigation inside each panel.
- `Laptop`: local product screenshot framed as a tilted dark laptop.
- `BlackCard`, `LimeCard`, `WhiteCard`: overlapping callouts with rounded corners.
- `MetricCard`: image, lime, chart, and dark variants.
- `PathCard`: tall dark, pale, and lime variants.
- `PlusMark`: decorative plus indicator, not a false navigation control.

## Motion and accessibility

- Hover feedback is limited to the header action and real links.
- Focus rings use the lime accent and remain visible on both light and dark panels.
- `prefers-reduced-motion` disables smooth scrolling and transitions.
- Panels collapse to a single-column flow below `840px`; navigation hides below `560px` while the panel content remains accessible.

## Brand boundary

Fence demo uses original product copy, the Fence mark, and local EduROI dashboard imagery. It does not reproduce the reference brand name, logo, presenter photo, certification marks, or proprietary wording.
