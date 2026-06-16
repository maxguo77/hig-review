#!/usr/bin/env bash
# SessionStart hook (plugin-only): proactively nudge the user to build the local
# HIG baseline the first time(s) after install. Goes SILENT once the baseline
# exists (rules/index.json present) or the user opts out (.hig-skip-setup-notice).
#
# Why a SessionStart hook: Claude Code has no "post-install" event, but a missing
# baseline IS the freshly-installed state — checking for it at session start gives
# a proactive, self-resolving nudge that disappears after the build.
set -euo pipefail

# Plugin context exports CLAUDE_PLUGIN_ROOT; fall back to this script's location
# (this file lives at <plugin-root>/hooks/, so the parent dir is the plugin root).
BASE="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$BASE" ]; then
  BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

RULES="$BASE/skills/hig-review/rules"
[ -f "$RULES/index.json" ] && exit 0             # baseline already built -> silent
[ -f "$RULES/.hig-skip-setup-notice" ] && exit 0 # user opted out -> silent

# stdout from a SessionStart hook is added to the session context; the model
# relays this to the user at a suitable moment.
cat <<'EOF'
[hig-review] 本地 HIG 规范基线尚未构建（rules/index.json 不存在）。请在本次会话里，用一句话主动提示用户：
「HIG Review 已就绪，但首次「离线审查」前需联网同步一次 Apple HIG 规范基线（约 15–20 分钟，视网络情况），之后审查全程离线、更快。现在可运行 /hig-review:baseline-init 建库；或在审查时改用「联网获取最新规范」零等待开始。」
若用户只打算用联网模式、不想再看到此提示，可创建空文件 rules/.hig-skip-setup-notice 关闭它。
EOF
