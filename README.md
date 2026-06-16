# HIG Review

**English** | [简体中文](README.zh-CN.md)

HIG Review runs a systematic quality review of your design against Apple's Human
Interface Guidelines (HIG).

Inputs can be code, UI screenshots, interactive prototypes, UX spec docs, user-flow
diagrams, or design files (a Figma link, a Pencil `.pen`). Coverage spans iPhone,
iPad, Mac, Apple Watch, Apple TV, and Vision Pro — plus a general mode for web pages
and data dashboards.

Every finding has five parts: **location · problem · impact · suggested fix · the
guideline it's based on (with a link)** — so every change is justified.

Shipped as a Plugin and an Agent Skill, callable directly in Claude Code, Codex,
Kimi Code CLI, and other compatible agents; Claude Code and Codex plugin versions
are provided.

## What it reviews
- **Inputs:** source code · UI images / screenshots / mockups · UX docs, specs &
  flows · design files (paste a **Figma** link, or a Pencil **`.pen`**) · or a
  whole **project folder** (auto-inventoried by `detect_inputs.py`).
- **Apple platforms:** iPhone · iPad · Mac · Apple Watch · Apple TV · Vision Pro.
- **General mode** for **web pages & data dashboards** — applies the HIG's
  cross-platform design principles as a quality lens, and uses **WCAG** for the
  web-specific checks (contrast, target size, keyboard, focus). These read as
  design guidance, not platform rules.

## What you get
Every finding is concrete and traceable — a **severity**, the exact **location**,
the **problem**, its **impact**, a **concrete fix**, and the **guideline** it's
based on (name + link). For example:

```
【Blocker】Sources/Views/CartButton.swift:33 — Custom button has no pressed state
  Problem:  Built with .onTapGesture, so a tap shows no visual change.
  Impact:   People think the tap didn't register and tap again repeatedly.
  Fix:      Use a ButtonStyle with a pressed state (drive opacity/scale from
            configuration.isPressed).
  Based on: Apple HIG — Buttons
            https://developer.apple.com/design/human-interface-guidelines/buttons
```

Measurements are grounded in real data (real-pixel color sampling, WCAG contrast,
image dimensions), not eyeballing. A machine-readable JSON sidecar is available for
CI when you ask for it.

## Key features
- **Grounded in the real HIG.** Cite from a **locally-built offline baseline** or
  fetch the **latest rules live** — every finding maps to an actual guideline, no
  invented rules.
- **Real-pixel visual checks.** Contrast ratios and sizes come from
  `visual_checks.py`, not from eyeballing a mockup.
- **Cross-platform & cross-agent.** Six Apple platforms plus a web/dashboard mode;
  ships as an open Skill and as a Claude Code plugin with four slash commands.
- **Privacy-friendly & offline-first.** Ships only the *generator*, never Apple's
  HIG text; rules are built on your machine, and reviews then run fully offline.

## Install
The **skill** and the **plugin** install independently — pick whichever fits your
agent.

### Option A — as a skill (any compatible agent)
The skill lives in this repo at **`.claude/skills/hig-review/`**. Copy that whole
folder into your agent's skills directory:

| Agent | Skills directory |
|-------|------------------|
| Claude Code | `.claude/skills/hig-review/` (project) or `~/.claude/skills/hig-review/` (user) |
| Codex | `.agents/skills/hig-review/` (project) or `~/.agents/skills/hig-review/` (user) |
| Kimi Code CLI / others | that agent's skills directory (any folder containing `SKILL.md` is discovered) |

