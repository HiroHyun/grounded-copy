<p align="center">
  <img src="assets/banner.png" alt="grounded-copy：每条声明都写出功能、数字或机制。" width="960">
</p>

<p align="center">
  <strong>适用于各类可读文本的文字风格检查器。</strong>
</p>

<p align="center">
  <a href="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml"><img src="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml/badge.svg" alt="Self-test status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f.svg" alt="MIT License"></a>
  <a href="https://www.skills.sh/hirohyun/grounded-copy"><img src="https://www.skills.sh/b/hirohyun/grounded-copy" alt="Skills CLI installs"></a>
</p>

<p align="center">
  <strong>其他语言：</strong>
  <a href="README.md">English</a> ·
  <a href="README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#install">安装</a> ·
  <a href="#pick-your-profile">配置</a> ·
  <a href="#what-it-does">功能</a> ·
  <a href="#before-and-after">改写示例</a> ·
  <a href="#nine-languages">九种语言</a> ·
  <a href="#documentation">文档</a>
</p>

`grounded-copy` 适用于聊天回复、文档、计划、报告、提交说明、拉取请求描述、代码注释和产品文案。它要求每条声明写出功能、数字或机制。Python 检查器会识别目录中的对比模式、夸张词和含糊归因。

<a id="install"></a>
## 安装

一条命令会在 CLI 可用时安装 Claude Code 和 Codex 插件，并通过 Skills CLI 为 17 个以上的代理安装便携技能。

```bash
# macOS · Linux · WSL · Git Bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

```powershell
# Windows · PowerShell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

启动器需要 Python 3 和 Node。每次执行前都会打印主机命令。在检出目录中运行 `sh install.sh --dry-run` 可查看计划，`python3 install.py --skills-only` 可安装便携路径，`python3 install.py --uninstall` 可移除已安装条目。

### 各主机命令

| 主机 | 命令 |
|---|---|
| 便携技能，17 个以上代理 | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |
| Claude Code 插件 | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex 插件 | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| 从检出目录运行检查器 | `python3 skills/grounded-copy/scripts/copy_lint.py draft.md` |

便携命令会复制规范技能目录：`SKILL.md`、两份参考资料、检查器和两套测试语料。Claude Code 和 Codex 插件会加入生命周期钩子、三个存储配置和配置控制器。

| 能力 | 便携版，17 个以上代理 | 插件，Claude Code 和 Codex |
|---|:---:|:---:|
| 规则、目录、九种语言、检查器和语料 | 是 | 是 |
| `SessionStart` 策略，在压缩后重复执行 |  | 是 |
| `UserPromptSubmit` 回合提醒 |  | 是 |
| 带存储偏好的 `chat`、`copy` 和 `off` 配置 |  | 是 |
| 配置控制器和管控指令 |  | 是 |

代理会在每个回合评估技能描述。插件钩子会在注册的会话事件运行，因此 Claude Code 和 Codex 会在会话开始、压缩后及每次提示时收到存储的配置。

当通用安装与 Claude 插件共用一台机器时，Claude Code 可能显示 `grounded-copy@skills-dir` 为 `Not loaded`，因为插件拥有当前技能名称。插件会提供技能和钩子。

Codex 缓存也包含检查器。0.5.1 版本使用此路径：

```bash
python3 ~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/0.5.1/skills/grounded-copy/scripts/copy_lint.py draft.md
```

<a id="pick-your-profile"></a>
## 选择配置

三个配置。在 Claude Code 中用 `/grounded-copy:grounded chat|copy|off` 切换，在 Codex 中用 `$grounded-profile chat|copy|off|status` 切换。所选值记录在 `<config-dir>/grounded-copy/profile`，重启后依然保留，直到下一次设置覆盖它。

| 配置 | `SessionStart` 注入内容 | 字节 | 回合提醒 |
|---|---|---:|---|
| `chat`（默认） | 引言及其示例、被禁形态及其七种外衣、正向表述、适用范围与优先级、来源规则 | 3,679 | 一行，写明 `chat` |
| `copy` | 以上全部，加营销语域和两条漏洞封堵 | 5,140 | 一行，写明 `copy` |
| `off` | 无 | 0 | 无 |

> [!IMPORTANT]
> **处理既有文本前请设为 `off`。** 这套规则约束的是你自己撰写的文字。当处理本身就带有对比结构的文本时——原文的译文、引用的段落、法律或监管条款、账单说明——模型可能删掉那处对比，从而改变文本的意思。翻译是最常见的情形：原文写下的对比出自作者的选择，配置仍然开启时，译文会丢掉这层区分。这类工作请先设为 `off`。

> [!TIP]
> **检查器按设计会报出的一类短语。** `without` 后面的 `-ing` 名词一律按动名词处理，因此 "without warning" 和 "without training" 会报 `without-gerund`。需要这类表达的文案请用 `off` 撰写。

<a id="what-it-does"></a>
## 功能

- **规则：** `SKILL.md` 定义七种对比形态、正向约束术语、来源规则和具体改写方法。
- **检查器：** `copy_lint.py` 使用 Python 3 标准库；干净文件返回退出码 0，发现问题返回 1，参数或 I/O 错误返回 2。
- **会话策略：** Claude Code 和 Codex 插件在会话开始注入所选策略，并在每次提示时注入简短提醒。
- **CI 门禁：** 工作流要求坏语料返回 1、好语料在 Ubuntu 和 Windows 上返回 0。

两层。钩子在会话开始、每次压缩后以及每次提示时把规则送入模型上下文，模型对它的遵循程度与遵循任何指令相同。`copy_lint.py` 发现问题时返回退出码 1，对任何指定目标都成立：草稿、差异、CI 路径。

<a id="before-and-after"></a>
## 改写示例

左栏引用被拦截的模式，规则栏写出 `copy_lint.py` 打印的规则 id。目录为每种记录的形态提供具体改写。

| 被拦截的草稿 | 落地改写 | 规则 |
|---|---|---|
| “它不仅仅是一个项目跟踪工具。” | “Acme 把每项任务关联到对应的拉取请求，并每天向 Slack 发布状态摘要。” | `zh-not-just` |
| “告别隐藏费用。” | “标示价格就是完整价格；发票不会增加费用。” | `zh-not-just` |
| “它不是善意，是一套算出来的生意。” | “低价来自三处结构调整：砍掉一层渠道、压缩营销预算、把周转天数做到 30 天以内。” | `zh-not-x-but-y` |

参见完整的[模式目录](skills/grounded-copy/references/patterns.md)。

<a id="nine-languages"></a>
## 九种语言

检查器按三种已记录的深度覆盖九种语言。

| 层级 | 语言 | 正则表达式匹配内容 |
|---|---|---|
| 完整 | 英语 | 57 条规则，每种形态至少有一条规则 |
| 结构 | 中文、日语、韩语 | 否定与断言之间的有限距离，以及列出的触发词 |
| 列举 | 俄语、西班牙语、阿拉伯语、法语、德语 | 覆盖弱化、时代结束、超越和设问诱导类别的 6 至 18 个触发短语 |

目标语言的触发词表提供基础覆盖。译者也要遵循目录规则：翻译有依据的原文，并保留具体事实。

<a id="documentation"></a>
## 文档

- [安装与接线](skills/grounded-copy/references/setup.md)介绍安装布局、配置、钩子生命周期、上下文成本、CI 和回滚。
- [模式目录](skills/grounded-copy/references/patterns.md)列出每个记录的触发类别及其改写。
- [贡献指南](CONTRIBUTING.md)介绍模式、语言和测试语料。
- [MIT 许可证](LICENSE)说明使用与再分发条款。
