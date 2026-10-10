# Pattern guide

Use this guide when the checker reports a phrase or when a draft feels vague. Each section explains a writing habit and shows how to state the useful detail directly.

The examples are invented for teaching. Product names, figures, awards, and source attributions in the tables are placeholders. Use facts from your own source when you rewrite. If a detail is missing, ask for it or keep the claim within what you know.

The quoted triggers and Draft columns deliberately contain wording the checker reports. The Rewrite columns show the intended style.

With `--profile chat` the checker runs the reversal rules, the contrast-marker rules, and the suspended-list rule. With `--profile copy`, or with no option, it runs every rule.

## Everyday examples

The rewrite is the draft with its contrast half removed, so it comes out shorter. Each draft below sets a fact against something nobody raised.

| Draft | Rewrite |
|---|---|
| "The file isn't missing, it's empty." | "The file is empty." |
| "Your plant isn't dying, it's dormant." | "Your plant is dormant." |
| "A budget is a plan, not a punishment." | "A budget is a plan." |
| "Rinse the rice rather than skipping that step." | "Rinse the rice." |
| "Use olive oil instead of butter." | "Use olive oil." |
| "The museum is no longer free on Sundays." | "The museum charges on Sundays." |
| "You can cancel without paying a fee." | "Cancelling is free." |
| "He wasn't fired, he quit." | "He quit." |
| "The printer isn't broken, it needs paper." | "The printer needs paper." |
| "You don't need a gym, you need a routine." | "You need a routine." |

Keep the second half when the reader raised it. If someone asked about butter, "Use olive oil; butter burns at this heat." answers them.

## 1. Placed against an alternative

Describe the subject directly. A comparison often leaves the reader waiting for the actual feature or action.

