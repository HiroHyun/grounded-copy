<p align="center">
  <img src="assets/banner.png" alt="grounded-copy：给 AI 智能体用的输出规则，附带文案检查脚本。" width="960">
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
  <a href="#check-a-file">检查文件</a> ·
  <a href="#before-and-after">改写示例</a> ·
  <a href="#what-to-expect">使用时需要了解的事</a> ·
  <a href="#more-help">更多说明</a>
</p>

# grounded-copy

你与智能体（Claude Code、Codex、Cursor 等）对话时，可能会发现它频繁使用生硬的转折和意义不明的破折号，让短短一段回复变得绕口晦涩。`grounded-copy`会在会话开始和每轮对话时提醒智能体使用清楚、直接的表达。

你让智能体写文案的时候，TA用词总是夸张，动不动就来一句“核弹级发布”，宽泛又空洞。`grounded-copy`就会提醒智能体写清楚实际功能、操作步骤和具体事实。草稿保存成文件后，你也可以用 Python 脚本检查措辞。


<a id="try-it"></a>
## 试着用一次

安装技能后，可以这样对智能体说：

> 帮我写一份日程应用 2.1 版的更新说明。这个版本新增了 Google 日历同步，把导出耗时从 40 秒缩短到 4 秒，并修复了重复发送邀请的问题。 请用 grounded-copy，完成后运行文案检查。

选择安装使用 Claude/Codex 插件的话，开启新对话时只要说：

> 将grounded-copy切换到chat模式与我对话。

智能体会按规则与你对话，避免死板无谓的句式。

<a id="install"></a>
## 安装

安装脚本需要 Python 3，以及带有 `npx` 的 Node.js。它会查找 Claude Code 和 Codex 的命令行程序，为找到的程序安装插件。它也会调用 Skills CLI，为支持的智能体安装技能。

**macOS、Linux、WSL 或 Git Bash：**

```bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

**Windows PowerShell：**

```powershell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

也可以按需要单独安装：

| 安装到哪里 | 命令 |
|---|---|
| Claude Code | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Skills CLI 支持的智能体 | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

技能包含写作规则、示例和检查脚本。Claude Code 和 Codex 插件还会在会话开始时加载规则，并在每次发送提示时加入一条提醒。插件支持保存写作模式。

[安装说明](skills/grounded-copy/references/setup.md)中有安装检查、Windows 使用说明和卸载命令。

<details>
<summary><strong>更多安装方式</strong> · 点击展开</summary>

<br>

在本仓库的克隆目录中，安装脚本支持这些参数：

```bash
sh install.sh --dry-run
python3 install.py --skills-only
python3 install.py --uninstall
```

| 能得到什么 | Skills CLI | Claude Code 与 Codex 插件 |
|---|:---:|:---:|
| 九种语言的写作规则、示例和检查脚本 | 有 | 有 |
| 会话开始时加载规则，压缩上下文后再次加载（`SessionStart`） |  | 有 |
| 每次发送提示时加入一条提醒（`UserPromptSubmit`） |  | 有 |
| 写作模式在会话之间保存 |  | 有 |
| 一条切换模式的命令 |  | 有 |

在同一台机器上用两种方式都安装时，Claude Code 可能把 `grounded-copy@skills-dir` 显示为 `Not loaded`。这种情况下由插件提供技能和钩子。

</details>

<a id="choose-a-writing-mode"></a>
## 选择写作模式

插件把写作模式称为 *profile*。选择会保存下来，重启后仍然有效。

| 模式 | 适用场景 |
|---|---|
| `chat`（默认） | 日常回复、项目文档和技术说明。 |
| `copy` | 产品页面和营销文案，增加对宣传用语的要求。 |
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
> **需要忠实翻译原文时，先切换到 `off`。** 否则，智能体可能为了遵守写作规则，删掉原文中有意义的对比。你的明确要求优先于技能规则。

<details>
<summary><strong>每种模式的开销</strong> · 点击展开</summary>

<br>

| 模式 | 会话开始时增加的字节 | 每轮提醒 |
|---|---:|---|
| `chat`（默认） | 3,693 | 一行，写明 `chat` |
| `copy` | 5,118 | 一行，写明 `copy` |
| `off` | 0 | 无 |

以上是规则正文的字节数。钩子输出还有 106 字节的头部和切换提示，每轮提醒为 218 字节。

选择保存在 `<config-dir>/grounded-copy/profile`。

