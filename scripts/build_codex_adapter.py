#!/usr/bin/env python3
"""Generate and verify the Codex grounded-copy plugin.

The canonical skill lives at skills/grounded-copy/ and its internal layout is
the layout every host reads, so this builder mirrors that directory into the
generated tree at the same relative path. SKILL.md's own relative references
resolve in a checkout, in a Claude plugin install, in a skills-directory clone,
and here.

What stays generated: the Codex manifest, its hooks registration, the
$grounded-profile controller skill, and the package README. What gets rewritten
on the way in: the two hook entrypoints, through the seams below.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAPTER = os.path.join("dist", "codex", "grounded-copy")
SKILL_SOURCE = os.path.join("skills", "grounded-copy")
PLUGIN_MANIFEST = os.path.join(".claude-plugin", "plugin.json")
EXIT_OK = 0
EXIT_DRIFT = 1

# Junk that lands in a working tree stays out of a shipped package, on both
# walks: the source walk that builds the payload and the inventory walk that
# reports unexpected files.
#
# __pycache__ is load-bearing on each side. tests/test_corpus.py imports
# copy_lint in process, which writes a .pyc inside the payload tree, and
# running the generated hooks writes three more beside them. .gitignore keeps
# every one of them out of a commit, so a walk that counted them would ship a
# file that cannot travel, and report drift on a tree that has none.
IGNORED_DIRS = {"__pycache__", ".git"}
IGNORED_SUFFIXES = (".pyc", ".pyo", ".orig", ".rej", "~")


def _read(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def _version():
    """One number covers both packages; the Claude manifest carries it."""
    with open(os.path.join(REPO_ROOT, PLUGIN_MANIFEST), encoding="utf-8") as handle:
        return json.load(handle)["version"]


VERSION = _version()


def _copy_source(source, destination):
    payload = _read(os.path.join(REPO_ROOT, source))
    if payload is None:
        raise IOError("unreadable source: " + source)
    return destination, payload


# What each host-specific constant becomes in the copied entrypoint.
CODEX_PREFERENCE = (
    b'PREFERENCE_PATH = os.path.join(\n'
    b'    os.environ.get("CODEX_HOME") or os.path.join(\n'
    b'        os.path.expanduser("~"), ".codex"\n'
    b'    ),\n'
    b'    "grounded-copy",\n'
    b'    "profile",\n'
    b')'
)
CODEX_SWITCH = b'SWITCH_HINT = "$grounded-profile chat|copy|off"'
CODEX_RESTORE = b'RESTORE_HINT = "$grounded-profile chat"'

# The seams each entrypoint carries. grounded_activate.py writes the session
# policy and names the switch; grounded_tracker.py prints the status line and
# names the restore command. Neither carries the other's seam.
SEAMS = {
    "grounded_activate.py": (
        (b'PREFERENCE_PATH = None', CODEX_PREFERENCE),
        (b'SWITCH_HINT = None', CODEX_SWITCH),
    ),
    "grounded_tracker.py": (
        (b'PREFERENCE_PATH = None', CODEX_PREFERENCE),
        (b'RESTORE_HINT = None', CODEX_RESTORE),
    ),
}


def _codex_entrypoint(name):
    """The canonical entrypoint with its host seams rewritten.

    `bytes.replace` returns its input unchanged when the anchor is absent, so a
    renamed constant would ship a Claude-shaped entrypoint to Codex with the
    build still reporting success. A missing anchor raises here instead.
    """
    payload = _read(os.path.join(REPO_ROOT, "hooks", name))
    if payload is None:
        raise IOError("unreadable source: hooks/" + name)
    for anchor, replacement in SEAMS[name]:
        if anchor not in payload:
            raise IOError(
                "seam %r absent from hooks/%s" % (anchor.decode(), name)
            )
        payload = payload.replace(anchor, replacement)
    return payload


MANIFEST = json.dumps({
    "name": "grounded-copy", "version": VERSION,
    "description": "Grounded copy rules, lifecycle hooks, and an explicit profile controller.",
    "author": {"name": "HiroHyun", "url": "https://github.com/HiroHyun"},
    "homepage": "https://github.com/HiroHyun/grounded-copy",
    "repository": "https://github.com/HiroHyun/grounded-copy",
    "license": "MIT", "keywords": ["copywriting", "style", "linter", "i18n"],
    "skills": "./skills/", "hooks": "./hooks/hooks.json",
}, indent=2) + "\n"

HOOKS = json.dumps({"hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": 'sh "${PLUGIN_ROOT}/hooks/run.sh" grounded_activate.py', "commandWindows": '"${PLUGIN_ROOT}\\hooks\\run.cmd" grounded_activate.py'}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": 'sh "${PLUGIN_ROOT}/hooks/run.sh" grounded_tracker.py', "commandWindows": '"${PLUGIN_ROOT}\\hooks\\run.cmd" grounded_tracker.py'}]}],
}}, indent=2) + "\n"

PROFILE_SKILL = """---
name: grounded-profile
description: Show or change the grounded-copy writing mode.
---

