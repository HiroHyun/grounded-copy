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
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = str(REPO_ROOT / "install.py")

sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT))
import install  # noqa: E402


def machine(commands=(), npx=True):
    """A detection result for a described machine, with no filesystem read."""
    present = set(commands)
    if npx:
        present.add("npx")
    return install.detect(which=lambda name: name in present)


def commands_in(steps):
    return [argv for _label, argv in steps]


class DetectionTests(unittest.TestCase):
    def test_a_bare_machine_reports_nothing(self):
        found = machine(npx=False)
        self.assertEqual(found["commands"], [])
        self.assertFalse(found["npx"])
        self.assertNotIn("agents", found)

    def test_a_plugin_cli_is_found_on_the_path(self):
        found = machine(commands=("claude",))
        self.assertEqual(found["commands"], ["claude"])


class PlanTests(unittest.TestCase):
    def options(self, **overrides):
        options = install.Options()
        for key, value in overrides.items():
            setattr(options, key, value)
        return options

    def test_a_bare_machine_plans_nothing(self):
        steps = install.plan(self.options(), machine(npx=False))
        self.assertEqual(steps, [])

    def test_claude_takes_the_marketplace_then_the_plugin(self):
        steps = install.plan(self.options(), machine(commands=("claude",)))
        self.assertEqual(commands_in(steps), [
            ["claude", "plugin", "marketplace", "add", install.REPO],
            ["claude", "plugin", "install", "grounded-copy@hirohyun-plugins",
             "-s", "user"],
            ["npx", "-y", "skills", "add", install.REPO,
             "--skill", install.SKILL, "--yes"],
        ])

    def test_codex_takes_its_own_verbs(self):
        steps = install.plan(self.options(), machine(commands=("codex",)))
        self.assertEqual(commands_in(steps), [
            ["codex", "plugin", "marketplace", "add", install.REPO],
            ["codex", "plugin", "add", "grounded-copy@hirohyun-plugins"],
            ["npx", "-y", "skills", "add", install.REPO,
             "--skill", install.SKILL, "--yes"],
        ])

    def test_default_adds_one_universal_skill_step_alongside_plugins(self):
        steps = install.plan(
            self.options(), machine(commands=("claude", "codex"))
        )
        skills = [argv for argv in commands_in(steps) if argv[0] == "npx"]
        self.assertEqual(skills, [[
            "npx", "-y", "skills", "add", install.REPO,
            "--skill", install.SKILL, "--yes",
        ]])
        self.assertNotIn("-a", skills[0])

    def test_skills_only_plans_one_universal_step(self):
        steps = install.plan(
            self.options(skills_only=True),
            machine(commands=("claude", "codex")),
        )
        self.assertEqual(commands_in(steps), [[
            "npx", "-y", "skills", "add", install.REPO,
            "--skill", install.SKILL, "--yes",
        ]])

    def test_only_narrows_the_plan_to_one_target(self):
        found = machine(commands=("claude", "codex"))
        steps = install.plan(self.options(only=["codex"]), found)
        self.assertEqual(commands_in(steps), [
            ["codex", "plugin", "marketplace", "add", install.REPO],
            ["codex", "plugin", "add", "grounded-copy@hirohyun-plugins"],
        ])

    def test_only_skills_plans_the_universal_step(self):
        found = machine(commands=("claude", "codex"))
        steps = install.plan(self.options(only=["skills"]), found)
        self.assertEqual(commands_in(steps), [[
            "npx", "-y", "skills", "add", install.REPO,
            "--skill", install.SKILL, "--yes",
        ]])

    def test_a_missing_npx_drops_the_skills_steps_and_keeps_the_plugins(self):
        steps = install.plan(
            self.options(), machine(commands=("claude",), npx=False)
        )
        self.assertEqual([argv[0] for argv in commands_in(steps)],
                         ["claude", "claude"])

    def test_uninstall_maps_to_each_host_removal_verb(self):
        steps = install.plan(
            self.options(uninstall=True),
            machine(commands=("claude", "codex")),
        )
        self.assertEqual(commands_in(steps), [
            ["claude", "plugin", "uninstall", "grounded-copy@hirohyun-plugins", "-y"],
            ["codex", "plugin", "remove", "grounded-copy@hirohyun-plugins"],
            ["npx", "-y", "skills", "remove", "grounded-copy", "--yes"],
        ])

    def test_every_removal_selector_names_its_marketplace(self):
        """Measured on codex-cli: a bare plugin name exits with "plugin
        requires --marketplace unless passed as <plugin>@<marketplace>".
        """
        steps = install.plan(
            self.options(uninstall=True),
            machine(commands=("claude", "codex")),
        )
        for argv in commands_in(steps):
            if argv[0] in ("claude", "codex"):
                self.assertIn("grounded-copy@hirohyun-plugins", argv)

    def test_successful_combined_run_prints_claude_precedence_note(self):
        found = machine(commands=("claude",))
        output = StringIO()
        with mock.patch.object(install, "detect", return_value=found), \
                mock.patch.object(install, "confirm", return_value=True), \
                mock.patch.object(install, "run", return_value=install.EXIT_OK), \
                redirect_stdout(output):
            code = install.main(["--yes", "--no-color"])
        self.assertEqual(code, install.EXIT_OK)
        self.assertIn("grounded-copy@skills-dir", output.getvalue())
        self.assertIn("grounded-copy@hirohyun-plugins", output.getvalue())


