#!/usr/bin/env python3
"""Interface tests for the OpenAI/Codex adapter.

The adapter reuses canonical skill and runtime files by copy, so the reuse
claim needs a test that fails when a copy drifts. These cases cover the Codex
plugin layout, lifecycle hooks, profile controller, generated inventory, and
the license notice that travels with a redistributed package.
"""

import json
import os
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = str(REPO_ROOT / "scripts" / "build_codex_adapter.py")
ADAPTER_REL = Path("dist") / "codex" / "grounded-copy"
ADAPTER = REPO_ROOT / ADAPTER_REL
SKILL_DIR = ADAPTER / "skills" / "grounded-copy"
SKILL_SOURCE = REPO_ROOT / "skills" / "grounded-copy"
CODEX_ACTIVATE = ADAPTER / "hooks" / "grounded_activate.py"
CODEX_TRACKER = ADAPTER / "hooks" / "grounded_tracker.py"

# Every file the generated package holds. The builder walks the skill
# directory, so a new reference ships automatically; this set is what keeps
# that walk under review, so an added or dropped file is a decision someone
# made here.
GENERATED_INVENTORY = {
    "assets/logo.png",
    "assets/logo-dark.png",
    ".codex-plugin/plugin.json",
    "LICENSE",
    "NOTICE",
    "README.md",
    "hooks/_hook_io.py",
    "hooks/_policy.py",
    "hooks/_preference.py",
    "hooks/grounded_activate.py",
    "hooks/grounded_gate.py",
    "hooks/grounded_tracker.py",
    "hooks/hooks.json",
    "hooks/run.cmd",
    "hooks/run.sh",
    "skills/grounded-copy/SKILL.md",
    "skills/grounded-copy/references/patterns.md",
    "skills/grounded-copy/references/setup.md",
    "skills/grounded-copy/scripts/copy_lint.py",
    "skills/grounded-copy/tests/bad-samples.md",
    "skills/grounded-copy/tests/good-samples.md",
    "skills/grounded-profile/SKILL.md",
    "skills/grounded-profile/agents/openai.yaml",
    "skills/grounded-profile/scripts/profile.py",
}


