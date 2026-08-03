#!/usr/bin/env python3
"""One command that installs grounded-copy wherever it can run.

    curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.py | python3 -

`python3 -` forwards trailing arguments, so flags work from the pipe:

    curl -fsSL .../install.py | python3 - --skills-only --yes

What it does: detect which agents are present, then drive each host's own
CLI. Claude Code and Codex install the full plugin through their marketplace
verbs; every other agent gets the skill through the Skills CLI. Updates and
removal stay with those same tools, so this script owns no state and writes no
file of its own.

Every step is planned before anything runs, and `--dry-run` prints the plan and
stops. Re-running is safe: each underlying verb is idempotent.

Usage:
    install.py [--only NAME]... [--skills-only] [--dry-run] [--list]
               [--yes] [--uninstall] [--no-color]
"""

import os
import shutil
import subprocess
import sys

REPO = "HiroHyun/grounded-copy"
MARKETPLACE = "hirohyun-plugins"
PLUGIN = "grounded-copy"
SKILL = "grounded-copy"
RAW_BASE = "https://raw.githubusercontent.com/HiroHyun/grounded-copy/main"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

# Agents the Skills CLI installs into, and the marker under $HOME that says the
# agent is present. The name on the left is the CLI's own `-a` profile.
SKILL_AGENTS = (
    ("claude-code", ".claude"),
    ("codex", ".codex"),
    ("cursor", ".cursor"),
    ("windsurf", ".windsurf"),
    ("github-copilot", ".copilot"),
    ("gemini-cli", ".gemini"),
    ("opencode", os.path.join(".config", "opencode")),
)

# Hosts with a plugin CLI of their own. These carry the hooks, the profiles,
# and the profile switch, which the portable skill leaves out.
PLUGIN_HOSTS = ("claude", "codex")

MANUAL = """No agent CLI resolved. Fetch the skill directly:

  base=%s/skills/grounded-copy
  mkdir -p grounded-copy/references grounded-copy/scripts grounded-copy/tests
  curl -o grounded-copy/SKILL.md                $base/SKILL.md
  curl -o grounded-copy/references/patterns.md  $base/references/patterns.md
  curl -o grounded-copy/references/setup.md     $base/references/setup.md
  curl -o grounded-copy/scripts/copy_lint.py    $base/scripts/copy_lint.py
  curl -o grounded-copy/tests/bad-samples.md    $base/tests/bad-samples.md
  curl -o grounded-copy/tests/good-samples.md   $base/tests/good-samples.md

Point any agent at SKILL.md and run copy_lint.py from the command line.""" % (
    RAW_BASE,
)


class Options(object):
    """Everything the plan depends on, parsed once."""

    def __init__(self):
        self.only = []
        self.skills_only = False
        self.dry_run = False
        self.listing = False
        self.assume_yes = False
        self.uninstall = False
        self.color = True


def parse_args(argv):
    """(Options, error). A rejected flag reports itself and installs nothing."""
    options = Options()
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--only":
            index += 1
            if index >= len(argv):
                return None, "--only wants a name"
            options.only.append(argv[index].strip().lower())
        elif argument.startswith("--only="):
            options.only.append(argument.split("=", 1)[1].strip().lower())
        elif argument == "--skills-only":
            options.skills_only = True
        elif argument == "--dry-run":
            options.dry_run = True
        elif argument in ("--list", "-l"):
            options.listing = True
        elif argument in ("--yes", "-y"):
            options.assume_yes = True
        elif argument in ("--uninstall", "-u"):
            options.uninstall = True
        elif argument == "--no-color":
            options.color = False
        elif argument in ("--help", "-h"):
            return None, "help"
        else:
            return None, "unknown flag: " + argument
        index += 1

    known = set(PLUGIN_HOSTS) | {"skills"} | {name for name, _ in SKILL_AGENTS}
    for name in options.only:
        if name not in known:
            return None, "unknown --only target: " + name
    return options, ""


def have_command(name):
    return shutil.which(name) is not None


def detect(home=None, which=have_command):
    """What is present: plugin CLIs on PATH, agents by their config directory.

    `which` and `home` are parameters so a test can describe a machine.
    """
    home = home or os.path.expanduser("~")
    found = {
        "commands": sorted(n for n in PLUGIN_HOSTS if which(n)),
        "npx": which("npx") or which("node"),
        "agents": [],
    }
    for name, marker in SKILL_AGENTS:
        if os.path.isdir(os.path.join(home, marker)):
            found["agents"].append(name)
    return found