class ResolveTests(unittest.TestCase):
    """What `subprocess` needs that a bare name does not supply.

    CreateProcess applies no PATHEXT search, and npm installs `codex.ps1`,
    `codex.cmd`, and an extensionless `codex` with no `.exe` among them, so a
    bare argv[0] raises OSError on Windows and the step reports "failed to
    start". `shutil.which` reads PATHEXT and returns the shim that launches.
    """

    def test_a_bare_name_becomes_the_path_which_reports(self):
        self.assertEqual(
            install.resolve("codex", which=lambda _n: r"C:\fake\codex.CMD"),
            r"C:\fake\codex.CMD",
        )

    def test_a_name_off_the_path_is_handed_back_unchanged(self):
        self.assertEqual(install.resolve("codex", which=lambda _n: None),
                         "codex")


class RunTests(unittest.TestCase):
    def _record(self, steps, returncode=0):
        """Run the steps, capturing each argv `subprocess.call` receives."""
        calls = []

        def record(argv):
            calls.append(argv)
            return returncode

        with mock.patch.object(install.subprocess, "call", record), \
                mock.patch.object(install, "resolve",
                                  lambda name: r"C:\fake\%s.CMD" % name), \
                redirect_stdout(StringIO()):
            code = install.run(steps)
        return code, calls

    def test_the_launch_uses_the_resolved_path_and_the_original_arguments(self):
        steps = install.plan(install.Options(),
                             machine(commands=("codex",), npx=False))
        code, calls = self._record(steps)
        self.assertEqual(code, install.EXIT_OK)
        self.assertEqual([argv[0] for argv in calls],
                         [r"C:\fake\codex.CMD"] * len(calls))
        self.assertEqual([argv[1:] for argv in calls],
                         [argv[1:] for _label, argv in steps])

    def test_a_step_that_cannot_start_is_reported(self):
        def boom(_argv):
            raise OSError(5, "Access is denied")

        output = StringIO()
        with mock.patch.object(install.subprocess, "call", boom), \
                redirect_stdout(output):
            code = install.run([("codex: add the marketplace",
                                 ["codex", "plugin", "marketplace", "add"])])
        self.assertEqual(code, install.EXIT_FAILED)
        self.assertIn("failed to start", output.getvalue())

    def test_claude_uninstall_clears_only_grounded_copy_cache(self):
        with tempfile.TemporaryDirectory() as config:
            marketplace = (Path(config) / "plugins" / "cache" /
                           install.MARKETPLACE)
            grounded = marketplace / install.PLUGIN / "0.4.0"
            sibling = marketplace / "another-plugin" / "1.0.0"
            grounded.mkdir(parents=True)
            sibling.mkdir(parents=True)
            (grounded / ".orphaned_at").write_text("audit", encoding="utf-8")

            steps = [(
                "claude: remove the plugin",
                ["claude", "plugin", "uninstall",
                 "grounded-copy@hirohyun-plugins", "-y"],
            )]
            with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": config}), \
                    mock.patch.object(install.subprocess, "call", return_value=0), \
                    redirect_stdout(StringIO()):
                code = install.run(steps)

            self.assertEqual(code, install.EXIT_OK)
            self.assertFalse((marketplace / install.PLUGIN).exists())
            self.assertTrue(sibling.exists())


