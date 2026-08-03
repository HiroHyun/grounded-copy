#!/usr/bin/env python3
"""Interface tests for the two hook entry points.

One class per domain term, matching `### Profile lifecycle` in
skills/grounded-copy/references/setup.md: the profile preference on disk, the session policy
SessionStart injects, the turn reminder UserPromptSubmit injects, and the
governing directive `--set` prints.

Every case runs the CLI through subprocess with CLAUDE_CONFIG_DIR pointed at a
temporary directory, so the suite reads and writes nothing outside it and never
touches the user's own preference. Assertions cover observable output, exit
codes, and persisted state, which is the contract the plugin manifest depends
on.

These are the deterministic criteria. Whether the model then follows the
injected text is behavioral; `**Enforcement boundary**` in skills/grounded-copy/references/setup.md
states what Phase 1 does about that.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS = REPO_ROOT / "hooks"
SKILL_DIR = REPO_ROOT / "skills" / "grounded-copy"

ACTIVATE = str(HOOKS / "grounded_activate.py")
TRACKER = str(HOOKS / "grounded_tracker.py")

# Sections both profiles carry.
CORE_HEADINGS = (
    "## The one banned move",
    "## Positive forms",
    "## Scope and precedence",
    "## Sourcing",
)

# Rules inside those sections, asserted by their own text so a section that
# survives extraction while losing a rule still fails.
# SKILL.md is hard-wrapped, so each anchor stays short enough to sit on one
# line. A phrase spanning a wrap would fail here for its formatting alone,
# which makes this tuple a constraint on how SKILL.md may be rewrapped: each
# anchor below pins the paragraph under `## The one banned move`,
# `## Scope and precedence` (three bullets), `## Positive forms`, and
# `## Sourcing`, in that order. Re-wrap those paragraphs and check here first.
CORE_RULES = (
    "Every shape blocks with no",
    "**Verbatim source material.**",
    "**Governed everywhere else.**",
    "**User precedence.**",
    "**read-only**",
    "Name the source, the figure",
)

MARKETING_HEADING = "## Marketing register"

COPY_LABELS = (
    '**"It\'s a different language."**',
    '**"The linter passed, so it\'s fine."**',
)

EXCLUDED_LABELS = (
    '**"The banned string doesn\'t appear."**',
    '**"A synonym isn\'t on the list."**',
    '**"I\'ll adjust the linter/config."**',
)

DIRECTIVE_HEADER = "GROUNDED PROSE — governing profile:"
SUPERSESSION = "supersedes every grounded-copy policy statement"

EXIT_OK = 0
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2


class HookCase(unittest.TestCase):
    """Base: a throwaway config directory per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="grounded-hooks-")
        self.config_dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    @property
    def preference(self):
        return self.config_dir / "grounded-copy" / "profile"

    def write_preference(self, value):
        self.preference.parent.mkdir(parents=True, exist_ok=True)
        with open(self.preference, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)

    def read_preference(self):
        with open(self.preference, encoding="utf-8") as handle:
            return handle.read().strip()

    def block_data_dir(self):
        """Make the data directory unusable: a regular file at its path.

        os.makedirs(..., exist_ok=True) raises on both platforms for this,
        which is how the persistence-failure path gets exercised.
        """
        with open(self.config_dir / "grounded-copy", "w", encoding="utf-8"):
            pass

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
            # The hooks call _hook_io.utf8_streams() and hand the host UTF-8 on
            # every platform, so the reader names the same encoding. Leaving it
            # to the platform decodes an em dash as cp1252 on Windows and dies
            # on a byte that code page has no character for.
            encoding="utf-8",
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

    def reminder_text(self, result):
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]

    def assertNoSection(self, text, heading):
        """The heading starts no line.

        A cross-reference names the heading in running prose, so a substring
        check would read that mention as the section itself.
        """
        for line in text.splitlines():
            self.assertFalse(
                line.startswith(heading), "section present: " + heading
            )


