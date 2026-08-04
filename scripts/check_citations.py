#!/usr/bin/env python3
"""Assert the documented citation set is unchanged.

Files in this repository quote the patterns they document, so each reports
findings against its own gate. This pins that set: the rule id and the matched
snippet each cited file is known to carry, sorted, with line numbers dropped so
an edit that moves text leaves the record alone.

A read-only consumer of copy_lint. It imports the scanner and changes no
pattern, no exit code, and no finding. It can fail a build; it can never let
copy through that `copy_lint.py` would flag.

Usage:
    python3 scripts/check_citations.py            compare, exit 1 on drift
    python3 scripts/check_citations.py --write    record the current set
"""

import difflib
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "skills", "grounded-copy", "scripts"))
import copy_lint  # noqa: E402

BASELINE = os.path.join("tests", "citations-baseline.txt")

# Every file that quotes the patterns it documents. A file outside this list
# is held at zero by the corpus jobs in .github/workflows/copy-lint.yml.
CITED = (
    "README.md",
    "README.zh.md",
    os.path.join("skills", "grounded-copy", "references", "patterns.md"),
)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_IO = 2


def observed():
    rows = []
    for relative in CITED:
        path = os.path.join(REPO_ROOT, relative)
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        name = relative.replace(os.sep, "/")
        for _lineno, rule, snippet in copy_lint.scan_text(text):
            rows.append("%s\t%s\t%s" % (name, rule, snippet))
    return sorted(rows)


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    path = os.path.join(REPO_ROOT, BASELINE)
    rows = observed()

    if "--write" in argv:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(rows) + "\n")
        print("wrote %s, %d citations" % (BASELINE.replace(os.sep, "/"), len(rows)))
        return EXIT_OK

    try:
        with open(path, encoding="utf-8") as handle:
            recorded = [line for line in handle.read().split("\n") if line]
    except OSError as e:
        print("check_citations: cannot read %s: %s"
              % (BASELINE.replace(os.sep, "/"), e), file=sys.stderr)
        return EXIT_IO

    diff = list(difflib.unified_diff(recorded, rows, "recorded", "observed",
                                     lineterm=""))
    if diff:
        print("\n".join(diff))
        print("\ncheck_citations: the citation set moved, %d recorded and %d "
              "observed." % (len(recorded), len(rows)))
        print("A line under + that you did not add on purpose is prose to "
              "rewrite. A specimen you did add is recorded with --write.")
        return EXIT_DRIFT

    print("check_citations: %d citations, unchanged" % len(rows))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
