# 0.7.0

## English

- The `chat` rules open with one operation: state the fact, and cut the half of a sentence that sets it against something nobody raised. Three cases say what happens to a denial. Warnings, limits, corrections, and requested comparisons stay. The product lead, the developer terms, and four marketing forms now load under `copy` alone.
- The checker takes `--profile chat|copy`. `chat` runs 30 of the 71 rules: the reversal, comparison, and dash rules and the locale rules. It leaves out 41 rules that fit marketing copy: openers, slogans, hype words, and vague sources. `copy`, or no option, runs every rule, so existing commands and CI jobs behave as before.
- The finding line changed. A finding prints as the file, the line, the matched text, and the rule name in brackets, and each group of findings ends with one sentence that says what to cut. A script that parses the old line needs an update.
- New in the gate: a denial whose second half opens with a plain verb, under `not-x-its-y`; `do-verb-repeat`, for a denial of "need", "want", or "mean" followed by the same verb; and `fragment-reversal`, which runs under `copy`.
- `opener-stop` reports the paired slogan only, so a plain instruction that opens with "Stop" passes.
- A wrapped line that continues a condition passes. An opener behind a checked box reports. `ja-not-just` needs kana on the line, so the Chinese phrase for "of the revolution" passes.
- An optional hook, `hooks/grounded_gate.py`, checks each file as the agent saves it, for Claude Code and Codex. It follows the saved profile, and a sentence you typed in the session passes. The setup guide has the entry to add and the limits.
- `install.py --always-on` writes a marked block into the user-level instruction file for a host that gets the skill and no plugin, so every session applies the skill. `--uninstall` removes it.
- Session rules measure 4,032 bytes for `chat` and 6,292 for `copy`, and the turn reminder 238. Both READMEs list 62 English rules and describe `chat` and `copy` for ordinary users.

## 简体中文

- `chat` 规则开头只讲一个操作：陈述事实，删掉把事实与无人提起的事物对立起来的半句。三种情况说明否定句怎么处理。警告、限制、纠正和用户要求的比较保留原样。产品导语、开发者术语和四种营销句式现在只在 `copy` 模式下加载。
- 检查脚本新增 `--profile chat|copy` 选项。`chat` 运行 71 条规则中的 30 条：反转、对比和破折号规则，以及各语言规则。它略去 41 条适用于营销文案的规则：开场句式、口号、夸张词和来源含糊的说法。`copy` 或省略选项时运行全部规则，现有命令和 CI 任务的行为保持原样。
- 报告格式有变化。每条结果依次列出文件、行号、命中的文字和方括号里的规则名称，每组结果的末尾有一句话，说明该删掉哪一部分。解析旧格式的脚本需要更新。
- 新增检查：否定之后接普通动词的句式归入 `not-x-its-y`；`do-verb-repeat` 报出否定 “need”“want”“mean” 后又重复同一动词的句式；`fragment-reversal` 在 `copy` 模式下运行。
- `opener-stop` 现在只报成对的口号句，以 “Stop” 开头的普通指令可以通过。
- 承接上一行条件从句的折行可以通过。已勾选的复选框后面的开场句式会被报出。`ja-not-just` 要求同一行出现假名，含“革命”一词的中文短语可以通过。
- 新增可选钩子 `hooks/grounded_gate.py`，在智能体每次保存文件时检查，支持 Claude Code 和 Codex。它按已保存的模式运行，你在会话中输入过的句子可以通过。安装说明列出了需要添加的配置和限制。
- `install.py --always-on` 会为只安装技能、未安装插件的宿主，在用户级说明文件中写入一段带标记的说明，让每个会话都应用该技能。`--uninstall` 会删除这段说明。
- 会话规则的大小为 `chat` 4,032 字节、`copy` 6,292 字节，每轮提醒 238 字节。两份 README 的英语规则数更新为 62 条，并改用面向普通用户的说法介绍 `chat` 和 `copy`。

# 0.6.2

## English

- The checker reports a denial followed by "just", "only", "merely", or "simply" when other words sit between them. It needed the two words side by side.
- Two new rules. `no-x-just-y` reports a slogan that opens with "no" and continues with "just". `not-x-its-y` reports a denial with a form of "be", then a pronoun and the claim, for any subject.
- Eleven rules take near forms of what they already matched: a spaced hyphen where a dash was needed, any contracted auxiliary before "just", the past tense, and a repeated preposition after "but".
- The checker reads through Markdown emphasis, inline HTML tags, and look-alike quotes, dashes, and zero-width characters.
- A phrase that wraps onto the next line of a paragraph reports at the line where it starts.
- The Chinese rules take Traditional forms and two more sentence patterns.
- Both READMEs list 60 English rules.

## 简体中文

- 否定词与“just”“only”“merely”“simply”之间隔着其他词时，检查脚本现在也会报出，此前要求两个词紧邻。
- 新增两条规则：`no-x-just-y` 报出以“no”开头、以“just”承接的口号句；`not-x-its-y` 报出任意主语的“先否定、后断言”句式。
- 加宽 11 条已有规则：两侧带空格的连字符按破折号处理，“just”之前可接任意缩写助动词，并支持过去时和“but”之后重复的介词。
- 检查脚本会略过 Markdown 强调标记和行内 HTML 标签，并把形似的引号、破折号和零宽字符按标准字符处理。
- 段落内换行的短语同样会被检出，报告的行号是短语开始的那一行。
- 中文规则支持繁体写法，并新增两种句式。
- 两份 README 的英语规则数更新为 60 条。

# 0.6.1

## English

- Fixes the Codex plugin hooks on Windows. Each hook now starts the launcher through `cmd /d /c`, which runs under PowerShell and cmd.exe.
- Claude Code hooks run on Windows with or without Git Bash. Each hook starts a launcher that Git Bash and PowerShell both run.
- `/grounded-copy:grounded` lists PowerShell commands for Windows without Git Bash.
- The READMEs drop the before-and-after table; the pattern guide keeps the English versions of those examples.

## 简体中文

- 修复 Codex 插件在 Windows 上的钩子。钩子现在通过 `cmd /d /c` 运行启动器，在 PowerShell 和 cmd.exe 下均可运行。
- Claude Code 钩子在 Windows 上无论是否安装 Git Bash 都能运行。每个钩子启动一个 Git Bash 和 PowerShell 都能运行的启动器。
- `/grounded-copy:grounded` 为未安装 Git Bash 的 Windows 提供 PowerShell 命令。
- README 删除改写示例对照表，表达示例指南保留这些示例的英文版。

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
