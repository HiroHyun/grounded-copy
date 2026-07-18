# Contributing

## Adding a pattern

1. **Evidence.** Quote at least one real-world sighting of the pattern in
   published marketing copy (link or screenshot in the PR description).
2. **Failing test.** Add a line to `tests/bad-samples.md` that only your
   new pattern catches.
3. **False-positive check.** Search for factual uses of the same string.
   If they exist ("no more than 21 days", "mehr als ein Jahr"), narrow
   the regex or downgrade to WARN, and add a line to
   `tests/good-samples.md` proving the factual use passes.
4. **Catalog entry.** Add a bad → good row to `references/patterns.md`.
   The good cell must itself pass the linter.

## Adding a language

Follow the same four steps per pattern. Locale PRs need a note on which
constructions carry common factual uses in that language — those become
WARN, and the deletion test in `references/patterns.md` governs them.

## Ground rules

- `scripts/copy_lint.py` stays zero-dependency Python 3 stdlib.
- Changes to the linter and to `tests/` ship in the same PR; CI runs the
  self-test on both corpora.
- One pattern or one language per PR.