Triggers: phrases that downplay the subject ("not just/only/merely/simply", "doesn't just",
"more than just", "far from just/being"); comparisons ("rather than X",
"instead of X", "as opposed to X", "less a catalog than a trade desk");
claims about exceeding a category ("goes beyond", "beyond just", "redefines", "reimagines",
"reinvents"); claims about removing a problem ("without the hassle/hidden fees/middlemen",
"would add duplication without adding information", "zero guesswork/
compromises", "hassle-free", "frictionless").

| Draft | Rewrite |
|---|---|
| "We don't just store your files, we protect them." | "Every file is encrypted at rest with AES-256 and replicated across three regions." |
| "More than just a project tracker." | "Acme tracks tasks, links each one to its pull request, and posts a daily status digest to Slack." |
| "Far from being a reseller, Acme roasts its own beans." | "Acme roasts in-house; every bag ships within 48 hours of roasting." |
| "Acme is less a gym than a coaching program." | "Acme pairs every member with a coach who reviews training logs weekly." |
| "We ship every Friday rather than hoarding features." | "We ship every Friday." |
| "Acme answers tickets instead of queuing them." | "Acme replies to every ticket within four business hours." |
| "Acme goes beyond file storage." | "Acme saves document versions, searches their contents, and syncs them across five device types." |
| "We're redefining online booking." | "Acme books 40,000 appointments a month across 12 countries." |
| "Order direct without the hassle of middlemen." | "You order directly from the maker's workshop." |
| "Zero guesswork. Zero hidden fees." | "Each listing carries the serial number, condition report, and full price." |
| "A second index would add duplication without adding information." | "The existing index already represents that commit." |

The `doesnt-just` rule takes every contracted auxiliary, `cannot`, and `never`, so an instruction such as "You can't just subclass list." reports. The `is-more-than-a` rule takes the past tense and the contracted forms, so a quantity such as "The log was more than a gigabyte." reports.

The `less-a-x-than` rule also reports "less about speed and more about trust" and "not so much a gym as a coaching program".

The `without-gerund` rule matches `without` followed by an `-ing` form. It also reports ordinary phrases such as "without warning" and "without training". Preserve the meaning of required text and use the profile off for that work.

The `instead-of`, `no-longer`, and `without-gerund` rules joined the gate when Claude moved to those forms after early versions of the plugin blocked the reversal. They report ordinary substitutions, exclusions, and status lines too, so say what to do or what is true now.

## 2. Reversal reveals

Start with the fact. A denial followed by a reveal makes the reader work through two claims to reach it.

Triggers: "It's not X, it's Y", "isn't about X, it's about Y", "—not X, but Y",
"not your average X", "X, not Y",
", not by X", and a denial followed by a dash "isn't/wasn't X — it Y".
The denial can also set up "just", "only", "merely", or "simply": "not X, just Y".
A slogan opens the same way: "No X, just Y".

| Draft | Rewrite |
|---|---|
| "It's not a website. It's your storefront." | "The site takes orders, processes payments in 135 currencies, and prints shipping labels." |
| "Not your average newsletter." | "The newsletter delivers three vetted job listings every Tuesday, each with salary range and visa status." |
| "Acme is a partner, not a vendor." | "Acme assigns each client a strategist who joins quarterly planning." |
| "Acme isn't complicated — it books the job in one tap." | "Acme books the job in one tap." |
| "Freshness confirmed by query, not by the node count." | "The freshness query returned the current result." |
| "I'm not the plugin's author, just a user." | "I use this plugin; a friend wrote it." |
| "No hidden fees, just simple pricing." | "Each plan shows one monthly price, tax included." |
| "Acme isn't a tool, it's a platform." | "Acme runs the build, the tests, and the release in one pipeline." |
| "Not slow, just cold." | "The pool is 18 °C." |
| "Not a patch. A rewrite." | "Version 2 replaces the parser." |

The `comma-not-appositive` rule also catches `, not by`, `, not from`, and `, not through`. It can match an object that starts with a quote, backtick, or bracket.

The `not-just` rule also reports a denial and `just`, `only`, `merely`, or `simply` on either side of a comma or dash. The denial opens with a negated form of "be" or with "not" and a word such as "the" or "my". A plain limit of that shape reports too: "Windows is not supported, only Linux and macOS."

The `no-x-just-y` rule reports the slogan form: "no", "zero", or "nothing", one or two words, then "just". A longer status line such as "No fix was needed, just a restart." passes.

The `not-x-its-y` rule reports the first trigger with any subject, and as two sentences. A condition passes: "If the file is not there, it is created." A correction of fact in the same shape reports: "The file isn't missing, it's empty." State the fact: "The file is empty."

The `not-x-its-y` rule also reports a second half that opens with a plain verb: "He wasn't fired, he quit." A comma splice of two facts has the same shape and reports too: "The pan isn't oven-safe, it has a plastic handle." Join the reason with "because": "The pan isn't oven-safe because it has a plastic handle."

The `do-verb-repeat` rule reports a denial of "need" or "want" followed by the same verb, and "does not mean" followed by "it means" in one sentence or two. Another repeated verb gives two facts and passes: "I don't drink coffee, I drink tea."

The `fragment-reversal` rule runs under `copy` only. In a chat the same fragments are short answers and corrections: "Not a teaspoon, a tablespoon."

The `dash-not-contrast` and `negated-copula-dash` rules read a spaced hyphen or a double hyphen as a dash: "Acme is a partner - not a vendor." A plain limit written that way reports too: "The limit is 3 - not configurable."

The `not-x-but-y` rule takes a contracted negation and any determiner: "The result wasn't a failure but a delay." It also takes a preposition or "because" that repeats after "but": "The error was not in the config but in the loader." A concession reports too: "The build isn't the fastest but it works." The `isnt-about` rule takes the past tense and "never about", so the idiom "He wasn't about to quit." reports. "This is no ordinary newsletter." and "Not another todo app." report under `not-your-average`.

## 3. Era-ending

Give the current behavior or result. A claim about the end of an era usually adds little useful information.

Triggers: "no longer", "gone are the days", "the days of X are over", "say
goodbye/hello", "no more X", "never again", "welcome to a new era".

| Draft | Rewrite |
|---|---|
| "Gone are the days of opaque pricing." | "Every plan shows its full monthly price, including tax, before checkout." |
| "Say goodbye to hidden fees." | "The listed price is the complete price; the invoice adds nothing." |
| "No more waiting weeks for a quote." | "Quotes arrive within one business day." |
| "In today's fast-paced world, speed matters more than ever." | "Pages load in under 200 ms." |

## 4. Competitor put-downs

Explain what the product offers. A sentence about a rival needs evidence and can distract from the feature the reader came to understand.

Triggers: "unlike traditional/most/other X", "while others/most X, we Y".

| Draft | Rewrite |
|---|---|
| "Unlike traditional agencies, we publish our rates." | "Acme publishes its hourly rates on the pricing page." |
| "While others hide their fees, Acme lists them." | "Acme itemizes every charge on the invoice." |

The same comparison can span sentences. For example: "Most vendors bury their fees. Acme prints them." Rewrite it as "Acme prints every fee on the invoice."

The two rules also report "unlike competitors", "whereas most", and "where others". A comparison of two interfaces in that shape reports: "Whereas most functions return a list, this one returns an iterator."

## 5. Rhetorical bait

Put the useful information first. A question that immediately answers itself often adds an unnecessary step.

Triggers: "The result?", "The best part?", "Think again", "Ever wondered",
"Tired of", "What if", "Imagine", "Picture this", "In a world where",
"Stop Xing. Start Ying.", "Forget X", "Don't just X".

| Draft | Rewrite |
|---|---|
| "The best part? Every plan includes support." | "Every plan includes support." |
| "Tired of slow responses?" | "Support replies within four business hours." |
| "Imagine a report that writes itself." | "The report generates each Monday from the previous week's data." |
| "Look no further than Acme." | "Acme runs the three checks listed above." |
| "It's worth noting that every plan includes support." | "Every plan includes support." |

The `opener-stop` rule reports the pair. A plain instruction passes: "Stop the server before the upgrade."

## 6. Collision framing

Name a material, price, feature, or action. Pairing abstract qualities leaves the details unclear.

Trigger: "where X meets Y".

| Draft | Rewrite |
|---|---|
| "Where quality meets affordability." | "Solid-oak desks from $390, each with a 10-year warranty." |

## 7. Corporate throat-clearing

Start with what the customer gets or what the company does.

Trigger: "At [Company], we...".

| Draft | Rewrite |
|---|---|
| "At Acme, we put customers first." | "Customers have 30 days to pay and an account manager they can contact." |

## Hype vocabulary

Replace broad praise with the feature or fact it refers to. Review synonyms by meaning too.

Common examples: unleash, unlock, unparalleled, unwavering,
unmatched, unprecedented, unsung, unrivaled, elevate, seamless, empower,
revolutionize, game-changing, delve, supercharge, turbocharge, next-level,
cutting-edge, state-of-the-art, best-in-class, world-class, transformative,
effortless, one-stop shop, synergy; figurative "landscape" and "journey";
and "harness", "next-gen", "revolutionary".

| Draft | Rewrite |
|---|---|
| "seamless ordering" | "three-step ordering: pick, pay, track" |
| "unmatched support" | "one named rep per account, reachable within business hours" |
| "unlock new markets" | "ship to 40+ countries with customs documents prepared for you" |
| "world-class inspection" | "120-point inspection with the report attached to every listing" |
| "boasts a vibrant community" | "12,000 forum members, 300 posts a day" |
| "a testament to our quality" | "winner of the 2025 Red Dot product award" |

## Vague attribution

Name a source that the reader can check. A claim attributed to an unnamed group still needs evidence.

| Draft | Rewrite |
|---|---|
| "Experts agree Acme leads the market." | "The 2025 market report by [source] gives Acme a 34% share of [segment]." |
| "Studies show users prefer simple forms." | "In Acme's May 2026 survey of 1,200 users, 78% completed the three-field form." |

A trailing phrase can add praise too: ", highlighting our commitment to quality" or ", underscoring its value". Remove it and state the supported fact.

## Suspended lists

A list between paired dashes can separate the subject from its verb. The reader has to hold the sentence in mind while reading the examples. The `dash-pair-list` rule checks this across a paragraph, including line breaks. It recognizes English, Chinese, and Japanese comma separators.

First remove the inserted list. Keep one example inside the sentence if the reader needs it. When every item affects the reader's next step, put the items in a list below the sentence. Replacing the dashes with parentheses or a colon leaves the same interruption.

| Draft | Rewrite |
|---|---|
| "Copy that has to carry one — a legal disclaimer, regulatory text, a translation of supplied source — is written with the profile off." | "Use the profile off for required wording, such as a legal disclaimer." |
| "Pointed at text that carries a contrast of its own — a translation, a quoted passage, a legal clause, a billing statement — the model can delete that contrast." | "The assistant can remove a comparison when translating supplied text." |
| "Acme covers every channel — email, live chat, phone, and the help centre — with one queue." | "Acme brings customer requests into one queue." |
| "The hook — a read of the preference, a read of the skill file, a write to stdout — runs in 40 ms." | "The hook runs in 40 ms." |

## Paragraph review

Apply this review to English and other languages. Decide what the reader needs from the paragraph, then select the facts that serve that purpose. A fact can be accurate and still be unnecessary here. Omit incidental details and keep the resulting claim within what the source supports.

In English, watch for noun lists and chains of actions that keep restating one point. Adjacent sentences can form a catalog even when each sentence names only one item. Remove details that add no useful meaning, then explain the supported relationship between the remaining ideas. A shorter summary must keep any condition that changes the reader's conclusion or next step.

Changing commas to semicolons or moving each item into a bullet leaves the information burden intact. Review the whole passage again after cutting: make its point clear and connect the remaining details. Length and punctuation counts alone do not establish quality. This review is part of writing; the checker retains its existing pattern checks.

These invented examples show deliberate omissions. Their contexts establish what the reader needs.

| Context | Draft | Rewrite |
|---|---|---|
| A user-facing update about a fix for interrupted uploads. | "The fix changes chunk IDs, checksum records, and retry queues so interrupted uploads can resume." | "Interrupted uploads can now resume." |
| Introduce a task board's purpose to a new teammate. | "The board shows owners, dates, priorities, and next steps. Teammates can see who owns each task and what happens next." | "The board shows who owns each task and what happens next." |
| Explain how a team reviews blocked tasks. | "We read the status. We read the owner. We read the due date. We read the blocker note. We then ask the owner what is needed to unblock the task." | "We review blocked tasks and ask each owner what is needed to continue." |

The first example omits implementation details that belong in an explanation of the fix. The third removes a sequence of routine actions that obscured the meeting's purpose. Use the task to decide what belongs. Explicit requests for a complete inventory still require complete coverage.

## Positive forms

Use a familiar technical term when it describes the behavior accurately. Explain it in plain language when the reader needs that help.

| Draft | Rewrite |
|---|---|
| "the hook does not write" | "the hook is read-only" |
| "the value does not change after construction" | "the value is immutable" |
| "runs the migration but writes nothing" | "runs the migration as a dry run" |
| "the log is only ever appended to" | "the log is append-only" |
| "calling it twice changes nothing" | "the call is idempotent" |
| "only one component may write it" | "the value has a single writer" |

## Multilingual equivalents (all banned)

Apply the writing rules to meaning in each language. The Chinese, Japanese, and Korean checks include sentence patterns with a limited gap between the matched parts. The Russian, Spanish, Arabic, French, and German checks use phrase lists. Review the rest of the text yourself.

| Locale | Patterns |
|---|---|
| zh-Hans | 不仅仅是 / 不只是 / 不仅是 / 不止是 / 不再是 / 告别… / 重新定义 / 颠覆 / 不是 X，而是 Y |
| ru | не просто / больше, чем просто / попрощайтесь с… / переосмысливает |
| es-419 | no es solo / no solo es / más que un(a) simple / dile adiós a / olvídate de / atrás quedaron los días / va más allá / redefinimos |
| ar | ليس مجرد / أكثر من مجرد / وداعًا لـ / يعيد تعريف |
| fr | n'est pas qu'un simple / pas seulement / plus qu'un simple / dites adieu à / oubliez / imaginez / va au-delà / redéfinit |
| de | nicht nur ein / mehr als nur / verabschieden Sie sich von / Schluss mit / nie wieder / definiert … neu / geht über … hinaus / Stellen Sie sich vor |
| ja | 単なる〜ではない / 〜だけではない / 〜だけでなく / 〜にとどまらない / 〜とはおさらば / 再定義 / 革命的 / 想像してみてください |
| ko | 단순한 〜이 아니다 / 뿐만 아니라 / 〜에 그치지 않는다 / 〜와 작별하세요 / 더 이상 / 재정의 / 게임 체인저 / 상상해 보세요 |

When translating a draft written under these rules, keep its facts and use natural sentences in the target language. For a faithful translation of supplied text, preserve its intended comparisons and use the profile off as needed.

Some listed phrases have ordinary factual uses too. Japanese だけでなく and Korean 뿐만 아니라, 더 이상, and 혁신적 can appear in such uses and still produce findings.

The rules also match the forms below. X and Y mark a sentence pattern. The last column gives a plain sentence in the same shape.

| Locale | More patterns | An ordinary sentence that also reports |
|---|---|---|
| zh | 不僅僅是 / 告別 / 重新定義 / 顛覆 / 不光是 / 不单是 / 并非 X，而是 Y / 与其说 X，不如说 Y | 他不光是一个人去的。 |

### Chinese comparisons

The `zh-not-x-but-y` rule matches 不是 followed by 是 within 32 characters in one sentence. It also covers forms such as 并不是…而是, 不在于…而在于, 不是…，是, and 而不是. Read the sentence in context before changing it.

以下情境均为教学示例。改写依据同一行给出的事实，实际使用时请换成有来源的内容。

| 已知情境 | Draft | Rewrite |
|---|---|---|
| 问卷要求填写一个购买主因；这20位受访者均填写了续航。 | “这20位受访者不是看中价格，而是看中续航。” | “这20位受访者填报的购买主因是续航。” |
| 表单要求提交前填写每天的行驶距离和充电条件。 | “关键不是等待，而是先填好每天的行驶距离和充电条件。” | “提交前，请填写每天的行驶距离和充电条件。” |
| 服务说明规定每单收取2元服务费。 | “这项服务不是免费帮忙，是每单收取2元的生意。” | “这项服务每单收取2元服务费。” |
| 申请在提交后进入审批流程，获管理员批准后生效。 | “申请不是提交后立即生效，而是获管理员批准后生效。” | “提交的申请经管理员批准后生效。” |

## Chinese paragraph review

先明确读者需要知道什么，再决定写哪些事实。材料可以包含很多细节，正文应有所取舍。允许概括和删去无助于主旨的信息，包括正确的技术细节；保留下来的说法须有依据，省略关键限定不能造成误导。用户明确要求完整清单或逐字引用时，按要求处理。

以下五项用于写作和审读，检查脚本目前未检测这些问题。顿号数量只可辅助观察。审读时先看内容是否值得写，再看句式是否自然。

### 密集列举

先写清本段要让读者理解的一件事。检查每个列举项是否影响读者理解主旨或完成操作，无助于这两者的细节可以删去。几个项目共同说明一个意思时，可直接概括。技术术语也需要经过取舍，不能仅因事实正确或原文出现就全部写入正文。

把所有细节拆成短句、改成项目符号或换用逗号，仍然是在逐项复述。先删减内容，再调整句子之间的衔接。说明先后或因果时须有依据，避免给剩余事实补造关系。

### 模板化句式

留意相邻句子反复使用同一种起句，如“真正需要……的是……”。判断每句是否推进了论述；重复的意思可以删去，留下的内容按具体主语和动作展开。句式的变化应服务于表达。

### 欧化表达

检查主语、谓语和分句之间的衔接，按汉语习惯直接交代事情。引导句接冒号时，确认后文确实解释了前文；空泛的转接语可删去或并入具体陈述。冒号本身是正常标点，短句也可自然地引出说明。仅凭一种句式无法断定它源于英语翻译。

### 近距离冗余

检查同一句或相邻句中的重复词是否分别表达了必要信息。重复的时间范围、程度或判断若无新增含义，可合并表达。需要保持术语一致、明确指代或强调持续时间时，保留原词。避免仅为避重而换上含义不同的近义词。

### 语体一致

按读者和任务选择语体。日常解释可使用自然口语，申请材料和报告应采用相应的正式表达。技术术语可以配合通俗解释，判断重点是措辞是否适合这段文字。修改突兀的口语或书面套话时，保持原意；“愿意付费”不能改成“已经盈利”。文言词和商业术语也可能增加理解负担。

### 按用途取舍和改写

以下是新编的教学情境。改写只选用与用途相关的事实；保留下来的表述忠实于已知情境。

| 情境 | Draft | Rewrite |
|---|---|---|
| 面向普通用户的更新说明：修复了上传中断后重复提交的问题，实现涉及分片编号、校验记录和重试队列。 | “这次更新修改了分片编号、校验记录、重试队列，解决了上传中断后重复提交的问题。” | “修复了上传中断后重复提交的问题。” |
| 学习提醒：报名本周五截止；学员应按自己的时间选择课程。 | “真正需要留意的是本周五的报名截止时间。真正需要考虑的是自己的时间能否配合课程。” | “报名本周五截止，选课时请确认上课时间是否合适。” |
| 编辑记录：两篇摘要都缺少实验条件。 | “对于第二篇摘要，情况也是这样的：它同样缺少实验条件。” | “第二篇摘要也缺少实验条件。” |
| 项目计划：系统运行期间，设备状态的采集和显示均持续进行。 | “系统运行期间，将持续采集设备状态，并持续显示设备状态。” | “系统运行期间，将持续采集并显示设备状态。” |
| 正式报告：系统提供告警记录查询，方便人员追溯故障。 | “系统提供告警记录查询，出了岔子就翻一翻。” | “系统提供告警记录查询，便于工作人员追溯故障。” |

第一行省去了真实的实现细节，因为更新说明的读者只需知道问题已经修复。若任务是解释修复原理，这些细节才可能需要展开。信息是否出现，由本次任务决定。

删减后检查结论是否准确。例如“目前仅向受邀用户开放测试”可写为“测试目前仅对受邀用户开放”，适用范围和测试状态仍然清楚。涉及操作的关键条件也须交代；用户要求核对完整清单时，应完整列出。普通介绍无需主动扩展成清单。
