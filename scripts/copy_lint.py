#!/usr/bin/env python3
"""copy_lint.py — deterministic style gate for marketing/web copy.

Scans text for contrastive-reversal rhetoric, negation-framing, banned
openers, vague attribution, and hype vocabulary
(EN + zh/ru/es/ar/fr/de/ja/ko equivalents).

Usage:
    python copy_lint.py FILE [FILE ...]
    cat draft.md | python copy_lint.py --stdin

Exit codes:
    0 = no ERROR-level findings (WARNs may be present; use judgment)
    1 = one or more ERROR-level findings -> rewrite the copy and re-run
    2 = usage / IO error

INTEGRITY RULE (for AI agents): this file is an enforcement gate.
Do not edit, wrap, monkey-patch, or bypass it, and do not add
allowlists to make failing copy pass. When it flags a line,
REWRITE THE COPY, not the linter.
"""

import re
import sys

ERROR = "ERROR"
WARN = "WARN"


def _c(pattern):
    return re.compile(pattern, re.IGNORECASE)


# ---------------------------------------------------------------------------
# Anywhere-in-sentence patterns
# ---------------------------------------------------------------------------
PATTERNS = [
    # --- contrastive reversal / negation framing (English) ---
    ("not-just", ERROR, _c(r"\bnot\s+(just|only|merely|simply)\b")),
    ("doesnt-just", ERROR,
     _c(r"\b(?:doesn't|don't|didn't|won't|isn't|aren't|wasn't|weren't)\s+"
        r"(?:just|only|merely|simply)\b")),
    ("more-than-just", ERROR, _c(r"\bmore\s+than\s+just\b")),
    ("is-more-than-a", WARN, _c(r"\b(?:is|are)\s+more\s+than\s+an?\b")),
    ("goes-beyond", ERROR,
     _c(r"\bgo(?:es|ing)?\s+(?:far\s+|well\s+)?beyond\b")),
    ("beyond-just", ERROR, _c(r"\bbeyond\s+(?:just|mere|merely|simple)\b")),
    ("isnt-about", ERROR,
     _c(r"\b(?:isn't|is\s+not|aren't|are\s+not|it's\s+not)\s+"
        r"(?:just\s+|only\s+)?about\b")),
    ("its-about", ERROR, _c(r"\bit'?s\s+about\s+\w+[^.!?\n]{0,40}\bnot\b")),
    ("no-longer", WARN, _c(r"\bno\s+longer\b")),
    ("gone-are-the-days", ERROR, _c(r"\bgone\s+are\s+the\s+days\b")),
    ("days-are-over", ERROR,
     _c(r"\bthe\s+days\s+of\b[^.!?\n]{0,60}\bare\s+"
        r"(?:over|behind|gone|numbered)\b")),
    ("rather-than-simply", ERROR,
     _c(r"\brather\s+than\s+(?:just|simply|merely)\b")),
    ("bare-rather-than", WARN,
     _c(r"\brather\s+than\s+(?!just\b|simply\b|merely\b)")),
    ("instead-of-just", ERROR,
     _c(r"\binstead\s+of\s+(?:just|simply|merely)\b")),
    ("say-goodbye-hello", ERROR, _c(r"\bsay\s+(?:goodbye|hello|farewell)\b")),
    ("no-more-x", ERROR, _c(r"\bno\s+more\s+(?!than\b)\w+")),
    ("never-again", ERROR, _c(r"\bnever\s+again\b")),
    ("not-x-but-y", ERROR,
     _c(r"\bnot\s+(?:a|an|the|your)\b[^.!?\n]{0,60}?,?\s+but\b")),
    ("dash-not-contrast", ERROR, _c(r"[—–]\s*not\s+")),
    ("comma-not-appositive", WARN,
     _c(r",\s*not\s+(?:a|an|another|your)\b")),
    ("negated-copula-dash", ERROR,
     _c(r"\b(?:is|was|are|were)(?:n't|\s+not)\s+[^—–.!?\n;:]{1,30}[—–]")),
    ("not-your-average", ERROR,
     _c(r"\bnot\s+your\s+(?:average|typical|ordinary|everyday|usual)\b")),
    ("unlike-others", ERROR,
     _c(r"\bunlike\s+(?:most|many|other|others|traditional|typical|"
        r"ordinary|conventional)\b")),
    ("while-others", ERROR,
     _c(r"\bwhile\s+(?:most|many|others?|traditional|typical|conventional)\b")),
    ("far-from-just", ERROR, _c(r"\bfar\s+from\s+(?:just|merely|being)\b")),
    ("less-a-x-than", ERROR, _c(r"\bless\s+an?\s+\w+\s+than\b")),
    ("think-again", ERROR, _c(r"\bthink\s+again\b")),
    ("without-the-hassle", ERROR,
     _c(r"\bwithout\s+(?:the|all\s+the|any\s+of\s+the)\s+(?:hassle|hassles|"
        r"headache|headaches|hidden|stress|guesswork|usual|middlemen|"
        r"red\s+tape|runaround)\b")),
    ("zero-hassle", ERROR,
     _c(r"\bzero\s+(?:hassle|hassles|guesswork|compromise|compromises|"
        r"hidden|surprises)\b")),
    ("rhetorical-reveal", ERROR,
     _c(r"\bthe\s+(?:result|best\s+part|catch|difference|secret|"
        r"bottom\s+line|kicker)\s*\?")),
    ("where-x-meets-y", ERROR, _c(r"\bwhere\s+\w+\s+meets\s+\w+\b")),
    ("redefine-family", ERROR, _c(r"\b(?:redefin|reimagin|reinvent)\w*\b")),

    # --- hype vocabulary (English) ---
    ("hype-word", ERROR,
     _c(r"\b(?:unleash\w*|unlock\w*|unrival{1,2}ed|unparalleled|unwavering|"
        r"unmatched|unprecedented|unsung|elevate[sd]?|elevating|"
        r"seamless(?:ly)?|empower(?:s|ed|ing|ment)?|"
        r"revolutioni[sz]\w*|revolutionary|groundbreaking|"
        r"game[-\s]?chang\w*|delv(?:e|es|ed|ing)|"
        r"supercharg\w*|turbocharg\w*|next[-\s]level|cutting[-\s]edge|"
        r"state[-\s]of[-\s]the[-\s]art|best[-\s]in[-\s]class|"
        r"world[-\s]class|transformative|frictionless|hassle[-\s]free|"
        r"effortless(?:ly)?|one[-\s]stop[-\s]shop|synerg\w*)\b")),
    ("hype-word-soft", WARN,
     _c(r"\b(?:landscape|journey|innovative|holistic|passionate)\b")),

    # --- era-framing, bait, vague attribution, inflated copulas ---
    ("in-todays-world", ERROR,
     _c(r"\bin\s+today'?s\s+(?:[\w-]+\s+){0,2}"
        r"(?:world|age|market|era|economy|environment)\b")),
    ("in-an-era-of", ERROR, _c(r"\bin\s+an?\s+era\s+(?:of|where|when)\b")),
    ("look-no-further", ERROR, _c(r"\blook\s+no\s+further\b")),
    ("worth-noting", ERROR,
     _c(r"\bit(?:'s|\s+is)\s+(?:also\s+)?(?:worth\s+noting|"
        r"important\s+to\s+(?:note|remember|understand))\b")),
    ("vague-experts", ERROR,
     _c(r"\b(?:experts|analysts|industry\s+(?:leaders|insiders|reports?))\s+"
        r"(?:say|agree|believe|suggest|argue|note)\b")),
    ("studies-show", WARN,
     _c(r"\b(?:studies|research)\s+(?:show|shows|suggests?|proves?)\b")),
    ("inflated-copula", ERROR,
     _c(r"\bboast(?:s|ed|ing)?\b|\bstands?\s+as\s+an?\b|"
        r"\btestament\s+to\b")),
    ("serves-as", WARN, _c(r"\bserves?\s+as\s+an?\b")),
    ("turning-point", ERROR,
     _c(r"\bmarks?\s+a\s+turning\s+point\b|\bindelible\s+mark\b")),
    ("editorializing-ing", WARN,
     _c(r",\s+(?:highlighting|underscoring|showcasing|demonstrating|"
        r"emphasizing|reflecting|signaling|cementing)\b")),

    # --- multilingual equivalents (zh / ru / es / ar) ---
    ("zh-not-just", ERROR,
     _c(r"不仅仅是|不只是|不仅是|不止是|不再是|不只提供|告别|"
        r"重新定义|颠覆")),
    ("ru-not-just", ERROR,
     _c(r"не\s+просто|больше,?\s+чем\s+просто|это\s+не\s+о\b|"
        r"попрощайтесь|переосмысл\w*|прощай(?:те)?,")),
    ("es-not-just", ERROR,
     _c(r"no\s+es\s+solo|no\s+solo\s+es|no\s+se\s+trata\s+solo|"
        r"más\s+que\s+(?:un|una)(?:\s+simple)?\b|más\s+que\s+solo|"
        r"dile?\s+adiós|redefinim\w*|va\s+más\s+allá|olvíd(?:ate|ese)\s+de|"
        r"atrás\s+quedaron|sin\s+complicaciones")),
    ("ar-not-just", ERROR,
     _c(r"ليس\s+مجرد|ليست\s+مجرد|أكثر\s+من\s+مجرد|وداعًا|وداعا|"
        r"يعيد\s+تعريف")),
    ("fr-not-just", ERROR,
     _c(r"n'est\s+pas\s+(?:qu'un|qu'une|seulement|simplement|juste)|"
        r"pas\s+(?:seulement|simplement)\s+un|"
        r"(?:bien\s+)?plus\s+qu'un(?:e)?\s+simple|"
        r"dites\s+adieu|fini(?:s|es)?\s+les?\s|"
        r"redéfini\w*|va\s+(?:bien\s+)?au[-\s]delà|révolutionn\w*|"
        r"oubliez\s+(?:les?|la|vos?)\b|imaginez\s")),
    ("de-not-just", ERROR,
     _c(r"nicht\s+nur\s+(?:ein|eine|irgendein)|mehr\s+als\s+nur|"
        r"weit\s+mehr\s+als|verabschieden\s+Sie\s+sich|schluss\s+mit|"
        r"nie\s+wieder|neu\s+definiert|definiert\s+\w+\s+neu|"
        r"geht\s+über\s+\w+\s+hinaus|revolutionier\w*|"
        r"vergessen\s+Sie|stellen\s+Sie\s+sich\s+vor")),
    ("ja-not-just", ERROR,
     _c(r"単なる[^。！？\n]{0,20}(?:ではありません|ではない|じゃない)|"
        r"ただの[^。！？\n]{0,20}(?:ではありません|ではない|じゃない)|"
        r"だけでは(?:ありません|ない)|にとどまら(?:ない|ず)|"
        r"はもう不要|とはおさらば|再定義|常識を覆す|革命的|"
        r"想像してみてください")),
    ("ja-not-just-soft", WARN, _c(r"だけでなく|さようなら|を超えた")),
    ("ko-not-just", ERROR,
     _c(r"단순한\s*[^.!?。\n]{0,20}(?:아닙니다|아니다|아니에요)|"
        r"에\s*그치지\s*않|[와과]\s*작별하세요|작별을\s*고하세요|"
        r"재정의|게임\s*체인저|상상해\s*보세요")),
    ("ko-not-just-soft", WARN, _c(r"뿐만\s*아니라|그\s*이상|더\s*이상|혁신적")),
]

