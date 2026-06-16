# HIG Review

[English](README.md) | **简体中文**

HIG Review 对照 Apple 人机界面指南（HIG），对你的设计做一次系统性的质量审查。

输入可以是代码、UI 截图、交互原型、UX 规格文档、用户流程图，或 Figma 链接、Pencil
`.pen` 等设计文件。审查范围覆盖 iPhone、iPad、Mac、Apple Watch、Apple TV、Vision Pro，
以及网页与数据大屏的通用场景。

每条审查结果包含五个要素：**位置 · 问题 · 影响 · 修改建议 · 依据指南（附链接）**，让
每一处改动有理有据。

以 Plugin 和 Agent Skill 形式发布，可在 Claude Code、Codex、Kimi Code CLI 等兼容 agent
中直接调用；同时提供 Claude Code、codex plugin 版本。

## 评审什么
- **输入**：源代码 · UI 图 / 截图 / 原型 · UX 文档、规格与流程 · 设计文件（粘贴 **Figma**
  链接，或 Pencil **`.pen`**）· 或整个**项目目录**（由 `detect_inputs.py` 自动盘点）。
- **Apple 平台**：iPhone · iPad · Mac · Apple Watch · Apple TV · Vision Pro。
- **通用模式**：面向**网页与数据大屏**——把 HIG 的跨平台设计原则当作质量透镜，Web 的
  具体项（对比度、目标尺寸、键盘、焦点）用 **WCAG** 衡量。这类结论按设计建议呈现，而非
  平台硬性规则。

## 产出什么
每条发现都具体、可追溯——包含**严重度**、精确**位置**、**问题**、**影响**、具体**修复**，
以及所**依据的指南**（名称 + 链接）。例如：

```
【严重 Blocker】Sources/Views/CartButton.swift:33 — 自定义按钮没有按下反馈
  问题：用 .onTapGesture 实现，点击时没有任何视觉变化。
  影响：用户以为没点到，反复点击。
  修复：改用带按下态的 ButtonStyle（用 configuration.isPressed 驱动透明度/缩放）。
  依据：Apple 人机界面指南 — 按钮 (Buttons)
        https://developer.apple.com/design/human-interface-guidelines/buttons
```

涉及测量的结论都基于真实数据（真实像素取色、WCAG 对比度、图像尺寸），不靠肉眼估计。需要时
还能附带一份机读 JSON，便于接入 CI。

## 关键特性
- **论据扎实**：可用**本地离线基线**，也可**联网获取最新规范**——每条发现都落到真实存在的
  指南，绝不凭空编造。
- **真实像素核验**：对比度与尺寸由 `visual_checks.py` 实测，而不是对着原型目测。
- **跨平台、跨 agent**：六个 Apple 平台外加网页/大屏模式；以开放 Skill 与 Claude Code 插件
  两种形式发布，含 4 个斜杠命令。
- **隐私友好、离线优先**：只发*生成器*、绝不含 Apple 的 HIG 原文；规则在你本机构建，之后
  审查全程离线。

## 安装
**skill** 和 **plugin** 各自独立安装——按你的 agent 选其一即可。

### 方式 A —— 作为 skill（任何兼容 agent）
skill 位于本仓库 **`.claude/skills/hig-review/`**。把整个文件夹拷进你 agent 的
skills 目录：

| Agent | skills 目录 |
|-------|------------------|
| Claude Code | `.claude/skills/hig-review/`（项目级）或 `~/.claude/skills/hig-review/`（用户级） |
| Codex | `.agents/skills/hig-review/`（项目级）或 `~/.agents/skills/hig-review/`（用户级） |
| Kimi Code CLI / 其它 | 该 agent 的 skills 目录（任意含 `SKILL.md` 的文件夹都会被发现） |

agent 会根据 `SKILL.md` 描述自动触发它，你也可以显式调用**该 skill**（如 Claude Code 里
`/hig-review`——这是 skill 本身；插件的斜杠命令是下文的 `/hig-review:…` 那些）。文档里的工具名是
Claude Code 的叫法——其它 agent 的对应关系见
`SKILL.md` 中的 **“Running on non-Claude agents”**。

### 方式 B —— 作为 Claude Code 插件（一条命令安装）
本仓库同时是一个名为 `apple-hig` 的插件**市场（marketplace）**。在 Claude Code 里：
```text
/plugin marketplace add maxguo77/hig-review
/plugin install hig-review@apple-hig
```
打包的插件位于 `plugins/hig-review/`，自包含（自带一份 skill 副本，因为插件在安装时
会被复制到缓存）。安装后用 `/hig-review:review` 调用，或让 agent 自动触发。

> **维护者：** `.claude/skills/hig-review/`（skill）与 `.claude/commands/`（斜杠命令）
> 是 canonical 源。改动任一处后，运行 `./tools/sync-plugin.sh` 刷新
> `plugins/hig-review/`，让两者保持同步。

## 命令
插件提供 4 个斜杠命令，均带插件名作命名空间：

| 命令 | 作用 |
|------|------|
| `/hig-review:review [目标]` | 跑一次完整审查（代码 / UI 图 / UX 文档 / 设计稿）；可选传入要审查的路径、文件或链接 |
| `/hig-review:review-notes <补充指令>` | 同上，但把你的人工关注点 / 额外规则作为高优先侧重点纳入审查 |
| `/hig-review:baseline-init` | 首次构建本地 HIG 规范库（`build_rules.py`，需联网，约 15–20 分钟） |
| `/hig-review:baseline-upgrade` | 重新抓取并 diff（`build_rules.py --upgrade`），报告 +新增/~变更/−删除 并更新 `VERSION` |

