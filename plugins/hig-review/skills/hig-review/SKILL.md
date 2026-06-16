---
name: hig-review
description: >-
  Review a project against Apple's Human Interface Guidelines (HIG) like a code
  review — checks code, UI mockups/screenshots, UX flows, docs, and design
  source files for iPhone / iPad / Mac / Apple Watch / Apple TV / Vision Pro
  apps, plus a general review mode for web pages and data dashboards (数据大屏).
  Reports each issue with its exact location, the reason, the impact, a fix, and
  the guideline it is based on. Use when the user asks to "审查 HIG / HIG review /
  检查是否符合苹果设计规范 / Human Interface Guidelines check / HIG code review".
---

# HIG Review

A "code review for design quality": evaluate project artifacts against the Apple
Human Interface Guidelines and report each issue with **location + problem +
impact + fix + the guideline it's based on**. The user-facing report is titled
**「HIG 滚动基线审查报告」** (HIG Rolling Baseline Review). The "rolling baseline"
is the rule set in `rules/`, **built locally** by `scripts/build_rules.py` and
versioned in `VERSION`.

## First-run setup (build the baseline)
This skill ships the **generator**, not Apple's HIG text. **If `rules/index.json`
is missing, the baseline hasn't been built yet** — run `python3
scripts/build_rules.py` once (crawls Apple's HIG into `rules/`; needs network,
~15–20 min). After that, reviews run offline. (Live mode via `hig_fetch.py` needs no
prebuilt baseline.) Offer to run the build when you detect `rules/` is empty.

When the user picks **offline / 本地规范** but the baseline isn't built yet, show
this exact, user-facing notice before building (don't just fail or silently
build) — then act on their choice:
> 首次使用「离线审查」需先把 Apple HIG 同步到本地基线库（联网抓取一次，约 15–20
> 分钟，视网络情况）；完成后审查全程离线、更快。现在开始同步，还是改用「联网获取
> 最新规范」？

If they sync, run `python3 scripts/build_rules.py` and report the new `VERSION`;
if they'd rather not wait, fall back to live mode.

## Assets
- `rules/index.json` — (generated) map of rule set → `{title, url, platforms, file, category}`.
- `rules/pages/<slug>.md` — (generated) one file per HIG page; each guideline has a
  stable id (e.g. `HIG-BUTTONS-003`) and a source URL. The id is for internal
  traceability only — in the report, present the guideline by **name + link**, not by id.
- `rules/manifest.json` + `VERSION` — (generated) baseline version & per-page hashes.
- `scripts/` — `detect_inputs.py`, `hig_fetch.py` (live fetch), `build_rules.py`
  (build/update the baseline), `hig_lib.py` (shared fetch/parse),
  `visual_checks.py` (`dims` size/device, `sample` real PNG pixel colors,
  `contrast` WCAG ratio).
- `references/` — load as needed: `workflow.md`, `platforms.md`, `input-types.md`,
  `ui-image-review.md`, `ux-doc-review.md`, `figma-review.md`,
  `general-review-mode.md`, `output-format.md`.

## How to run a review

> **Mandatory reads — don't review from memory.** Before producing any finding,
> open the playbook(s) for the input type you're handling (`ui-image-review.md`,
> `ux-doc-review.md`, `figma-review.md`, `input-types.md`, or
> `general-review-mode.md`) **and** `output-format.md`. These carry the exact
> sampling strategy, severity labels (严重/重要/建议/提示), and citation rules; the
> report drifts (wrong severities, ungrounded citations, bad measurements) when
> you skip them.

### Step 0 — Ask first (do this before reviewing, every time)
Ask the user (the AskUserQuestion tool in Claude Code, or your agent's
equivalent) with **plain, user-facing wording** (no internal jargon like
"offline/online/corpus"). Confirm:
1. **Which product is this for?** — iPhone app / iPad app / Mac app /
   Apple Watch · TV · Vision Pro app / **web page · data dashboard (数据大屏)**.
   (Web/dashboard → general review mode, see `references/general-review-mode.md`.)
2. **What are you giving me?** — code / UI images / UX docs / design files
   (Pencil `.pen`, Figma). Infer this when obvious (a single pasted screenshot ⇒
   UI image; a pasted **Figma link** ⇒ Figma design, go to
   `references/figma-review.md`) and just state your assumption instead of asking.
3. **Which rules should I check against?** — "本地规范(更快)" (the locally-built
   baseline) or "联网获取最新规范(稍慢)" (fetch the latest live). If they pick 本地
   but the baseline isn't built yet, show the first-run sync notice (see First-run
   setup) — the one estimating ~15–20 min — then build or fall back to live.

You may infer obvious answers and state them; still confirm the product type and
the rule source, since those change the result most.

### Step 1 — Find & sort what to review
**Single pasted/named artifact?** If the user gives one image, doc, link, or file
(not a project), skip `detect_inputs.py` and go straight to the matching playbook
(`ui-image-review.md` for an image, `ux-doc-review.md` for a spec, a **Figma link
(`figma.com/(design|file|proto)/…`) ⇒ `figma-review.md`**, the code checks in
`input-types.md` for a source file).

For a **project or folder**, run `python3 scripts/detect_inputs.py <project_dir>
--pretty`. It returns an inventory (code / design_images / design_sources / docs
/ configs) plus `component_hits` (UI symbols with `file:line` and candidate rule
sets). See `references/input-types.md` for how to handle each type. For UI images
follow `references/ui-image-review.md` (run `scripts/visual_checks.py`); for UX
specs follow `references/ux-doc-review.md`.

### Step 2 — Load the applicable rules
- Filter `rules/index.json` to the chosen product/platform(s) (a rule set applies
  if its `platforms` includes the target or `"all"`). See `references/platforms.md`.
- For each detected component, open the matching `rules/pages/<slug>.md`.
- **Bundled baseline (default)**: use only the local `rules/`.
- **Latest live rules**: additionally run `python3 scripts/hig_fetch.py <slug>` and
  **read the full fetched body** — base citations on that text; if it matches the
  bundled baseline, note "与内置规范一致". For **web · 数据大屏**, the latest Apple HIG
  rarely changes the general principles — the bundled baseline is usually enough.
- **Web · 数据大屏**: use `references/general-review-mode.md`.

### Step 3 — Evaluate
For each artifact, compare it against the loaded guidelines. Map components to
rule sets (the `component_hits` candidates — confirm against the index). Report
only real issues; don't invent rules. Base every citation on a guideline that
exists in the baseline (or that you actually fetched). Ground measurements in
real data (`visual_checks.py sample` / a known scale), not eyeballing.

### Step 4 — Report
Produce the report exactly as specified in `references/output-format.md`: the
title 「HIG 滚动基线审查报告」, a summary table, then findings — each with
severity (bilingual), location, the problem, its impact, a concrete fix, and the
guideline it's based on (name + link). Offer the machine-readable JSON sidecar
when the user wants CI integration.

## Maintaining the baseline
- **Build / regenerate**: `python3 scripts/build_rules.py`
- **Update & diff**: `python3 scripts/build_rules.py --upgrade` — re-crawls,
  reports added/changed/removed pages, bumps `VERSION`.
- **Rebuild index only (no network)**: `python3 scripts/build_rules.py --reindex`.

## Scope notes
- Web pages and data dashboards (数据大屏) aren't Apple platforms. The general
  review mode applies HIG's cross-platform design principles as a quality lens,
  and uses WCAG as the standard for web specifics (contrast, target size,
  keyboard). Phrase such findings as design guidance, not platform rules.
- This is a Skill; it can later move into a plugin
  (`plugins/hig-review/skills/hig-review/`) unchanged.

## Running on non-Claude agents
This skill follows the open Agent Skills format and works on any compatible agent
(Claude Code, Codex, Kimi, …). Tool names in these docs are **Claude Code** names —
on another agent, use its equivalent:
- **AskUserQuestion** → ask the user a question however your agent does it.
- **the Read tool** → your agent's file / image / PDF reader.
- **ToolSearch** → your agent's tool discovery/search.
- **MCP connectors** (claude.ai Figma, Pencil) and **`/mcp`** →
  connect the equivalent MCP through your agent's MCP setup. All MCP use here is
  **optional** — the bundled rules + Python scripts work without any MCP.
- **`python3`** → whatever launches Python 3 on your OS (`python` or `py` on
  Windows).
