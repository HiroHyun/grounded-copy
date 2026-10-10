#!/usr/bin/env python3
"""One command that installs grounded-copy wherever it can run.

    curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh

The shell launcher forwards trailing arguments to this installer:

    curl -fsSL .../install.sh | sh -s -- --skills-only --yes

What it does: detect the Claude Code and Codex plugin CLIs, then drive each
host's marketplace verbs. One universal Skills CLI step installs the portable
skill for every agent that CLI supports. Updates and removal stay with those
same tools, so this script owns no state and writes no file of its own.

One exception, on request: `--always-on` adds a marked block to the user-level
instruction file of Claude Code and Codex, for a host that gets the skill and
no plugin. A skill loads when the agent judges it relevant, and the block makes
every session apply it. Re-running replaces the block; `--uninstall` removes
it.

Every step is planned before anything runs, and `--dry-run` prints the plan and
stops. Re-running is safe: each underlying verb is idempotent.

Usage:
    install.py [--only NAME]... [--skills-only] [--always-on] [--dry-run]
               [--list] [--yes] [--uninstall] [--no-color]
"""

import os
import shutil
import subprocess
import sys
import time

REPO = "HiroHyun/grounded-copy"
MARKETPLACE = "hirohyun-plugins"
PLUGIN = "grounded-copy"
SKILL = "grounded-copy"
RAW_BASE = "https://raw.githubusercontent.com/HiroHyun/grounded-copy/main"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

# Hosts with a plugin CLI of their own. These carry the hooks, the profiles,
# and the profile switch, which the portable skill leaves out.
PLUGIN_HOSTS = ("claude", "codex")

# Where `--always-on` writes: (host, variable naming its config directory, the
# default directory, the instruction file). A plugin's SessionStart hook already
# delivers the rules, so a host that gets its plugin in the same run is skipped.
INSTRUCTION_FILES = (
    ("claude", "CLAUDE_CONFIG_DIR", "~/.claude", "CLAUDE.md"),
    ("codex", "CODEX_HOME", "~/.codex", "AGENTS.md"),
)
# argv[0] of a plan step that `run()` performs itself.
WRITE_BLOCK = "write-block"
BLOCK_START = "<!-- grounded-copy:start -->"
BLOCK_END = "<!-- grounded-copy:end -->"
BLOCK = "\n".join((
    BLOCK_START,
    "# Prose",
    "Apply the grounded-copy skill's `chat` rules to every reply and every "
    "file a person reads.",
    "Load the skill once per session if its rules are not in context.",
    BLOCK_END,
)) + "\n"

CLAUDE_PRECEDENCE_NOTE = """Claude Code may list grounded-copy@skills-dir as
\"Not loaded\" because grounded-copy@hirohyun-plugins owns that skill name.
The installed plugin supplies the same skill plus hooks."""

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
        self.always_on = False
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
        elif argument == "--always-on":
            options.always_on = True
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

    known = set(PLUGIN_HOSTS) | {"skills"}
    for name in options.only:
        if name not in known:
            return None, "unknown --only target: " + name
    return options, ""


def have_command(name):
    return shutil.which(name) is not None


def resolve(name, which=shutil.which):
    """The launch path for a bare command name.

    `subprocess` hands argv[0] to CreateProcess, which applies no PATHEXT
    search, so a bare `codex` misses the `codex.CMD` that npm installs on
    Windows and the call raises OSError. `shutil.which` reads PATHEXT and
    returns that path. On POSIX it returns the same file the shell would run.
    """
    return which(name) or name


def detect(which=have_command):
    """Return the plugin and Skills CLIs available on PATH."""
    return {
        "commands": sorted(n for n in PLUGIN_HOSTS if which(n)),
        "npx": which("npx") or which("node"),
    }


def _wanted(options, target):
    """Does `--only` admit this step? With no `--only`, everything runs."""
    return not options.only or target in options.only


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

    if found["npx"] and _wanted(options, "skills"):
        if options.uninstall:
            steps.append((
                "skills: remove the universal skill",
                ["npx", "-y", "skills", "remove", SKILL, "--yes"],
            ))
        else:
            steps.append((
                "skills: %s the universal skill" % verb,
                ["npx", "-y", "skills", "add", REPO,
                 "--skill", SKILL, "--yes"],
            ))
            if options.always_on:
                for host, _variable, directory, filename in INSTRUCTION_FILES:
                    gets_plugin = (not options.skills_only
                                   and host in found["commands"]
                                   and _wanted(options, host))
                    if not gets_plugin:
                        steps.append((
                            "%s: add the Prose block to %s/%s"
                            % (host, directory, filename),
                            [WRITE_BLOCK, host],
                        ))
    return steps


