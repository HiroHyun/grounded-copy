<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/53e20949-13a7-4092-8008-5f68c1390b2a">
    <img src="https://github.com/user-attachments/assets/3350709a-b668-4416-911f-4a35cac9c23b" alt="Grounded Copy。“文件不是丢了，而是空的。”删去“不是丢了，而”。帮助 AI 清楚直接地表达。" width="960">
  </picture>
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
  <a href="https://hirohyun.github.io/groundedcopy/zh/">产品网站</a> ·
  <a href="https://github.com/HiroHyun/groundedcopy">网站源码</a>
</p>

<p align="center">
  <a href="#try-it">试着用一次</a> ·
  <a href="#install">安装</a> ·
  <a href="#choose-a-writing-mode">选择写作模式</a> ·
  <a href="#how-it-works">工作原理</a> ·
  <a href="#before-and-after">改写示例</a> ·
  <a href="#more-help">更多说明</a>
</p>

# grounded-copy

`grounded-copy` 让智能体直接陈述事实、把话说到点上，聊天回复和它写的文档都适用。产品页面和营销文案另有一个更严格的模式。

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/b05fee0b-75df-4fa4-bad0-1ea2c710267c">
    <img src="https://github.com/user-attachments/assets/a60ea723-4143-4ec4-a8e3-1fcf6261d8ae" alt="Grounded Copy 帮助 AI 清楚直接地表达：有插件时 14% 的回答含有 Grounded Copy 针对的句式（例如 “rather than”），没有插件时为 64%，人写的回答在同一批问题上为 20%，画成横穿两条柱的一条线；每个回答的英文单词和 token 基本相同，有插件时 276.3 个单词、23,084 个 token，没有插件时 273.8 个单词、22,871 个 token；问题是 300 个来自 Stack Exchange 的日常问题，由 gpt-6.1-sol 在 Codex 中回答，人写的回答取自原帖下的回复。" width="880">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/4025f222-e6cc-47ab-985a-b0eaa5a1ee68">
    <img src="https://github.com/user-attachments/assets/65869bfd-c709-40cd-b08b-d24d7a5a8411" alt="一遍还是两遍，基于其中 100 个问题：使用 Grounded Copy，一个回答比先写再用 humanizer 改写少用 36% 的 token、少用 40% 的时间；每一行的最低值有标记，token、秒数和单词这三行里，其余数值标出比最低多多少；没有插件时，智能体用一次请求写出回答，每个回答 22,441 个 token（最低）、47.3 秒（比最低多 10%）、280.1 个英文单词（最低），68% 的回答含有 Grounded Copy 针对的句式，71% 含有长破折号（humanizer 针对的习惯）；使用 Grounded Copy 时，规则在智能体动笔前载入，一次请求，23,501 个 token（比最低多 5%）、42.9 秒（最低）、283.8 个单词（比最低多 1%），比例为 18%（最低） 和 37%；先写再用开源技能 humanizer 改写需要两次请求，36,957 个 token（比最低多 65%）、71.7 秒（比最低多 67%）、287.0 个单词（比最低多 2%），比例为 45% 和 1%（最低），这一列计入两遍。" width="880">
  </picture>
</p>

<a id="try-it"></a>
## 试着用一次

Claude Code 和 Codex 插件会在每个会话开始时加载 `chat` 规则，无需你额外下指令。开启会话，直接提问即可。Codex 首次提示时，请批准插件的钩子。

只安装技能时，请在请求中点名，例如“用 grounded-copy 回答”。

在不支持插件的聊天应用里，把规则粘贴到它的自定义指令中即可，[安装说明](skills/grounded-copy/references/setup.md#chat-apps)写明了要复制哪一部分。

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

<details>
<summary><strong>只为一个智能体安装</strong></summary>

<br>

| 安装到哪里 | 命令 |
|---|---|
| Claude Code | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Skills CLI 支持的智能体 | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

</details>

> [!TIP]
> 插件会在每次对话中应用规则，检查智能体保存的文件，并保存你的写作模式。单独安装的技能只在智能体判断相关时加载。
>
> [安装说明](skills/grounded-copy/references/setup.md)中有安装检查、更新命令、Windows 使用说明和卸载方法。

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

<a id="how-it-works"></a>
## 工作原理

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/8158ddb1-c8f4-4479-9e8f-29104f8f4111">
    <img src="https://github.com/user-attachments/assets/5211fe96-d3a7-4541-88ec-d08db3302152" alt="一条规则：陈述事实；遇到否定说法，智能体逐一判断是删掉、说出背后的事实还是保留，以三份草稿和智能体写出的句子为例：事实本身已经回答了，就删掉前半句，“文件不是丢了，而是空的。” 变成 “文件是空的。”（标签：删掉）；背后有一个事实，就说出那个事实，“这项服务不是免费帮忙，是每单收取2元的生意。” 变成 “这项服务每单收取2元服务费。”（标签：说出事实）；警告本身就是事实，就保留，“不要把漂白剂和氨水混在一起。” 原样不变（标签：保留）。" width="880">
  </picture>
</p>

- 会话开始时，插件就加载规则，智能体的初稿已经遵守这些规则。
- 智能体保存文件时，插件检查这次新写的内容，智能体改写被标出的句子。
- 你自己输入的句子保持原样。

<a id="before-and-after"></a>
## 改写示例

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/ba15160f-8e9e-40d6-8244-186d430d89d1">
    <img src="https://github.com/user-attachments/assets/98f30873-d0d0-4cbb-9a16-d0072ed4456f" alt="测试中的一个问题 “When do children become aware of time?”（Parenting Stack Exchange 用户 2221 提问，https://parenting.stackexchange.com/q/20350，CC BY-SA 3.0）：没有插件时，227 个单词的回答中有一句 “These are broad ranges, not deadlines.”，检查脚本标出 “not deadlines”；使用 Grounded Copy 时，209 个单词的回答写道 “These are broad ranges. Research finds that performance depends on the language a child speaks and how the question is asked.”；节选前后的原文以浅色显示；300 个问题中有 151 个是这种情况：只有不用插件的回答含有这类句式，反过来的情况有 2 个。" width="880">
  </picture>
</p>

[表达示例](skills/grounded-copy/references/patterns.md)中有更多改写方法。

<a id="more-help"></a>
## 更多说明

- [安装说明](skills/grounded-copy/references/setup.md)：安装检查、检查文件和问题排查。
- [写作规则](skills/grounded-copy/SKILL.md)：智能体读取的指令。
- [表达示例](skills/grounded-copy/references/patterns.md)：需要检查的措辞和改写方法。
- [贡献指南](CONTRIBUTING.md)：如何提交修改。
- [许可证](LICENSE)：AGPL-3.0-only，版权声明见 [NOTICE](NOTICE)。
