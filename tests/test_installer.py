#!/usr/bin/env python3
"""Interface tests for the one-command installer.

`install.py` plans before it acts, so the plan is the testable surface:
detection and command construction are pure functions, and every case here
describes a machine and asserts the commands that machine would run. Nothing in
this file touches a real agent, a real PATH, or the network.

The published one-liner pipes a remote script into an interpreter, which makes
the argument surface part of the contract: `--dry-run` and `--list` have to
print and stop, and a rejected flag has to install nothing.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = str(REPO_ROOT / "install.py")

sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT))
import install  # noqa: E402


def machine(home, commands=(), agents=(), npx=True):
    """A detection result for a described machine, with no filesystem read."""
    for marker in agents:
        os.makedirs(os.path.join(home, marker), exist_ok=True)
    present = set(commands)
    if npx:
        present.add("npx")
    return install.detect(home=home, which=lambda name: name in present)


def commands_in(steps):
    return [argv for _label, argv in steps]


class DetectionTests(unittest.TestCase):
    def test_a_bare_machine_reports_nothing(self):
        with tempfile.TemporaryDirectory() as home:
            found = machine(home, npx=False)
            self.assertEqual(found["commands"], [])
            self.assertEqual(found["agents"], [])
            self.assertFalse(found["npx"])

    def test_an_agent_is_found_by_its_configuration_directory(self):
        with tempfile.TemporaryDirectory() as home:
            found = machine(home, agents=(".cursor", ".claude"))
            self.assertIn("cursor", found["agents"])
            self.assertIn("claude-code", found["agents"])
            self.assertNotIn("codex", found["agents"])

    def test_a_plugin_cli_is_found_on_the_path(self):
        with tempfile.TemporaryDirectory() as home:
            found = machine(home, commands=("claude",))
            self.assertEqual(found["commands"], ["claude"])


class PlanTests(unittest.TestCase):
    def options(self, **overrides):
        options = install.Options()
        for key, value in overrides.items():
            setattr(options, key, value)
        return options

    def test_a_bare_machine_plans_nothing(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(self.options(), machine(home, npx=False))
            self.assertEqual(steps, [])

    def test_claude_takes_the_marketplace_then_the_plugin(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(), machine(home, commands=("claude",), agents=(".claude",))
            )
            self.assertEqual(commands_in(steps), [
                ["claude", "plugin", "marketplace", "add", install.REPO],
                ["claude", "plugin", "install", "grounded-copy@hirohyun-plugins",
                 "-s", "user"],
            ])

    def test_codex_takes_its_own_verbs(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(), machine(home, commands=("codex",), agents=(".codex",))
            )
            self.assertEqual(commands_in(steps), [
                ["codex", "plugin", "marketplace", "add", install.REPO],
                ["codex", "plugin", "add", "grounded-copy@hirohyun-plugins"],
            ])

    def test_an_agent_with_a_plugin_cli_skips_the_portable_skill(self):
        """The plugin carries the skill plus the hooks, so one install covers it."""
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(),
                machine(home, commands=("claude",), agents=(".claude", ".cursor")),
            )
            rendered = " ".join(" ".join(argv) for argv in commands_in(steps))
            self.assertIn("-a cursor", rendered)
            self.assertNotIn("-a claude-code", rendered)

    def test_skills_only_routes_every_agent_through_the_skills_cli(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(skills_only=True),
                machine(home, commands=("claude", "codex"),
                        agents=(".claude", ".codex", ".cursor")),
            )
            for argv in commands_in(steps):
                self.assertEqual(argv[0], "npx")
            rendered = " ".join(" ".join(argv) for argv in commands_in(steps))
            for agent in ("claude-code", "codex", "cursor"):
                self.assertIn("-a " + agent, rendered)

    def test_only_narrows_the_plan_to_one_target(self):
        with tempfile.TemporaryDirectory() as home:
            found = machine(home, commands=("claude", "codex"),
                            agents=(".claude", ".codex", ".cursor"))
            steps = install.plan(self.options(only=["codex"]), found)
            self.assertEqual(commands_in(steps), [
                ["codex", "plugin", "marketplace", "add", install.REPO],
                ["codex", "plugin", "add", "grounded-copy@hirohyun-plugins"],
            ])

    def test_only_accepts_a_skills_agent_name(self):
        with tempfile.TemporaryDirectory() as home:
            found = machine(home, commands=("claude",),
                            agents=(".claude", ".cursor", ".gemini"))
            steps = install.plan(self.options(only=["cursor"]), found)
            self.assertEqual(len(steps), 1)
            self.assertIn("-a", steps[0][1])
            self.assertIn("cursor", steps[0][1])

    def test_a_missing_npx_drops_the_skills_steps_and_keeps_the_plugins(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(),
                machine(home, commands=("claude",),
                        agents=(".claude", ".cursor"), npx=False),
            )
            self.assertEqual([argv[0] for argv in commands_in(steps)],
                             ["claude", "claude"])

    def test_uninstall_maps_to_each_host_removal_verb(self):
        with tempfile.TemporaryDirectory() as home:
            steps = install.plan(
                self.options(uninstall=True),
                machine(home, commands=("claude", "codex"),
                        agents=(".claude", ".codex", ".cursor")),
            )
            self.assertEqual(commands_in(steps), [
                ["claude", "plugin", "uninstall", "grounded-copy@hirohyun-plugins", "-y"],
                ["codex", "plugin", "remove", "grounded-copy"],
                ["npx", "-y", "skills", "remove", "grounded-copy", "--yes"],
            ])


class ArgumentTests(unittest.TestCase):
    def test_every_documented_flag_parses(self):
        options, error = install.parse_args([
            "--only", "claude", "--only=cursor", "--skills-only", "--dry-run",
            "--list", "--yes", "--uninstall", "--no-color",
        ])
        self.assertEqual(error, "")
        self.assertEqual(options.only, ["claude", "cursor"])
        for field in ("skills_only", "dry_run", "listing", "assume_yes", "uninstall"):
            self.assertTrue(getattr(options, field), field)
        self.assertFalse(options.color)

    def test_an_unknown_flag_is_rejected(self):
        options, error = install.parse_args(["--wat"])
        self.assertIsNone(options)
        self.assertIn("unknown flag", error)

    def test_an_unknown_only_target_is_rejected(self):
        options, error = install.parse_args(["--only", "emacs"])
        self.assertIsNone(options)
        self.assertIn("unknown --only target", error)

    def test_only_without_a_value_is_rejected(self):
        options, error = install.parse_args(["--only"])
        self.assertIsNone(options)
        self.assertIn("--only", error)


class CommandLineTests(unittest.TestCase):
    """The published entry point, run as a user would run it."""

    def _run(self, args):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, INSTALLER, *args],
            cwd=str(REPO_ROOT), text=True, capture_output=True, env=env,
        )

    def test_dry_run_prints_a_plan_and_runs_nothing(self):
        result = self._run(["--dry-run"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("grounded-copy installer", result.stdout)

    def test_list_reports_what_it_found(self):
        result = self._run(["--list"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for label in ("plugin CLIs:", "agents:", "npx:"):
            self.assertIn(label, result.stdout)

    def test_a_rejected_flag_exits_two(self):
        result = self._run(["--nope"])
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("unknown flag", result.stdout)

    def test_help_prints_the_published_one_liner(self):
        result = self._run(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("install.py | python3 -", result.stdout)

    def test_the_shims_hand_off_to_one_implementation(self):
        """Two shims and one installer: the caveman repository records what
        parallel shell and PowerShell implementations cost in drift.
        """
        for name in ("install.sh", "install.ps1"):
            with self.subTest(shim=name):
                text = (REPO_ROOT / name).read_text(encoding="utf-8")
                self.assertIn("install.py", text)
                self.assertIn("HiroHyun/grounded-copy", text)


if __name__ == "__main__":
    unittest.main()
