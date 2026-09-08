#!/usr/bin/env python3
"""What skills/grounded-copy/tests/bad-samples.md covers.

CONTRIBUTING asks every new pattern to arrive with a line in the corpus that
catches it. A rule with no line is a rule nobody has seen fire, which is how a
regex that matches nothing survives review.

Scope bound: this asserts coverage for the per-locale rules only. 38 of the 58
English rules carry no corpus line today, so the same assertion over the whole
rule set would ship red. Widening it means adding those lines first.
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "grounded-copy"
LINTER = str(SKILL_DIR / "scripts" / "copy_lint.py")
CORPUS = str(SKILL_DIR / "tests" / "bad-samples.md")

LOCALE_RULE = re.compile(r"^(?:zh|ru|es|ar|fr|de|ja|ko)-")
REPORTED = re.compile(r"^\S+ ([a-z0-9-]+):", re.M)


def locale_rules():
    # The linter now sits inside the payload the Codex builder mirrors, and a
    # .pyc written beside it would ship. The builder filters __pycache__; this
    # keeps the file from appearing in the first place.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    import copy_lint

    return [n for n, _ in copy_lint.PATTERNS + copy_lint.OPENERS
            if LOCALE_RULE.match(n)]


def run_linter(path, env=None):
    return subprocess.run(
        [sys.executable, LINTER, path],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )


class OutputEncodingTests(unittest.TestCase):
    """The linter reports UTF-8 whatever the platform hands it.

    Measured on windows-latest, Python 3.12: the reader thread died with
    "UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97", 0x97 being the
    cp1252 em dash out of the FAIL line, and the caller read stdout as None.
    Eight of the nine covered languages are non-ASCII, so a locale file is the
    normal case for this path.
    """

    def test_findings_decode_as_utf8_under_a_legacy_code_page(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        result = run_linter(CORPUS, env=env)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("copy_lint:", result.stdout)
        for snippet in ("不仅仅是", "단순한 도구가 아닙니다", "ليس مجرد"):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, result.stdout)


class LocaleCoverageTests(unittest.TestCase):
    def setUp(self):
        result = run_linter(CORPUS)
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