基线相关命令只是 [维护基线](#维护基线) 里脚本的薄封装。`hig-review` skill 仍会从请求中自动
触发，这些命令只是显式入口。在本仓库内作**裸项目命令**使用时去掉命名空间：`/review`、
`/review-notes`、`/baseline-init`、`/baseline-upgrade`。

## 环境要求
- **Python 3.7+**，仅用标准库——**无需 `pip install`**。
- 用你系统上启动 Python 3 的命令：macOS/Linux 用 `python3`，Windows 用 `python` 或 `py`。
- **联网构建一次，之后离线。** 本仓库只发*生成器*，不发 Apple 的 HIG 原文。首次构建与
  *「联网获取最新规范」*会从 `developer.apple.com` 拉取；其余全部离线运行。

## 首次设置：构建基线
规则语料未随仓库提交（它派生自 Apple 的 HIG——见[来源与署名](#来源与署名)）。在你的本地
副本里构建一次（在 skill 目录下，需联网，约 15–20 分钟）：
```bash
cd .claude/skills/hig-review        # 或安装后插件的 skills/hig-review/
python3 scripts/build_rules.py
```
这会写出 `rules/pages/`、`rules/index.json`、`rules/manifest.json` 和 `VERSION`。
之后审查全程离线。若你只用「联网获取最新规范」，可跳过这一步。

通常你无需手动运行它：
- **作为插件安装时**，一个 `SessionStart` 钩子会检测到基线缺失，并主动提示你运行
  `/hig-review:baseline-init`（基线建好后自动静默）。只想用联网规范？建一个空文件
  `skills/hig-review/rules/.hig-skip-setup-notice` 即可关闭提示。
- **作为 skill 运行 / 审查途中**，助手在发现 `rules/` 为空时会主动提议构建（首次同步提示，约 15–20 分钟）。

## `.claude/skills/hig-review/` 里有什么
```
├── SKILL.md             入口 / 工作流
├── agents/openai.yaml   可选的 Codex/Agent-Skills 展示元数据
├── references/          按需加载的指引：
│   ├── workflow.md, platforms.md, input-types.md,
│   ├── ui-image-review.md, ux-doc-review.md, figma-review.md,
│   └── general-review-mode.md, output-format.md
├── rules/               HIG 基线 —— 由 build_rules.py 本地构建，不随仓库提交
│   ├── index.json       （生成）rule set -> {title, url, platforms, file, category}
│   ├── manifest.json    （生成）基线版本 + 各页内容哈希
│   └── pages/<slug>.md  （生成）每个 HIG 页一个文件；稳定 id（HIG-<SLUG>-NNN）
├── scripts/
│   ├── hig_lib.py, build_rules.py, hig_fetch.py,
│   └── detect_inputs.py, visual_checks.py
└── VERSION              基线版本（按日期）
```

## 维护基线
在 `.claude/skills/hig-review/` 目录内运行：
```bash
python3 scripts/build_rules.py            # 构建 / 重新生成整个基线
python3 scripts/build_rules.py --upgrade  # 重新抓取、diff，报告 +新增/~变更/-删除
python3 scripts/build_rules.py --reindex  # 仅从文件重建 index/manifest（不联网）
python3 scripts/build_rules.py --limit 10 # 冒烟测试（不触碰 canonical 基线）
```
基线通过 `scripts/hig_lib.py` 爬取 Apple 的 DocC JSON 端点
（`…/tutorials/data/design/human-interface-guidelines/{path}.json`）构建。

### 联网抓取 & 图像辅助工具
```bash
python3 scripts/hig_fetch.py buttons              # 某一页的最新指南
python3 scripts/visual_checks.py dims shot.png --platform macos --scale 2
python3 scripts/visual_checks.py sample shot.png 0.3 0.4 0.5 0.4 --norm --contrast
python3 scripts/visual_checks.py contrast "#767676" "#FFFFFF"
```

## 可选的 MCP 增强
所有 MCP 都是可选的——不接任何 MCP，skill 也能工作。
- **Figma**：从粘贴的链接审查设计（接入 Figma MCP —— Claude Code 里 `/mcp`）。
- **Pencil**：通过 Pencil MCP 审查 `.pen` 设计文件。

## 来源与署名
本仓库只发**生成器**（`scripts/`），**不**包含 Apple 的 HIG 原文。`rules/` 下的规则语料
由 `build_rules.py` 在**你的机器上**从 Apple 的**人机界面指南**（developer.apple.com）抓取。
Apple HIG 内容版权归 Apple Inc. 所有；本项目与 Apple 无隶属或背书关系。本地构建的 `rules/`
仅供你自己使用——请勿再分发抽取出的文本。

## 许可
本仓库的工具代码采用 [MIT](LICENSE) 许可。Apple HIG 内容版权归 Apple Inc. 所有，**未**
包含在本仓库中——见[来源与署名](#来源与署名)。

## 路线图
- Pencil `.pen` 设计源审查；面向 CI 的可选 JSON 报告附件。
