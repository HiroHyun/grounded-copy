# Contributing

## Adding a pattern

1. **Evidence.** Quote at least one real-world sighting of the pattern in
   published marketing copy (link or screenshot in the PR description).
2. **Failing test.** Add a line to `tests/bad-samples.md` that only your
   new pattern catches.
3. **Over-match note.** Every rule blocks, and no rule carries an
   exception. Search for factual uses of the same string and name them in
   the PR description ("no more than 21 days", "mehr als ein Jahr", the
   `-ing` nouns `without-gerund` reads as gerunds), so a reader knows what
   else the regex reports. Copy needing one of those forms is written with
   the profile off, which `README.md` documents.
4. **Catalog entry.** Add a bad → good row to `references/patterns.md`.
   The good cell must itself pass the linter.

## Adding a language

Follow the same four steps per pattern. A locale PR names the
constructions that also carry factual uses in that language; they block
alongside the rest, and the over-match note records them.

State which tier the rule reaches: a bounded gap between the negation and
the assertion, which reports phrasings outside the list, or a trigger list,
which reports the listed phrases. `## Nine languages` in `README.md`
publishes the tier per language, so a PR that changes one updates it.

## Ground rules

- `scripts/copy_lint.py` stays zero-dependency Python 3 stdlib. Each line
  runs the 53 whole-line patterns; each sentence in it runs the 13 anchored
  openers. Every nested quantifier stays bounded, so scan time holds linear
  in the length of the line.
- One severity and the 0/1/2 exit contract: 0 clean, 1 findings, 2 usage
  or IO error.
- Changes to the linter and to `tests/` ship in the same PR; CI runs the
  self-test on both corpora.
- One pattern or one language per PR.
