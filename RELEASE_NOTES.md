# 0.6.1

## English

- Fixes the Codex plugin hooks on Windows. Each hook now starts the launcher through `cmd /d /c`, which runs under PowerShell and cmd.exe.
- Corrects the Windows instructions for Claude Code without Git Bash. The setup guide and `/grounded-copy:grounded` give PowerShell commands that start the launcher.

## 简体中文

- 修复 Codex 插件在 Windows 上的钩子。钩子现在通过 `cmd /d /c` 运行启动器，在 PowerShell 和 cmd.exe 下均可运行。
- 更正未安装 Git Bash 时 Claude Code 的 Windows 说明。安装指南和 `/grounded-copy:grounded` 提供可运行启动器的 PowerShell 命令。

# 0.6.0

## English

- Revises the shared rules to reduce repeated enumeration in English and Chinese.
- Adds Chinese paragraph guidance to the plugins and standalone skill. Thanks to @moAxins for the feedback.
- Grounds Chinese rewrite examples in stated facts.

## 简体中文

- 调整共享写作规则，中英文均按读者需要取舍信息，减少反复列举。
- 同步更新 Claude Code/Codex 插件和技能，新增中文段落审读指导，覆盖冗余句式和密集列举（感谢 @moAxins 的反馈）等多种问题。仅安装技能也会获得相同的指导和参考信息。
- 为中文对比句改写示例补充已知情境，确保改写中的事实有据可依。

# 0.5.4

## English

- Includes the documentation and checker updates from 0.5.2 and 0.5.3.
- Rewrites the Chinese README introduction to pass the citation check.
- Restores the full AGPL license text and adds NOTICE.

## 简体中文

- 包含 0.5.2 和 0.5.3 的文档与检查脚本更新。
- 改写中文 README 开头，通过引用检查。
- 恢复完整 AGPL 许可证文本并添加 NOTICE。

# 0.5.3

## English

- Both READMEs restore the banner and navigation, with collapsible technical details.
- Examples show how to write app release notes. The setup guide and session instructions are shorter.
- The license is AGPL-3.0-only. Releases through 0.5.2 stay under the MIT license.

## 简体中文

- 中英文 README 恢复横幅和导航，技术细节收进可折叠区块。
- 示例说明如何撰写应用更新说明，并精简安装指南和会话指令。
- 许可证改为 AGPL-3.0-only。0.5.2 及更早的版本仍按 MIT 许可证发布。

# 0.5.2

## English

- The English and Chinese READMEs explain how to install the tool and check a draft.
- The setup guide and skill instructions use plain language and practical examples.
- The copy checker now finds lists between paired dashes across lines in a paragraph.
- Chat replies omit the check-result line. File tasks report the check result.

## 简体中文

- 中英文 README 说明了安装步骤和草稿检查方法。
- 安装说明和技能指令采用通俗表达，并提供实际用法示例。
- 文案检查脚本现在能识别段落中跨行的成对破折号列表。
- 日常聊天回复省去检查结果行。文件任务仍会报告检查结果。

# 0.5.1

## English

- Fixes installation through the Windows PowerShell command.
- The checker detects sentence openers in Markdown tables. CI checks recorded citations.
- Both READMEs explain profiles and show rewrite examples.

## 简体中文

- 修复 Windows PowerShell 安装命令。
- 检查脚本识别 Markdown 表格中的句首表达，CI 核对已记录的引用。
- 中英文 README 说明写作模式，并提供改写示例。

# 0.5.0

## English

- The installer adds the shared skill through Skills CLI and plugins for Claude Code and Codex.
- Adds a Chinese README and updates installation and profile guidance.
- Fixes installer exit codes, Python detection, and marketplace cleanup.

## 简体中文

- 安装程序通过 Skills CLI 安装共享技能，并为 Claude Code 和 Codex 安装插件。
- 新增中文 README，更新安装和写作模式说明。
- 修复安装退出码、Python 检测和插件市场清理。

# 0.4.0

## English

- Adds an installer with preview and removal options.
- Moves the skill to `skills/grounded-copy/` and the Codex package to `dist/codex/grounded-copy/`. Update scripted paths and reinstall the Codex plugin.
- Fixes skill metadata, UTF-8 output, and Codex plugin removal.

## 简体中文

- 新增安装程序，支持预览和卸载。
- 技能移至 `skills/grounded-copy/`，Codex 包移至 `dist/codex/grounded-copy/`。请更新脚本路径并重新安装 Codex 插件。
- 修复技能元数据、UTF-8 输出和 Codex 插件卸载。