# grounded-profile

Use this skill when the user explicitly asks to view or change the writing mode.

    $grounded-profile chat
    $grounded-profile copy
    $grounded-profile off
    $grounded-profile status

Run `python scripts/profile.py <operation>` from this skill directory. Accept exactly `chat`, `copy`, `off`, or `status` as the operation.

`chat` applies everyday writing rules. `copy` adds rules for promotional text. `off` stops the rules and reminders. `status` shows the saved setting.

The setting is saved at `$CODEX_HOME/grounded-copy/profile`, using `~/.codex` as the default home. After a successful change, report the status and apply the printed instructions from this turn forward. If saving fails, report the error.
"""

PROFILE_AGENT = """interface:\n  display_name: grounded-profile\n  short_description: Manage grounded-copy profile\n  default_prompt: Run the explicitly requested profile operation.\npolicy:\n  allow_implicit_invocation: false\n"""

PROFILE_SCRIPT = r'''#!/usr/bin/env python3
"""Explicit Codex profile controller."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "..", "..", "hooks")
sys.path.insert(0, os.path.abspath(HOOKS))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

OPS = {"chat": "chat", "copy": "copy", "off": "off", "status": "status"}
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2
RESTORE_HINT = "$grounded-profile chat"
SWITCH_HINT = "$grounded-profile chat|copy|off"
PREFERENCE_PATH = os.path.join(
    os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex"),
    "grounded-copy",
    "profile",
)

def main(argv):
    raw = argv[0].strip().lower() if argv else "status"
    operation = OPS.get(raw)
    if operation is None or len(argv) != 1:
        print("grounded: choose exactly chat, copy, off, or status")
        return EXIT_REJECTED
    if operation == "status":
        print(_preference.status_line(PREFERENCE_PATH, RESTORE_HINT))
        return 0
    ok, detail = _preference.write_preference(operation, PREFERENCE_PATH)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE
    print(_preference.status_line(PREFERENCE_PATH, RESTORE_HINT))
    print()
    root = os.environ.get("PLUGIN_ROOT") or os.path.abspath(os.path.join(ROOT, "..", ".."))
    skill = _policy.read_skill(root)
    source = "recorded at " + _preference.preference_path(PREFERENCE_PATH)
    print(_policy.governing_directive(skill, operation, source))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

README = """# grounded-copy for Codex

This package gives Codex writing rules, a copy checker, and three writing modes.

Use `$grounded-profile status` to see the current mode. Choose `$grounded-profile chat` for everyday writing, `$grounded-profile copy` for product copy, or `$grounded-profile off` to turn the rules off. Your choice stays saved after a restart.

The plugin loads rules at session start and adds a reminder with each prompt. Enable the hooks in Codex and complete any hook review requested by the app. The hooks guide the assistant; they do not scan each reply. Run `skills/grounded-copy/scripts/copy_lint.py` on saved files to check them.

The setting lives at `$CODEX_HOME/grounded-copy/profile`, or `~/.codex/grounded-copy/profile` by default.

Read the [setup guide](skills/grounded-copy/references/setup.md) for details and the [pattern guide](skills/grounded-copy/references/patterns.md) for examples. The repository has [English](https://github.com/HiroHyun/grounded-copy#readme) and [Chinese](https://github.com/HiroHyun/grounded-copy/blob/main/README.zh.md) introductions.

## Package maintenance

This directory is generated by `scripts/build_codex_adapter.py` in the repository. Edit the source files there, run the builder, and commit the generated files. The builder's `--check` option reports differences, missing files, and unexpected files.

## License

[MIT](LICENSE).
"""


