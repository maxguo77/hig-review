# Report format (user-facing)

The deliverable is a review report a normal user can read. Write it in plain
language — no internal jargon. The title is always **「HIG 滚动基线审查报告」**.

## Severity levels (bilingual labels)
- **严重 (Blocker)** — breaks a core requirement or an accessibility/usability
  floor (e.g. tap target too small, a custom button with no pressed state, text
  below the contrast minimum). Shouldn't ship.
- **重要 (Major)** — a clear deviation that noticeably hurts the experience.
- **建议 (Minor)** — a smaller deviation; fix when convenient.
- **提示 (Info)** — advisory, or a general-principle note for web · 数据大屏
  reviewed in general review mode.

For web · 数据大屏 (general review mode): issues covered by a real web standard
(WCAG — contrast, target size, keyboard, focus, semantics) keep their real
severity and cite WCAG. General design-principle notes are advisory → 提示
(Info). See `references/general-review-mode.md`.

## Report header (start every report with this)
```
# HIG 滚动基线审查报告
产品 / Product: <iPhone app | iPad app | Mac app | … | 网页·数据大屏>
审查对象 / Scope: <files / image / spec reviewed>
规范基线 / Baseline: 内置规范 <VERSION>   |   依据来源: 本地内置规范 | 联网最新规范
```

## Per-finding format
```
【<严重 (Blocker) | 重要 (Major) | 建议 (Minor) | 提示 (Info)>】<位置> — <一句话标题>
  问题 / Problem: <what's wrong, in plain terms>
  影响 / Impact: <why it matters to the user>
  建议 / Fix: <a concrete change>
  依据 / Based on: <guideline name> (<source link>)
```
- `依据` shows the **guideline name + link** (e.g. "Apple 人机界面指南 — 按钮
  (Buttons) https://developer.apple.com/design/human-interface-guidelines/buttons").
  You may add the internal id in parentheses for traceability — never as the
  headline.
- For web · 数据大屏 web-standard findings, `依据` is the standard, e.g.
  "WCAG 1.4.3 (AA) 对比度 4.5:1"; you may add "对齐 Apple 设计原则:Color".

`<位置>` precision rules:
- **Code**: `path/to/File.swift:42` (line, or range `:42-58`).
- **UI image**: `mockup.png` + a described region (e.g. "底部标签栏第 3 项" or
  normalized coords "≈ x:0.8, y:0.95").
- **UX doc**: `spec.md:line` + a quoted sentence (PDF: `page N`).
- **Design file**: `.pen` node name / Figma layer path.
- **Config**: `Info.plist → UISupportedInterfaceOrientations`.

## Example finding
```
【严重 (Blocker)】Sources/Views/CartButton.swift:33 — 自定义按钮没有按下反馈
  问题 / Problem: 这个按钮用 .onTapGesture 实现,点击时没有任何按下/高亮的视觉变化。
  影响 / Impact: 用户会以为没点到、反复点击,觉得界面没反应。
  建议 / Fix: 改用带按下态的 ButtonStyle,或用 configuration.isPressed 驱动透明度/缩放。
  依据 / Based on: Apple 人机界面指南 — 按钮 (Buttons)
                  https://developer.apple.com/design/human-interface-guidelines/buttons
```

## Keeping it honest
- Only cite a guideline that exists in the baseline (or that you actually
  fetched). Don't invent guidelines.
- If the closest guideline is only a loose fit, say "参考(最相近)" in `依据`,
  or lower the finding to 提示 (Info). Never stretch a rule to fill the field.
- For contrast, say where the numbers came from: real pixels (`sample`), a stated
  design color, or an estimate (estimates → 提示 (Info), label "估值").
- Don't assert a size pass/fail without a known scale — mark it "待核实" and ask
  for the device/viewport.
- **Don't give a confirmed 重要/严重 to something you can't actually see.** If a
  problem rests on an *omission* you can't verify from the artifact — e.g. a menu
  bar that simply isn't drawn in a component board, behavior you can't observe —
  mark it **需核实** and state the condition (e.g. "若确实缺失则 Major"). Reserve
  confirmed Major/Blocker for violations visible in what you were given.
- **Live mode (联网最新规范): only cite a page you actually fetched this run.** If
  you reference a guideline you didn't `hig_fetch.py`, either fetch it or label
  `依据` as "本地内置基线" — don't imply live text you didn't pull.

## Summary table (always include)
| 严重程度 / Severity | 数量 / Count |
|---------------------|--------------|
| 严重 (Blocker) | n |
| 重要 (Major)   | n |
| 建议 (Minor)   | n |
| 提示 (Info)    | n |

| 类别 / Category | 已审 / Reviewed | 通过 / Pass | 发现 / Findings |
|-----------------|-----------------|-------------|------------------|
| 代码 Code           | … | … | … |
| UI 图 Images        | … | … | … |
| UX / 文档 Docs       | … | … | … |
| 设计文件 Design       | … | … | … |
| 配置 Config          | … | … | … |

End with: the baseline version (`VERSION`), the rule source used (本地内置 / 联网
最新), and the product/platform(s) reviewed.

## Optional JSON sidecar (for CI)
When asked, also emit:
```json
{
  "tool": "hig-review",
  "report_title": "HIG 滚动基线审查报告",
  "baseline_version": "<VERSION>",
  "rule_source": "bundled|live",
  "platforms": ["iPhone"],
  "summary": {"blocker": 0, "major": 0, "minor": 0, "info": 0},
  "findings": [
    {
      "severity": "blocker",
      "location": "Sources/Views/CartButton.swift:33",
      "title": "自定义按钮没有按下反馈",
      "problem": "...",
      "impact": "...",
      "fix": "...",
      "based_on": "Apple 人机界面指南 — 按钮 (Buttons)",
      "source_url": "https://developer.apple.com/design/human-interface-guidelines/buttons",
      "guideline_id": "HIG-BUTTONS-002"
    }
  ]
}
```
