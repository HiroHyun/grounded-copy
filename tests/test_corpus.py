#!/usr/bin/env python3
"""What skills/grounded-copy/tests/bad-samples.md covers.

CONTRIBUTING asks every new pattern to arrive with a line in the corpus that
catches it. A rule with no line is a rule nobody has seen fire, which is how a
regex that matches nothing survives review.

Scope bound: this asserts coverage for the per-locale rules only. Some English
rules carry no corpus line today, so the same assertion over the whole rule set
would ship red. Widening it means adding those lines first.
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


def linter():
    # The linter now sits inside the payload the Codex builder mirrors, and a
    # .pyc written beside it would ship. The builder filters __pycache__; this
    # keeps the file from appearing in the first place.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    import copy_lint

    return copy_lint


def locale_rules():
    copy_lint = linter()
    return [n for n, _ in copy_lint.PATTERNS + copy_lint.OPENERS
            if LOCALE_RULE.match(n)]


def reported(text):
    """The rule names the linter reports for `text`, scanned in process."""
    return {name for _, name, _ in linter().scan_text(text)}


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


class ReversalGapTests(unittest.TestCase):
    """A reversal reports with words between its two halves.

    `not-just` once needed "not" and "just" adjacent, so "I'm not the author,
    just a user." reported nothing. Each REPORTS row pins one such shape. A
    row marked shipped holds the form its rule matched before the rule
    widened, so a widening that drops the old match fails here.
    """

    REPORTS = (
        ("not-just", "Acme is not just a tool."),  # shipped
        ("not-just", "I'm not the author, just a user."),
        ("not-just", "I'm not the plugin's author, I just use it."),
        ("not-just", "This isn't magic, just math."),
        ("not-just", "I'm not the author. Just a user."),
        ("not-just", "I'm not the author - just a user."),
        ("not-just", "Acme is not really just a tool."),
        ("no-x-just-y", "No hidden fees, just simple pricing."),
        ("no-x-just-y", "No fluff. Just facts."),
        ("no-x-just-y", "Nothing fancy, just a script."),
        ("not-x-its-y", "Acme isn't a tool, it's a platform."),
        ("not-x-its-y", "- That's not a bug, that's a feature."),
        ("not-x-its-y", "This isn't a bug. It's a feature."),
        ("not-x-its-y", "The problem is not speed. The problem is trust."),
        ("dash-not-contrast", "Acme is a partner — not a vendor."),  # shipped
        ("dash-not-contrast", "Acme is a partner - not a vendor."),
        ("dash-not-contrast", "Acme is a partner -- not a vendor."),
        ("negated-copula-dash",
         "Acme isn't complicated — it books the job in one tap."),  # shipped
        ("negated-copula-dash",
         "Acme isn't complicated - it books the job in one tap."),
        ("negated-copula-dash", "I'm not the author — I use the plugin."),
        ("negated-copula-dash", "That's not a bug -- it's a feature."),
        ("doesnt-just", "Acme doesn't just store files."),  # shipped
        ("doesnt-just", "You can't just store files."),
        ("doesnt-just", "Acme never just stores files."),
        ("doesnt-just", "Acme cannot simply store files."),
        ("more-than-just", "Acme is more than just a tool."),  # shipped
        ("more-than-just", "Acme does more than simply store files."),
        ("is-more-than-a", "Acme is more than a tool."),  # shipped
        ("is-more-than-a", "Acme was more than a tool."),
        ("is-more-than-a", "The tracker's more than a list."),
        ("is-more-than-a", "Acme is so much more than a tool."),
        ("isnt-about", "Design isn't about decoration."),  # shipped
        ("isnt-about", "The talk wasn't about the money."),
        ("isnt-about", "Design was never about decoration."),
        ("isnt-about", "This isn't really about speed."),
        ("not-x-but-y", "Acme is not a vendor but a partner."),  # shipped
        ("not-x-but-y", "The result wasn't a failure but a delay."),
        ("not-x-but-y", "The tool is not my work but my friend's."),
        ("not-x-but-y",
         "We chose it not because it is cheap but because it is fast."),
        ("not-x-but-y", "The error was not in the config but in the loader."),
        ("less-a-x-than", "Acme is less a gym than a coaching program."),  # shipped
        ("less-a-x-than", "It is less about speed and more about trust."),
        ("less-a-x-than", "Acme is not so much a gym as a coaching program."),
        ("less-a-x-than", "The change is less a rewrite and more a cleanup."),
        ("not-your-average", "Not your average newsletter."),  # shipped
        ("not-your-average", "This is no ordinary newsletter."),
        ("not-your-average", "Not another todo app."),
        ("unlike-others",
         "Unlike traditional agencies, we publish our rates."),  # shipped
        ("unlike-others", "Unlike competitors, Acme publishes its rates."),
        ("while-others", "While others hide their fees, Acme lists them."),  # shipped
        ("while-others", "Whereas most tools hide rates, Acme publishes them."),
        ("while-others", "Where others see noise, Acme sees signal."),
    )

    # Ordinary sentences that share a surface form with a row above.
    KEPT = (
        "Do not edit the file, just run the script.",
        "Not yet, only the first step is done.",
        "No fix was needed, just a restart.",
        "No password is stored, only a hash.",
        "It has no fees, just a flat rate.",
        "If the file is not there, it is created on the first run.",
        "- When the flag is not set, it is ignored.",
        "Note that if the name is not given, it is read from the config.",
        "The worker is not running. It is scheduled for 09:00.",
        "  - not supported on Windows",
        "Set the offset to 3 - 1.",
        "Try not to restart the server, but if you must, drain it first.",
        "Memory use is less of an issue than CPU time.",
        "I have not so much as looked at it.",
        "Unlike the v1 API, v2 paginates by cursor.",
        "It runs in places where other modules might be loaded.",
    )

    def test_each_shape_reports_its_rule(self):
        for rule, sentence in self.REPORTS:
            with self.subTest(sentence=sentence):
                self.assertIn(rule, reported(sentence))

    def test_kept_sentences_report_nothing(self):
        for sentence in self.KEPT:
            with self.subTest(sentence=sentence):
                self.assertEqual(reported(sentence), set())


if __name__ == "__main__":
    unittest.main()