# ---------------------------------------------------------------------------
# Session policy: what SessionStart injects
# ---------------------------------------------------------------------------
class OutputEncodingTests(HookCase):
    """Both hooks hand the host UTF-8 whatever encoding the platform picks.

    The payloads carry em dashes, and Python takes a pipe's encoding from the
    platform. Measured before `utf8_streams()`: a Windows interpreter at
    cp1252 made a UTF-8 reader fail on byte 0x97 and receive no policy, so the
    session ran with the rules absent and nothing reported.
    """

    def legacy_code_page(self, script, args=()):
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["CLAUDE_CONFIG_DIR"] = str(self.config_dir)
        env["PYTHONIOENCODING"] = "cp1252"
        return subprocess.run(
            [sys.executable, script, *args],
            input="{}", env=env, cwd=str(REPO_ROOT),
            text=True, encoding="utf-8", capture_output=True,
        )

    def test_the_session_policy_decodes_as_utf8(self):
        self.write_preference("copy\n")
        result = self.legacy_code_page(
            ACTIVATE, ["--plugin-root", str(REPO_ROOT)]
        )
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertIn("GROUNDED PROSE ACTIVE", result.stdout)
        self.assertIn("—", result.stdout)

    def test_the_turn_reminder_decodes_as_utf8(self):
        self.write_preference("chat\n")
        result = self.legacy_code_page(
            TRACKER, ["--plugin-root", str(REPO_ROOT)]
        )
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertIn("GROUNDED PROSE", self.reminder_text(result))

    def test_the_governing_directive_decodes_as_utf8(self):
        result = self.legacy_code_page(
            TRACKER, ["--plugin-root", str(REPO_ROOT), "--set", "copy"]
        )
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)
        self.assertIn(DIRECTIVE_HEADER, result.stdout)
        self.assertIn("—", result.stdout)


