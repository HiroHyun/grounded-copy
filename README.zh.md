<p align="center">
  <img src="assets/banner.png" alt="Grounded Copy：帮助 AI 清楚直接地表达。" width="960">
</p>

<p align="center">
  <strong>给 AI 智能体用的输出规则，附带文案检查脚本。</strong>
</p>

<p align="center">
  <a href="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml"><img src="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml/badge.svg" alt="Self-test status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--only-2ea44f.svg" alt="AGPL-3.0-only License"></a>
  <a href="https://www.skills.sh/hirohyun/grounded-copy"><img src="https://www.skills.sh/b/hirohyun/grounded-copy" alt="Skills CLI installs"></a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#try-it">试着用一次</a> ·
  <a href="#install">安装</a> ·
  <a href="#choose-a-writing-mode">选择写作模式</a> ·
  <a href="#before-and-after">改写示例</a> ·
  <a href="#more-help">更多说明</a>
</p>

# grounded-copy

`grounded-copy` 让智能体直接陈述事实、把话说到点上，聊天回复和它写的文档都适用。产品页面和营销文案另有一个更严格的模式。

<a id="try-it"></a>
## 试着用一次

Claude Code 和 Codex 插件会在每个会话开始时加载 `chat` 规则，无需你额外下指令。开启会话，直接提问即可。Codex 首次提示时，请批准插件的钩子。

只安装技能时，请在请求中点名，例如“用 grounded-copy 回答”。

写产品页面或营销文案时，先切换到 `copy` 模式。

<a id="install"></a>
## 安装

安装脚本需要 Python 3，以及带有 `npx` 的 Node.js。它会为找到的 Claude Code 和 Codex 安装插件，并通过 Skills CLI 为其他智能体安装技能。

**macOS、Linux、WSL 或 Git Bash：**

```bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

**Windows PowerShell：**

```powershell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

只为一个智能体安装：

| 安装到哪里 | 命令 |
|---|---|
| Claude Code | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Skills CLI 支持的智能体 | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

插件会在每次对话中应用规则，检查智能体保存的文件，并保存你的写作模式。单独安装的技能只在智能体判断相关时加载。

[安装说明](skills/grounded-copy/references/setup.md)中有安装检查、更新命令、Windows 使用说明和卸载方法。

<a id="choose-a-writing-mode"></a>
## 选择写作模式

选择会保存下来，重启后仍然有效。

| 模式 | 适用场景 |
|---|---|
| `chat`（默认） | 日常交流和普通文档处理。 |
| `copy` | 产品页面、营销文案等。 |
| `off` | 需要保留原文表达，或采用其他写作风格的任务。 |

**Claude Code：**

```text
/grounded-copy:grounded chat
/grounded-copy:grounded copy
/grounded-copy:grounded off
```

输入 `/grounded-copy:grounded` 查看当前模式。

**Codex：**

```text
$grounded-profile chat
$grounded-profile copy
$grounded-profile off
$grounded-profile status
```

> [!IMPORTANT]
> **需要忠实翻译原文时，先切换到 `off`。** 否则，智能体可能为了遵守写作规则，删掉原文中有意义的对比。

<a id="before-and-after"></a>
## 改写示例

| 草稿 | 使用 grounded-copy 后 |
|---|---|
| “文件不是丢了，而是空的。” | “文件是空的。” |
| “这盆花不是死了，是在休眠。” | “这盆花在休眠。” |
| “先淘米，而不是直接下锅。” | “先淘米。” |
| “它不仅仅是一个任务管理工具。” | “它能把任务关联到拉取请求，每天早上把摘要发到 Slack。” |
| “告别手工整理。” | “脚本每天早上自动生成摘要。” |

[表达示例](skills/grounded-copy/references/patterns.md)中有更多改写方法。

<a id="more-help"></a>
## 更多说明

- [安装说明](skills/grounded-copy/references/setup.md)：安装检查、检查文件和问题排查。
- [写作规则](skills/grounded-copy/SKILL.md)：智能体读取的指令。
- [表达示例](skills/grounded-copy/references/patterns.md)：需要检查的措辞和改写方法。
- [贡献指南](CONTRIBUTING.md)：如何提交修改。
- [许可证](LICENSE)：AGPL-3.0-only，版权声明见 [NOTICE](NOTICE)。