class CodexAdapterTests(unittest.TestCase):
    def test_listing_metadata_and_packaged_icons(self):
        manifest = json.loads(
            (ADAPTER / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        listing = manifest["interface"]
        self.assertEqual(listing["displayName"], "Grounded Copy")
        self.assertEqual(listing["shortDescription"],
                         "Help AI write clearly and get to the point.")
        self.assertEqual(listing["developerName"], manifest["author"]["name"])
        self.assertEqual(listing["websiteURL"], manifest["homepage"])
        self.assertEqual(listing["category"], "Productivity")
        self.assertEqual(listing["capabilities"], ["Instructions", "Lifecycle hooks"])
        self.assertTrue(listing["longDescription"])
        prompts = listing["defaultPrompt"]
        self.assertEqual(len(prompts), 3)
        self.assertEqual(len(set(prompts)), 3)
        for prompt in prompts:
            self.assertTrue(0 < len(prompt) <= 128)
            self.assertNotIn("\n", prompt)
        for field, filename in (("logo", "logo.png"), ("logoDark", "logo-dark.png"),
                                ("composerIcon", "logo.png"),
                                ("composerIconDark", "logo-dark.png")):
            with self.subTest(field=field):
                self.assertEqual(listing[field], "./assets/" + filename)
                data = (ADAPTER / "assets" / filename).read_bytes()
                self.assertEqual(data, (REPO_ROOT / "assets" / filename).read_bytes())
                self.assertLess(len(data), 5 * 1024 * 1024)
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual(width, height)
                self.assertTrue(48 <= width <= 4096)
                self.assertEqual(data[25], 6, "icons must retain RGBA transparency")

    def test_claude_package_and_portable_skill_paths_resolve(self):
        catalog = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(p for p in catalog["plugins"] if p["name"] == "grounded-copy")
        self.assertEqual(entry["source"], "./")
        manifest = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["skills"], ["./skills/"])
        self.assertEqual(entry["skills"], manifest["skills"])
        for event, script in (("SessionStart", "grounded_activate.py"),
                              ("UserPromptSubmit", "grounded_tracker.py")):
            # The hook dot-sources a launcher that bash, sh, zsh, and
            # PowerShell all start; each half names the same entrypoint.
            command = manifest["hooks"][event][0]["hooks"][0]["command"]
            argv = shlex.split(command.replace("${CLAUDE_PLUGIN_ROOT}", REPO_ROOT.as_posix()))
            self.assertEqual(argv[0], ".")
            self.assertEqual(len(argv), 2)
            launcher = Path(argv[1])
            self.assertTrue(launcher.is_file(), str(launcher))
            body = launcher.read_bytes()
            self.assertIn(b'@"%~dp0run.cmd" ' + script.encode(), body)
            self.assertIn(b'/hooks/run.sh" ' + script.encode() + b" #", body)
            self.assertTrue((launcher.parent / script).is_file())
        skill = (SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")
        for relative in ("references/patterns.md", "references/setup.md",
                         "scripts/copy_lint.py", "tests/bad-samples.md", "tests/good-samples.md"):
            with self.subTest(path=relative):
                self.assertIn(relative, skill)
                self.assertTrue((SKILL_SOURCE / relative).is_file())
        guide = (SKILL_SOURCE / "references" / "patterns.md").read_text(encoding="utf-8")
        self.assertIn("## Chinese paragraph review", guide)
        self.assertIn("## Paragraph review", guide)

    def test_every_skill_file_ships_byte_identical(self):
        """The whole canonical directory travels, at the same relative path.

        This walks the source tree. Reading the builder's payload list back
        would make the case tautological with the `--check` test, so a builder
        that dropped a file would satisfy both.
        """
        sources = sorted(
            p for p in SKILL_SOURCE.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        )
        self.assertTrue(sources, "no skill source files; the walk stopped working")
        for source in sources:
            relative = source.relative_to(SKILL_SOURCE)
            with self.subTest(path=str(relative)):
                copy = SKILL_DIR / relative
                self.assertTrue(copy.exists(), "missing: " + str(relative))
                self.assertEqual(
                    source.read_bytes(), copy.read_bytes(),
                    "adapter copy drifted from " + str(relative),
                )

    def test_the_generated_inventory_matches_the_published_set(self):
        found = {
            p.relative_to(ADAPTER).as_posix()
            for p in ADAPTER.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        self.assertEqual(found, GENERATED_INVENTORY)

    def test_the_check_mode_passes_against_the_committed_adapter(self):
        result = subprocess.run(
            [sys.executable, BUILDER, "--check"],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
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
                cwd=str(root), text=True, encoding="utf-8", capture_output=True,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

            clean = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=str(root), text=True, encoding="utf-8", capture_output=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout)

            copy = root / ADAPTER_REL / "skills" / "grounded-copy" / "SKILL.md"
            copy.write_bytes(copy.read_bytes() + b"\ndrift\n")

            drifted = subprocess.run(
                [sys.executable, str(builder), "--check"],
                cwd=str(root), text=True, encoding="utf-8", capture_output=True,
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
                                   text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            generated = root / ADAPTER_REL
            missing = generated / "hooks" / "hooks.json"
            self.assertTrue(missing.exists(), str(missing))
            missing.unlink()
            extra = generated / "unexpected-generated-file.txt"
            extra.write_text("drift", encoding="utf-8")
            result = subprocess.run([sys.executable, str(builder), "--check"],
                                    cwd=root, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("missing", result.stdout)
            self.assertIn("unexpected", result.stdout)

    def test_the_manifest_declares_the_required_fields(self):
        manifest = json.loads(
            (ADAPTER / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "grounded-copy")
        self.assertEqual(manifest["license"], "AGPL-3.0-only")
        self.assertEqual(manifest["skills"], "./skills/")
        for field in ("version", "description", "repository", "homepage"):
            self.assertIn(field, manifest)

    def test_the_skill_sits_where_the_specification_asks(self):
        self.assertTrue((SKILL_DIR / "SKILL.md").exists())
        header = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")[:400]
        self.assertIn("name: grounded-copy", header)

    def test_the_license_notice_travels_with_the_package(self):
        notice = (ADAPTER / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", notice)
        holder = (ADAPTER / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Copyright (C) 2026 HiroHyun", holder)
        self.assertIn("Version 3, 19 November 2007", notice)
        self.assertIn("13. Remote Network Interaction", notice)

    def test_every_catalog_entry_and_manifest_declares_the_license(self):
        """`README.md` claims both manifests and both catalog entries say AGPL.

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
                self.assertEqual(entries[0].get("license"), "AGPL-3.0-only")
        manifest = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["license"], "AGPL-3.0-only")

    def test_the_adapter_ships_hooks_and_no_claude_commands(self):
        for name in ("hooks",):
            with self.subTest(directory=name):
                self.assertTrue((ADAPTER / name).exists())
        # The Python suites and the repository build stay behind; the corpora
        # that travel sit inside the skill, at `skills/grounded-copy/tests`.
        for name in ("commands", ".claude-plugin", "tests", "scripts"):
            with self.subTest(directory=name):
                self.assertFalse((ADAPTER / name).exists())

    def test_the_linter_runs_against_the_corpora_it_ships_with(self):
        """SKILL.md points a reader at both corpora; the package carries them."""
        linter = str(SKILL_DIR / "scripts" / "copy_lint.py")
        good = subprocess.run(
            [sys.executable, linter, str(SKILL_DIR / "tests" / "good-samples.md")],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(good.returncode, 0, good.stdout)
        bad = subprocess.run(
            [sys.executable, linter, str(SKILL_DIR / "tests" / "bad-samples.md")],
            cwd=str(REPO_ROOT), text=True, encoding="utf-8", capture_output=True,
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
                              text=True, encoding="utf-8", capture_output=True, env=env)

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
            self.assertIn("Select relevant facts", block["additionalContext"])
            self.assertIn("quote exactly", block["additionalContext"])
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

    def test_paragraph_review_reaches_codex_switch_startup_and_compaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            for profile in ("chat", "copy"):
                outputs = [self._hook(CODEX_TRACKER, ("--set", profile), home=tmp)]
                for source in ("startup", "compact"):
                    outputs.append(self._hook(
                        CODEX_ACTIVATE, home=tmp, stdin=json.dumps({"source": source})
                    ))
                for result in outputs:
                    with self.subTest(profile=profile, output=result.args):
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("Chinese paragraph review", result.stdout)
                        self.assertIn("In English and other languages", result.stdout)
                        self.assertIn("Read Paragraph review", result.stdout)
                        self.assertIn("Splitting them across sentences or bullets", result.stdout)
                        self.assertIn("references/patterns.md", result.stdout)
                        self.assertIn("Select facts for the reader's purpose", result.stdout)
                        self.assertIn("Omit incidental details", result.stdout)
                        self.assertIn("Honor explicit requests for complete coverage", result.stdout)
                        for concern in ("dense lists", "repeated frames", "translationese",
                                        "redundant words", "register shifts"):
                            self.assertIn(concern, result.stdout)

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
        # A bare `cmd` leads each string, so PowerShell and cmd.exe both run
        # it. test_launchers runs these through both shells on Windows.
        for event, script in (("SessionStart", "grounded_activate.py"),
                              ("UserPromptSubmit", "grounded_tracker.py")):
            with self.subTest(event=event):
                self.assertEqual(
                    hooks["hooks"][event][0]["hooks"][0]["commandWindows"],
                    'cmd /d /c "${PLUGIN_ROOT}\\hooks\\run.cmd" ' + script,
                )
        for corpus in ("bad-samples.md", "good-samples.md"):
            with self.subTest(corpus=corpus):
                self.assertTrue((SKILL_DIR / "tests" / corpus).exists())

    def test_one_version_number_covers_both_packages(self):
        """Four manifests carried two numbers by hand. The Claude one is source."""
        def load(*parts):
            return json.loads((REPO_ROOT.joinpath(*parts)).read_text(encoding="utf-8"))

        version = load(".claude-plugin", "plugin.json")["version"]
        self.assertEqual(
            load(".claude-plugin", "marketplace.json")["plugins"][0]["version"],
            version,
        )
        self.assertEqual(
            load(".agents", "plugins", "marketplace.json")["plugins"][0]["version"],
            version,
        )
        manifest = json.loads(
            (ADAPTER / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], version)

    def test_no_page_pins_a_version_in_the_codex_cache_path(self):
        """Prose that repeats the number makes every release a prose edit.

        The READMEs once quoted the cache path with the version spelled out.
        `<version>` states the shape and leaves the number in the manifests,
        where one bump covers all four. The setup guide carries the path now.
        """
        guide = "skills/grounded-copy/references/setup.md"
        for page in ("README.md", "README.zh.md", guide):
            with self.subTest(page=page):
                text = (REPO_ROOT / page).read_text(encoding="utf-8")
                self.assertNotRegex(
                    text, r"/grounded-copy/\d+\.\d+\.\d+/",
                    "%s pins a version in a path; write <version> instead"
                    % page,
                )
        self.assertIn(
            "/grounded-copy/<version>/skills/grounded-copy/",
            (REPO_ROOT / guide).read_text(encoding="utf-8"),
            "the setup guide no longer shows the Codex cache path",
        )

    def test_the_codex_catalog_points_at_the_generated_tree(self):
        """A stale path here surfaces at install time on a user's machine."""
        catalog = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
            .read_text(encoding="utf-8")
        )
        entry = [p for p in catalog["plugins"] if p["name"] == "grounded-copy"][0]
        self.assertEqual(entry["source"]["path"], "./" + ADAPTER_REL.as_posix())

    def test_the_codex_payloads_name_the_codex_profile_verb(self):
        """`_policy.py` and `_preference.py` ship byte-for-byte, so the host
        verbs travel through the entrypoint seams. Codex has no slash command.
        """
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            policy = self._hook(CODEX_ACTIVATE, home=home,
                                stdin='{"source":"startup"}').stdout
            self.assertIn("$grounded-profile chat|copy|off", policy)
            self.assertNotIn("/grounded-copy:grounded", policy)
            self.assertEqual(
                self._hook(CODEX_TRACKER, ("--set", "off"), home=home).returncode, 0
            )
            status = self._hook(CODEX_TRACKER, ("--status",), home=home).stdout
            self.assertIn("run $grounded-profile chat to restore", status)


if __name__ == "__main__":
    unittest.main()
