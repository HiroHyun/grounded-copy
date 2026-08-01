# Pattern catalog: every disguise, with rewrites

Each entry: the pattern, why it is the banned move, and a rewrite that
keeps the information. The rewrite recipe never changes — delete the
contrast, state what the subject does, attach a specific (feature,
number, mechanism).

Company and product names below ("Acme", "the app", "the store") are
placeholders spanning different domains — SaaS, e-commerce, services,
physical goods. When rewriting real copy, substitute the actual product
and its actual specifics; the specifics are the point.

## 1. Negated intensifiers

| Bad | Good |
|---|---|
| "We don't just store your files, we protect them." | "Every file is encrypted at rest with AES-256 and replicated across three regions." |
| "More than just a project tracker." | "Acme tracks tasks, links each one to its pull request, and posts a daily status digest to Slack." |
| "Far from being a reseller, Acme roasts its own beans." | "Acme roasts in-house; every bag ships within 48 hours of roasting." |

## 2. Reversal reveals

| Bad | Good |
|---|---|
| "It's not a website. It's your storefront." | "The site takes orders, processes payments in 135 currencies, and prints shipping labels." |
| "Not your average newsletter." | "The newsletter delivers three vetted job listings every Tuesday, each with salary range and visa status." |
| "Acme is less a gym than a coaching program." | "Acme pairs every member with a coach who reviews training logs weekly." |
| "Acme is a partner, not a vendor." | "Acme assigns each client a strategist who joins quarterly planning." |
| "Acme isn't complicated — it books the job in one tap." | "Acme books the job in one tap." |
| "We ship every Friday rather than hoarding features." | "We ship every Friday." |
| "Freshness confirmed by query, not by the node count." | "The freshness query returned the current result." |

The last row is the prepositional form. `comma-not-appositive` matches a comma
and `not` before any object, so `, not by`, `, not from`, `, not through`, and
an object opening with a backtick, a quote, or a bracket all report.

## 3. Era-ending

| Bad | Good |
|---|---|
| "Gone are the days of opaque pricing." | "Every plan shows its full monthly price, including tax, before checkout." |
| "Say goodbye to hidden fees." | "The listed price is the complete price; the invoice adds nothing." |
| "No more waiting weeks for a quote." | "Quotes arrive within one business day." |
| "In today's fast-paced world, speed matters more than ever." | "Pages load in under 200 ms." |

## 4. Competitor put-downs

| Bad | Good |
|---|---|
| "Unlike traditional agencies, we publish our rates." | "Acme publishes its hourly rates on the pricing page." |
| "While others hide their fees, Acme lists them." | "Acme itemizes every charge on the invoice." |

Cross-sentence variant — equally banned:
"Most vendors bury their fees. Acme prints them." →
"Acme prints every fee on the invoice."

## 5. Transcendence verbs

| Bad | Good |
|---|---|
| "Acme goes beyond file storage." | "Acme stores, versions, and full-text-searches every document, and syncs across five device types." |
| "We're redefining online booking." | "Acme books 40,000 appointments a month across 12 countries." |

## 6. Absence-as-benefit

| Bad | Good |
|---|---|
| "Order direct without the hassle of middlemen." | "You order directly from the maker's own workshop stock." |
| "Zero guesswork. Zero hidden fees." | "Each listing carries the serial number, condition report, and full price." |
| "A second index would add duplication without adding information." | "The existing index already represents that commit." |

The last row is absence-framed justification, which reaches technical prose as
readily as marketing copy. `without-gerund` reports it and every other
`without` + `-ing` form. A regex reads an `-ing` noun the same way, so "without
warning" and "without training" report too; copy that needs one of those is
written with the profile off.

## 7. Rhetorical bait

| Bad | Good |
|---|---|
| "The best part? Every plan includes support." | "Every plan includes support." |
| "Tired of slow responses?" | "Support replies within four business hours." |
| "Imagine a report that writes itself." | "The report generates each Monday from the previous week's data." |
| "Look no further than Acme." | "Acme runs the three checks listed above." |
| "It's worth noting that every plan includes support." | "Every plan includes support." |

## 8. Collision framing

| Bad | Good |
|---|---|
| "Where quality meets affordability." | "Solid-oak desks from $390, each with a 10-year warranty." |

## 9. Corporate throat-clearing

| Bad | Good |
|---|---|
| "At Acme, we put customers first." | "Customers get net-30 payment terms and a named account manager." |

## 10. Hype vocabulary

Replace the word with the fact it was hiding:

| Bad | Good |
|---|---|
| "seamless ordering" | "three-step ordering: pick, pay, track" |
| "unmatched support" | "one named rep per account, reachable within business hours" |
| "unlock new markets" | "ship to 40+ countries with customs documents prepared for you" |
| "world-class inspection" | "120-point inspection with the report attached to every listing" |
| "boasts a vibrant community" | "12,000 forum members, 300 posts a day" |
| "a testament to our quality" | "winner of the 2025 Red Dot product award" |

Register test for unlisted synonyms: if the word could appear unchanged in
a perfume ad and a SaaS deck, it is hype. Replace it.

## 11. Vague attribution

Unnamed authority is the vagueness twin of contrast: it praises without a
checkable fact. Name the source or state the measurable claim.

| Bad | Good |
|---|---|
| "Experts agree Acme leads the market." | "Acme holds 34% of the segment, per Gartner's 2025 market report." |
| "Studies show users prefer simple forms." | "In Acme's May 2026 survey of 1,200 users, 78% completed the three-field form." |

