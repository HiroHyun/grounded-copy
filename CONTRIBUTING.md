# Contributing

Choose one pattern or one language for each pull request. Explain the writing problem and show the sentence your change should catch.

## Add a pattern

1. Link to a published example, or attach a screenshot in the pull request.
2. Add a sentence to `skills/grounded-copy/tests/bad-samples.md` that your new rule catches.
3. Look for ordinary factual uses of the same wording. Describe any matches that readers might need to keep.
4. Add a draft and rewrite to `skills/grounded-copy/references/patterns.md`. Check that the rewrite passes.

Each rule reports every match. If a task needs wording that a rule rejects, the writer can use the `off` profile. A manual checker run still reports that wording.

## Add a language

Follow the same steps for each new rule. Explain whether it matches a list of phrases or a sentence pattern. Include examples of factual wording that it also matches. Update the language summary in both READMEs if the coverage changes.

## Edit documentation

Write for someone trying to use the tool. Explain the task, give the command, and describe what happens next. Use verified facts. Label invented examples so readers can distinguish them from product claims.

Run the copy checker on changed prose. The README comparison tables and pattern guide quote rejected wording on purpose. Check each finding in those files, then run:

```bash
python3 scripts/check_citations.py
```

If you changed a quoted example, record the new findings with `python3 scripts/check_citations.py --write`. Review the diff in `tests/citations-baseline.txt`. Findings in ordinary prose need a rewrite. Keep the checker and its rules intact.

After a skill or reference edit, rebuild the Codex package:

```bash
python3 scripts/build_codex_adapter.py
python3 scripts/build_codex_adapter.py --check
```

Commit the generated files too. For a `SKILL.md` edit, also run `python3 hooks/grounded_activate.py --self-test`; the hooks read some headings and bullet labels directly.

## Change the checker

The checker uses the Python 3 standard library. Keep regular expressions bounded and preserve the exit codes: `0` for a pass, `1` for findings, and `2` for command or file errors.

Submit checker changes with the relevant sample-file changes. The bad samples must return `1`; the good samples must return `0`. Run the existing tests that cover the change. Add tests when they verify new behavior or a bug fix.

The sample files are in `skills/grounded-copy/tests/`. The Python test suites are in the root `tests/` directory. The [setup guide](skills/grounded-copy/references/setup.md) explains the package layout and CI checks.
