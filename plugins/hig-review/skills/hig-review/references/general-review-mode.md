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
      mark the finding 待核实 (verify), not a violation (see principle 6).
- **Design-principle findings** — clarity, hierarchy, consistency,
  affordance/feedback, information density. These are advisory for web/dashboard
  → 提示 (Info); cite the related Apple guideline by name as a reference.

## Core principles (from the HIG foundations)
1. **Clarity** — legible at every size; precise icons; text/background meet
   contrast minimums (WCAG 1.4.3). Reference: Color, Accessibility, Typography.
2. **Deference** — UI defers to content; restrained chrome; meaningful space.
   Reference: design principles, Materials.
3. **Depth & hierarchy** — clear visual hierarchy, layering, focus order.
   Reference: Layout, Typography.
4. **Consistency** — consistent components, terminology, color meaning, and
   interaction patterns. Reference: Color, Menus.
5. **Feedback & affordance** — interactive elements look interactive and respond
   (hover/press/focus/disabled); progress & status are communicated. Reference:
   Buttons, Progress indicators.
6. **Target sizing** — comfortably large targets. Web standard: WCAG 2.5.8 (AA)
   24×24 CSS px, 2.5.5 (AAA) 44×44 CSS px; touch/大屏 at distance want the larger
   end. **Caveat:** judge only with a known scale — a screenshot's pixels are
   device px, not CSS px. If `visual_checks.py dims` can't establish scale and
   the user hasn't said, report size concerns as 待核实 (verify) and ask for the
   viewport/scale. Reference: Buttons, Gestures.
7. **Accessibility** — keyboard navigation, visible focus, semantic markup
   (`aria-*`, landmarks), color not the sole channel, respects reduced-motion.
   Reference: Accessibility.

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
- Design-principle line: `依据 / Based on: Apple 设计原则 — 反馈与可供性
  (Buttons)` (提示 / Info).
- The bundled baseline is usually enough here (Apple's general principles are
  stable); fetch the latest live only if the user wants it, and read the body.
- Ground contrast in real pixels (`visual_checks.py sample`); never eyeball a
  ratio. Output via `references/output-format.md`.
