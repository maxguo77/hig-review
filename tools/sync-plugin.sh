#!/usr/bin/env bash
# Mirror the canonical standalone skill and commands into the distributable plugin.
#
#   canonical source : .claude/skills/hig-review/   +   .claude/commands/
#   plugin copy      : plugins/hig-review/skills/hig-review/   +   plugins/hig-review/commands/
#
# A plugin is copied to a cache on install and must be self-contained, so the
# plugin bundles its own copy of the skill and the slash commands. Edit them under
# .claude/, then run this script to keep the plugin copy in step.
#
# NOT synced: plugins/hig-review/hooks/ — hooks only run in plugin context (they
# rely on ${CLAUDE_PLUGIN_ROOT}), so they're authored directly in the plugin and
# have no .claude/ counterpart. The rsync targets below don't touch hooks/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude/skills/hig-review/"
DST="$REPO_ROOT/plugins/hig-review/skills/hig-review/"

mkdir -p "$DST"
rsync -a --delete \
  --exclude '.DS_Store' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$SRC" "$DST"

echo "synced: .claude/skills/hig-review/ -> plugins/hig-review/skills/hig-review/"

# Slash commands live at the plugin root (commands/), not inside the skill.
CMD_SRC="$REPO_ROOT/.claude/commands/"
CMD_DST="$REPO_ROOT/plugins/hig-review/commands/"

mkdir -p "$CMD_DST"
rsync -a --delete \
  --exclude '.DS_Store' \
  "$CMD_SRC" "$CMD_DST"

echo "synced: .claude/commands/ -> plugins/hig-review/commands/"
