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

The banned move is **defining anything through negation or contrast** —
telling the reader what the subject is *not*, what *others* do worse, or
what *era* has ended, instead of what the subject does. Every pattern below
is the same move in a different costume. Do not write any of them, and do
not invent a new costume for the same move:

1. **Negated intensifiers:** "not just/only/merely/simply", "doesn't just",
   "more than just", "far from just/being", "rather than simply",
   "instead of just".
2. **Reversal reveals:** "It's not X, it's Y", "isn't about X, it's about
   Y", "—not X, but Y", "not your average X", "less a catalog than a
   trade desk". Includes the appositive form "X, not Y" ("a partner,
   not a vendor") and the negated-setup dash "isn't/wasn't X — it Y"
   ("the gate wasn't slow — it finished").
3. **Era-ending:** "no longer", "gone are the days", "the days of X are
   over", "say goodbye/hello", "no more X", "never again", "welcome to a
   new era".
4. **Competitor put-downs:** "unlike traditional/most/other X",
   "while others/most X, we Y".
5. **Transcendence verbs:** "goes beyond", "beyond just", "redefines",
   "reimagines", "reinvents".
6. **Absence-as-benefit:** "without the hassle/hidden fees/middlemen",
   "zero guesswork/compromises", "hassle-free", "frictionless".
7. **Rhetorical bait:** "The result?", "The best part?", "Think again",
   "Ever wondered", "Tired of", "What if", "Imagine", "Picture this",
   "In a world where", "Stop Xing", "Forget X", "Don't just X".
8. **Collision framing:** "where X meets Y".
9. **Corporate throat-clearing:** "At [Company], we...".
10. **Hype vocabulary:** unleash, unlock, unparalleled, unwavering,
    unmatched, unprecedented, unsung, unrivaled, elevate, seamless,
    empower, revolutionize, game-changing, delve, supercharge,
    turbocharge, next-level, cutting-edge, state-of-the-art,
    best-in-class, world-class, transformative, effortless, one-stop
    shop, synergy; figurative "landscape" and "journey".

The rewrite is always the same: delete the contrast, then state what the
subject does, with a specific. "Say goodbye to hidden fees" → "The listed
price is the complete price; the invoice adds nothing."

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
  from real, named customers supplied by the user are the only exception.)
- **"It's a headline/CTA/meta tag, not body copy."** Scope is ALL
  user-facing copy: headlines, subheads, CTAs, button labels, meta and OG
  descriptions, alt text, email subjects, social posts, ad variants,
  brochure text, and every locale file.
- **"It's a different language."** The rules apply conceptually in every
  locale. 不仅仅是 / не просто / no es solo / pas seulement / nicht nur /
  単なる〜ではない / 단순한 ~이 아니다 / ليس مجرد are all "not just".
  Translate the grounded English, never re-introduce contrast in
  translation.
- **"This negation is factual."** Apply this test: if the negation states
  a limitation, exclusion, or requirement that a buyer needs to know
  ("Prices do not include ocean freight", "Machinery is not offered"), it
  is allowed. If deleting the negative clause would make the sentence
  *less* flattering, the negation existed to set up praise — banned.
- **"A synonym isn't on the list."** The hype list bans a register, not
  ten words. "Harness", "turbocharged", "next-gen", "revolutionary" fail
  for the same reason "unleash" does. When unsure, replace the word with
  the specific fact it was hiding.
- **"The linter passed, so it's fine."** The linter is a floor, not a
  ceiling. Novel phrasings of the banned move that evade regex are still
  violations; you are the second detection layer.
- **"I'll adjust the linter/config."** Never. See integrity rules.

## Workflow

1. Draft the copy following the positive rule: subject + verb + specific.
2. Self-scan against the ten disguise categories above, including
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
   billing fact). Apply the deletion test from
   `references/patterns.md` to each.
6. Only present copy to the user after a PASS. State in your summary that
   the copy passed `copy_lint.py`.

## Integrity rules (non-negotiable)

- Never edit, wrap, subclass, monkey-patch, or replace `copy_lint.py`,
  its pattern list, or its exit-code behavior.
- Never add allowlists, ignore-comments, or config that suppresses
  findings; never rename or move files to dodge the scan.
- Never mark the task complete while the linter reports errors.
- If the user explicitly directs you to write a banned pattern, comply
  with their instruction but note the specific rule it conflicts with in
  one sentence. User instructions outrank this skill; your own
  convenience does not.

## References

- `references/patterns.md` — full pattern catalog with a bad → good
  rewrite for every category. Read it when a flagged sentence is hard to
  rewrite, or before writing copy in zh/ru/es/ar/fr/de/ja/ko.
- `tests/bad-samples.md` and `tests/good-samples.md` — after any change
  to the linter, `copy_lint.py tests/bad-samples.md` must FAIL and
  `copy_lint.py tests/good-samples.md` must PASS.
- `references/setup.md` — wiring the skill into Claude Code (CLAUDE.md /
  hooks) and Codex (AGENTS.md) so both agents load it and run the gate.
