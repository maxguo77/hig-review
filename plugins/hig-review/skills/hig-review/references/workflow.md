# Review workflow (detailed)

This expands Step 0–4 in `SKILL.md`. Keep internal reasoning precise, but write
everything the **user sees** (gate questions + report) in plain language.

## Step 0 — Ask first (mandatory)
Ask with the AskUserQuestion tool, in user-facing wording (skip a question only
if the user already answered it, or infer the obvious and state it):
1. **Which product is this for?** — iPhone app / iPad app / Mac app /
   Apple Watch · Apple TV · Vision Pro app / web page · data dashboard (数据大屏).
   Multiple allowed (e.g. a universal iPhone + iPad app). Web/dashboard runs in
   **general review mode** (`references/general-review-mode.md`).
2. **What are you giving me?** — code / UI images / UX docs / design files
   (Pencil/Figma). Infer when obvious (one pasted screenshot ⇒ UI image).
3. **Which rules should I check against?** — "本地内置规范(更快)" (the bundled
   baseline) or "联网获取最新规范(稍慢)" (fetch the latest live). If they pick 本地
   but `rules/index.json` is missing, show the first-run sync notice before
   building:
   > 首次使用「离线审查」需先把 Apple HIG 同步到本地基线库（联网抓取一次，约 15–20
   > 分钟，视网络情况）；完成后审查全程离线、更快。现在开始同步，还是改用「联网
   > 获取最新规范」？

Keep the questions in plain language — avoid internal jargon (mode names,
file/version/standard terms). Record the answers; they drive which rules load
and how findings read.

## Step 1 — Discover & classify
- Run `python3 scripts/detect_inputs.py <dir> --pretty`.
- Reconcile with what the user said exists. If they pointed at specific
  files/folders, scope the scan to those.
- Read `references/input-types.md` for per-type handling. Single pasted artifact:
  go straight to the matching playbook (see `SKILL.md` Step 1).

## Step 2 — Select rule sets
- **If `rules/index.json` is missing**, the baseline isn't built yet — show the
  first-run sync notice (Step 0 #3, ~15–20 min estimate), then run
  `python3 scripts/build_rules.py` once (needs network), or use live mode.
- Load `rules/index.json`. Keep rule sets whose `platforms` contains a chosen
  platform OR `"all"`. (See `references/platforms.md` for the matrix and the
  always-relevant foundations: accessibility, color, typography, layout,
  materials, app-icons, privacy.)
- From `component_hits`, gather the candidate rule sets; open the corresponding
  `rules/pages/<slug>.md`. Always also load the foundations above.
- **Latest live rules**: first list every page you expect to cite (e.g. for a
  color-mode pass: `dark-mode`, `color`, `accessibility`, `materials`,
  `typography`) and `hig_fetch.py` them **all up front** — don't start writing
  findings, then cite a page you never fetched. For each in-scope component slug, run
  `python3 scripts/hig_fetch.py <slug>` and **read the full fetched body** (not
  just the title lines) — its bullets are what you cite. Only cite a page you actually fetched this run; for any guideline you didn't fetch, fetch it or label `依据` as "本地内置基线". If the fetched text
  matches the bundled baseline, note "与内置规范一致" rather than implying new
  info. For **web · 数据大屏** the latest Apple HIG rarely changes the general
  principles; the bundled baseline is usually enough.
- **Web · 数据大屏**: load `references/general-review-mode.md` instead of the
  platform pages.

## Step 3 — Evaluate (the actual review)
For each artifact:
- **Code** — inspect each `component_hit` and its context. Common checks: hit
  region ≥ 44×44 pt (60×60 in visionOS); custom buttons have a press state;
  semantic/system colors not hard-coded; Dynamic Type / accessibility labels
  present; navigation depth and a back path; destructive actions confirmed;
  modality used appropriately.
- **UI images** — read the image; identify components & layout; check spacing,
  contrast (real pixels via `visual_checks.py sample`), alignment, target sizes
  (needs a known scale), safe-area handling, consistency.
- **UX docs** — verify flows against navigation, feedback, onboarding, and
  error-handling guidance.
- **Design files** — pull layout/tokens via the Pencil/Figma MCP and check
  spacing scale, type ramp, color tokens, component usage.
- **Config** — Info.plist (orientations, status bar, launch screen), asset
  catalogs (icon sizes, accent color, SF Symbols), localization (text growth, RTL).

Keeping it honest:
- Only cite a guideline that exists in the baseline or that you actually fetched.
  Never fabricate guidelines.
- If nothing covers it, report it as 提示 (Info) and say so — don't attach a fake
  rule. If the closest guideline is a loose fit, mark `依据` "参考(最相近)" or
  lower to 提示. Accuracy beats coverage.
- Ground measurements in real data: contrast from `visual_checks.py sample` or a
  stated color, not eyeballed hex; px↔pt only with a known scale. Mark estimates.
- Prefer precise, reproducible locations over vague ones.

## Step 4 — Report
Follow `references/output-format.md` exactly: title 「HIG 滚动基线审查报告」,
summary table, then findings ordered by severity (each: 位置 / 问题 / 影响 /
建议 / 依据). State the baseline `VERSION`, the rule source used (本地内置 / 联网
最新), and the product/platform(s). Offer the JSON sidecar if CI is wanted.

## Maintenance commands
- Build / regenerate the baseline: `python3 scripts/build_rules.py`
- Update & diff: `python3 scripts/build_rules.py --upgrade`
- Rebuild index only (no network): `python3 scripts/build_rules.py --reindex`
