# UI image review playbook

How to review a screenshot / mockup / exported PNG against the HIG. The model
reads the image (the Read tool renders it); this playbook makes the pass
systematic and the findings precisely located. Cite only guidelines that exist
in the baseline, and present each by **name + link** (see `output-format.md`) —
the internal id (e.g. `HIG-TAB-BARS-003`) lives in the page file for
traceability; never invent one.

## Step 1 — Establish context with `visual_checks.py dims`
Run `python3 scripts/visual_checks.py dims <image>` first. For a **full-device
screenshot** it returns the device, `@2x/@3x` scale, point size, and a
safe-area note; use the scale for **points = pixels ÷ scale** (a 44pt tap
target = 88px @2x, 132px @3x).

For a **window / region / non-standard capture** (very common on macOS, web,
dashboards) `dims` will say "no full-device match" and will NOT invent a device
or safe area — don't trust an aspect-only guess. In that case pass the context
you already have from the Step 0 gate:
`dims <image> --platform macos --scale 2` → enables px↔pt and a platform-correct
safe-area note. If you don't know the scale, say so rather than assuming.

## Step 2 — Map the image to a coordinate system (for locating findings)
Describe every finding with **component name + named region + normalized
coordinates** so it's reproducible:
- Named regions (3×3): top-left / top-center / top-right / mid-left / center /
  mid-right / bottom-left / bottom-center / bottom-right.
- Normalized coords: `(x, y)` each in 0–1 from the top-left
  (e.g. a bottom tab bar's 3rd item ≈ `(0.5, 0.96)`).

### Annotated mockups (callouts / arrows / notes)
If the image carries annotations — arrows, leader lines, or notes like "tap logo
to return to new chat" — it's a **hybrid UI image + UX spec**. Don't ignore the
annotations: review the *visual* design with this playbook AND review the
*behavior they describe* against `references/ux-doc-review.md` (navigation, back
paths, feedback, etc.). Treat each annotation as a stated requirement to check.

## Step 3 — Visual checklist (grouped by rule set)
Work through each; open the matching `rules/pages/<slug>.md` for the exact
guidelines and sub-IDs.

| Area | What to inspect | Rule set |
|------|-----------------|----------|
| Layout & spacing | Alignment to a grid, consistent margins/gutters, balanced whitespace, no crowding/clipping, content not under the notch/home indicator | `HIG-LAYOUT` |
| Safe areas / bars | Status bar legibility & style, content clear of Dynamic Island & home indicator, overscan margins on tvOS | `HIG-STATUS-BARS`, `HIG-LAYOUT` |
| Tab bar | ≤5 top-level tabs, clear icons+labels, correct bottom placement, one selected | `HIG-TAB-BARS` |
| Navigation | Clear title, working back affordance, predictable hierarchy, search placement | `HIG-NAVIGATION-AND-SEARCH`, `HIG-TOOLBARS`, `HIG-SIDEBARS` |
| Tap targets | Interactive elements look tappable and are ≥44×44pt (visionOS ≥60pt; web: WCAG 24px AA / 44px AAA). **Needs a known scale** — see "Sizing" below | `HIG-BUTTONS`, `HIG-GESTURES` |
| Buttons | Visible affordance, distinguishable styles, prominent primary action, destructive styling where due | `HIG-BUTTONS` |
| Typography | Clear hierarchy, legible sizes, not too many fonts/weights, no truncation of key text | `HIG-TYPOGRAPHY` |
| Color & contrast | Text/background & icon contrast — see "Measuring contrast" below; meaning not conveyed by color alone | `HIG-COLOR`, `HIG-ACCESSIBILITY` |
| Materials | Appropriate use of translucency/vibrancy/Liquid Glass; legibility over materials | `HIG-MATERIALS` |
| Dark mode | If both appearances shown, both legible; no hard-coded colors implied | `HIG-COLOR`, `HIG-DARK-MODE` |
| Consistency | Repeated components look/behave consistently across screens | `HIG-LAYOUT`, `HIG-COLOR` |
| Accessibility | Visible focus/selection, sufficient sizing, icon+label not icon-only for key actions | `HIG-ACCESSIBILITY` |

### Measuring contrast (ground it in REAL pixels)
`visual_checks.py contrast` is exact, but only as good as the colors you feed
it. Do not eyeball hex values and present the result as precise.

**First decide if the image is even sampleable.** A multi-frame design board, a
downscaled export, or small text at an unknown scale will mostly land on
anti-aliased edges or the text caret — not the glyph stroke. If a couple of
probes clearly aren't hitting clean glyph pixels, don't burn more tries or report
a shaky ratio: mark contrast **需核实**, say you couldn't measure it reliably from
the export, and recommend the source color tokens (connect Figma / `.pen`).
1. **Prefer real pixels** (PNG): sample the text and its background with
   `python3 scripts/visual_checks.py sample <img> X Y X2 Y2 --contrast`.
   Coordinates may be normalized with `--norm` (0–1).
   - **For text, use `--box R`** (e.g. `--box 10`): it samples a window per point
     and, with `--contrast`, auto-picks the glyph **stroke = the luminance extreme
     furthest from the background**, then measures stroke-vs-background. This is the
     reliable way to hit thin/anti-aliased text without pixel-perfect aim. Put
     point 1 *on the text* and point 2 *on a clean adjacent background patch*.
   - The stroke is **not always the darkest pixel**: on a **dark background
     (Dark Mode) the text is the lightest** pixel in the window; on a light
     background it's the darkest. `--box` handles both automatically; if you sample
     single points by hand, pick the extreme *away from* the background, not just
     "the darkest".
   - **Heed the warning.** If `--contrast` prints "两点颜色几乎相同 … 未命中文字/前景",
     you sampled background twice — re-aim or add `--box`; never report that ratio.
2. **Or use a color the design states** (e.g. a `#007AFF` token printed in the
   UI / spec) — that's ground truth too.
3. **If you can only eyeball** (e.g. a JPEG you can't sample), you may estimate,
   but mark the finding **`Info`** and label the ratio "estimated" — never
   present an eyeballed input with tool precision.

## Step 4 — Report
Use `references/output-format.md`. For each finding, the location is the image
filename + region + normalized coords, e.g.:
```
【重要 (Major)】home.png(bottom-center, ≈ x:0.5, y:0.96)— 标签栏有 6 个一级标签
  依据 / Based on: Apple 人机界面指南 — 标签栏 (Tab bars)
                  https://developer.apple.com/design/human-interface-guidelines/tab-bars
```
When you cite a contrast problem, include the measured ratio and say whether it
came from `sample` (real pixels), a stated token, or an estimate.

## Sizing (needs a known scale — don't assert a violation without one)
Element sizes and coordinates here are **model-estimated** from the rendered
image; the tools measure the image and sample pixels, but cannot measure an
element's bounding box. A target-size verdict also needs the scale: a
screenshot's pixels are device px, and 44pt = 88px @2x / 132px @3x (web: CSS px,
so a 2× capture doubles the numbers). If `visual_checks.py dims` can't establish
the scale and the user hasn't said, report size concerns as **"verify"** and ask
for the device/viewport/scale — do not assert a pass/fail.

## Limits
Pixel measurements and coordinates are estimates; state assumptions (e.g.
assumed @3x). For exact specs (spacing tokens, type ramp, target sizes) prefer
the design source (`.pen`/Figma) when available — see `references/input-types.md`.
