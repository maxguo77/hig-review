# Input types — discovery & handling

`scripts/detect_inputs.py` classifies project files into: `code`,
`design_images`, `design_sources`, `docs`, `configs`, and emits
`component_hits` (UI symbols with `file:line` + candidate `rule_sets`). Below is
how to actually review each type.

## 1. Code
Languages: Swift / SwiftUI, UIKit, AppKit, Objective-C, and web
(HTML/CSS/JS/TS/Vue) for general review mode.
- Use `component_hits` as entry points; open each `file:line` and read context.
- Map the symbol to its rule set (confirm the candidate against `rules/index.json`).
- High-signal checks:
  - **Buttons**: press/disabled states, label clarity, sufficient hit region.
  - **Targets**: `frame(width:height:)`, padding, gesture areas ≥ 44×44 pt
    (60×60 in visionOS).
  - **Color**: avoid hard-coded hex / `UIColor(red:…)`; prefer semantic/system
    colors; light+dark variants.
  - **Typography**: Dynamic Type (`.font(.body)` vs fixed sizes), legible sizes.
  - **Accessibility**: `accessibilityLabel`/`Hint`, `aria-*`, VoiceOver support.
  - **Navigation/modality**: correct use of stacks, sheets, alerts, popovers.
  - **Destructive actions**: confirmation, `.destructive` role.
- Report locations as `path:line` (or `:line-line`).

## 2. UI images (screenshots / mockups)
Read each image with the Read tool (it renders visually). For the full method —
device/scale detection, the per-rule-set visual checklist, contrast measurement,
and how to locate findings by region + normalized coordinates — follow
**`references/ui-image-review.md`**. Start by running
`python3 scripts/visual_checks.py dims <image>` to get size, device/@x scale, and
safe-area context (drives px↔pt conversion for tap-target checks).

## 3. UX docs / specs
Read Markdown/txt directly; for PDF use the Read tool's `pages` parameter. For
the full flow-review method — extracting the screen/step/state skeleton, the
concern-by-concern checklist, and catching omitted states (error/loading/empty,
missing confirmations, upfront permissions) — follow
**`references/ux-doc-review.md`**. Locate findings by `doc.md:line` (or `page N`)
plus a quoted sentence.

## 4. Design sources
- **`.pen` (Pencil)**: NEVER read `.pen` with Read/Grep — they are encrypted.
  Use the Pencil MCP: `get_editor_state(include_schema: true)` first, then
  `snapshot_layout`, `get_screenshot`, `get_variables`, `batch_get` to inspect
  layout, components, and design tokens.
- **Figma**: the usual entry point is a **pasted Figma link** (not a file on
  disk). Follow **`references/figma-review.md`** — it covers connecting the Figma
  MCP (authorize if needed), parsing the link, pulling structure/variables/render,
  and using the exact geometry + tokens for definitive target-size/contrast checks.
- Check spacing scale, type ramp, color tokens, component consistency, and
  target sizes against the rule sets.

## 5. Config / project files
- **Info.plist**: `UISupportedInterfaceOrientations`, status bar style,
  `UILaunchScreen`, privacy usage strings (`NS…UsageDescription`).
- **`*.xcassets`** (asset catalogs): app icon completeness/sizes, AccentColor,
  light/dark image variants, SF Symbols usage.
- **Storyboards / XIBs** (`.storyboard`, `.xib`): segues, size classes,
  Auto Layout, accessibility traits.
- **Localization** (`.strings`, `.xcstrings`): text growth (German/Finnish),
  RTL readiness, truncation risk in tight layouts.

## Reconcile with the user
If the user named specific files or folders in Step 0, scope the review to
those and skip unrelated inventory entries.
