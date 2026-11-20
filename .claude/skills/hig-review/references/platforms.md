# Platform matrix

The crawler tags every rule page with `platforms` (from page metadata when
present, otherwise inferred from the page slug). A rule set applies to a target
platform when its `platforms` list contains that platform **or** `"all"`.

## Supported targets
| Target | HIG "Designing for…" page | Notes |
|--------|---------------------------|-------|
| iOS (iPhone) | `designing-for-ios` | Touch-first; Liquid Glass bars float above content. |
| iPhone Duo | `designing-for-iphone-duo` (+ `designing-for-ios`) | Two displays + hinge; bars move to the **side**; reserved regions. Tagged `iOS`. |
| iPadOS | `designing-for-ipados` | Resizable windows, multitasking, pointer, keyboard, menu bar; tab bar near the top. |
| macOS | `designing-for-macos` | Menu bar, windows, keyboard + pointer; **touch is a secondary input** on Macs with a touch display. |
| watchOS | `designing-for-watchos` | Glanceable, complications, Digital Crown. |
| tvOS | `designing-for-tvos` | Focus engine, 10-ft UI, remote. |
| visionOS | `designing-for-visionos` | Spatial, eyes + hands, ornaments, vertical tab bar on the leading side. |
| CarPlay | `carplay` | Driver-safe, templated UI. |
| Games (any platform) | `designing-for-games` | Load in addition to the platform page for games. |
| **Web / 数据大屏** | — (not an Apple platform) | **General review mode** only — see `general-review-mode.md`. |

## Always-load foundations (any Apple platform)
Regardless of detected components, include these foundation rule sets — they
apply broadly and catch the most common violations:
- `HIG-DESIGN-PRINCIPLES` (reintroduced June 2026: Purpose 目标感, Agency 能动性,
  Responsibility 责任感, Familiarity 熟悉感, Flexibility 灵活, Simplicity 简洁,
  Craft 匠心, Delight 愉悦感)
- `HIG-ACCESSIBILITY`
- `HIG-COLOR`
- `HIG-TYPOGRAPHY`
- `HIG-LAYOUT`
- `HIG-MATERIALS` (Liquid Glass)
- `HIG-APP-ICONS`
- `HIG-PRIVACY`

Plus the per-platform "Designing for <platform>" page for each chosen platform.

## Size & legibility minimums (from the HIG Accessibility page)
These are the numbers to judge against — don't apply the iPhone 44 pt to every
platform. Re-check `rules/pages/accessibility.md` (or fetch it live) if the
baseline is newer than this table.

| Platform | Control size: default | Control size: minimum | Text: default | Text: minimum |
|----------|-----------------------|-----------------------|---------------|---------------|
| iOS, iPadOS | 44×44 pt | 28×28 pt | 17 pt | 11 pt |
| macOS | 28×28 pt | 20×20 pt | 13 pt | 10 pt |
| tvOS | 66×66 pt | 56×56 pt | 29 pt | 23 pt |
| visionOS | 60×60 pt | 28×28 pt | 17 pt | 12 pt |
| watchOS | 44×44 pt | 28×28 pt | 16 pt | 12 pt |

- **Hit region**: the Buttons page's rule of thumb is a hit region of at least
  44×44 pt (60×60 pt in visionOS), whatever the input. In visionOS, place
  button centers at least 60 pt apart.
- **Spacing**: about 12 pt of padding around bezeled elements, about 24 pt
  around elements without a bezel.
- **Contrast** (all platforms): at least 4.5:1 for text up to 17 pt; 3:1 for
  text 18 pt and up, or bold text at any size. (The HIG adopts these WCAG AA
  values — they're what Accessibility Inspector checks.)
- **How to grade target size** (this skill's severity policy, not HIG text):
  below the platform **minimum** → 严重 (Blocker);
  between minimum and default for a primary/frequent control → 重要 (Major),
  otherwise 建议 (Minor). Always state the scale the measurement relies on.

## Platform-specific gotchas to check
- **iOS**: safe areas and the Dynamic Island, Dynamic Type, hit targets,
  modality, Dark Mode. The tab bar **floats** on Liquid Glass at the bottom
  (it can minimize on scroll, and can end with a dedicated search tab).
  Separate controls from content with the scroll edge effect, not solid or
  semi-opaque bar backgrounds.
- **iPhone Duo**: lay out by **size class**, not device or idiom (compact on
  the outer display, regular on the inner display). Toolbars, tab bars, the
  status bar and the Dynamic Island sit on the **side** on the outer display
  and on the inner display in landscape; the inner display in portrait keeps
  horizontal bars. Keep content clear of **reserved regions** (corner camera,
  inner camera when active, the fold when partially open). Keep the same
  functions and relative control positions across poses. Give every toolbar
  item a title **and** a symbol, and use the system overflow menu (the ellipsis
  is reserved for overflow). Games must fill the screen in every pose.
- **iPadOS**: resizable windows and multitasking sizes, pointer/hover states,
  menu bar, tab bar near the top (optionally convertible to a sidebar),
  sidebar vs tab bar.
- **macOS**: menu bar coverage, keyboard shortcuts, window restoration,
  resizable layouts, pointer affordances, nothing critical at the bottom edge
  of a window, content clear of the camera housing. **On a Mac with a touch
  display**: keep control size and layout the same, but enlarge **tap targets**
  (not the controls); consider expandable variants of small controls; never
  make touch the only path; give hover-revealed controls a touch path (tap to
  reveal, plus a context menu for essential ones). Keep the current selection
  when a tap reveals a hidden control.
- **watchOS**: short interactions, complication relevance, Digital Crown
  input, at most 2–3 side-by-side controls.
- **tvOS**: every interactive element is focusable and legible at distance;
  safe area insets of 60 pt top/bottom and 80 pt sides.
- **visionOS**: 60×60 pt targets with centers ≥ 60 pt apart, depth and
  ornaments (ornaments are for controls, not supplemental content), a
  comfortable field of view, glass materials, gaze + pinch, a vertical tab bar
  on the leading side.

## How to filter (pseudocode)
```python
chosen = {"iOS", "iPadOS"}          # from Step 0
applies = lambda rs: ("all" in rs["platforms"]) or (set(rs["platforms"]) & chosen)
active = {rid: rs for rid, rs in index.items() if applies(rs)}
```
Load `designing-for-iphone-duo` only when the app targets iPhone Duo (it is
tagged `iOS`, so the filter keeps it for any iPhone review; don't cite it for
an app that doesn't run there).