def _wanted(options, target, agent=None):
    """Does `--only` admit this step? With no `--only`, everything runs."""
    if not options.only:
        return True
    if target in options.only:
        return True
    return agent is not None and agent in options.only


def plan(options, found):
    """The ordered steps, as (label, argv) pairs. Pure: it runs nothing."""
    steps = []
    verb = "uninstall" if options.uninstall else "install"

    if not options.skills_only:
        for host in found["commands"]:
            if not _wanted(options, host):
                continue
            if options.uninstall:
                if host == "claude":
                    steps.append((
                        "claude: remove the plugin",
                        ["claude", "plugin", "uninstall",
                         "%s@%s" % (PLUGIN, MARKETPLACE), "-y"],
                    ))
                else:
                    # `codex plugin remove` wants PLUGIN@MARKETPLACE or a
                    # --marketplace flag; a bare name exits with
                    # "plugin requires --marketplace unless passed as
                    # <plugin>@<marketplace>".
                    steps.append((
                        "codex: remove the plugin",
                        ["codex", "plugin", "remove",
                         "%s@%s" % (PLUGIN, MARKETPLACE)],
                    ))
                continue
            steps.append((
                "%s: add the marketplace" % host,
                [host, "plugin", "marketplace", "add", REPO],
            ))
            if host == "claude":
                steps.append((
                    "claude: install the plugin",
                    ["claude", "plugin", "install",
                     "%s@%s" % (PLUGIN, MARKETPLACE), "-s", "user"],
                ))
            else:
                steps.append((
                    "codex: install the plugin",
                    ["codex", "plugin", "add", "%s@%s" % (PLUGIN, MARKETPLACE)],
                ))

    agents = list(found["agents"])
    if not options.skills_only:
        # A host that took the plugin already has the skill, with the hooks.
        agents = [a for a in agents
                  if a.split("-")[0] not in found["commands"]]
    if agents and found["npx"]:
        if options.uninstall:
            if _wanted(options, "skills"):
                steps.append((
                    "skills: remove the skill",
                    ["npx", "-y", "skills", "remove", SKILL, "--yes"],
                ))
        else:
            for agent in agents:
                if not _wanted(options, "skills", agent):
                    continue
                steps.append((
                    "skills: %s the skill for %s" % (verb, agent),
                    ["npx", "-y", "skills", "add", REPO,
                     "--skill", SKILL, "-a", agent, "--yes"],
                ))
    return steps


def render(steps, color=True):
    lines = []
    bold, plain = ("\033[1m", "\033[0m") if color else ("", "")
    for label, argv in steps:
        lines.append("  %s%s%s\n      %s" % (bold, label, plain, " ".join(argv)))
    return "\n".join(lines)


def confirm(steps, options, reader=None):
    """Ask once, before the first command runs."""
    if options.assume_yes or options.dry_run or options.listing:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        # Under `curl | python3 -` stdin holds the script, so a prompt would
        # read the remaining source as an answer. Announce and proceed.
        print("No terminal on stdin; running the plan above.")
        return True
    reader = reader or input
    try:
        answer = reader("Run these %d command(s)? [y/N] " % len(steps))
    except (EOFError, KeyboardInterrupt):
        return False
    return answer.strip().lower() in ("y", "yes")


def run(steps):
    """Execute each step, reporting the ones that fail. Returns an exit code."""
    failed = []
    for label, argv in steps:
        print("\n==> " + label)
        try:
            code = subprocess.call(argv)
        except OSError as exc:
            print("    failed to start: %s" % exc)
            failed.append(label)
            continue
        if code != 0:
            print("    exited %d" % code)
            failed.append(label)
    if failed:
        print("\n%d step(s) failed:" % len(failed))
        for label in failed:
            print("  " + label)
        return EXIT_FAILED
    return EXIT_OK


def main(argv):
    options, error = parse_args(argv)
    if options is None:
        print(__doc__ if error == "help" else "grounded-copy: " + error)
        return EXIT_OK if error == "help" else EXIT_USAGE

    found = detect()
    steps = plan(options, found)

    print("grounded-copy installer")
    print("  plugin CLIs: %s" % (", ".join(found["commands"]) or "none"))
    print("  agents:      %s" % (", ".join(found["agents"]) or "none"))
    print("  npx:         %s" % ("yes" if found["npx"] else "no"))

    if not steps:
        print()
        print(MANUAL if not found["commands"] else
              "Nothing matched the requested targets.")
        return EXIT_OK

    print("\nPlan:")
    print(render(steps, options.color))

    if options.listing or options.dry_run:
        return EXIT_OK
    if not confirm(steps, options):
        print("Cancelled.")
        return EXIT_OK
    return run(steps)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
