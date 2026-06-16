---
description: "初始化本地基线：首次构建本地 HIG 规范库（需联网，约 15–20 分钟）"
---

构建本地 HIG 规范基线（`hig-review` skill 的「滚动基线」）。**仅在本地基线尚未构建时需要**
——判断依据：skill 的 `rules/index.json` 不存在。若已存在，提示用户用
`baseline-upgrade` 命令升级即可，不要重复全量构建。

步骤：

1. 确定 `build_rules.py` 的**完整路径**（下面整条就是要执行的脚本路径，不要再往后拼接文件名）：
   - 在本仓库开发时：`.claude/skills/hig-review/scripts/build_rules.py`
   - 作为已安装插件运行时：`${CLAUDE_PLUGIN_ROOT}/skills/hig-review/scripts/build_rules.py`
2. 用 **Bash 工具**直接运行该脚本（不要预执行；这是一次约 15–20 分钟的联网爬取）。本仓库即：
   `python3 .claude/skills/hig-review/scripts/build_rules.py`
   （插件环境换成 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/hig-review/scripts/build_rules.py`）
   脚本输出目录由其自身 `__file__` 推导，与当前工作目录无关。
3. 完成后回报：新的 `VERSION`、构建出的页面数量（`rules/pages/` 文件数），以及一句话说明
   「之后审查可离线运行」。若失败（如网络问题），原样转述错误并给出可行的下一步。
