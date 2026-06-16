# Platform matrix

The crawler tags every rule page with `platforms` (from page metadata when
present, otherwise inferred from the page slug and content keywords). A rule set
applies to a target platform when its `platforms` list contains that platform
**or** `"all"`.

## Supported targets
| Target | HIG "Designing for…" page | Notes |
|--------|---------------------------|-------|
| iOS | `designing-for-ios` | Touch-first; hit target ≥ 44×44 pt. |
| iPadOS | `designing-for-ipados` | Multitasking, pointer, sidebars, keyboard. |
| macOS | `designing-for-macos` | Menu bar, windows, pointer precision, toolbars. |
| watchOS | `designing-for-watchos` | Glanceable, complications, Digital Crown. |
| tvOS | `designing-for-tvos` | Focus engine, 10-ft UI, remote. |
| visionOS | `designing-for-visionos` | Spatial, eyes+hands, hit target ≥ 60×60 pt, ornaments. |
| CarPlay | `carplay` | Driver-safe, templated UI. |
| **Web / 数据大屏** | — (not an Apple platform) | **General review mode** only — see `general-review-mode.md`. |

## Always-load foundations (any Apple platform)
Regardless of detected components, include these foundation rule sets — they
apply broadly and catch the most common violations:
- `HIG-ACCESSIBILITY`
- `HIG-COLOR`
- `HIG-TYPOGRAPHY`
- `HIG-LAYOUT`
- `HIG-MATERIALS` (Liquid Glass / vibrancy)
- `HIG-APP-ICONS`
- `HIG-PRIVACY`
- `HIG-DESIGN-PRINCIPLES`

Plus the per-platform "Designing for <platform>" page for each chosen platform.

## Platform-specific gotchas to check
- **iOS/iPadOS**: safe areas, Dynamic Type, hit targets, modality, Dark Mode.
- **iPadOS**: pointer/hover states, multitasking sizes, sidebar vs tab bar.
- **macOS**: menu bar coverage, keyboard shortcuts, window restoration,
  resizable layouts, pointer affordances.
- **watchOS**: short interactions, complication relevance, Digital Crown input.
- **tvOS**: every interactive element is focusable & legible at distance.
- **visionOS**: 60×60 pt targets, depth/ornaments, comfortable field of view,
  glass materials, gaze + pinch.

## How to filter (pseudocode)
```python
chosen = {"iOS", "iPadOS"}          # from Step 0
applies = lambda rs: ("all" in rs["platforms"]) or (set(rs["platforms"]) & chosen)
active = {rid: rs for rid, rs in index.items() if applies(rs)}
```