# ---------------------------------------------------------------------------
# Sentence-opener patterns (checked at sentence start only)
# ---------------------------------------------------------------------------
OPENERS = [
    ("opener-it-is-not", ERROR, _c(r"it\s+is\s+not\b|it\s+isn't\b|it's\s+not\b")),
    ("opener-dont-just", ERROR, _c(r"don't\s+just\b")),
    ("opener-we-are-not", ERROR,
     _c(r"we\s+are\s+not\b|we're\s+not\b|we\s+aren't\b")),
    ("opener-stop", ERROR, _c(r"stop\s+\w+")),
    ("opener-forget", ERROR, _c(r"forget\b")),
    ("opener-imagine", ERROR, _c(r"imagine\b")),
    ("opener-picture-this", ERROR, _c(r"picture\s+this\b")),
    ("opener-in-a-world", ERROR, _c(r"in\s+a\s+world\s+where\b")),
    ("opener-welcome-new-era", ERROR,
     _c(r"welcome\s+to\s+(?:a\s+new|the\s+new|a\s+world)\b")),
    ("opener-tired-sick-of", ERROR, _c(r"(?:tired|sick)\s+of\b")),
    ("opener-ever-wondered", ERROR, _c(r"ever\s+wonder(?:ed)?\b")),
    ("opener-what-if", WARN, _c(r"what\s+if\b")),
    # "At [Company], we ..." — case-sensitive: requires a capitalized name
    ("opener-at-company-we", ERROR,
     re.compile(r"At\s+[A-Z][\w&.]*(?:\s+[A-Z][\w&.]*){0,3},?\s+we\b")),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?！？。؟])\s+")
