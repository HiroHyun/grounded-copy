---
name: grounded-copy
description: Enforces grounded, contrast-free marketing and web copy. Every value proposition must state what the subject IS or DOES using concrete nouns, verbs, and specifics — never negation, contrast, or hype vocabulary. Use this skill whenever writing, editing, translating, reviewing, or localizing ANY user-facing copy — headlines, taglines, value propositions, landing pages, product descriptions, About pages, CTAs, button labels, meta/OG descriptions, alt text, email subjects and bodies, social posts, ad copy, brochures, or locale/i18n string files — even if the user does not mention style rules. Also use when the user says "on-brand", "our writing style", "no AI clichés", or asks to check copy.
---

# Grounded Copy

Copy describes things by what they ARE. Every value proposition is a direct
declarative statement built on concrete nouns, verbs, and specifics: the
feature, the number, the mechanism.

- Bad: "This isn't just a task tracker — it's your team's second brain."
- Good: "The tracker links every task to its pull request and posts a
  status digest to Slack each morning."

## The one banned move (and every disguise it wears)

The banned move is **defining the subject by placing it against
something** — against what it is *not*, against what *others* do worse,
against what *era* has ended. Grounded prose states what the subject is
and does, and attaches a specific.

One structure wears four costumes. They are the same rule:

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

Three further shapes carry the same defect and are equally banned:

5. **Rhetorical bait:** "The result?", "The best part?", "Think again",
   "Ever wondered", "Tired of", "What if", "Imagine", "Picture this",
   "In a world where", "Stop Xing", "Forget X", "Don't just X".
6. **Collision framing:** "where X meets Y".
7. **Corporate throat-clearing:** "At [Company], we...".

Write none of them, and invent no new costume for the same move. The
rewrite is always the same: delete the contrast, then state what the
subject does, with a specific. "Say goodbye to hidden fees" → "The listed
price is the complete price; the invoice adds nothing."

A booster word carries the same defect in one word: it offers praise where
a fact belongs. Replace it with the fact it covered. The full catalog
lives in `## Marketing register`.

## The deletion test

One test decides every negative, comparative, and absence clause, in
marketing copy and technical prose alike.

Delete the clause and read what remains. If the sentence loses a
requirement, a limitation, a causal fact, a selection rule, a
compatibility boundary, a safety condition, or any other information the
reader acts on, the clause carried content and it stays. If the sentence
carries the same information, the clause was rhetorical: rewrite it as a
direct statement of what the subject is or does.

Clauses that carry content and stay:

- "Prices do not include ocean freight."
- "Delivery takes no more than 21 days within the EU."
- "General information, not a substitute for legal advice."

Clauses that were rhetorical, with the direct form beside them:

- "Freshness confirmed by query, not by the node count." → "The freshness
  query returned the current result."
- "A second index would add duplication without adding information." →
  "The existing index already represents that commit."
- "The gate wasn't slow — it finished." → "The gate finished in 1.2 s."

`references/patterns.md` carries a bad → good rewrite for every category.

## Positive forms

Where an established positive term carries the constraint unambiguously,
write the term: **read-only**, **immutable**, **append-only**,
**idempotent**, **dry run**, **single-writer**, **fixed-width**,
**allowlist**, **constant-time**, **exit code 2**.

- "the hook does not write" → "the hook is read-only"
- "the value does not change after construction" → "the value is
  immutable"
- "runs the migration but writes nothing" → "runs the migration as a dry
  run"

Where no such term exists and the exclusion defines a required limit, a
prohibited side effect, a compatibility boundary, or a safety condition,
write the exclusion plainly and keep it.

## Scope and precedence

- **Scope.** Every stretch of prose written for a person to read: chat
  replies, commit bodies, pull request descriptions, code comments,
  documentation, plans, reports, and all user-facing copy.
- **Verbatim source material.** Exact text supplied by the user or
  returned by an external system — a pasted error, an existing file's
  contents, tool output, a quoted third-party document — is reproduced
  character for character. Reproduce it as given, and write the prose
  around it under these rules.
- **Governed everywhere else.** Prose you write stays governed wherever
  it sits: inside quotation marks, Markdown fences, code comments, commit
  bodies, and command examples. A fence is a formatting choice, and it
  grants no exemption.
- **User precedence.** If the user explicitly directs you to write a
  banned pattern, comply with their instruction and note the specific
  rule it conflicts with in one sentence. User instructions outrank this
  skill; your own convenience does not.

## Sourcing

An unnamed authority offers praise where a checkable fact belongs, which
is the vagueness twin of contrast. Name the source, the figure, and the
date, or state the measurable claim.

- "Experts agree Acme leads the market." → "Acme holds 34% of the
  segment, per Gartner's 2025 market report."
- "Studies show users prefer simple forms." → "In Acme's May 2026 survey
  of 1,200 users, 78% completed the three-field form."

Editorializing participles carry the same defect: ", highlighting our
commitment to quality", ", underscoring its value". Delete the tail and
state the fact it gestured at. An unsourced claim in a status report costs
the reader the same check it costs on a landing page.

## Marketing register

