---
name: grounded-copy
description: Enforces grounded, contrast-free prose. Every value proposition and every claim must state what the subject IS or DOES using concrete nouns, verbs, and specifics — never negation, contrast, or hype vocabulary. Use this skill whenever writing, editing, translating, reviewing, or localizing ANY user-facing copy — headlines, taglines, value propositions, landing pages, product descriptions, About pages, CTAs, button labels, meta/OG descriptions, alt text, email subjects and bodies, social posts, ad copy, brochures, or locale/i18n string files — and whenever writing any other prose a person reads — chat replies, commit bodies, pull request descriptions, code comments, documentation, plans, and reports. Use it even if the user does not mention style rules. Also use when the user says "on-brand", "our writing style", "no AI clichés", or asks to check copy.
---

# Grounded Copy

Copy describes things by what they ARE. Every value proposition is a direct
declarative statement built on concrete nouns, verbs, and specifics: the
feature, the number, the mechanism.

Grounded: "The tracker links every task to its pull request and posts a
status digest to Slack each morning." Every claim in it is checkable.

## The one banned move (and every disguise it wears)

The banned move is **defining the subject by placing it against
something** — against what it is *not*, against what *others* do worse,
against what *era* has ended. Grounded prose states what the subject is
and does, and attaches a specific.

Seven shapes, one rule. `references/patterns.md` carries the trigger
phrases for each shape and pairs every one with a rewrite.

1. **Placed against an alternative** — negated intensifiers, comparative
   clauses, transcendence verbs, absence framing.
2. **Reversal reveals** — a negated clause staging the assertion that
   follows it, joined by a comma, a dash, or a sentence break.
3. **Era-ending** — the old way declared finished, the past waved off.
4. **Competitor put-downs** — a rival class named as the foil.
5. **Rhetorical bait** — a question or command that stages its own answer.
6. **Collision framing** — two abstractions announced as meeting.
7. **Corporate throat-clearing** — a company preamble before the claim.

Write none of them, and invent no new costume. Every shape blocks with no
exception; copy that has to carry one — a legal disclaimer, regulatory
text, a translation of supplied source — is written with the profile off.
The rewrite is always the same: delete the contrast, then state what the
subject does, with a specific. A booster word does the same in one word,
offering praise where a fact belongs; `## Marketing register` holds that
catalog.

## Positive forms

Where an established positive term carries the constraint unambiguously,
write the term: **read-only**, **immutable**, **append-only**,
**idempotent**, **dry run**, **single-writer**, **fixed-width**,
**allowlist**, **constant-time**, **exit code 2**.

Where no term exists, state the constraint plainly as what holds.

## Scope and precedence

- **Scope.** Every stretch of prose written for a person to read: chat
  replies, commit bodies, pull request descriptions, code comments,
  documentation, plans, reports, and all user-facing copy.
- **Verbatim source material.** Text the user supplied or a system
  returned — a pasted error, a file's contents, tool output, a quoted
  document, a real named customer's words — is reproduced character for
  character; write the prose around it under these rules. An invented
  testimonial, a hypothetical quote, and a tagline are your own prose,
  and quotation marks launder nothing.
- **Governed everywhere else.** Your prose stays governed wherever it
  sits: inside quotation marks, Markdown fences, code comments, commit
  bodies, and command examples. A fence is a formatting choice and grants
  no exemption.
- **User precedence.** When the user directs you to write a banned
  pattern, comply and name the rule it conflicts with in one sentence.
  User instructions outrank this skill; your own convenience does not.

## Sourcing

An unnamed authority offers praise where a checkable fact belongs, which
is the vagueness twin of contrast. Name the source, the figure, and the
date, or state the measurable claim. An editorializing participle carries
the same defect: a clause hung off a comma that praises the subject where a
fact belongs. Delete the tail and state the fact it gestured at.
`## Vague attribution` in `references/patterns.md` has the forms.

## Marketing register

These rules govern marketing and web copy; the core rules above govern
every register. Scope here is every user-facing string: headlines,
subheads, CTAs, button labels, meta and OG descriptions, alt text, email
subjects, social posts, ad variants, brochure text, and locale files.

**Hype vocabulary.** Replace the word with the fact it was hiding. The
register runs to booster verbs, superlative adjectives, and figurative
nouns standing in for a specific. `## Hype vocabulary` in
`references/patterns.md` enumerates it and rewrites each entry.

Register test for an unlisted synonym: a word that could appear unchanged
in a perfume ad and a SaaS deck is hype. Replace it.

**Plain negation.** Keep a negation when it states a limit the reader acts
on — "does not support batching", "ships within the EU only". State every
other point positively.

## Loophole closures — read these before claiming compliance

Agents under output pressure rationalize around style rules. Each
rationalization below is pre-emptively rejected:

- **"The banned string doesn't appear."** The rule bans the *move*, not
  the string. "Most vendors bury their fees. Acme prints them." is the
  reversal pattern split across two sentences — still banned. A contrast
  spread across sentences, paragraphs, or a headline/subhead pair counts.
- **"It's a different language."** The rules apply conceptually in every
  locale, and every locale has its own stock phrase for the minimizing
  shape. `## Multilingual equivalents` in `references/patterns.md` lists
  the eight covered so far. Translate the grounded English, and keep
  contrast out of the translation.
- **"A synonym isn't on the list."** The hype list bans a whole register,
  and the register is wider than any ten words. Apply the register test in
  `## Marketing register`. When unsure, replace the word with the specific
  fact it was hiding.
- **"The linter passed, so it's fine."** The linter is a floor; holding
  the ceiling is your job. Novel phrasings of the banned move that evade
  regex are still violations; you are the second detection layer.
- **"I'll adjust the linter/config."** Never. See integrity rules.

## Workflow

1. Draft the copy following the positive rule: subject + verb + specific.
2. Self-scan against the seven shapes above, including cross-sentence
   contrast and non-English text.
3. Save the draft (or pipe it) and run the gate:

   ```
   python3 <skill-path>/scripts/copy_lint.py file1.md locales/en.json ...
   cat draft.md | python3 <skill-path>/scripts/copy_lint.py --stdin
   ```

4. Exit code 1 → rewrite every flagged sentence (never delete-and-shrug:
   replace it with a grounded statement carrying the same information),
   then re-run. Repeat until exit code 0.
5. Only present copy to the user after a PASS. State in your summary that
   the copy passed `copy_lint.py`.

## Integrity rules (non-negotiable)

- Never edit, wrap, subclass, monkey-patch, or replace `copy_lint.py`,
  its pattern list, or its exit-code behavior.
- Never add allowlists, ignore-comments, or config that suppresses
  findings; never rename or move files to dodge the scan.
- Never mark the task complete while the linter reports errors.

## References

- `references/patterns.md` — one section per shape with its full trigger
  list and a bad → good rewrite for every entry, plus the hype,
  attribution, positive-form, and multilingual tables. Read it when a
  rewrite is hard, or before writing copy in zh/ru/es/ar/fr/de/ja/ko.
- `tests/bad-samples.md` and `tests/good-samples.md` — the linter's own
  corpora, which sit beside this file in every install path that copies the
  skill directory. After a change to the linter,
  `copy_lint.py tests/bad-samples.md` must FAIL and
  `copy_lint.py tests/good-samples.md` must PASS.
- `references/setup.md` — wiring the skill into Claude Code (CLAUDE.md /
  hooks) and Codex (AGENTS.md) so both agents load it and run the gate.
  `### Profile lifecycle` there is the one description of how the profile
  preference, the session policy, the turn reminder, and the effective
  policy relate.