def _skill_payloads():
    """Mirror skills/grounded-copy/ into the adapter at the same relative path.

    The source path is the destination path, which is the property the layout
    exists to produce. Sorted, so the build log reads the same on every
    platform.
    """
    base = os.path.join(REPO_ROOT, SKILL_SOURCE)
    items = []
    for current, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for name in sorted(files):
            if name.endswith(IGNORED_SUFFIXES):
                continue
            relative = os.path.relpath(os.path.join(current, name), REPO_ROOT)
            items.append(_copy_source(relative, relative.replace(os.sep, "/")))
    if not items:
        raise IOError("no skill payload under " + SKILL_SOURCE)
    return items


def payloads():
    items = _skill_payloads()
    items.append(_copy_source("LICENSE", "LICENSE"))
    items.append(_copy_source("hooks/_policy.py", "hooks/_policy.py"))
    for name in sorted(SEAMS):
        items.append(("hooks/" + name, _codex_entrypoint(name)))
    for name in ("run.sh", "run.cmd"):
        items.append(_copy_source("hooks/" + name, "hooks/" + name))
    items.append(_copy_source("hooks/_hook_io.py", "hooks/_hook_io.py"))
    items.append(_copy_source("hooks/_preference.py", "hooks/_preference.py"))
    items.extend([
        ("hooks/hooks.json", HOOKS.encode()),
        ("skills/grounded-profile/SKILL.md", PROFILE_SKILL.encode()),
        ("skills/grounded-profile/scripts/profile.py", PROFILE_SCRIPT.encode()),
        ("skills/grounded-profile/agents/openai.yaml", PROFILE_AGENT.encode()),
        (".codex-plugin/plugin.json", MANIFEST.encode()),
        ("README.md", README.encode()),
    ])
    return [(os.path.normpath(os.path.join(ADAPTER, dest)), data) for dest, data in items]


def _inventory(root):
    """Every shippable file under the generated tree, as a repo-relative set."""
    result = []
    if os.path.isdir(root):
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for name in files:
                if name.endswith(IGNORED_SUFFIXES):
                    continue
                result.append(os.path.normpath(os.path.relpath(os.path.join(base, name), REPO_ROOT)))
    return set(result)


def build():
    expected = {dest for dest, _ in payloads()}
    actual = _inventory(os.path.join(REPO_ROOT, ADAPTER))
    for orphan in sorted(actual - expected):
        os.remove(os.path.join(REPO_ROOT, orphan))
        print("deleted " + orphan.replace(os.sep, "/"))
    adapter_root = os.path.join(REPO_ROOT, ADAPTER)
    for base, dirs, _files in os.walk(adapter_root, topdown=False):
        for name in dirs:
            directory = os.path.join(base, name)
            if not os.listdir(directory):
                os.rmdir(directory)
                print("deleted " + os.path.relpath(directory, REPO_ROOT).replace(os.sep, "/"))
    for destination, data in payloads():
        path = os.path.join(REPO_ROOT, destination)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
        print("wrote " + destination.replace(os.sep, "/"))
    return EXIT_OK


def check():
    expected = {dest: data for dest, data in payloads()}
    drift = []
    for destination, data in expected.items():
        current = _read(os.path.join(REPO_ROOT, destination))
        if current is None:
            drift.append("missing: " + destination.replace(os.sep, "/"))
        elif current != data:
            drift.append("differs: " + destination.replace(os.sep, "/"))
    for orphan in sorted(_inventory(os.path.join(REPO_ROOT, ADAPTER)) - set(expected)):
        drift.append("unexpected: " + orphan.replace(os.sep, "/"))
    for line in drift:
        print("codex adapter " + line)
    if drift:
        print("run scripts/build_codex_adapter.py to rebuild")
        return EXIT_DRIFT
    print("codex adapter matches the canonical files")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv[1:] else build())