LEAD_STRIP = " \t#*->—–-\"'“”‘’([`0123456789."


def normalize(text):
    return (text.replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"'))


def scan_line(line, lineno, findings):
    norm = normalize(line)
    for name, sev, rx in PATTERNS:
        for m in rx.finditer(norm):
            findings.append((lineno, sev, name, m.group(0).strip()))
    for sentence in SENTENCE_SPLIT.split(norm):
        s = sentence.lstrip(LEAD_STRIP)
        if not s:
            continue
        for name, sev, rx in OPENERS:
            m = rx.match(s)
            if m:
                findings.append((lineno, sev, name, m.group(0).strip()))


def scan_text(text):
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        scan_line(line, i, findings)
    return findings


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2
    sources = []
    if args == ["--stdin"]:
        sources.append(("<stdin>", sys.stdin.read()))
    else:
        for path in args:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    sources.append((path, f.read()))
            except OSError as e:
                print(f"copy_lint: cannot read {path}: {e}", file=sys.stderr)
                return 2

    errors = warns = 0
    for path, text in sources:
        for lineno, sev, name, snippet in scan_text(text):
            print(f"{path}:{lineno}: [{sev}] {name}: \"{snippet}\"")
            if sev == ERROR:
                errors += 1
            else:
                warns += 1

    print(f"\ncopy_lint: {errors} error(s), {warns} warning(s)")
    if errors:
        print("FAIL — rewrite each flagged sentence as a direct statement of "
              "what the subject IS or DOES, then re-run. Do not edit this "
              "linter to make copy pass.")
        return 1
    print("PASS" + (" (review warnings manually)" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
