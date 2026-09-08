# grounded-copy

[English](README.md) · [简体中文](README.zh.md)

给 AI 助手用的写作规则，附带文案检查脚本。

你让 AI 写一份 README，它写了很多宽泛的介绍，你还得补上用户能拿这个工具做什么。`grounded-copy` 会提醒助手写清楚实际功能、操作步骤和具体事实。草稿保存成文件后，你也可以用 Python 脚本检查措辞。

写产品介绍、项目文档或日常回复时都可以用。把需要保留的事实交给助手，再告诉它读者是谁。

## 试着用一次

安装后，可以这样对助手说：

> 用 grounded-copy 改写这份 README，写给第一次安装这个工具的人。保留命令和技术事实，讲清楚安装后能做什么。完成后运行文案检查。

写产品介绍时，先给出具体信息：

> 帮我写一小段任务管理工具的介绍。它能把任务关联到拉取请求，每天早上把摘要发到 Slack。请用 grounded-copy。

助手会按规则起草并检查文字。检查脚本会列出命中规则的词句。最后还需要你确认内容是否准确、读起来是否顺畅。

## 安装

安装脚本需要 Python 3，以及带有 `npx` 的 Node.js。它会查找 Claude Code 和 Codex 的命令行程序，为找到的程序安装插件。它也会调用 Skills CLI，为支持的助手安装技能。

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
| Skills CLI 支持的助手 | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

技能包含写作规则、示例和检查脚本。Claude Code 和 Codex 插件还会在会话开始时加载规则，并在每次发送提示时加入一条提醒。插件支持保存写作模式。

[安装说明](skills/grounded-copy/references/setup.md)中有安装检查、Windows 使用说明和卸载命令。

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

需要忠实翻译原文时，先切换到 `off`。否则，助手可能为了遵守写作规则，删掉原文中有意义的对比。你的明确要求优先于技能规则。

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

## 改写示例

以下内容是虚构示例。写自己的文案时，请使用经过核实的事实。左栏特意保留了会被检查脚本报出的表达。

| 草稿 | 改写 |
|---|---|
| “它不仅仅是一个任务管理工具。” | “它能把任务关联到拉取请求，每天早上把摘要发到 Slack。” |
| “它不是供应商，而是合作伙伴。” | “你的客户经理每季度都会参加一次规划会。” |
| “Acme 覆盖每个渠道 —— 邮件、在线客服、电话、帮助中心 —— 只用一个队列。” | “Acme 把邮件、在线客服、电话和帮助中心的请求放进同一个队列。” |

[表达示例](skills/grounded-copy/references/patterns.md)中有更多改写方法。

## 使用时需要了解的事

插件会向助手提供写作指令，不会逐条扫描或拦截聊天回复。需要可重复的检查时，请把文字保存为文件，再运行脚本。

检查通过表示文字没有命中脚本中的规则。脚本不能核实事实，也不能保证文字自然。有些日常表达也会命中规则，修改前请确认句意。如果任务需要保留某种被规则拦截的表达，可以切换到 `off`。

检查脚本覆盖英语、中文、日语、韩语、俄语、西班牙语、阿拉伯语、法语和德语。英语规则最详细。中文、日语和韩语会检查部分句式，其他语言按短语表匹配。大部分检查逐行进行，分成两行的短语可能漏检。夹在成对破折号中的列表会按段落检查，换行后也能识别。

## 更多说明

- [安装说明](skills/grounded-copy/references/setup.md)：模式切换、问题排查和项目检查。
- [写作规则](skills/grounded-copy/SKILL.md)：助手读取的指令。
- [表达示例](skills/grounded-copy/references/patterns.md)：需要检查的措辞和改写方法。
- [贡献指南](CONTRIBUTING.md)：如何提交修改。
- [MIT 许可证](LICENSE)。
