#!/usr/bin/env python3
"""Argument forwarding, closed-set dispatch, and exit-code propagation.

Both launchers resolve an interpreter once, run the hook once, accept only the
two shipped script names, and hand the interpreter's exit code back. The probes
below read those promises out of observable behavior: an unrecognized `--set`
value comes back in the tracker's message as a repr and exits 2, so a mangled
argument shows up as a changed string and a swallowed exit code shows up as a 0.

Scope bound: these cases measure what the launchers do with the arguments a
shell already parsed. The shell parsing that happens before a launcher starts
lives at the manifest seam, which references/setup.md records as an open
residual under `### Shell-facing values`.
"""

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
# `"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"` form the manifest writes. as_posix()
# reproduces that separator on every platform.

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

        Activation reads SKILL.md from the root it is handed and falls back to
        the repository copy when that read fails, so the marker in stdout is
        what proves the path arrived whole.
        """
        root = self.config_dir / name
        root.mkdir(parents=True, exist_ok=True)
        (root / "SKILL.md").write_text(
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

    def launch(self, argv):
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["CLAUDE_CONFIG_DIR"] = str(self.config_dir)
        return subprocess.run(
            argv, env=env, cwd=str(REPO_ROOT), text=True, capture_output=True
        )


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
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("MARKER-INTRO", result.stdout)

    def test_a_hostile_path_arrives_whole(self):
        result = self.launch(
            [SH, RUN_SH.as_posix(), "grounded_activate.py",
             "--plugin-root", self.hostile_plugin_root()]
        )
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("MARKER-INTRO", result.stdout)
        self.assertIn("MARKER-SCOPE", result.stdout)

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
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("MARKER-INTRO", result.stdout)

    def test_a_hostile_path_arrives_whole(self):
        result = self.launch(
            ["cmd", "/c", str(RUN_CMD), "grounded_activate.py",
             "--plugin-root", self.hostile_plugin_root()]
        )
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("MARKER-INTRO", result.stdout)
        self.assertIn("MARKER-SCOPE", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
