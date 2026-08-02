#!/usr/bin/env python3
"""What tests/bad-samples.md covers.

CONTRIBUTING asks every new pattern to arrive with a line in the corpus that
catches it. A rule with no line is a rule nobody has seen fire, which is how a
regex that matches nothing survives review.

Scope bound: this asserts coverage for the per-locale rules only. 38 of the 57
English rules carry no corpus line today, so the same assertion over the whole
rule set would ship red. Widening it means adding those lines first.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER = str(REPO_ROOT / "scripts" / "copy_lint.py")
CORPUS = str(REPO_ROOT / "tests" / "bad-samples.md")

LOCALE_RULE = re.compile(r"^(?:zh|ru|es|ar|fr|de|ja|ko)-")
REPORTED = re.compile(r"^\S+ ([a-z0-9-]+):", re.M)


def locale_rules():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import copy_lint

    return [n for n, _ in copy_lint.PATTERNS + copy_lint.OPENERS
            if LOCALE_RULE.match(n)]


class LocaleCoverageTests(unittest.TestCase):
    def setUp(self):
        result = subprocess.run(
            [sys.executable, LINTER, CORPUS],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.reported = set(REPORTED.findall(result.stdout))

    def test_every_locale_rule_reports_a_corpus_line(self):
        rules = locale_rules()
        self.assertEqual(len(rules), 9, "the locale rule set changed size")
        for rule in rules:
            with self.subTest(rule=rule):
                self.assertIn(
                    rule, self.reported,
                    "%s fires on no line in bad-samples.md" % rule,
                )

    def test_every_language_the_readme_tiers_has_a_rule(self):
        """The published tier table and the rule set name the same languages."""
        languages = {r.split("-")[0] for r in locale_rules()}
        self.assertEqual(
            languages, {"zh", "ru", "es", "ar", "fr", "de", "ja", "ko"},
            "README publishes a tier per language; the rule set moved",
        )


if __name__ == "__main__":
    unittest.main()