class SessionPolicyTests(HookCase):
    def test_both_profiles_carry_every_core_section(self):
        for value in ("chat", "copy"):
            with self.subTest(profile=value):
                self.write_preference(value + "\n")
                result = self.activate()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Copy describes things by what they ARE", result.stdout)
                for heading in CORE_HEADINGS:
                    self.assertIn(heading, result.stdout)

    def test_both_profiles_carry_the_scope_and_precedence_rules(self):
        for value in ("chat", "copy"):
            with self.subTest(profile=value):
                self.write_preference(value + "\n")
                result = self.activate()
                for rule in CORE_RULES:
                    self.assertIn(rule, result.stdout)

    def test_default_policy_names_the_chat_profile(self):
        result = self.activate()
        self.assertIn("profile: chat", result.stdout)
        self.assertNotIn("profile: technical", result.stdout)

    def test_the_session_policy_names_the_claude_slash_command(self):
        """The switch line carries a host verb, and this is the Claude host.

        `_policy.py` ships byte-for-byte into the Codex package, where the verb
        is `$grounded-profile`, so the two hosts assert their own line: this
        case and `test_the_codex_payloads_name_the_codex_profile_verb`.
        """
        self.write_preference("chat\n")
        result = self.activate()
        self.assertIn("`/grounded-copy:grounded chat|copy|off`", result.stdout)
        self.assertNotIn("$grounded-profile", result.stdout)

    def test_chat_policy_excludes_the_marketing_register(self):
        self.write_preference("chat\n")
        result = self.activate()
        self.assertNoSection(result.stdout, MARKETING_HEADING)
        for label in COPY_LABELS:
            self.assertNotIn(label, result.stdout)

    def test_copy_policy_adds_the_marketing_register_and_closures(self):
        self.write_preference("copy\n")
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("profile: copy", result.stdout)
        self.assertIn(MARKETING_HEADING, result.stdout)
        for label in COPY_LABELS:
            self.assertIn(label, result.stdout)

    def test_hype_catalog_reaches_copy_and_sourcing_reaches_both(self):
        """Directive: the register test is copy-side; sourcing is core.

        The anchor is the register test rather than a hype word: SKILL.md
        holds no hype word now, so that it passes copy_lint.py itself, and
        `## Hype vocabulary` in skills/grounded-copy/references/patterns.md enumerates them.
        """
        self.write_preference("chat\n")
        chat = self.activate().stdout
        self.write_preference("copy\n")
        copy = self.activate().stdout
        self.assertNotIn("a perfume ad and a SaaS deck", chat)
        self.assertIn("a perfume ad and a SaaS deck", copy)
        for text in (chat, copy):
            self.assertIn("## Sourcing", text)

    def test_neither_policy_carries_the_excluded_sections(self):
        for value in ("chat", "copy"):
            with self.subTest(profile=value):
                self.write_preference(value + "\n")
                result = self.activate()
                self.assertNotIn("## Workflow", result.stdout)
                self.assertNotIn("## Integrity rules", result.stdout)
                self.assertNotIn("## References", result.stdout)
                self.assertNotIn("copy_lint.py", result.stdout)
                for label in EXCLUDED_LABELS:
                    self.assertNotIn(label, result.stdout)

    def test_copy_policy_exceeds_chat_policy(self):
        self.write_preference("chat\n")
        chat = len(self.activate().stdout.encode("utf-8"))
        self.write_preference("copy\n")
        copy = len(self.activate().stdout.encode("utf-8"))
        self.assertGreater(copy, chat)

    def test_self_test_passes(self):
        result = self.run_hook(
            ACTIVATE, ["--self-test", "--plugin-root", str(REPO_ROOT)]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("baseline", result.stdout)


# ---------------------------------------------------------------------------
# Turn reminder: what UserPromptSubmit injects
# ---------------------------------------------------------------------------
class TurnReminderTests(HookCase):
    # One clause per boundary the reminder keeps in reach. `Prefer established
    # positive terms` came out with the payload cut, since `## Positive forms`
    # states it at session start; `### Measured recurring cost` in
    # skills/grounded-copy/references/setup.md records that. The reminder also carries a byte
    # budget, asserted below.
    CLAUSES = (
        "State what the subject is or does.",
        "No contrast, era-ending, or hype.",
        "Rules hold in quotes, fences, and comments",
        "given source text stays verbatim",
        "A user instruction outranks this",
    )
    CEILING = 260

    def test_reminder_names_the_resolved_profile(self):
        for value, expected in (("chat", "chat"), ("copy", "copy"),
                                ("technical", "chat")):
            with self.subTest(preference=value):
                self.write_preference(value + "\n")
                self.assertEqual(
                    self.reminder_profile(self.track("hello")), expected
                )

    def test_reminder_carries_every_clause(self):
        self.write_preference("chat\n")
        text = self.reminder_text(self.track("hello"))
        for clause in self.CLAUSES:
            self.assertIn(clause, text)

    def test_reminder_stays_inside_its_budget(self):
        """The reminder is the per-prompt cost, so its ceiling is asserted."""
        self.write_preference("chat\n")
        size = len(self.reminder_text(self.track("hello")).encode("utf-8"))
        self.assertLessEqual(size, self.CEILING, "turn reminder grew")

    def test_off_silences_both_hooks(self):
        self.write_preference("off\n")
        activation = self.activate()
        self.assertEqual(activation.returncode, 0)
        self.assertEqual(activation.stdout, "")
        reminder = self.track("hello")
        self.assertEqual(reminder.returncode, 0)
        self.assertEqual(reminder.stdout, "")


# ---------------------------------------------------------------------------
# Profile preference: resolution and the failure policy
# ---------------------------------------------------------------------------
class PreferenceResolutionTests(HookCase):
    def test_missing_preference_writes_no_file(self):
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.preference.exists(), "activation created a file")

    def test_activation_output_carries_no_absolute_path(self):
        result = self.activate()
        self.assertNotIn(str(self.config_dir), result.stdout)

    def test_legacy_technical_reads_as_chat(self):
        self.write_preference("technical\n")
        self.assertIn("profile: chat", self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")

    def test_off_persists_across_runs(self):
        self.write_preference("off\n")
        for _ in range(2):
            self.assertEqual(self.activate().stdout, "")
        self.assertEqual(self.read_preference(), "off")

    def test_unknown_value_falls_back_in_both_hooks(self):
        self.write_preference("bogus\n")
        self.assertIn(CORE_HEADINGS[0], self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")
        self.assertEqual(self.read_preference(), "bogus", "fallback rewrote it")

    def test_oversized_preference_falls_back_in_both_hooks(self):
        self.write_preference("chat" * 64)
        self.assertIn(CORE_HEADINGS[0], self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")

    @unittest.skipUnless(hasattr(os, "symlink"), "platform has no symlink")
    def test_symlinked_preference_falls_back_in_both_hooks(self):
        target = self.config_dir / "elsewhere"
        target.write_text("copy\n", encoding="utf-8")
        self.preference.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(str(target), str(self.preference))
        except (OSError, NotImplementedError) as exc:
            self.skipTest("symlink creation refused: %s" % exc)
        self.assertIn(CORE_HEADINGS[0], self.activate().stdout)
        self.assertEqual(self.reminder_profile(self.track("hello")), "chat")


class MalformedInputTests(HookCase):
    def test_activation_survives_malformed_stdin(self):
        for stdin in ("", "   ", "{not json", "[1, 2, 3]", "null"):
            with self.subTest(stdin=stdin):
                result = self.activate(stdin)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(CORE_HEADINGS[0], result.stdout)
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


# ---------------------------------------------------------------------------
# The hook path is read-only
# ---------------------------------------------------------------------------
class ReadOnlyHookTests(HookCase):
    """No prompt records a preference.

    The first group carried the control words inside other content and each one
    reproduced a live switch against an earlier parser. The second group was
    the parser's own accepted vocabulary. skills/grounded-copy/references/setup.md records why the
    natural-language path came out; both groups stay here as the invariant.
    """

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

    FORMER_CONTROL = (
        "stop grounded prose",
        "grounded prose off",
        "turn off grounded",
        "disable grounded",
        "switch grounded to copy",
        "set grounded prose to off",
        "grounded copy",
        "grounded chat",
        "enable grounded prose",
    )

    def test_no_prompt_creates_a_preference(self):
        for prompt in self.INERT + self.FORMER_CONTROL:
            with self.subTest(prompt=prompt):
                self.track(prompt)
                self.assertFalse(
                    self.preference.exists(), "a prompt created a preference"
                )

    def test_no_prompt_changes_a_recorded_preference(self):
        for prompt in self.INERT + self.FORMER_CONTROL:
            with self.subTest(prompt=prompt):
                self.write_preference("chat\n")
                self.track(prompt)
                self.assertEqual(self.read_preference(), "chat")

    def test_a_non_string_prompt_leaves_the_preference_alone(self):
        payload = json.dumps({"prompt": {"nested": "stop grounded prose"}})
        result = self.run_hook(TRACKER, ["--plugin-root", str(REPO_ROOT)], payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.preference.exists())

    def test_a_slash_prompt_reaches_no_parser(self):
        """A `/` prompt resolves as a slash command before the hook fires.

        skills/grounded-copy/references/setup.md records the measurement. commands/grounded.md owns
        that path through --set.
        """
        self.write_preference("chat\n")
        self.track("/grounded-copy:grounded copy")
        self.assertEqual(self.read_preference(), "chat")


# ---------------------------------------------------------------------------
# Governing directive: what --set prints
# ---------------------------------------------------------------------------
class GoverningDirectiveTests(HookCase):
    def set_profile(self, value):
        return self.run_hook(
            TRACKER, ["--plugin-root", str(REPO_ROOT), "--set", value]
        )

    def test_each_recorded_switch_prints_a_directive(self):
        for value in ("chat", "copy", "off"):
            with self.subTest(profile=value):
                result = self.set_profile(value)
                self.assertEqual(result.returncode, EXIT_OK, result.stdout)
                self.assertIn(DIRECTIVE_HEADER, result.stdout)
                self.assertIn("governing profile: " + value, result.stdout)
                self.assertIn(SUPERSESSION, result.stdout)

    def test_the_directive_is_self_contained(self):
        """It restates the whole policy, so no transition needs a delta."""
        self.write_preference("off\n")
        result = self.set_profile("copy")
        for heading in CORE_HEADINGS:
            self.assertIn(heading, result.stdout)
        self.assertIn(MARKETING_HEADING, result.stdout)
        for label in COPY_LABELS:
            self.assertIn(label, result.stdout)

    def test_the_chat_directive_excludes_the_marketing_register(self):
        self.write_preference("copy\n")
        result = self.set_profile("chat")
        self.assertIn(CORE_HEADINGS[0], result.stdout)
        self.assertNoSection(result.stdout, MARKETING_HEADING)

    def test_the_off_directive_carries_no_rules(self):
        self.write_preference("copy\n")
        result = self.set_profile("off")
        self.assertIn("No grounded-copy rule governs", result.stdout)
        self.assertNotIn(CORE_HEADINGS[0], result.stdout)
        self.assertNoSection(result.stdout, MARKETING_HEADING)

    def test_a_rejected_value_prints_no_directive(self):
        result = self.set_profile("bogus")
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertNotIn(DIRECTIVE_HEADER, result.stdout)


# ---------------------------------------------------------------------------
# The explicit-control exit-code contract
# ---------------------------------------------------------------------------
class SetAndStatusTests(HookCase):
    def status(self):
        return self.run_hook(TRACKER, ["--status"])

    def set_profile(self, value):
        return self.run_hook(TRACKER, ["--set", value])

    def test_set_records_each_profile_and_exits_zero(self):
        for arg, stored in (
            ("chat", "chat"),
            ("copy", "copy"),
            ("off", "off"),
            ("technical", "chat"),
            ("marketing", "copy"),
        ):
            with self.subTest(arg=arg):
                result = self.set_profile(arg)
                self.assertEqual(result.returncode, EXIT_OK, result.stderr)
                self.assertEqual(self.read_preference(), stored)
                self.assertIn(stored, result.stdout)

    def test_an_unknown_value_exits_two_and_holds_the_preference(self):
        self.write_preference("chat\n")
        result = self.set_profile("bogus")
        self.assertEqual(result.returncode, EXIT_REJECTED)
        self.assertIn("chat, copy, or off", result.stdout)
        self.assertEqual(self.read_preference(), "chat")

    def test_the_retired_parser_words_are_rejected(self):
        """`on`, `stop`, and `disable` belonged to the removed switch.

        The rejection message names three profiles, so the accepted set is the
        three plus the two documented aliases and nothing else.
        """
        for value in ("on", "stop", "disable"):
            with self.subTest(value=value):
                self.write_preference("chat\n")
                result = self.set_profile(value)
                self.assertEqual(result.returncode, EXIT_REJECTED, result.stdout)
                self.assertEqual(self.read_preference(), "chat")

    def test_set_outranks_status_when_both_are_passed(self):
        result = self.run_hook(TRACKER, ["--set", "copy", "--status"])
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)
        self.assertEqual(self.read_preference(), "copy")

    def test_a_symlinked_preference_is_reported_and_left_in_place(self):
        """`--set` reports the link; removing it reaches past what it owns.

        resolve_preference() already reads a symlink as unreadable, so the link
        changes no behavior. Deleting a file the user placed there would.
        """
        target = self.config_dir / "elsewhere"
        target.write_text("copy\n", encoding="utf-8")
        self.preference.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(str(target), str(self.preference))
        except (OSError, NotImplementedError) as exc:
            self.skipTest("cannot create a symlink here: %s" % exc)

        result = self.set_profile("chat")
        self.assertEqual(result.returncode, EXIT_PERSISTENCE, result.stdout)
        self.assertIn("symlink", result.stdout)
        self.assertTrue(self.preference.is_symlink(), "the link was removed")
        self.assertEqual(target.read_text(encoding="utf-8").strip(), "copy")

    def test_a_persistence_failure_exits_one_and_names_the_path(self):
        self.block_data_dir()
        result = self.set_profile("copy")
        self.assertEqual(result.returncode, EXIT_PERSISTENCE, result.stdout)
        self.assertIn("grounded:", result.stdout)
        self.assertIn(str(self.config_dir), result.stdout)

    def test_an_empty_value_reports_status_and_exits_zero(self):
        result = self.set_profile("")
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertIn("grounded profile:", result.stdout)
        self.assertFalse(self.preference.exists(), "empty --set wrote a file")

    def test_status_names_the_source_for_each_state(self):
        cases = (
            (None, "chat", "no preference at"),
            ("chat\n", "chat", "recorded at"),
            ("technical\n", "chat", "recorded at"),
            ("copy\n", "copy", "recorded at"),
            ("off\n", "off", "recorded at"),
            ("bogus\n", "chat", "unreadable preference at"),
        )
        for value, profile, source in cases:
            with self.subTest(preference=value):
                if value is None:
                    if self.preference.exists():
                        self.preference.unlink()
                else:
                    self.write_preference(value)
                result = self.status()
                self.assertEqual(result.returncode, EXIT_OK, result.stderr)
                self.assertIn("grounded profile: %s" % profile, result.stdout)
                self.assertIn(source, result.stdout)
                self.assertIn(str(self.preference), result.stdout)

    def test_status_names_the_restore_command_when_off(self):
        self.write_preference("off\n")
        self.assertIn("--set chat", self.status().stdout)


# ---------------------------------------------------------------------------
# What SKILL.md points a reader at
# ---------------------------------------------------------------------------
# Backticked repository paths only. A bare filename carries no directory and
# names a file rather than locating one, and the fenced command examples use
# `<skill-path>/` and placeholders like draft.md, none of which sit in
# backticks.
SKILL_PATH = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|py))`")


class SkillReferenceTests(unittest.TestCase):
    """A path SKILL.md names has to exist, so a rename fails here.

    `## References` sends a reader to files by path. A rename or a move leaves
    the pointer behind with nothing to catch it, and the skill ships to four
    install paths that carry no test suite of their own.

    Resolution is against the skill directory, which is the property the
    canonical layout exists to give: every path SKILL.md names sits beside it,
    so the same pointer resolves in a checkout, in a Claude plugin install, in
    a skills-directory clone, in a portable install, and in the Codex package.
    """

    def test_every_path_skill_md_names_exists(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        named = sorted(set(SKILL_PATH.findall(text)))
        self.assertTrue(named, "no paths matched; the pattern stopped working")
        for relative in named:
            with self.subTest(path=relative):
                self.assertTrue(
                    (SKILL_DIR / relative).exists(),
                    "SKILL.md points at %s, which is absent" % relative,
                )


if __name__ == "__main__":
    unittest.main()