Related tail pattern — editorializing participles: ", highlighting our
commitment to quality", ", underscoring its value". Delete the tail and
state the fact it gestured at.

## 12. Positive forms

Where an established positive term carries the constraint unambiguously,
`SKILL.md` asks for the term. These are the rewrites:

| Bad | Good |
|---|---|
| "the hook does not write" | "the hook is read-only" |
| "the value does not change after construction" | "the value is immutable" |
| "runs the migration but writes nothing" | "runs the migration as a dry run" |
| "the log is only ever appended to" | "the log is append-only" |
| "calling it twice changes nothing" | "the call is idempotent" |
| "only one component may write it" | "the value has a single writer" |

## Trigger phrases by shape

`## The one banned move` in `SKILL.md` names seven shapes and gives the
openers. These are the complete lists; the sections above carry a rewrite
for each shape.

1. **Placed against an alternative.** Negated intensifiers ("not
   just/only/merely/simply", "doesn't just", "more than just", "far from
   just/being"); comparative clauses ("rather than X", "instead of X",
   "less a catalog than a trade desk"); transcendence verbs ("goes
   beyond", "beyond just", "redefines", "reimagines", "reinvents"); and
   absence framing ("without the hassle/hidden fees/middlemen", "would
   add duplication without adding information", "zero
   guesswork/compromises", "hassle-free", "frictionless").
2. **Reversal reveals.** "It's not X, it's Y", "isn't about X, it's about
   Y", "—not X, but Y", "not your average X". Includes the appositive
   form "X, not Y" ("a partner, not a vendor"), the prepositional form
   ("confirmed by query, not by the node count"), and the negated-setup
   dash "isn't/wasn't X — it Y" ("the gate wasn't slow — it finished").
3. **Era-ending.** "no longer", "gone are the days", "the days of X are
   over", "say goodbye/hello", "no more X", "never again", "welcome to a
   new era".
4. **Competitor put-downs.** "unlike traditional/most/other X",
   "while others/most X, we Y".
5. **Rhetorical bait.** "The result?", "The best part?", "Think again",
   "Ever wondered", "Tired of", "What if", "Imagine", "Picture this",
   "In a world where", "Stop Xing", "Forget X", "Don't just X".
6. **Collision framing.** "where X meets Y".
7. **Corporate throat-clearing.** "At [Company], we...".

## Multilingual equivalents (all banned)

| Locale | Patterns |
|---|---|
| zh-Hans | 不仅仅是 / 不只是 / 不仅是 / 不止是 / 不再是 / 告别… / 重新定义 / 颠覆 |
| ru | не просто / больше, чем просто / попрощайтесь с… / переосмысливает |
| es-419 | no es solo / no solo es / más que un(a) simple / dile adiós a / olvídate de / atrás quedaron los días / va más allá / redefinimos |
| ar | ليس مجرد / أكثر من مجرد / وداعًا لـ / يعيد تعريف |
| fr | n'est pas qu'un simple / pas seulement / plus qu'un simple / dites adieu à / oubliez / imaginez / va au-delà / redéfinit |
| de | nicht nur ein / mehr als nur / verabschieden Sie sich von / Schluss mit / nie wieder / definiert … neu / geht über … hinaus / Stellen Sie sich vor |
| ja | 単なる〜ではない / 〜だけではない / 〜にとどまらない / 〜とはおさらば / 再定義 / 革命的 / 想像してみてください |
| ko | 단순한 〜이 아니다 / 〜에 그치지 않는다 / 〜와 작별하세요 / 재정의 / 게임 체인저 / 상상해 보세요 |

Rule for translators: translate the grounded English sentence literally.
If the target-language draft contains a contrast the English source does
not, the translation is wrong, even if it "sounds more natural."

だけでなく, 뿐만 아니라, 더 이상, and 혁신적 report alongside the rest. Each also
carries a coordinating factual use; copy that needs one is written with the
profile off.

**zh reversal reveal.** The rows above cover the minimizing forms (不仅仅是 /
不只是) and the era-ending forms (不再是 / 告别). The reversal reveal in Chinese
is 不是 X，而是 Y and its variants 并不是…而是, 不在于…而在于, 不是…，是, and
而不是. `zh-not-x-but-y` reports every one: 不是 followed by 是 within 32
characters of the same sentence, plus the two standalone forms. The connector
slot (而 / 或 / 却 / one word / nothing) sits inside the gap, so the pattern
holds one bounded quantifier. Sightings:

| Bad | Good |
|---|---|
| "消费者不是图便宜才买的，而是真心认可产品本身的价值。" | "该品牌主力车型均价 20 万以上，购车用户中 68% 将续航和智驾列为首选理由。" |
| "关键不是等，而是看你的用车场景适不适合现在入手。" | "有固定车位可装充电桩的用户，每公里电费几分钱，现在入手即可回本。" |
| "它不是善意，是一套算出来的生意。" | "低价来自三处结构调整：砍掉一层渠道、压缩营销预算、把周转天数做到 30 天以内。" |
| "量贩零食卖的不是零食，是情绪和节奏。" | "量贩零食按口味把品类拆到 SKU 级，一筐几十元，顾客平均停留 12 分钟。" |

Plain negation in Chinese opens with the same two characters, so the bounded gap
is what separates the two shapes: 不是 with no 是 behind it in the same sentence
reports nothing.
