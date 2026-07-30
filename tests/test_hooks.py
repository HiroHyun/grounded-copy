#!/usr/bin/env python3
"""Interface tests for the two hook entry points.

Every case runs the CLI through subprocess with CLAUDE_CONFIG_DIR pointed at a
temporary directory, so the suite reads and writes nothing outside it and never
touches the user's own profile flag. Assertions cover observable output and
persisted state, which is the contract the plugin manifest depends on.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS = REPO_ROOT / "hooks"

ACTIVATE = str(HOOKS / "grounded_activate.py")
TRACKER = str(HOOKS / "grounded_tracker.py")

BANNED_HEADING = "## The one banned move"
FACTUAL_LABEL = '- **"This negation is factual."**'

COPY_LABELS = (
    '**"It\'s in a quote/testimonial."**',
    '**"It\'s a headline/CTA/meta tag, not body copy."**',
    '**"It\'s a different language."**',
    '**"The linter passed, so it\'s fine."**',
)

EXCLUDED_LABELS = (
    '**"The banned string doesn\'t appear."**',
    '**"A synonym isn\'t on the list."**',
    '**"I\'ll adjust the linter/config."**',
)


class HookCase(unittest.TestCase):
    """Base: a throwaway config directory per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="grounded-hooks-")
        self.config_dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    @property
    def flag(self):
        return self.config_dir / "grounded-copy" / "profile"

    def write_flag(self, value):
        self.flag.parent.mkdir(parents=True, exist_ok=True)
        with open(self.flag, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)

    def read_flag(self):
        with open(self.flag, encoding="utf-8") as handle:
            return handle.read().strip()

    def run_hook(self, script, args=(), stdin=""):
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["CLAUDE_CONFIG_DIR"] = str(self.config_dir)
        return subprocess.run(
            [sys.executable, script, *args],
            input=stdin,
            env=env,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
        )

    def activate(self, stdin='{"hook_event_name":"SessionStart","source":"startup"}'):
        return self.run_hook(ACTIVATE, ["--plugin-root", str(REPO_ROOT)], stdin)

    def track(self, prompt):
        payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        return self.run_hook(TRACKER, ["--plugin-root", str(REPO_ROOT)], payload)

    def reminder_profile(self, result):
        """The profile named in the tracker's additionalContext, or None."""
        if not result.stdout.strip():
            return None
        data = json.loads(result.stdout)
        block = data["hookSpecificOutput"]
        self.assertEqual(block["hookEventName"], "UserPromptSubmit")
        context = block["additionalContext"]
        for name in ("chat", "copy"):
            if "(%s)" % name in context:
                return name
        self.fail("reminder names no known profile: %r" % context)


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------
class ActivationPayloadTests(HookCase):
    def test_default_payload_carries_the_three_pieces(self):
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(BANNED_HEADING, result.stdout)
        self.assertIn("Copy describes things by what they ARE", result.stdout)
        self.assertIn(FACTUAL_LABEL, result.stdout)

    def test_default_payload_names_the_chat_profile(self):
        result = self.activate()
        self.assertIn("profile: chat", result.stdout)
        self.assertNotIn("profile: technical", result.stdout)

    def test_chat_payload_excludes_the_copy_closures(self):
        self.write_flag("chat\n")
        result = self.activate()
        for label in COPY_LABELS:
            self.assertNotIn(label, result.stdout)

    def test_copy_payload_adds_the_four_closures(self):
        self.write_flag("copy\n")
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("profile: copy", result.stdout)
        for label in COPY_LABELS:
            self.assertIn(label, result.stdout)

    def test_neither_payload_carries_the_excluded_sections(self):
        for value in ("chat", "copy"):
            with self.subTest(profile=value):
                self.write_flag(value + "\n")
                result = self.activate()
                self.assertNotIn("## Workflow", result.stdout)
                self.assertNotIn("## Integrity rules", result.stdout)
                self.assertNotIn("## References", result.stdout)
                self.assertNotIn("copy_lint.py", result.stdout)
                for label in EXCLUDED_LABELS:
                    self.assertNotIn(label, result.stdout)

    def test_copy_payload_exceeds_chat_payload(self):
        self.write_flag("chat\n")
        chat = len(self.activate().stdout.encode("utf-8"))
        self.write_flag("copy\n")
        copy = len(self.activate().stdout.encode("utf-8"))
        self.assertGreater(copy, chat)

    def test_self_test_passes(self):
        result = self.run_hook(
            ACTIVATE, ["--self-test", "--plugin-root", str(REPO_ROOT)]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("baseline", result.stdout)


# ---------------------------------------------------------------------------
# Profile resolution and the failure policy
# ---------------------------------------------------------------------------
class ProfileResolutionTests(HookCase):
    def test_missing_flag_writes_no_file(self):
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.flag.exists(), "activation created a flag file")

    def test_activation_output_carries_no_absolute_path(self):
        result = self.activate()
        self.assertNotIn(str(self.config_dir), result.stdout)
        self.assertNotIn("Profile flag:", result.stdout)

    def test_legacy_technical_reads_as_chat(self):
        self.write_flag("technical\n")
        self.assertIn("profile: chat", self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")

    def test_off_silences_both_hooks(self):
        self.write_flag("off\n")
        activation = self.activate()
        self.assertEqual(activation.returncode, 0)
        self.assertEqual(activation.stdout, "")
        reminder = self.track("hello")
        self.assertEqual(reminder.returncode, 0)
        self.assertEqual(reminder.stdout, "")

    def test_off_persists_across_runs(self):
        self.write_flag("off\n")
        for _ in range(2):
            self.assertEqual(self.activate().stdout, "")
        self.assertEqual(self.read_flag(), "off")

    def test_unknown_value_falls_back_in_both_hooks(self):
        self.write_flag("bogus\n")
        self.assertIn(BANNED_HEADING, self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")
        self.assertEqual(self.read_flag(), "bogus", "fallback rewrote the flag")

    def test_oversized_flag_falls_back_in_both_hooks(self):
        self.write_flag("chat" * 64)
        self.assertIn(BANNED_HEADING, self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")

    @unittest.skipUnless(hasattr(os, "symlink"), "platform has no symlink")
    def test_symlinked_flag_falls_back_in_both_hooks(self):
        target = self.config_dir / "elsewhere"
        target.write_text("copy\n", encoding="utf-8")
        self.flag.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(str(target), str(self.flag))
        except (OSError, NotImplementedError) as exc:
            self.skipTest("symlink creation refused: %s" % exc)
        self.assertIn(BANNED_HEADING, self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")


class MalformedInputTests(HookCase):
    def test_activation_survives_malformed_stdin(self):
        for stdin in ("", "   ", "{not json", "[1, 2, 3]", "null"):
            with self.subTest(stdin=stdin):
                result = self.activate(stdin)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(BANNED_HEADING, result.stdout)
                self.assertEqual(result.stderr, "")

    def test_tracker_survives_malformed_stdin(self):
        for stdin in ("", "   ", "{not json", "[1, 2, 3]", "null"):
            with self.subTest(stdin=stdin):
                result = self.run_hook(
                    TRACKER, ["--plugin-root", str(REPO_ROOT)], stdin
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.reminder_profile(result), "chat")
                self.assertEqual(result.stderr, "")

    def test_non_string_prompt_leaves_the_flag_alone(self):
        payload = json.dumps({"prompt": {"nested": "stop grounded prose"}})
        result = self.run_hook(TRACKER, ["--plugin-root", str(REPO_ROOT)], payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.flag.exists())


# ---------------------------------------------------------------------------
# Prompt parsing
# ---------------------------------------------------------------------------
class PromptSwitchTests(HookCase):
    #  Prompts that carry the control words inside other content. Each one
    #  reproduces a live switch against the shipped parser.
    INERT = (
        'add a test for "stop grounded prose"',
        "we should disable grounded in tests",
        "the doc says grounded copy off is persistent, update README",
        "why does stop grounded prose match?",
        "grounded prose off?",
        "document how to stop grounded prose, then commit",
        "the audit reproduction is: stop grounded prose",
        "switch grounded to copy is the phrase users type",
    )

    CONTROL = (
        ("stop grounded prose", "off"),
        ("grounded prose off", "off"),
        ("turn off grounded", "off"),
        ("disable grounded", "off"),
        ("switch grounded to copy", "copy"),
        ("set grounded prose to off", "off"),
        ("grounded copy", "copy"),
        ("grounded chat", "chat"),
        ("enable grounded prose", "chat"),
    )

    def test_incidental_mentions_leave_the_flag_alone(self):
        for prompt in self.INERT:
            with self.subTest(prompt=prompt):
                self.write_flag("chat\n")
                self.track(prompt)
                self.assertEqual(self.read_flag(), "chat")

    def test_complete_control_instructions_switch(self):
        for prompt, expected in self.CONTROL:
            with self.subTest(prompt=prompt):
                self.write_flag("chat\n")
                self.track(prompt)
                self.assertEqual(self.read_flag(), expected)

    def test_switch_takes_effect_in_the_same_turn(self):
        self.write_flag("chat\n")
        self.assertEqual(self.reminder_profile(self.track("grounded copy")), "copy")

    def test_slash_prompts_reach_no_parser(self):
        """A `/` prompt resolves as a slash command before the hook fires.

        references/setup.md records the measurement. The command file owns that
        path through --set, so the hook treats the text as ordinary content.
        """
        self.write_flag("chat\n")
        self.track("/grounded-copy:grounded copy")
        self.assertEqual(self.read_flag(), "chat")


# ---------------------------------------------------------------------------
# Shell entry points
# ---------------------------------------------------------------------------
class SetAndStatusTests(HookCase):
    def status(self):
        return self.run_hook(TRACKER, ["--status"])

    def set_profile(self, value):
        return self.run_hook(TRACKER, ["--set", value])

    def test_set_writes_each_profile(self):
        for arg, stored in (
            ("chat", "chat"),
            ("copy", "copy"),
            ("off", "off"),
            ("technical", "chat"),
            ("marketing", "copy"),
        ):
            with self.subTest(arg=arg):
                result = self.set_profile(arg)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.read_flag(), stored)
                self.assertIn(stored, result.stdout)

    def test_set_rejects_an_unknown_value(self):
        self.write_flag("chat\n")
        result = self.set_profile("bogus")
        self.assertEqual(result.returncode, 0)
        self.assertIn("chat, copy, or off", result.stdout)
        self.assertEqual(self.read_flag(), "chat")

    def test_set_with_an_empty_value_reports_status(self):
        result = self.set_profile("")
        self.assertEqual(result.returncode, 0)
        self.assertIn("grounded profile:", result.stdout)
        self.assertFalse(self.flag.exists(), "empty --set wrote a flag")

    def test_status_names_the_source_for_each_state(self):
        cases = (
            (None, "chat", "no flag at"),
            ("chat\n", "chat", "recorded at"),
            ("technical\n", "chat", "recorded at"),
            ("copy\n", "copy", "recorded at"),
            ("off\n", "off", "recorded at"),
            ("bogus\n", "chat", "unreadable flag at"),
        )
        for value, profile, source in cases:
            with self.subTest(flag=value):
                if value is None:
                    if self.flag.exists():
                        self.flag.unlink()
                else:
                    self.write_flag(value)
                result = self.status()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("grounded profile: %s" % profile, result.stdout)
                self.assertIn(source, result.stdout)
                self.assertIn(str(self.flag), result.stdout)

    def test_status_names_the_restore_command_when_off(self):
        self.write_flag("off\n")
        self.assertIn("--set chat", self.status().stdout)


if __name__ == "__main__":
    unittest.main()
