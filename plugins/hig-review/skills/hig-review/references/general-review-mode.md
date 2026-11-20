# General review mode — web pages & data dashboards (通用审查模式)

Web pages and large-screen data dashboards (数据大屏) aren't Apple platforms.
**General review mode** reuses the cross-platform design principles behind the
HIG as a general quality lens, and uses **WCAG** as the standard for web
specifics. Phrase findings as design guidance — not as platform rules.

## Two kinds of findings (this sets severity & what you cite)
Don't flatten everything to 提示 (Info). Split by what actually governs the surface:

- **Web-standard findings** — contrast, target size, keyboard operability, focus
  visibility, semantics/labels, reduced-motion. For web/dashboards the standard
  is **WCAG 2.2**. Cite WCAG and keep the **real severity** (严重/重要/建议);
  you may add "对齐 Apple 设计原则:<topic>" as the lens.
    - Contrast: WCAG 1.4.3 (AA) 4.5:1 body / 3:1 large text; 1.4.11 3:1 for UI
      components & graphics.
    - Target size: WCAG 2.5.8 (AA) **24×24 CSS px**; 2.5.5 (AAA) **44×44 CSS px**
      (≈ Apple's 44pt). A size verdict needs a **known scale** — if it's unknown,
      mark the finding 待核实 (verify), not a violation (see "Target sizing").
- **Design-principle findings** — purpose, hierarchy, consistency,
  feedback, information density, recoverability. These are advisory for
  web/dashboard → 提示 (Info); cite the related Apple design principle (or
  guideline page) by name as a reference.

## Core principles (Apple's Design principles, reintroduced June 2026)
The HIG's `design-principles` page now lists eight principles (the older
"Clarity / Deference / Depth" trio is retired — don't cite it). Use them as the
quality lens, mapped to concrete web/dashboard checks. Cite by name, e.g.
"Apple 设计原则 — 简洁 (Simplicity)", and pair with WCAG wherever a web
standard exists.

1. **Purpose (目标感)** — the page's main job is obvious; the key task or KPI is
   prominent, not buried among secondary widgets.
2. **Agency (能动性)** — stay out of the way; guided flows can be skipped or
   escaped; mistakes are recoverable (undo, confirm destructive actions, keep
   input on error).
3. **Responsibility (责任感)** — be transparent about what is collected and why;
   ask for permissions in context with a clear reason.
4. **Familiarity (熟悉感)** — consistent components, terminology, color meaning
   and interaction patterns; **clear feedback**: controls look interactive and
   respond (hover/press/focus/disabled), and status/progress is communicated.
   Reference: Buttons, Progress indicators.
5. **Flexibility (灵活)** — design for everyone: accessibility from the start,
   multiple input methods (keyboard, pointer, touch, voice), responsive layouts
   that keep context across sizes. Web standards: keyboard operable (WCAG
   2.1.1), visible focus (2.4.7 / 2.4.11), semantic labels (`aria-*`,
   landmarks; 4.1.2), not color alone (1.4.1), reduced motion
   (`prefers-reduced-motion`; 2.3.3).
6. **Simplicity (简洁)** — only what's necessary, concise wording, clear
   hierarchy (type scale, grouping, alignment). Legible text with contrast
   ≥ 4.5:1 body / 3:1 large (WCAG 1.4.3 — the HIG Accessibility page adopts
   these same WCAG AA values); non-text UI ≥ 3:1 (1.4.11). Reference: Typography,
   Color, Layout.
7. **Craft (匠心)** — precise alignment and spacing, polished states (empty,
   loading, error), smooth non-janky motion.
8. **Delight (愉悦感)** — personality that serves the task; never decoration
   that gets in the way of it.

**Target sizing** (part of Flexibility): comfortably large targets. Web
standard: WCAG 2.5.8 (AA) 24×24 CSS px, 2.5.5 (AAA) 44×44 CSS px; touch and
dashboards viewed at a distance want the larger end. **Caveat:** judge only
with a known scale — a screenshot's pixels are device px, not CSS px. If
`visual_checks.py dims` can't establish the scale and the user hasn't said,
report size concerns as 待核实 (verify) and ask for the viewport/scale.
Reference: Buttons, Gestures.

## Data dashboard (数据大屏) specifics
- **Legibility at distance** — font sizes scaled to viewing distance; avoid thin
  weights and low-contrast palettes on dark backgrounds.
- **Information density & grouping** — group related metrics; avoid clutter; give
  each KPI clear hierarchy (primary number vs supporting detail).
- **Color semantics** — consistent status colors (e.g. red = alert), a
  colorblind-safe palette; never rely on color alone for thresholds.
- **Motion & refresh** — smooth, non-distracting updates; respect reduced-motion;
  avoid flicker on auto-refresh.
- **Chart clarity** — labeled axes/units, honest scales, restrained decoration.

## How to apply
- Run the normal workflow, but load this file instead of the platform pages.
- Web-standard line: `依据 / Based on: WCAG 1.4.3 (AA) — 对比度 4.5:1` (real
  severity); optionally add "对齐 Apple 设计原则:Color".
- Design-principle line: `依据 / Based on: Apple 设计原则 — 熟悉感 (Familiarity):
  提供清晰的反馈` (提示 / Info). Link:
  https://developer.apple.com/cn/design/human-interface-guidelines/design-principles
- The bundled baseline is usually enough here (Apple's general principles are
  stable); fetch the latest live only if the user wants it, and read the body.
- Ground contrast in real pixels (`visual_checks.py sample`); never eyeball a
  ratio. Output via `references/output-format.md`.