class ConfirmTests(unittest.TestCase):
    """The prompt, on the two stdin conditions the one-liner produces.

    Under `irm install.ps1 | iex` the child process keeps the console, so
    `sys.stdin.isatty()` reports a terminal and the no-terminal branch is
    skipped, and the first read still hits end of file. Reading that as a
    refusal printed "Cancelled." and exited 0, which is why the published
    Windows command installed nothing and reported success.
    """

    STEPS = [("codex: add the marketplace",
              ["codex", "plugin", "marketplace", "add"])]

    class Terminal(object):
        """stdin that claims a terminal, which is what `iex` hands the child.

        The runner's own stdin decides which branch `confirm` takes, and a CI
        job has none, so every case here would return on the no-terminal
        branch and assert nothing about the reader.
        """

        def isatty(self):
            return True

    def _confirm(self, reader):
        output = StringIO()
        with mock.patch.object(install.sys, "stdin", self.Terminal()), \
                redirect_stdout(output):
            answer = install.confirm(self.STEPS, install.Options(),
                                     reader=reader)
        return answer, output.getvalue()

    def test_end_of_file_runs_the_plan_and_says_so(self):
        def eof(_prompt):
            raise EOFError

        answer, output = self._confirm(eof)
        self.assertTrue(answer)
        self.assertIn("No answer available on stdin", output)

    def test_an_interrupt_still_cancels(self):
        def interrupt(_prompt):
            raise KeyboardInterrupt

        answer, _output = self._confirm(interrupt)
        self.assertFalse(answer)

    def test_a_typed_answer_decides(self):
        for typed, expected in (("y", True), ("YES", True), ("", False),
                                ("n", False)):
            with self.subTest(typed=typed):
                answer, _output = self._confirm(lambda _p, t=typed: t)
                self.assertEqual(answer, expected)


class ArgumentTests(unittest.TestCase):
    def test_every_documented_flag_parses(self):
        options, error = install.parse_args([
            "--only", "claude", "--only=skills", "--skills-only", "--dry-run",
            "--list", "--yes", "--uninstall", "--no-color",
        ])
        self.assertEqual(error, "")
        self.assertEqual(options.only, ["claude", "skills"])
        for field in ("skills_only", "dry_run", "listing", "assume_yes", "uninstall"):
            self.assertTrue(getattr(options, field), field)
        self.assertFalse(options.color)

    def test_an_unknown_flag_is_rejected(self):
        options, error = install.parse_args(["--wat"])
        self.assertIsNone(options)
        self.assertIn("unknown flag", error)

    def test_an_unknown_only_target_is_rejected(self):
        options, error = install.parse_args(["--only", "cursor"])
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
        for label in ("plugin CLIs:", "npx:"):
            self.assertIn(label, result.stdout)
        self.assertNotIn("agents:", result.stdout)

    def test_a_rejected_flag_exits_two(self):
        result = self._run(["--nope"])
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("unknown flag", result.stdout)

    def test_help_prints_the_published_one_liner(self):
        result = self._run(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("install.sh | sh", result.stdout)

    def test_the_shims_hand_off_to_one_implementation(self):
        """Two shims and one installer: the caveman repository records what
        parallel shell and PowerShell implementations cost in drift.
        """
        for name in ("install.sh", "install.ps1"):
            with self.subTest(shim=name):
                text = (REPO_ROOT / name).read_text(encoding="utf-8")
                self.assertIn("install.py", text)
                self.assertIn("HiroHyun/grounded-copy", text)

    @unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"),
                         "PowerShell installer runs on Windows with pwsh")
    def test_powershell_shim_streams_the_plan_and_propagates_exit_codes(self):
        launcher = str(REPO_ROOT / "install.ps1")
        dry_run = subprocess.run(
            ["pwsh", "-NoProfile", "-File", launcher, "--dry-run"],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
        self.assertIn("grounded-copy installer", dry_run.stdout)
        self.assertIn("Plan:", dry_run.stdout)

        rejected = subprocess.run(
            ["pwsh", "-NoProfile", "-File", launcher, "--nope"],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(rejected.returncode, 2, rejected.stdout + rejected.stderr)
        self.assertIn("unknown flag", rejected.stdout)

    @unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"),
                         "PowerShell installer runs on Windows with pwsh")
    def test_powershell_pipe_branch_streams_the_plan(self):
        source = str(REPO_ROOT / "install.py").replace("'", "''")
        launcher = str(REPO_ROOT / "install.ps1").replace("'", "''")
        command = (
            "$source = '%s'; "
            "function Invoke-WebRequest { param($Uri, $OutFile, "
            "[switch] $UseBasicParsing); Copy-Item -LiteralPath $source "
            "-Destination $OutFile }; "
            "$body = Get-Content -Raw -LiteralPath '%s'; "
            "& ([scriptblock]::Create($body)) --dry-run"
        ) % (source, launcher)
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", command],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("grounded-copy installer", result.stdout)
        self.assertIn("Plan:", result.stdout)


if __name__ == "__main__":
    unittest.main()