These rules govern marketing and web copy. The core rules above govern
every register.

**Hype vocabulary.** Replace the word with the fact it was hiding:
unleash, unlock, unparalleled, unwavering, unmatched, unprecedented,
unsung, unrivaled, elevate, seamless, empower, revolutionize,
game-changing, delve, supercharge, turbocharge, next-level, cutting-edge,
state-of-the-art, best-in-class, world-class, transformative, effortless,
one-stop shop, synergy; figurative "landscape" and "journey"; and
"harness", "next-gen", "revolutionary" for the same reason.

Register test for unlisted synonyms: if the word could appear unchanged in
a perfume ad and a SaaS deck, it is hype. Replace it.

- "seamless ordering" → "three-step ordering: pick, pay, track"
- "unmatched support" → "one named rep per account, reachable within
  business hours"

**The era-ending marketing form.** "Say goodbye to hidden fees." → "The
listed price is the complete price; the invoice adds nothing."

Sections 10 and 3 of `references/patterns.md` carry the full tables.

## Loophole closures — read these before claiming compliance

Agents under output pressure rationalize around style rules. Each
rationalization below is pre-emptively rejected:

- **"The banned string doesn't appear."** The rule bans the *move*, not
  the string. "Most vendors bury their fees. Acme prints them." is the
  reversal pattern split across two sentences — still banned. A contrast
  spread across sentences, paragraphs, or a headline/subhead pair counts.
- **"It's in a quote/testimonial."** Banned patterns inside invented
  testimonials, hypothetical customer quotes, taglines, or dialogue are
  violations. Quotation marks do not launder rhetoric. (Verbatim quotes
  from real, named customers supplied by the user are the only exception,
  under the verbatim-source rule in `## Scope and precedence`.)
- **"It's a headline/CTA/meta tag, not body copy."** Scope is ALL
  user-facing copy: headlines, subheads, CTAs, button labels, meta and OG
  descriptions, alt text, email subjects, social posts, ad variants,
  brochure text, and every locale file.
- **"It's a different language."** The rules apply conceptually in every
  locale. 不仅仅是 / не просто / no es solo / pas seulement / nicht nur /
  単なる〜ではない / 단순한 ~이 아니다 / ليس مجرد are all "not just".
  Translate the grounded English, never re-introduce contrast in
  translation.
- **"This negation is factual."** Apply `## The deletion test`. It decides
  every negative, comparative, and absence clause, and it asks what the
  reader loses when the clause goes.
- **"A synonym isn't on the list."** The hype list bans a register, not
  ten words. Apply the register test in `## Marketing register`. When
  unsure, replace the word with the specific fact it was hiding.
- **"The linter passed, so it's fine."** The linter is a floor, not a
  ceiling. Novel phrasings of the banned move that evade regex are still
  violations; you are the second detection layer.
- **"I'll adjust the linter/config."** Never. See integrity rules.

## Workflow

1. Draft the copy following the positive rule: subject + verb + specific.
2. Self-scan against the disguise categories above, including
   cross-sentence contrast and non-English text.
3. Save the draft (or pipe it) and run the gate:

   ```
   python3 <skill-path>/scripts/copy_lint.py file1.md locales/en.json ...
   cat draft.md | python3 <skill-path>/scripts/copy_lint.py --stdin
   ```

4. Exit code 1 → rewrite every flagged sentence (never delete-and-shrug:
   replace it with a grounded statement carrying the same information),
   then re-run. Repeat until exit code 0.
5. Review WARN lines manually: "no longer", "journey", "landscape",
   "What if", bare "rather than", and ", not a/an/your X" are allowed
   only in factual, non-rhetorical use ("What if my order arrives
   damaged?" as an FAQ heading; "not a substitute for legal advice" as a
   required disclaimer; "billed monthly rather than per seat" as a
   billing fact). Apply `## The deletion test` to each.
6. Only present copy to the user after a PASS. State in your summary that
   the copy passed `copy_lint.py`.

## Integrity rules (non-negotiable)

- Never edit, wrap, subclass, monkey-patch, or replace `copy_lint.py`,
  its pattern list, or its exit-code behavior.
- Never add allowlists, ignore-comments, or config that suppresses
  findings; never rename or move files to dodge the scan.
- Never mark the task complete while the linter reports errors.
- User instructions outrank this skill. `## Scope and precedence` holds
  the rule and what to do when one conflicts; your own convenience
  outranks nothing.

## References

- `references/patterns.md` — full pattern catalog with a bad → good
  rewrite for every category. Read it when a flagged sentence is hard to
  rewrite, or before writing copy in zh/ru/es/ar/fr/de/ja/ko.
- `tests/bad-samples.md` and `tests/good-samples.md` — after any change
  to the linter, `copy_lint.py tests/bad-samples.md` must FAIL and
  `copy_lint.py tests/good-samples.md` must PASS.
- `references/setup.md` — wiring the skill into Claude Code (CLAUDE.md /
  hooks) and Codex (AGENTS.md) so both agents load it and run the gate.
  `### Profile lifecycle` there is the one description of how the profile
  preference, the session policy, the turn reminder, and the effective
  policy relate.
