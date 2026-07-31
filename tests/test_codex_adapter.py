#!/usr/bin/env python3
"""Interface tests for the OpenAI/Codex adapter.

The adapter reuses the canonical skill, references, linter, and sample corpora
by copy, so the reuse claim needs a test that fails when a copy drifts. These
cases assert byte identity against the sources, the MIT notice that has to
travel with a redistributed package, the layout the Codex plugin specification
asks for, and the scope the adapter claims: a skill and a linter, with no hooks
and no commands.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = str(REPO_ROOT / "scripts" / "build_codex_adapter.py")
ADAPTER = REPO_ROOT / "adapters" / "codex" / "grounded-copy"
SKILL_DIR = ADAPTER / "skills" / "grounded-copy"

# Source, then its place in the adapter.
COPIES = (
    ("SKILL.md", SKILL_DIR / "SKILL.md"),
    ("references/patterns.md", SKILL_DIR / "references" / "patterns.md"),
    ("references/setup.md", SKILL_DIR / "references" / "setup.md"),
    ("scripts/copy_lint.py", SKILL_DIR / "scripts" / "copy_lint.py"),
    ("tests/bad-samples.md", SKILL_DIR / "tests" / "bad-samples.md"),
    ("tests/good-samples.md", SKILL_DIR / "tests" / "good-samples.md"),
    ("LICENSE", ADAPTER / "LICENSE"),
)


class CodexAdapterTests(unittest.TestCase):
    def test_every_copied_file_matches_its_source(self):
        for source, destination in COPIES:
            with self.subTest(source=source):
                self.assertTrue(destination.exists(), "missing: " + source)
                self.assertEqual(
                    (REPO_ROOT / source).read_bytes(),
                    destination.read_bytes(),
                    "adapter copy drifted from " + source,
                )

    def test_the_check_mode_passes_against_the_committed_adapter(self):
        result = subprocess.run(
            [sys.executable, BUILDER, "--check"],
            cwd=str(REPO_ROOT), text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_check_mode_reports_a_modified_copy(self):
        """A red-capable case: the check has to fail on real drift."""
        target = SKILL_DIR / "SKILL.md"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\ndrift\n")
            result = subprocess.run(
                [sys.executable, BUILDER, "--check"],
                cwd=str(REPO_ROOT), text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("differs", result.stdout)
            self.assertIn("SKILL.md", result.stdout)
        finally:
            target.write_bytes(original)

    def test_the_manifest_declares_the_required_fields(self):
        manifest = json.loads(
            (ADAPTER / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "grounded-copy")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["skills"], "./skills/")
        for field in ("version", "description", "repository", "homepage"):
            self.assertIn(field, manifest)

    def test_the_skill_sits_where_the_specification_asks(self):
        self.assertTrue((SKILL_DIR / "SKILL.md").exists())
        header = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")[:400]
        self.assertIn("name: grounded-copy", header)

    def test_the_mit_notice_travels_with_the_package(self):
        notice = (ADAPTER / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", notice)
        self.assertIn("Permission is hereby granted", notice)

    def test_the_adapter_ships_no_hooks_and_no_commands(self):
        for name in ("hooks", "commands", ".claude-plugin"):
            with self.subTest(directory=name):
                self.assertFalse(
                    (ADAPTER / name).exists(),
                    "the adapter claims a skills-only scope: " + name,
                )

    def test_the_linter_runs_from_the_adapter_path(self):
        linter = str(SKILL_DIR / "scripts" / "copy_lint.py")
        good = subprocess.run(
            [sys.executable, linter, str(SKILL_DIR / "tests" / "good-samples.md")],
            cwd=str(REPO_ROOT), text=True, capture_output=True,
        )
        self.assertEqual(good.returncode, 0, good.stdout)
        bad = subprocess.run(
            [sys.executable, linter, str(SKILL_DIR / "tests" / "bad-samples.md")],
            cwd=str(REPO_ROOT), text=True, capture_output=True,
        )
        self.assertEqual(bad.returncode, 1, bad.stdout)


if __name__ == "__main__":
    unittest.main()