The agent then triggers it automatically from the `SKILL.md` description, or you
can invoke the **skill** explicitly (e.g. `/hig-review` in Claude Code — this is
the skill itself; the plugin's slash commands are the `/hig-review:…` ones below).
Tool names in the
docs are Claude Code names — see **“Running on non-Claude agents”** in `SKILL.md`
for the equivalents.

### Option B — as a Claude Code plugin (one-command install)
This repo doubles as a plugin **marketplace** named `apple-hig`. In Claude Code:
```text
/plugin marketplace add maxguo77/hig-review
/plugin install hig-review@apple-hig
```
The bundled plugin lives at `plugins/hig-review/` and is self-contained (it ships
its own copy of the skill, since plugins are copied to a cache on install). Once
installed, invoke it with `/hig-review:review`, or let the agent trigger it
automatically.

> **Maintainers:** `.claude/skills/hig-review/` (the skill) and `.claude/commands/`
> (the slash commands) are the canonical copies. After editing either, run
> `./tools/sync-plugin.sh` to refresh `plugins/hig-review/` so the two stay in sync.

## Commands
The plugin ships four slash commands, namespaced under the plugin name:

| Command | What it does |
|---------|--------------|
| `/hig-review:review [target]` | Run a full review (code / UI images / UX docs / designs); optionally pass a path, file, or link |
| `/hig-review:review-notes <notes>` | Same, but folds your manual focus / extra rules in as a high-priority emphasis |
| `/hig-review:baseline-init` | Build the local HIG baseline for the first time (`build_rules.py`, online, ~15–20 min) |
| `/hig-review:baseline-upgrade` | Re-crawl and diff (`build_rules.py --upgrade`); report +added/~changed/−removed and bump `VERSION` |

The baseline commands are thin wrappers around the scripts in
[Maintaining the baseline](#maintaining-the-baseline). The `hig-review` skill also
auto-triggers from a request — these commands are just explicit entry points. As
**bare project commands** in this repo, drop the namespace: `/review`,
`/review-notes`, `/baseline-init`, `/baseline-upgrade`.

## Requirements
- **Python 3.7+**, standard library only — **no `pip install`**.
- Use whatever launches Python 3 on your OS: `python3` on macOS/Linux,
  `python` or `py` on Windows.
- **Build once (online), then offline.** This repo ships only the *generator*, not
  Apple's HIG text. The first build and *“latest live rules”* fetch from
  `developer.apple.com`; everything else runs offline.

## First-time setup: build the baseline
The rule corpus isn't committed (it's derived from Apple's HIG — see
[Source & attribution](#source--attribution)). Build it once into your local copy
(from the skill directory, needs network, ~15–20 min):
```bash
cd .claude/skills/hig-review        # or the plugin's skills/hig-review/ once installed
python3 scripts/build_rules.py
```
This writes `rules/pages/`, `rules/index.json`, `rules/manifest.json`, and
`VERSION`. After that, reviews run fully offline. Skip this if you only ever use
“latest live rules”.

You rarely need to run this by hand:
- **Installed as a plugin**, a `SessionStart` hook detects a missing baseline and
  proactively nudges you to run `/hig-review:baseline-init` (it goes silent once
  the baseline exists). Only-using-live-rules? Create an empty
  `skills/hig-review/rules/.hig-skip-setup-notice` to mute it.
- **Run as a skill / mid-review**, the assistant offers to build when it sees
  `rules/` is empty (the first-run sync notice, ~15–20 min).

## What's inside `.claude/skills/hig-review/`
```
├── SKILL.md             entry point / workflow
├── agents/openai.yaml   optional Codex/Agent-Skills display metadata
├── references/          load-on-demand guidance:
│   ├── workflow.md, platforms.md, input-types.md,
│   ├── ui-image-review.md, ux-doc-review.md, figma-review.md,
│   └── general-review-mode.md, output-format.md
├── rules/               HIG baseline — built locally by build_rules.py, NOT committed
│   ├── index.json       (generated) rule set -> {title, url, platforms, file, category}
│   ├── manifest.json    (generated) baseline version + per-page content hashes
│   └── pages/<slug>.md  (generated) one HIG page per file; stable ids (HIG-<SLUG>-NNN)
├── scripts/
│   ├── hig_lib.py, build_rules.py, hig_fetch.py,
│   └── detect_inputs.py, visual_checks.py
└── VERSION              baseline version (date-based)
```

## Maintaining the baseline
Run from inside `.claude/skills/hig-review/`:
```bash
python3 scripts/build_rules.py            # build / regenerate the whole baseline
python3 scripts/build_rules.py --upgrade  # re-crawl, diff, report +added/~changed/-removed
python3 scripts/build_rules.py --reindex  # rebuild index/manifest from files (no network)
python3 scripts/build_rules.py --limit 10 # smoke test (does not touch the canonical baseline)
```
The baseline is built by crawling Apple's DocC JSON endpoints
(`…/tutorials/data/design/human-interface-guidelines/{path}.json`) via
`scripts/hig_lib.py`.

### Live fetch & image helpers
```bash
python3 scripts/hig_fetch.py buttons              # latest guidance for one page
python3 scripts/visual_checks.py dims shot.png --platform macos --scale 2
python3 scripts/visual_checks.py sample shot.png 0.3 0.4 0.5 0.4 --norm --contrast
python3 scripts/visual_checks.py contrast "#767676" "#FFFFFF"
```

## Optional MCP enhancements
All MCP use is optional — the skill works without any MCP.
- **Figma** review from a pasted link (connect the Figma MCP — `/mcp` in Claude Code).
- **Pencil** `.pen` design files via the Pencil MCP.

## Source & attribution
This repo ships **only the generator** (`scripts/`), **not** Apple's HIG text. The
rule corpus under `rules/` is fetched on your machine by `build_rules.py` from
Apple's **Human Interface Guidelines** (developer.apple.com). Apple HIG content is
© Apple Inc.; this project isn't affiliated with or endorsed by Apple. The locally
built `rules/` are for your own use — don't redistribute the extracted text.

## License
[MIT](LICENSE) for the tooling in this repo. Apple HIG content is © Apple Inc. and
is **not** included here — see [Source & attribution](#source--attribution).

## Roadmap
- Pencil `.pen` design-source review; optional JSON report sidecar for CI.
