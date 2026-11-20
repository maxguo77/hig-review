# UX doc / interaction-spec review playbook

How to review a UX interaction spec, flow doc, or requirements doc (Markdown /
text / PDF) against the HIG. The model reads the doc; this playbook turns it
into a systematic flow review with precise citations. Cite only guidelines that
exist in the baseline, and present each by **name + link** (see
`output-format.md`) — the internal id (e.g. `HIG-ALERTS-003`) lives in the page
file for traceability; never invent one.

## Step 1 — Extract the flow skeleton
Read the doc and outline it as: **screens → steps → states**. For Markdown/text,
note line numbers (cite `doc.md:line`); for PDF, use the Read tool's `pages`
parameter and cite `page N` + a quoted sentence. List every state the doc
mentions (and, importantly, the ones it omits).

## Step 2 — Evaluate the flow (grouped by rule set)
Walk the flow and check each concern; open the matching `rules/pages/<slug>.md`
for exact guidelines.

| Concern | What to verify | Rule set |
|---------|----------------|----------|
| Purpose & agency | The flow's main job is clear; guided flows can be skipped or escaped; people aren't locked into modes; mistakes are reversible | `HIG-DESIGN-PRINCIPLES` (Purpose, Agency) |
| Launch / first run | Fast, useful launch; no unnecessary splash/setup; value before sign-in where possible | `HIG-LAUNCHING` |
| Onboarding | Brief, skippable, teaches by doing, doesn't gate core value behind long tutorials | `HIG-ONBOARDING` |
| Navigation & back | Clear hierarchy; every screen has a predictable way back; no dead ends | `HIG-NAVIGATION-AND-SEARCH` |
| Modality | Sheets/alerts used only when warranted; dismissible; not nested needlessly. Sheets: Cancel/Close dismisses without saving, Done is always paired with Cancel or Back, Back never dismisses the sheet, never all three at once; swipe-to-dismiss with unsaved changes asks to confirm | `HIG-MODALITY`, `HIG-SHEETS`, `HIG-ALERTS` |
| Feedback & progress | Every action acknowledges; long tasks show progress; success/failure communicated | `HIG-FEEDBACK`, `HIG-PROGRESS-INDICATORS` |
| Loading / empty states | Loading state defined; empty state guides the user (not a blank screen) | `HIG-LOADING`, `HIG-FEEDBACK` |
| Error handling & recovery | Errors are explained, recoverable, and avoid blame; offer next steps | `HIG-ALERTS`, `HIG-FEEDBACK` |
| Destructive actions | Significant/irreversible actions are confirmed and use destructive styling | `HIG-ALERTS`, `HIG-ACTION-SHEETS` |
| Permission requests | Asked in context, with a clear reason, at the moment of need — not upfront/blanket | `HIG-PRIVACY` |
| Accounts / sign-in | Let people explore before requiring an account; support Sign in with Apple where relevant | `HIG-MANAGING-ACCOUNTS`, `HIG-PRIVACY` |
| Notifications | Opt-in explained; not required to use the app; respectful frequency | `HIG-NOTIFICATIONS`, `HIG-MANAGING-NOTIFICATIONS` |
| Flow accessibility & input | Doesn't rely on one sense/gesture; supports VoiceOver/keyboard paths; on Mac, touch is never the only path and hover-only actions have a touch path | `HIG-ACCESSIBILITY`, `HIG-GESTURES`, `HIG-POINTING-DEVICES` |
| Adaptivity across sizes | Same functions and state across sizes/poses (iPhone Duo outer ↔ inner display, resized iPad windows); the spec doesn't drop features on smaller sizes | `HIG-LAYOUT`, `HIG-DESIGNING-FOR-IPHONE-DUO` |
| AI features | Generated results can be refined and given feedback on; progress shown during generation; limits disclosed | `HIG-GENERATIVE-AI` |

## Step 3 — Look for omissions (common in specs)
Flag missing states explicitly — they're frequent and high-impact:
- No **error / failure** path described.
- No **loading** or **empty** state.
- **Destructive** action with no confirmation.
- **Permission** requested at launch with no contextual reason.
- No **back / cancel** path from a step.
- A sheet that ends in **Done** with no Cancel/Back.

## Step 4 — Report
Use `references/output-format.md`. Location = `doc.md:line` (or `page N`) plus a
quoted sentence and the step it belongs to, e.g.:
```
【严重 (Blocker)】checkout-flow.md:42 —「删除账户」点击后立即执行
  问题 / Problem: 不可逆操作未二次确认……
  依据 / Based on: Apple 人机界面指南 — 提醒 (Alerts)
                  https://developer.apple.com/cn/design/human-interface-guidelines/alerts
```
A missing state is a legitimate finding even though it has no line: cite the
nearest heading and describe what's absent.
