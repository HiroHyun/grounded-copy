#!/usr/bin/env python3
"""Interface tests for the OpenAI/Codex adapter.

The adapter reuses canonical skill and runtime files by copy, so the reuse
claim needs a test that fails when a copy drifts. These cases cover the Codex
plugin layout, lifecycle hooks, profile controller, generated inventory, and
the MIT notice that travels with a redistributed package.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = str(REPO_ROOT / "scripts" / "build_codex_adapter.py")
ADAPTER = REPO_ROOT / "adapters" / "codex" / "grounded-copy"
SKILL_DIR = ADAPTER / "skills" / "grounded-copy"
CODEX_ACTIVATE = ADAPTER / "hooks" / "grounded_activate.py"
CODEX_TRACKER = ADAPTER / "hooks" / "grounded_tracker.py"

# Source, then its place in the adapter.
COPIES = (
    ("SKILL.md", SKILL_DIR / "SKILL.md"),
    ("references/patterns.md", SKILL_DIR / "references" / "patterns.md"),
    ("references/setup.md", SKILL_DIR / "references" / "setup.md"),
    ("scripts/copy_lint.py", SKILL_DIR / "scripts" / "copy_lint.py"),
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
            root = Path(tmp) / "mirror"
            shutil.copytree(REPO_ROOT, root)
            builder = root / "scripts" / "build_codex_adapter.py"

            built = subprocess.run(
                [sys.executable, str(builder)],
                cwd=str(root), text=True, capture_output=True,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

            clean = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=str(root), text=True, capture_output=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout)

            copy = root / "adapters" / "codex" / "grounded-copy" / \
                "skills" / "grounded-copy" / "SKILL.md"
            copy.write_bytes(copy.read_bytes() + b"\ndrift\n")

            drifted = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=str(root), text=True, capture_output=True,
            )
            self.assertEqual(drifted.returncode, 1, drifted.stdout)
            self.assertIn("differs", drifted.stdout)
            self.assertIn("SKILL.md", drifted.stdout)

    def test_check_mode_reports_missing_and_unexpected_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "mirror"
            shutil.copytree(REPO_ROOT, root)
            builder = root / "scripts" / "build_codex_adapter.py"
            built = subprocess.run([sys.executable, str(builder)], cwd=root,
                                   text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            generated = root / "adapters" / "codex" / "grounded-copy"
            missing = generated / "hooks" / "hooks.json"
            self.assertTrue(missing.exists(), str(missing))
            missing.unlink()
            extra = generated / "unexpected-generated-file.txt"
            extra.write_text("drift", encoding="utf-8")
            result = subprocess.run([sys.executable, str(builder), "--check"],
                                    cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("missing", result.stdout)
            self.assertIn("unexpected", result.stdout)

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

    def test_the_adapter_ships_hooks_and_no_claude_commands(self):
        for name in ("hooks",):
            with self.subTest(directory=name):
                self.assertTrue((ADAPTER / name).exists())
        for name in ("commands", ".claude-plugin"):
            with self.subTest(directory=name):
                self.assertFalse((ADAPTER / name).exists())

    def test_the_linter_runs_from_the_adapter_path(self):
        linter = str(SKILL_DIR / "scripts" / "copy_lint.py")
        good = subprocess.run(
            [sys.executable, linter, str(REPO_ROOT / "tests" / "good-samples.md")],
            cwd=str(REPO_ROOT), text=True, capture_output=True,
        )
        self.assertEqual(good.returncode, 0, good.stdout)
        bad = subprocess.run(
            [sys.executable, linter, str(REPO_ROOT / "tests" / "bad-samples.md")],
            cwd=str(REPO_ROOT), text=True, capture_output=True,
        )
        self.assertEqual(bad.returncode, 1, bad.stdout)

    def _hook(self, script, args=(), home=None, stdin="{}"):
        env = os.environ.copy()
        env.pop("CLAUDE_CONFIG_DIR", None)
        env.pop("PLUGIN_ROOT", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if home is not None:
            env["CODEX_HOME"] = str(home)
        return subprocess.run([sys.executable, str(script), *args],
                              cwd=str(REPO_ROOT), input=stdin,
                              text=True, capture_output=True, env=env)

    def test_codex_session_start_recovers_policy_after_compaction_and_off_is_silent(self):
        self.assertTrue(CODEX_ACTIVATE.exists())
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            startup = self._hook(CODEX_ACTIVATE, home=home,
                                 stdin='{"source":"startup"}')
            compact = self._hook(CODEX_ACTIVATE, home=home,
                                 stdin='{"source":"compact"}')
            self.assertEqual(startup.returncode, 0)
            self.assertEqual(startup.stdout, compact.stdout)
            self.assertIn("profile: chat", startup.stdout)
            set_off = self._hook(CODEX_TRACKER, ("--set", "off"), home=home)
            self.assertEqual(set_off.returncode, 0, set_off.stdout)
            silent = self._hook(CODEX_ACTIVATE, home=home)
            self.assertEqual(silent.returncode, 0)
            self.assertEqual(silent.stdout, "")

    def test_codex_user_prompt_submit_emits_context_json_and_off_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self._hook(CODEX_TRACKER, home=home, stdin='{"prompt":"hi"}')
            payload = json.loads(result.stdout)
            block = payload["hookSpecificOutput"]
            self.assertEqual(block["hookEventName"], "UserPromptSubmit")
            self.assertIn("GROUNDED PROSE (chat)", block["additionalContext"])
            self.assertEqual(self._hook(CODEX_TRACKER, ("--set", "off"), home=home).returncode, 0)
            self.assertEqual(self._hook(CODEX_TRACKER, home=home).stdout, "")

    def test_codex_profile_controller_persists_transitions_and_rejects_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for profile in ("copy", "chat", "off"):
                result = self._hook(CODEX_TRACKER, ("--set", profile), home=home)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("governing profile: " + profile, result.stdout)
                self.assertEqual((home / "grounded-copy" / "profile").read_text().strip(), profile)
            rejected = self._hook(CODEX_TRACKER, ("--set", "bogus"), home=home)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("unknown profile", rejected.stdout)
            self.assertEqual((home / "grounded-copy" / "profile").read_text().strip(), "off")

    def test_codex_profile_failed_write_preserves_existing_preference(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertEqual(self._hook(CODEX_TRACKER, ("--set", "chat"), home=home).returncode, 0)
            profile = home / "grounded-copy" / "profile"
            blocked = home / "blocked-target"
            try:
                blocked.write_text("chat\n", encoding="utf-8")
                profile.unlink()
                profile.symlink_to(blocked)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            failed = self._hook(CODEX_TRACKER, ("--set", "copy"), home=home)
            self.assertEqual(failed.returncode, 1)
            self.assertIn("symlink", failed.stdout)
            self.assertEqual(blocked.read_text(encoding="utf-8").strip(), "chat")

    def test_codex_manifest_hooks_profile_skill_and_generated_inventory(self):
        manifest = json.loads((ADAPTER / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
        self.assertTrue((ADAPTER / "hooks" / "hooks.json").exists())
        profile_yaml = ADAPTER / "skills" / "grounded-profile" / "agents" / "openai.yaml"
        self.assertTrue(profile_yaml.exists())
        self.assertIn("allow_implicit_invocation: false", profile_yaml.read_text(encoding="utf-8"))
        hooks = json.loads((ADAPTER / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        rendered = json.dumps(hooks)
        self.assertIn("PLUGIN_ROOT", rendered)
        self.assertIn("commandWindows", rendered)
        self.assertFalse((SKILL_DIR / "tests").exists())


if __name__ == "__main__":
    unittest.main()
