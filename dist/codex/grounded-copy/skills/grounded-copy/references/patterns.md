# Pattern catalog: every disguise, with rewrites

One section per shape in `## The one banned move` in `SKILL.md`. The recipe
holds throughout: delete the contrast, state what the subject does, attach a
specific (feature, number, mechanism). "Acme", "the app", and "the store" are
placeholders spanning SaaS, e-commerce, services, and physical goods;
substitute the real product and its real specifics.

## 1. Placed against an alternative

Triggers: negated intensifiers ("not just/only/merely/simply", "doesn't just",
"more than just", "far from just/being"); comparative clauses ("rather than X",
"instead of X", "as opposed to X", "less a catalog than a trade desk");
transcendence verbs ("goes beyond", "beyond just", "redefines", "reimagines",
"reinvents"); absence framing ("without the hassle/hidden fees/middlemen",
"would add duplication without adding information", "zero guesswork/
compromises", "hassle-free", "frictionless").

| Bad | Good |
|---|---|
| "We don't just store your files, we protect them." | "Every file is encrypted at rest with AES-256 and replicated across three regions." |
| "More than just a project tracker." | "Acme tracks tasks, links each one to its pull request, and posts a daily status digest to Slack." |
| "Far from being a reseller, Acme roasts its own beans." | "Acme roasts in-house; every bag ships within 48 hours of roasting." |
| "Acme is less a gym than a coaching program." | "Acme pairs every member with a coach who reviews training logs weekly." |
| "We ship every Friday rather than hoarding features." | "We ship every Friday." |
| "Acme answers tickets instead of queuing them." | "Acme replies to every ticket within four business hours." |
| "Acme goes beyond file storage." | "Acme stores, versions, and full-text-searches every document, and syncs across five device types." |
| "We're redefining online booking." | "Acme books 40,000 appointments a month across 12 countries." |
| "Order direct without the hassle of middlemen." | "You order directly from the maker's own workshop stock." |
| "Zero guesswork. Zero hidden fees." | "Each listing carries the serial number, condition report, and full price." |
| "A second index would add duplication without adding information." | "The existing index already represents that commit." |

The last row is absence-framed justification, which reaches technical prose as
readily as marketing copy. `without-gerund` reports it and every other
`without` + `-ing` form. A regex reads an `-ing` noun the same way, so "without
warning" and "without training" report too; copy needing one of those is
written with the profile off.

## 2. Reversal reveals

Triggers: "It's not X, it's Y", "isn't about X, it's about Y", "—not X, but Y",
"not your average X", the appositive "X, not Y", the prepositional
", not by X", and the negated-setup dash "isn't/wasn't X — it Y".

| Bad | Good |
|---|---|
| "It's not a website. It's your storefront." | "The site takes orders, processes payments in 135 currencies, and prints shipping labels." |
| "Not your average newsletter." | "The newsletter delivers three vetted job listings every Tuesday, each with salary range and visa status." |
| "Acme is a partner, not a vendor." | "Acme assigns each client a strategist who joins quarterly planning." |
| "Acme isn't complicated — it books the job in one tap." | "Acme books the job in one tap." |
| "Freshness confirmed by query, not by the node count." | "The freshness query returned the current result." |

`comma-not-appositive` matches a comma and `not` before any object, so
`, not by`, `, not from`, `, not through`, and an object opening with a
backtick, a quote, or a bracket all report.

## 3. Era-ending

Triggers: "no longer", "gone are the days", "the days of X are over", "say
goodbye/hello", "no more X", "never again", "welcome to a new era".

| Bad | Good |
|---|---|
| "Gone are the days of opaque pricing." | "Every plan shows its full monthly price, including tax, before checkout." |
| "Say goodbye to hidden fees." | "The listed price is the complete price; the invoice adds nothing." |
| "No more waiting weeks for a quote." | "Quotes arrive within one business day." |
| "In today's fast-paced world, speed matters more than ever." | "Pages load in under 200 ms." |

## 4. Competitor put-downs

Triggers: "unlike traditional/most/other X", "while others/most X, we Y".

| Bad | Good |
|---|---|
| "Unlike traditional agencies, we publish our rates." | "Acme publishes its hourly rates on the pricing page." |
| "While others hide their fees, Acme lists them." | "Acme itemizes every charge on the invoice." |

Cross-sentence variant — equally banned:
"Most vendors bury their fees. Acme prints them." →
"Acme prints every fee on the invoice."

## 5. Rhetorical bait

Triggers: "The result?", "The best part?", "Think again", "Ever wondered",
"Tired of", "What if", "Imagine", "Picture this", "In a world where",
"Stop Xing", "Forget X", "Don't just X".

| Bad | Good |
|---|---|
| "The best part? Every plan includes support." | "Every plan includes support." |
| "Tired of slow responses?" | "Support replies within four business hours." |
| "Imagine a report that writes itself." | "The report generates each Monday from the previous week's data." |
| "Look no further than Acme." | "Acme runs the three checks listed above." |
| "It's worth noting that every plan includes support." | "Every plan includes support." |

## 6. Collision framing

Trigger: "where X meets Y".

| Bad | Good |
|---|---|
| "Where quality meets affordability." | "Solid-oak desks from $390, each with a 10-year warranty." |

## 7. Corporate throat-clearing

Trigger: "At [Company], we...".

| Bad | Good |
|---|---|
| "At Acme, we put customers first." | "Customers get net-30 payment terms and a named account manager." |

## Hype vocabulary

The register, enumerated: unleash, unlock, unparalleled, unwavering,
unmatched, unprecedented, unsung, unrivaled, elevate, seamless, empower,
revolutionize, game-changing, delve, supercharge, turbocharge, next-level,
cutting-edge, state-of-the-art, best-in-class, world-class, transformative,
effortless, one-stop shop, synergy; figurative "landscape" and "journey";
and "harness", "next-gen", "revolutionary" for the same reason. `SKILL.md`
carries the register test that covers the synonyms this list omits.

Replace the word with the fact it was hiding:

| Bad | Good |
|---|---|
| "seamless ordering" | "three-step ordering: pick, pay, track" |
| "unmatched support" | "one named rep per account, reachable within business hours" |
| "unlock new markets" | "ship to 40+ countries with customs documents prepared for you" |
| "world-class inspection" | "120-point inspection with the report attached to every listing" |
| "boasts a vibrant community" | "12,000 forum members, 300 posts a day" |
| "a testament to our quality" | "winner of the 2025 Red Dot product award" |

## Vague attribution

| Bad | Good |
|---|---|
| "Experts agree Acme leads the market." | "Acme holds 34% of the segment, per Gartner's 2025 market report." |
| "Studies show users prefer simple forms." | "In Acme's May 2026 survey of 1,200 users, 78% completed the three-field form." |

Related tail pattern — editorializing participles: ", highlighting our
commitment to quality", ", underscoring its value". Delete the tail and
state the fact it gestured at.

## Suspended lists

A pair of dashes holds the clause open. Three or four examples sit in the gap.
The reader carries the subject across the list to reach the verb.
`dash-pair-list` reports it, and the block pass gives that rule a paragraph as
its unit, so a dash pair that opens on one line and closes on the next still
reports. The rule reads `,`, `，`, and `、` as the separator, so a Chinese or
Japanese dash pair reports on the same terms.

Cut the list, in this order:

1. Delete the interrupter. The sentence often needs none of the items.
2. Keep the one example the reader needs, inside the clause: "such as a legal
   disclaimer".
3. Keep every item only where each one changes what the reader does. Then
   write the items as a list under the sentence.

A colon in place of the dashes, parentheses in place of the dashes, and a
split into two sentences each keep the same suspended list. None of the three
is a rewrite.

| Bad | Good |
|---|---|
| "Copy that has to carry one — a legal disclaimer, regulatory text, a translation of supplied source — is written with the profile off." | "Copy that must carry one, such as a legal disclaimer, is written with the profile off." |
| "Pointed at text that carries a contrast of its own — a translation, a quoted passage, a legal clause, a billing statement — the model can delete that contrast." | "Pointed at a translation of a supplied source, the model can delete the contrast the source carries." |
| "Acme covers every channel — email, live chat, phone, and the help centre — with one queue." | "Acme covers email, live chat, phone, and the help centre with one queue." |
| "The hook — a read of the preference, a read of the skill file, a write to stdout — runs in 40 ms." | "The hook runs in 40 ms." |

## Positive forms

| Bad | Good |
|---|---|
| "the hook does not write" | "the hook is read-only" |
| "the value does not change after construction" | "the value is immutable" |
| "runs the migration but writes nothing" | "runs the migration as a dry run" |
| "the log is only ever appended to" | "the log is append-only" |
| "calling it twice changes nothing" | "the call is idempotent" |
| "only one component may write it" | "the value has a single writer" |

## Multilingual equivalents (all banned)

Every form below is banned in prose. What the linter reports depends on the
tier: `zh`, `ja`, and `ko` match a bounded gap between the negation and the
assertion, so a phrasing outside the list can still report; `ru`, `es`, `ar`,
`fr`, and `de` match the listed phrases only. Outside English the regexes are a
floor, and the translator rule below carries the rest.

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

Rule for translators: a target-language draft carrying a contrast the English
source lacks is a wrong translation, however natural it sounds. だけでなく,
뿐만 아니라, 더 이상, and 혁신적 each also carry a coordinating factual use and
report all the same; copy needing one is written with the profile off.

**zh reversal reveal.** The row above covers the minimizing forms (不仅仅是 /
不只是) and the era-ending forms (不再是 / 告别). The reversal reveal is
不是 X，而是 Y, with the variants 并不是…而是, 不在于…而在于, 不是…，是, and 而不是.
`zh-not-x-but-y` reports every one: 不是 followed by 是 within 32 characters of
one sentence, plus the two standalone forms. Plain negation opens with the same
two characters, so the bounded gap is what separates the shapes.

| Bad | Good |
|---|---|
| "消费者不是图便宜才买的，而是真心认可产品本身的价值。" | "该品牌主力车型均价 20 万以上，购车用户中 68% 将续航和智驾列为首选理由。" |
| "关键不是等，而是看你的用车场景适不适合现在入手。" | "有固定车位可装充电桩的用户，每公里电费几分钱，现在入手即可回本。" |
| "它不是善意，是一套算出来的生意。" | "低价来自三处结构调整：砍掉一层渠道、压缩营销预算、把周转天数做到 30 天以内。" |
| "量贩零食卖的不是零食，是情绪和节奏。" | "量贩零食按口味把品类拆到 SKU 级，一筐几十元，顾客平均停留 12 分钟。" |
