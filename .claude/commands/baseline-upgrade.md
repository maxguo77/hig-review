---
description: "升级本地审查基线：重新抓取并 diff，报告 +新增/~变更/-删除 并更新 VERSION"
---

升级本地 HIG 规范基线：重新抓取 Apple HIG，与现有 manifest 做 diff，报告变化并更新版本。

步骤：

1. 确定 `build_rules.py` 的**完整路径**（下面整条就是要执行的脚本路径，不要再往后拼接文件名）：
   - 在本仓库开发时：`.claude/skills/hig-review/scripts/build_rules.py`
   - 作为已安装插件运行时：`${CLAUDE_PLUGIN_ROOT}/skills/hig-review/scripts/build_rules.py`
2. 用 **Bash 工具**直接运行该脚本（不要预执行；这是一次联网爬取）。本仓库即：
   `python3 .claude/skills/hig-review/scripts/build_rules.py --upgrade`
   （插件环境换成 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/hig-review/scripts/build_rules.py --upgrade`）
3. 汇总脚本输出：**+新增 / ~变更 / -删除** 的页面，以及更新后的 `VERSION`。若与上一版无变化，
   明确说明「基线已是最新」。若本地基线还不存在（`rules/index.json` 缺失），提示先运行
   `baseline-init` 命令做首次构建。失败时原样转述错误。
