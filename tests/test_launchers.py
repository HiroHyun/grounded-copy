#!/usr/bin/env python3
"""Argument forwarding, closed-set dispatch, and exit-code propagation.

Both launchers resolve an interpreter once, run the hook once, accept only the
three shipped script names, and hand the interpreter's exit code back. The probes
below read those promises out of observable behavior: an unrecognized `--set`
value comes back in the tracker's message as a repr and exits 2, so a mangled
argument shows up as a changed string and a swallowed exit code shows up as a 0.

Scope bound: the launcher cases measure what the launchers do with the
arguments a shell already parsed. WindowsHookCommandTests covers the parsing
before a launcher starts, for the hook strings hosts hand to PowerShell and
cmd.exe.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_SH = REPO_ROOT / "hooks" / "run.sh"
RUN_CMD = REPO_ROOT / "hooks" / "run.cmd"

# run.sh finds its own directory by trimming argv0 at the last `/`, matching the
# `.../hooks/run.sh` form the Codex manifest and the Claude launchers write.
# as_posix() reproduces that separator on every platform.

SH = shutil.which("sh")

EXIT_OK = 0
EXIT_REJECTED = 2

# Values that survive `--set`'s strip and lower, so the echoed repr is a
# byte-for-byte report of what reached argv.
PROBES = ("co!py", "co py", "a!b!c", "50%off")

# Two probes measure the caller's own quoting rather than the launcher's, so
# each runs where its result is attributable. On Windows, subprocess joins the
# argument list into one string by C runtime rules and `sh` and `cmd` re-split
# it by theirs: a literal `"` and a literal `^` change at that boundary, before
# either launcher runs. Both launchers handle both characters when a shell hands
# them over directly.
POSIX_ONLY_PROBES = ('q"r', "x^y")

# A directory name carrying every character a shell would otherwise act on.
# Windows filenames forbid `"`, so that character joins the POSIX run alone.
HOSTILE_NAME = "gc $t`e;s&t v"
POSIX_HOSTILE_NAME = HOSTILE_NAME + '"'

UNKNOWN_SCRIPTS = ("evil.py", "../../etc/passwd", "grounded_tracker", "")

ADAPTER = REPO_ROOT / "dist" / "codex" / "grounded-copy"
CLAUDE_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
HOOK_EVENTS = ("SessionStart", "UserPromptSubmit")
POWERSHELLS = [name for name in ("pwsh", "powershell") if shutil.which(name)]

# Claude Code on Windows runs hooks in the Git Bash it finds at this path, and
# in PowerShell when none is installed. Elsewhere it runs them in a POSIX
# shell; every one present here takes a turn.
GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
POSIX_SHELLS = [name for name in ("sh", "bash", "dash", "zsh") if shutil.which(name)]

# A plugin root holding a space, an apostrophe, `;`, parentheses, and `%`,
# which pass through both PowerShell double quotes and `cmd /d /c`. Codex
# substitutes ${PLUGIN_ROOT} as text, so two limits remain: PowerShell expands
# a `$` or backtick in the root, and `cmd /c` splits a root holding `&`.
# HOSTILE_NAME carries all three.
PLUGIN_ROOT_NAME = "gc o'k;x (v) 5%"


def claude_hook_commands():
    """The shipped Claude hook command for each event, as the manifest writes it."""
    hooks = json.loads(CLAUDE_MANIFEST.read_text(encoding="utf-8"))["hooks"]
    return [(event, hooks[event][0]["hooks"][0]["command"]) for event in HOOK_EVENTS]


class LauncherCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="grounded-launcher-")
        self.config_dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    @property
    def preference(self):
        return self.config_dir / "grounded-copy" / "profile"

    def read_preference(self):
        with open(self.preference, encoding="utf-8") as handle:
            return handle.read().strip()

    def probe_plugin_root(self, name):
        """A plugin root under `name`, with a marked SKILL.md.

        Activation reads `skills/grounded-copy/SKILL.md` under the root it is
        handed and falls back to the repository copy when that read fails, so
        the marker in stdout is what proves the path arrived whole. Write the
        probe anywhere else and the fallback answers, which reports an
        interpreter failure for what is a lost path.
        """
        root = self.config_dir / name
        skill = root / "skills" / "grounded-copy"
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            "---\nname: probe\n---\n\n"
            "MARKER-INTRO probe intro.\n\n"
            "## The one banned move (probe)\n\n"
            "MARKER-BANNED probe body.\n\n"
            "## Positive forms\n\nMARKER-POSITIVE\n\n"
            "## Scope and precedence\n\nMARKER-SCOPE\n\n"
            "## Sourcing\n\nMARKER-SOURCING\n",
            encoding="utf-8",
        )
        return str(root)

    def hostile_plugin_root(self):
        name = HOSTILE_NAME if os.name == "nt" else POSIX_HOSTILE_NAME
        try:
            return self.probe_plugin_root(name)
        except OSError as exc:
            self.skipTest("filesystem refused the hostile name: %s" % exc)

    def launch(self, argv, env=None, stdin=""):
        merged = os.environ.copy()
        merged.pop("CLAUDE_PLUGIN_ROOT", None)
        merged["CLAUDE_CONFIG_DIR"] = str(self.config_dir)
        merged.update(env or {})
        return subprocess.run(
            argv, env=merged, cwd=str(REPO_ROOT),
            # Both entrypoints call drain_stdin(), which reads to EOF. With no
            # input the child inherits the caller's stdin, so the suite hangs
            # wherever that stays open — measured against a backgrounded shell,
            # where the run sat for an hour. A string closes the pipe after
            # writing, matching the host, which writes the event and closes.
            input=stdin,
            text=True, encoding="utf-8", capture_output=True,
        )

    def assertMarkers(self, result, *markers):
        """Assert the probe SKILL.md reached stdout, naming the other cause.

        A launcher whose interpreter probe finds nothing exits 0 with empty
        stdout by design, which reads here as a missing marker. Separating the
        two says which happened: an empty stdout is the environment, a
        populated stdout missing a marker is the path arriving mangled.
        """
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertTrue(
            result.stdout.strip(),
            "launcher produced no output: the interpreter probe resolved "
            "neither `python` nor `python3`, so this run measured nothing. "
            "stderr: %r" % result.stderr,
        )
        for marker in markers:
            self.assertIn(marker, result.stdout)


@unittest.skipUnless(SH, "no `sh` on PATH")
class RunShTests(LauncherCase):
    def run_sh(self, *args):
        return self.launch([SH, RUN_SH.as_posix(), "grounded_tracker.py", *args])

    def test_probe_values_arrive_unchanged_and_report_exit_two(self):
        probes = PROBES if os.name == "nt" else PROBES + POSIX_ONLY_PROBES
        for probe in probes:
            with self.subTest(probe=probe):
                result = self.run_sh("--set", probe)
                self.assertEqual(result.returncode, EXIT_REJECTED, result.stdout)
                self.assertIn(repr(probe), result.stdout)

    def test_a_recognized_value_still_writes(self):
        result = self.run_sh("--set", "copy")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(self.read_preference(), "copy")

    def test_an_empty_value_reports_status(self):
        result = self.run_sh("--set", "")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("grounded profile:", result.stdout)

    def test_a_path_holding_a_space_arrives_whole(self):
        result = self.launch(
            [SH, RUN_SH.as_posix(), "grounded_activate.py",
             "--plugin-root", self.probe_plugin_root("gc test")]
        )
        self.assertMarkers(result, "MARKER-INTRO")

    def test_a_hostile_path_arrives_whole(self):
        result = self.launch(
            [SH, RUN_SH.as_posix(), "grounded_activate.py",
             "--plugin-root", self.hostile_plugin_root()]
        )
        self.assertMarkers(result, "MARKER-INTRO", "MARKER-SCOPE")

    def test_an_unknown_script_name_exits_zero_and_writes_nothing(self):
        for name in UNKNOWN_SCRIPTS:
            with self.subTest(script=name):
                result = self.launch(
                    [SH, RUN_SH.as_posix(), name, "--set", "copy"]
                )
                self.assertEqual(result.returncode, EXIT_OK)
                self.assertEqual(result.stdout, "")
                self.assertFalse(self.preference.exists())

    def test_forwarding_has_no_argument_ceiling(self):
        filler = ["--f%d" % i for i in range(8)]
        result = self.run_sh(*filler, "--set", "copy")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(self.read_preference(), "copy")

    def test_a_missing_script_name_exits_zero(self):
        result = self.launch([SH, RUN_SH.as_posix()])
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertEqual(result.stdout, "")


@unittest.skipUnless(os.name == "nt", "run.cmd runs on Windows only")
class RunCmdTests(LauncherCase):
    def run_cmd(self, *args):
        return self.launch(
            ["cmd", "/c", str(RUN_CMD), "grounded_tracker.py", *args]
        )

    def test_probe_values_arrive_unchanged_and_report_exit_two(self):
        for probe in PROBES:
            with self.subTest(probe=probe):
                result = self.run_cmd("--set", probe)
                self.assertEqual(result.returncode, EXIT_REJECTED, result.stdout)
                self.assertIn(repr(probe), result.stdout)

    def test_a_nonzero_exit_propagates(self):
        """`exit /b 0` used to mask every result the hook reported."""
        result = self.run_cmd("--set", "bogus")
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertIn("unknown profile", result.stdout)

    def test_a_bang_value_writes_no_profile(self):
        """`co!py` reached the hook as `copy` while delayed expansion was on."""
        result = self.run_cmd("--set", "co!py")
        self.assertIn("unknown profile", result.stdout)
        self.assertFalse(self.preference.exists(), "a mangled value wrote one")

    def test_a_recognized_value_still_writes(self):
        result = self.run_cmd("--set", "copy")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(self.read_preference(), "copy")

    def test_an_empty_value_reports_status(self):
        result = self.run_cmd("--set", "")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("grounded profile:", result.stdout)

    def test_a_path_holding_a_space_arrives_whole(self):
        result = self.launch(
            ["cmd", "/c", str(RUN_CMD), "grounded_activate.py",
             "--plugin-root", self.probe_plugin_root("gc test")]
        )
        self.assertMarkers(result, "MARKER-INTRO")

    def test_a_hostile_path_arrives_whole(self):
        result = self.launch(
            ["cmd", "/c", str(RUN_CMD), "grounded_activate.py",
             "--plugin-root", self.hostile_plugin_root()]
        )
        self.assertMarkers(result, "MARKER-INTRO", "MARKER-SCOPE")

    def test_an_unknown_script_name_exits_zero_and_writes_nothing(self):
        for name in UNKNOWN_SCRIPTS:
            with self.subTest(script=name):
                result = self.launch(
                    ["cmd", "/c", str(RUN_CMD), name, "--set", "copy"]
                )
                self.assertEqual(result.returncode, EXIT_OK)
                self.assertEqual(result.stdout, "")
                self.assertFalse(self.preference.exists())

    def test_eight_arguments_arrive(self):
        """The documented ceiling: %2 through %9 forward, and %10 does not."""
        filler = ["--f%d" % i for i in range(6)]
        result = self.run_cmd(*filler, "--set", "copy")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(self.read_preference(), "copy")

    def test_a_ninth_argument_is_dropped(self):
        filler = ["--f%d" % i for i in range(7)]
        result = self.run_cmd(*filler, "--set", "copy")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("grounded profile:", result.stdout)
        self.assertFalse(self.preference.exists())

    def test_a_missing_script_name_exits_zero(self):
        result = self.launch(["cmd", "/c", str(RUN_CMD)])
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertEqual(result.stdout, "")


class GateLauncherTests(LauncherCase):
    """The gate's name is in both closed sets, and its exit code 2 and its
    stderr come back through each launcher."""

    def test_each_launcher_runs_the_gate_and_returns_its_exit_code(self):
        target = self.config_dir / "notes.md"
        target.write_text("The file isn't missing, it's empty.\n",
                          encoding="utf-8")
        event = json.dumps({"hook_event_name": "PostToolUse",
                            "tool_input": {"file_path": str(target)}})
        launchers = []
        if SH:
            launchers.append([SH, RUN_SH.as_posix()])
        if os.name == "nt":
            launchers.append(["cmd", "/c", str(RUN_CMD)])
        if not launchers:
            self.skipTest("no launcher runs on this platform")
        for launcher in launchers:
            with self.subTest(launcher=launcher[0]):
                result = self.launch(
                    launcher + ["grounded_gate.py", "--plugin-root",
                                str(REPO_ROOT)], stdin=event)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("[not-x-its-y]", result.stderr)


class HookCommandCase(LauncherCase):
    """Run a host's hook strings through the shell that host would use.

    Shells localize their error text, so these cases read the exit code and
    stdout, and pass stderr along as the failure message.
    """

    def plugin_root(self, *trees, name=PLUGIN_ROOT_NAME):
        """Copy each (source, relative destination) tree under one root."""
        root = self.config_dir / name
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        for source, relative in trees:
            shutil.copytree(str(source), str(root / relative), ignore=ignore)
        return root

    def claude_root(self):
        """Claude hands the root over as an environment variable, which every
        shell expands without re-parsing, so the hostile name applies here."""
        name = HOSTILE_NAME if os.name == "nt" else POSIX_HOSTILE_NAME
        root = self.plugin_root(
            (REPO_ROOT / "hooks", "hooks"), (REPO_ROOT / "skills", "skills"), name=name
        )
        # .gitattributes ships the launchers CRLF. A checkout that ignored it
        # would hand the POSIX shells LF and skip the carriage-return path, so
        # the copies carry CRLF whatever the checkout did.
        for launcher in (root / "hooks").glob("claude_*.cmd"):
            body = launcher.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            launcher.write_bytes(body)
        return root

    def assertHooksRun(self, commands, env, shells):
        if not shells:
            self.skipTest("no shell of this kind is installed")
        for shell in shells:
            for event, command in commands:
                with self.subTest(shell=shell, event=event):
                    if shell == "cmd":
                        # A raw command line, as a host that quotes for
                        # cmd.exe would pass it.
                        argv = 'cmd.exe /d /s /c "' + command + '"'
                    elif shell in ("pwsh", "powershell"):
                        argv = [shell, "-NoProfile", "-NonInteractive", "-Command", command]
                    else:
                        argv = [shell, "-c", command]
                    result = self.launch(
                        argv,
                        env=env,
                        stdin=json.dumps({"hook_event_name": event, "session_id": "test"}),
                    )
                    if event == "SessionStart":
                        self.assertMarkers(
                            result, "GROUNDED PROSE ACTIVE", "Profile: chat. Switch:"
                        )
                    else:
                        self.assertMarkers(result, "GROUNDED PROSE (chat)")
                        output = json.loads(result.stdout)["hookSpecificOutput"]
                        self.assertEqual(output["hookEventName"], "UserPromptSubmit")


@unittest.skipUnless(os.name == "nt", "Windows hook commands run on Windows only")
class WindowsHookCommandTests(HookCommandCase):
    """Codex Desktop 0.159.2 runs `commandWindows` through
    `pwsh -NoProfile -Command` after replacing ${PLUGIN_ROOT} as text; another
    build could use cmd.exe, so the Codex strings run under both.

    Claude Code runs its hook commands in Git Bash when it finds one and in
    PowerShell otherwise, rewriting ${CLAUDE_PLUGIN_ROOT} to
    ${env:CLAUDE_PLUGIN_ROOT} for PowerShell and handing Git Bash the root with
    forward slashes. The shipped command runs under both.
    """

    def test_documented_gate_command_preserves_findings_through_powershell(self):
        if not POWERSHELLS:
            self.skipTest("PowerShell is not installed")
        root = self.plugin_root((ADAPTER, ""))
        setup = (REPO_ROOT / "skills/grounded-copy/references/setup.md").read_text(
            encoding="utf-8")
        command = next(line.split("'", 2)[1] for line in setup.splitlines()
                       if line.startswith("commandWindows = "))
        command = command.replace(
            r"C:\path\to\grounded-copy\dist\codex\grounded-copy", str(root))
        # The command the plugin registers, beside the one the guide prints.
        hooks = json.loads((root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        shipped = (hooks["hooks"]["PostToolUse"][0]["hooks"][0]["commandWindows"]
                   .replace("${PLUGIN_ROOT}", str(root)))
        target = self.config_dir / "notes.md"
        for shell, command in [(s, c) for s in POWERSHELLS for c in (command, shipped)]:
            for body, code in (("The file is empty.\n", 0),
                               ("The file isn't missing, it's empty.\n", 2)):
                with self.subTest(shell=shell, code=code, shipped=command is shipped):
                    target.write_text(body, encoding="utf-8")
                    event = json.dumps({
                        "tool_name": "apply_patch", "cwd": str(self.config_dir),
                        "tool_input": {"command": (
                            "*** Update File: notes.md\n+" + body)}})
                    result = self.launch(
                        [shell, "-NoProfile", "-NonInteractive", "-Command", command],
                        env={"CODEX_HOME": str(self.config_dir / "codex-home")},
                        stdin=event)
                    self.assertEqual(result.returncode, code, result.stderr)
                    if code:
                        self.assertIn("[not-x-its-y]", result.stderr)

    def test_codex_command_windows_runs_under_powershell_and_cmd(self):
        root = self.plugin_root((ADAPTER, ""))
        hooks = json.loads((root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        commands = [
            (event, hooks["hooks"][event][0]["hooks"][0]["commandWindows"]
             .replace("${PLUGIN_ROOT}", str(root)))
            for event in HOOK_EVENTS
        ]
        # An empty CODEX_HOME holds no profile file, which resolves to chat.
        self.assertHooksRun(
            commands, {"CODEX_HOME": str(self.config_dir / "codex-home")},
            POWERSHELLS + ["cmd"],
        )

    def test_claude_manifest_runs_under_powershell(self):
        root = self.claude_root()
        commands = [
            (event, command.replace("${CLAUDE_PLUGIN_ROOT}", "${env:CLAUDE_PLUGIN_ROOT}"))
            for event, command in claude_hook_commands()
        ]
        # Claude Code picks PowerShell only where Git Bash is missing, so no
        # `sh` is on that PATH. A test run from Git Bash or a CI image would
        # otherwise lend the hook one.
        path = os.pathsep.join(
            entry for entry in os.environ.get("PATH", "").split(os.pathsep)
            if not os.path.isfile(os.path.join(entry, "sh.exe"))
        )
        self.assertHooksRun(
            commands, {"CLAUDE_PLUGIN_ROOT": str(root), "PATH": path}, POWERSHELLS
        )

    def test_claude_manifest_runs_under_git_bash(self):
        root = self.claude_root()
        shells = [GIT_BASH] if os.path.isfile(GIT_BASH) else []
        self.assertHooksRun(
            claude_hook_commands(),
            {"CLAUDE_PLUGIN_ROOT": str(root).replace("\\", "/")},
            shells,
        )


@unittest.skipIf(os.name == "nt", "POSIX hook shells run off Windows")
class PosixHookCommandTests(HookCommandCase):
    """Claude Code runs its hook commands in a POSIX shell on macOS and Linux.

    The launchers keep CRLF endings for cmd.exe, so this run also proves each
    POSIX shell reads past the carriage returns.
    """

    def test_claude_manifest_runs_under_each_posix_shell(self):
        root = self.claude_root()
        self.assertHooksRun(
            claude_hook_commands(), {"CLAUDE_PLUGIN_ROOT": str(root)}, POSIX_SHELLS
        )

if __name__ == "__main__":
    unittest.main()