def installs_claude_and_skills(steps):
    """Whether a successful plan needs the Claude precedence note."""
    commands = [argv for _label, argv in steps]
    has_claude = any(argv[:3] == ["claude", "plugin", "install"]
                     for argv in commands)
    has_skills = any(argv[:4] == ["npx", "-y", "skills", "add"]
                    for argv in commands)
    return has_claude and has_skills


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
    except EOFError:
        # `irm install.ps1 | iex` leaves the console attached, so the isatty
        # check above reports a terminal and the first read still hits end of
        # file. Same condition as that branch: no answer is obtainable.
        print("\nNo answer available on stdin; running the plan above.")
        return True
    except KeyboardInterrupt:
        return False
    return answer.strip().lower() in ("y", "yes")


def cleanup_claude_cache(env=None, sleeper=time.sleep):
    """Remove this plugin's orphaned Claude cache after a successful uninstall."""
    env = os.environ if env is None else env
    config = env.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    marketplace = os.path.join(
        os.path.expanduser(config), "plugins", "cache", MARKETPLACE
    )
    plugin_cache = os.path.join(marketplace, PLUGIN)
    if not os.path.lexists(plugin_cache):
        return True

    error = None
    for attempt in range(2):
        try:
            shutil.rmtree(plugin_cache)
            error = None
            break
        except OSError as exc:
            error = exc
            if attempt == 0:
                sleeper(0.1)

    if os.path.lexists(plugin_cache):
        print("    Claude retained its cache at %s: %s" % (plugin_cache, error))
        return False

    try:
        os.rmdir(marketplace)
    except OSError:
        pass
    return True


def instruction_file(host, env=None):
    """A host's user-level instruction file, or None when the host's config
    directory is absent, which means the host is not on this machine."""
    env = os.environ if env is None else env
    for name, variable, default, filename in INSTRUCTION_FILES:
        if name == host:
            directory = os.path.expanduser(env.get(variable) or default)
            if os.path.isdir(directory):
                return os.path.join(directory, filename)
    return None


def edit_block(host, add, env=None):
    """Add, replace, or remove the marked block. False means a failure.

    The file is the user's own. Every byte outside the two markers stays, and
    a file that will not read as UTF-8, or that holds one marker of the pair,
    is left as it is.
    """
    path = instruction_file(host, env)
    if path is None:
        if add:
            print("    no %s config directory here; skipped" % host)
        return True
    text = ""
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as handle:
                text = handle.read()
    except (OSError, UnicodeError) as exc:
        print("    cannot read %s: %s" % (path, exc))
        return False

    start, end = text.find(BLOCK_START), text.find(BLOCK_END)
    if (start < 0) != (end < 0) or end < start:
        print("    %s holds half a grounded-copy block; left as it is" % path)
        return False
    newline = "\r\n" if "\r\n" in text else "\n"
    block = BLOCK.replace("\n", newline)
    if start >= 0:
        head, tail = text[:start], text[end + len(BLOCK_END):]
        if tail.startswith(newline):
            tail = tail[len(newline):]
        if not add and head.endswith(newline * 2):
            # The blank line this function put in front of the block.
            head = head[:-len(newline)]
        updated = head + (block if add else "") + tail
    elif add:
        if text and not text.endswith(newline):
            text += newline
        updated = text + (newline if text else "") + block
    else:
        return True

    try:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(updated)
    except OSError as exc:
        print("    cannot write %s: %s" % (path, exc))
        return False
    print("    %s the block in %s" % ("wrote" if add else "removed", path))
    return True


def run(steps):
    """Execute each step, reporting the ones that fail. Returns an exit code."""
    failed = []
    for label, argv in steps:
        print("\n==> " + label)
        if argv[0] == WRITE_BLOCK:
            # The block points at the skill, so it waits on the steps above.
            if failed:
                print("    skipped: an earlier step failed")
            elif not edit_block(argv[1], add=True):
                failed.append(label)
            continue
        try:
            code = subprocess.call([resolve(argv[0])] + argv[1:])
        except OSError as exc:
            print("    failed to start: %s" % exc)
            failed.append(label)
            continue
        if code != 0:
            print("    exited %d" % code)
            failed.append(label)
        elif argv[:4] == ["claude", "plugin", "uninstall",
                          "%s@%s" % (PLUGIN, MARKETPLACE)]:
            cleanup_claude_cache()
        elif argv[:4] == ["npx", "-y", "skills", "remove"]:
            for host, _variable, _directory, _filename in INSTRUCTION_FILES:
                edit_block(host, add=False)
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
    print("  npx:         %s" % ("yes" if found["npx"] else "no"))

    if not steps:
        print()
        print(MANUAL if not found["commands"] and not found["npx"] else
              "Nothing matched the requested targets.")
        return EXIT_OK

    print("\nPlan:")
    print(render(steps, options.color))

    if options.listing or options.dry_run:
        return EXIT_OK
    if not confirm(steps, options):
        print("Cancelled.")
        return EXIT_OK
    code = run(steps)
    if code == EXIT_OK and installs_claude_and_skills(steps):
        print("\nNote: " + CLAUDE_PRECEDENCE_NOTE)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