> [!TIP]
> **有些日常表达也会命中规则。** `without-gerund` 规则会报出 `without` 后面的所有 `-ing` 名词。如果任务需要保留某种被规则拦截的表达，可以切换到 `off`。

</details>

<a id="check-a-file"></a>
## 检查文件

在本仓库的克隆目录中运行：

```bash
python3 skills/grounded-copy/scripts/copy_lint.py draft.md
```

如果你的 Python 3 命令是 `python`，请替换命令开头。一次可以传入多个文件路径。脚本只用到 Python 标准库。

检查结果会列出行号、规则名称和命中的文字。根据原始资料修改句子，再检查一次。

| 退出码 | 含义 |
|---|---|
| `0` | 未发现命中规则的文字。 |
| `1` | 有需要检查的措辞。 |
| `2` | 命令参数有误，或文件读取失败。 |

通过 Codex 插件安装后，也可以使用缓存目录里的脚本：

```bash
python3 ~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/<version>/skills/grounded-copy/scripts/copy_lint.py draft.md
```

把 `<version>` 换成 `codex plugin list` 显示的版本号。

<a id="before-and-after"></a>
## 改写示例

以下内容是虚构示例，仅供参考。

| 草稿 | 改写 |
|---|---|
| “它不仅仅是一个任务管理工具。” | “它能把任务关联到拉取请求，每天早上把摘要发到 Slack。” |
| “它不是供应商，而是合作伙伴。” | “你的客户经理每季度都会参加一次规划会。” |
| “Acme 覆盖每个渠道 —— 邮件、在线客服、电话、帮助中心 —— 只用一个队列。” | “Acme 把邮件、在线客服、电话和帮助中心的请求放进同一个队列。” |

[表达示例](skills/grounded-copy/references/patterns.md)中有更多改写方法。

<details>
<summary><strong>四条草稿及各自命中的规则</strong></summary>

<br>

规则栏写出检查脚本为该草稿打印的规则名称。

| 草稿 | 改写 | 规则 |
|---|---|---|
| “它不仅仅是一个任务管理工具。” | “它能把任务关联到拉取请求，每天早上把摘要发到 Slack。” | `zh-not-just` |
| “告别手工整理。” | “脚本每天早上自动生成摘要。” | `zh-not-just` |
| “它不是供应商，而是合作伙伴。” | “你的客户经理每季度都会参加一次规划会。” | `zh-not-x-but-y` |
| “Acme 覆盖每个渠道 —— 邮件、在线客服、电话、帮助中心 —— 只用一个队列。” | “Acme 把邮件、在线客服、电话和帮助中心的请求放进同一个队列。” | `dash-pair-list` |

</details>

<a id="what-to-expect"></a>
## 使用时需要了解的事

插件会向智能体提供写作指令，不会逐条扫描或拦截聊天回复。需要可重复的检查时，请把文字保存为文件，再运行脚本。

检查通过表示文字没有命中脚本中的规则。脚本不能核实事实，也不能保证文字自然。有些日常表达也会命中规则，修改前请确认句意。如果任务需要保留某种被规则拦截的表达，可以切换到 `off`。

检查脚本覆盖英语、中文、日语、韩语、俄语、西班牙语、阿拉伯语、法语和德语。英语规则最详细。中文、日语和韩语会检查部分句式，其他语言按短语表匹配。大部分检查逐行进行，分成两行的短语可能漏检。夹在成对破折号中的列表会按段落检查，换行后也能识别。

<details>
<summary><strong>多语言现状</strong> · 点击展开</summary>

<br>

| 语言 | 检查脚本匹配的内容 |
|---|---|
| 英语 | 58 条规则 |
| 中文、日语、韩语 | 部分句式，以及一份短语表 |
| 俄语、西班牙语、阿拉伯语、法语、德语 | 各有一份 6 至 18 条的短语表 |

有些日语和韩语的日常表达也会命中，`ja-not-just` 和 `ko-not-just` 会报出这类用法。

</details>

<a id="more-help"></a>
## 更多说明

- [安装说明](skills/grounded-copy/references/setup.md)：模式切换、问题排查和项目检查。
- [写作规则](skills/grounded-copy/SKILL.md)：智能体读取的指令。
- [表达示例](skills/grounded-copy/references/patterns.md)：需要检查的措辞和改写方法。
- [贡献指南](CONTRIBUTING.md)：如何提交修改。
- [许可证](LICENSE)：AGPL-3.0-only 版权声明见 [NOTICE](NOTICE)。
