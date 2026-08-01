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
import subprocess
import sys
import tempfile
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
        """A red-capable case: the check has to fail on real drift.

        It runs against a temporary mirror, so every write stays inside the
        temporary directory and a kill mid-test leaves no tracked file
        modified. The builder takes its root from its own `__file__`, so
        copying the builder into the mirror is what redirects it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source, _ in COPIES:
                destination = root / source
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((REPO_ROOT / source).read_bytes())
            builder = root / "scripts" / "build_codex_adapter.py"
            builder.write_bytes(Path(BUILDER).read_bytes())

            built = subprocess.run(
                [sys.executable, str(builder)],
                cwd=tmp, text=True, capture_output=True,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

            clean = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=tmp, text=True, capture_output=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout)

            copy = root / "adapters" / "codex" / "grounded-copy" / \
                "skills" / "grounded-copy" / "SKILL.md"
            copy.write_bytes(copy.read_bytes() + b"\ndrift\n")

            drifted = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=tmp, text=True, capture_output=True,
            )
            self.assertEqual(drifted.returncode, 1, drifted.stdout)
            self.assertIn("differs", drifted.stdout)
            self.assertIn("SKILL.md", drifted.stdout)

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

    def test_every_catalog_entry_and_manifest_declares_mit(self):
        """`README.md` claims both manifests and both catalog entries say MIT.

        The adapter manifest is covered above; these are the other three, so the
        README sentence is a tested claim rather than a maintained one.
        """
        for path in (
            REPO_ROOT / ".claude-plugin" / "marketplace.json",
            REPO_ROOT / ".agents" / "plugins" / "marketplace.json",
        ):
            with self.subTest(catalog=path.parent.name):
                catalog = json.loads(path.read_text(encoding="utf-8"))
                entries = [
                    p for p in catalog["plugins"] if p["name"] == "grounded-copy"
                ]
                self.assertEqual(len(entries), 1, "one entry per catalog")
                self.assertEqual(entries[0].get("license"), "MIT")
        manifest = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["license"], "MIT")

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
