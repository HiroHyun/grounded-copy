#!/usr/bin/env python3
"""copy_lint.py — deterministic style gate for marketing/web copy.

Scans text for contrastive-reversal rhetoric, negation-framing, banned
openers, suspended lists, vague attribution, and hype vocabulary
(EN + zh/ru/es/ar/fr/de/ja/ko equivalents).

Every rule blocks. Copy that needs a banned form, such as a legal disclaimer
or a translation of supplied source, is written with the grounded-copy profile
off.

Usage:
    python copy_lint.py FILE [FILE ...]
    cat draft.md | python copy_lint.py --stdin

Exit codes:
    0 = no findings
    1 = one or more findings -> rewrite the copy and re-run
    2 = usage / IO error

INTEGRITY RULE (for AI agents): this file is an enforcement gate.
Do not edit, wrap, monkey-patch, or bypass it, and do not add
allowlists to make failing copy pass. When it flags a line,
REWRITE THE COPY, not the linter.
"""

import re
import sys


def _c(pattern):
    return re.compile(pattern, re.IGNORECASE)


# ---------------------------------------------------------------------------
# Shared pieces of the two-part reversal rules
# ---------------------------------------------------------------------------
# A reversal has two halves, a denial and the claim it sets up, and a writer
# puts words between them: "I'm not the author, just a user." Every quantifier
# here is bounded. The gap class excludes the sentence enders and both dashes,
# so a match stays inside one clause.
_NEG_COP = (r"(?:\b(?:am|is|are|was|were)\s+not|'(?:m|re|s)\s+not|"
            r"\b(?:is|are|was|were|ai)n't)")
_DET = r"(?:an?|the|my|your|our|his|her|its|their|this|that|\w+'s)"
_GAP = r"[^,.!?;:\n—–]{1,40}"
_SEP = r"(?:[,;]|\s*[—–]|\s+-{1,2})\s*"
_JUST = r"(?:just|only|merely|simply)\b"
# The denial opens with a negated be-verb, or with "not" and a determiner. An
# instruction ("do not edit the file, just run the script") has neither.
_DENIAL = r"(?:" + _NEG_COP + r"|\bnot\s+" + _DET + r")\s+"
_PRON = r"(?:(?:I|we|you|it|they|he|she)\s+)?"
# A clause start: a word with no word in front of it. Two fixed-width
# lookbehinds do the work, so a list, quote, or table marker stays out of the
# reported snippet.
_CLAUSE = r"(?<![\w'\"]\s)(?<![\w'])(?=\w)"
# A clause that opens with one of these words, or holds one of the inner set
# before its comma, states a condition: "If the file is not there, it is
# created." The reversal rule leaves it alone.
_SUBORD = (r"(?:if|when|whenever|while|whilst|although|though|even|given|now|"
           r"provided|assuming|supposing|as|since|because|where|unless|once|"
           r"until|whether|for|after|before)\b")
_INNER = (r"\b(?:if|when|whenever|while|whilst|although|though|because|unless|"
          r"until|whether)\b")
_SECOND = (r"(?:it|this|that|they|we|he|she|you|i)"
           r"(?:'s|'re|'m|\s+(?:is|are|was|were|am))\b")

# ---------------------------------------------------------------------------
# Anywhere-in-sentence patterns
# ---------------------------------------------------------------------------
PATTERNS = [
    # --- contrastive reversal / negation framing (English) ---
    # Three forms: the two words adjacent or one adverb apart, the denial and
    # "just" either side of a comma or dash, and the same pair as two sentences.
    ("not-just",
     _c(r"\bnot\s+(?:(?:really|actually|even|quite|necessarily|always)\s+)?"
        + _JUST + "|" + _DENIAL + _GAP + _SEP + _PRON + _JUST
        + "|" + _DENIAL + _GAP + r"\.\s+just\b")),
    # Any contracted auxiliary: "doesn't just", "can't just", "wouldn't only".
    ("doesnt-just", _c(r"\b(?:\w+n't|cannot|never)\s+" + _JUST)),
    # The slogan "No hidden fees, just simple pricing." One or two words after
    # "no", then "just", with no word in front of "no". A status line with a
    # verb in the denial ("No fix was needed, just a restart.") runs longer.
    ("no-x-just-y",
     _c(r"(?<!\w\s)\b(?:no|zero|nothing)\s+(?:[\w'-]+\s+)?[\w'-]+[,.;]\s+"
        r"just\b")),
    ("more-than-just", _c(r"\bmore\s+than\s+(?:just|simply|merely)\b")),
    # Present or past, contracted or not, with up to two intensifiers: "is
    # more than a", "was so much more than a", "it's more than a".
    ("is-more-than-a",
     _c(r"(?:\b(?:is|are|was|were)|'s|'re)\s+(?:(?:so|much|far|way)\s+){0,2}"
        r"more\s+than\s+an?\b")),
    ("goes-beyond", _c(r"\bgo(?:es|ing)?\s+(?:far\s+|well\s+)?beyond\b")),
    ("beyond-just", _c(r"\bbeyond\s+(?:just|mere|merely|simple)\b")),
    ("isnt-about",
     _c(r"\b(?:isn't|is\s+not|aren't|are\s+not|it's\s+not|wasn't|was\s+not|"
        r"weren't|were\s+not|(?:is|was|are|were)\s+never)\s+"
        r"(?:(?:really|just|only|actually)\s+)?about\b")),
    ("its-about", _c(r"\bit'?s\s+about\s+\w+[^.!?\n]{0,40}\bnot\b")),
    ("no-longer", _c(r"\bno\s+longer\b")),
    ("gone-are-the-days", _c(r"\bgone\s+are\s+the\s+days\b")),
    ("days-are-over",
     _c(r"\bthe\s+days\s+of\b[^.!?\n]{0,60}\bare\s+"
        r"(?:over|behind|gone|numbered)\b")),
    ("rather-than", _c(r"\brather\s+than\b")),
    ("instead-of", _c(r"\binstead\s+of\b")),
    ("as-opposed-to", _c(r"\bas\s+opposed\s+to\b")),
    ("say-goodbye-hello", _c(r"\bsay\s+(?:goodbye|hello|farewell)\b")),
    ("no-more-x", _c(r"\bno\s+more\s+(?!than\b)\w+")),
    ("never-again", _c(r"\bnever\s+again\b")),
    # Arm 1: "not" or a contracted negation, a determiner, then "but". Arm 2:
    # a preposition or "because" after the negation and the same word after
    # "but" ("not in the config but in the loader"). The repeat keeps "try not
    # to restart the server, but drain it first" out.
    ("not-x-but-y",
     _c(r"(?:\bnot|n't)\s+(?:a|an|the|your|my|our|his|her|its|their|this|"
        r"that|these|those)\b[^.!?\n]{0,60}?,?\s+but\b"
        r"|(?:\bnot|n't)\s+(because|to|for|by|in|on|with|from)\b"
        r"[^.!?\n]{0,60}?,?\s+but\s+\1\b")),
    # "Acme isn't a tool, it's a platform", with any subject. Arm 1: a clause
    # start, a negated be-verb, a comma or semicolon, then a pronoun and a
    # be-verb. Arm 2: the same pair as two sentences, where a determiner
    # follows the second be-verb. Arm 3: the subject repeated, as in "The
    # problem is not speed. The problem is trust."
    ("not-x-its-y",
     _c(_CLAUSE + r"(?!" + _SUBORD + r")(?![^,.!?;:\n—–]{0,60}?" + _INNER
        + r")[^,.!?;:\n—–]{0,40}?" + _NEG_COP + r"\s+" + _GAP + r"[,;]\s+"
        + _SECOND
        + "|" + _NEG_COP + r"\s+" + _GAP + r"\.\s+" + _SECOND
        + r"\s+(?:an?|the|your|our|my)\b"
        + r"|\b((?:the|our|your)\s+\w+|this|that|it)\s+(?:is|was)"
        + r"(?:n't|\s+not)\s+" + _GAP + r"[.,;]\s+\1\s+(?:is|was)\b")),
    # An em or en dash, or a spaced ASCII hyphen or double hyphen with a word
    # in front of it. A nested bullet ("  - not supported") has no such word.
    ("dash-not-contrast", _c(r"(?:[—–]|(?<=\S)\s+-{1,2}\s)\s*not\s+")),
    # Any object, including one opening with a backtick, a quote, or a bracket.
    ("comma-not-appositive", _c(r",\s*not\s+(?=\S)")),
    ("negated-copula-dash",
     _c(r"(?:\b(?:am|is|was|are|were)(?:n't|\s+not)|'(?:m|s|re)\s+not)\s+"
        r"[^—–.!?\n;:]{1,30}(?:[—–]|\s-{1,2}\s)")),
    ("not-your-average",
     _c(r"\bnot\s+your\s+(?:average|typical|ordinary|everyday|usual)\b"
        r"|\bno\s+(?:ordinary|mere)\b|\bnot\s+(?:just\s+)?another\b")),
    ("unlike-others",
     _c(r"\bunlike\s+(?:most|many|other|others|traditional|typical|"
        r"ordinary|conventional|"
        r"(?:(?:its|our|the)\s+)?(?:competitors?|rivals?|competition))\b")),
    ("while-others",
     _c(r"\b(?:while|whilst|whereas)\s+(?:most|many|others?|traditional|"
        r"typical|conventional|competitors|rivals)\b|\bwhere\s+others\b")),
    ("far-from-just", _c(r"\bfar\s+from\s+(?:just|merely|being)\b")),
    # "less a gym than a coaching program", "less about speed and more about
    # trust", "not so much a gym as a coaching program". The lookahead keeps
    # the idiom "not so much as looked at it" out.
    ("less-a-x-than",
     _c(r"\bless\s+an?\s+\w+\s+(?:than|and\s+more)\b"
        r"|\bless\s+about\b[^.!?\n]{0,40}\b(?:than|more\s+about)\b"
        r"|\bnot\s+so\s+much\s+(?!as\b)[^.!?\n]{1,50}?\bas\b")),
    ("think-again", _c(r"\bthink\s+again\b")),
    ("without-the-hassle",
     _c(r"\bwithout\s+(?:the|all\s+the|any\s+of\s+the)\s+(?:hassle|hassles|"
        r"headache|headaches|hidden|stress|guesswork|usual|middlemen|"
        r"red\s+tape|runaround)\b")),
    # "do A without doing B". A regex reads an -ing noun the same way, so
    # "without warning" and "without training" match too.
    ("without-gerund", _c(r"\bwithout\s+\w+ing\b")),
    ("zero-hassle",
     _c(r"\bzero\s+(?:hassle|hassles|guesswork|compromise|compromises|"
        r"hidden|surprises)\b")),
    ("rhetorical-reveal",
     _c(r"\bthe\s+(?:result|best\s+part|catch|difference|secret|"
        r"bottom\s+line|kicker)\s*\?")),
    ("where-x-meets-y", _c(r"\bwhere\s+\w+\s+meets\s+\w+\b")),
    ("redefine-family", _c(r"\b(?:redefin|reimagin|reinvent)\w*\b")),

    # --- hype vocabulary (English) ---
    ("hype-word",
     _c(r"\b(?:unleash\w*|unlock\w*|unrival{1,2}ed|unparalleled|unwavering|"
        r"unmatched|unprecedented|unsung|elevate[sd]?|elevating|"
        r"seamless(?:ly)?|empower(?:s|ed|ing|ment)?|"
        r"revolutioni[sz]\w*|revolutionary|groundbreaking|"
        r"game[-\s]?chang\w*|delv(?:e|es|ed|ing)|"
        r"supercharg\w*|turbocharg\w*|next[-\s]level|cutting[-\s]edge|"
        r"state[-\s]of[-\s]the[-\s]art|best[-\s]in[-\s]class|"
        r"world[-\s]class|transformative|frictionless|hassle[-\s]free|"
        r"effortless(?:ly)?|one[-\s]stop[-\s]shop|synerg\w*|"
        r"landscape|journey|innovative|holistic|passionate)\b")),

    # --- era-framing, bait, vague attribution, inflated copulas ---
    ("in-todays-world",
     _c(r"\bin\s+today'?s\s+(?:[\w-]+\s+){0,2}"
        r"(?:world|age|market|era|economy|environment)\b")),
    ("in-an-era-of", _c(r"\bin\s+an?\s+era\s+(?:of|where|when)\b")),
    ("look-no-further", _c(r"\blook\s+no\s+further\b")),
    ("worth-noting",
     _c(r"\bit(?:'s|\s+is)\s+(?:also\s+)?(?:worth\s+noting|"
        r"important\s+to\s+(?:note|remember|understand))\b")),
    ("vague-experts",
     _c(r"\b(?:experts|analysts|industry\s+(?:leaders|insiders|reports?))\s+"
        r"(?:say|agree|believe|suggest|argue|note)\b")),
    ("studies-show",
     _c(r"\b(?:studies|research)\s+(?:show|shows|suggests?|proves?)\b")),
    ("inflated-copula",
     _c(r"\bboast(?:s|ed|ing)?\b|\bstands?\s+as\s+an?\b|"
        r"\btestament\s+to\b")),
    ("serves-as", _c(r"\bserves?\s+as\s+an?\b")),
    ("turning-point",
     _c(r"\bmarks?\s+a\s+turning\s+point\b|\bindelible\s+mark\b")),
    ("editorializing-ing",
     _c(r",\s+(?:highlighting|underscoring|showcasing|demonstrating|"
        r"emphasizing|reflecting|signaling|cementing)\b")),

    # --- multilingual equivalents (zh / ru / es / ar) ---
    ("zh-not-just",
     _c(r"不仅仅是|不只是|不仅是|不止是|不再是|不只提供|告别|"
        r"重新定义|颠覆")),
    # The reversal reveal: negate, then assert. The connector slot (而 / 或 /
    # 却 / one word / nothing) sits inside the gap class, so the pattern holds
    # one bounded quantifier and cannot backtrack past it.
    ("zh-not-x-but-y",
     _c(r"不是[^。！？；\n]{0,32}是|而不是|不在于[^。！？；\n]{0,32}而在于")),
    ("ru-not-just",
     _c(r"не\s+просто|больше,?\s+чем\s+просто|это\s+не\s+о\b|"
        r"попрощайтесь|переосмысл\w*|прощай(?:те)?,")),
    ("es-not-just",
     _c(r"no\s+es\s+solo|no\s+solo\s+es|no\s+se\s+trata\s+solo|"
        r"más\s+que\s+(?:un|una)(?:\s+simple)?\b|más\s+que\s+solo|"
        r"dile?\s+adiós|redefinim\w*|va\s+más\s+allá|olvíd(?:ate|ese)\s+de|"
        r"atrás\s+quedaron|sin\s+complicaciones")),
    ("ar-not-just",
     _c(r"ليس\s+مجرد|ليست\s+مجرد|أكثر\s+من\s+مجرد|وداعًا|وداعا|"
        r"يعيد\s+تعريف")),
    ("fr-not-just",
     _c(r"n'est\s+pas\s+(?:qu'un|qu'une|seulement|simplement|juste)|"
        r"pas\s+(?:seulement|simplement)\s+un|"
        r"(?:bien\s+)?plus\s+qu'un(?:e)?\s+simple|"
        r"dites\s+adieu|fini(?:s|es)?\s+les?\s|"
        r"redéfini\w*|va\s+(?:bien\s+)?au[-\s]delà|révolutionn\w*|"
        r"oubliez\s+(?:les?|la|vos?)\b|imaginez\s")),
    ("de-not-just",
     _c(r"nicht\s+nur\s+(?:ein|eine|irgendein)|mehr\s+als\s+nur|"
        r"weit\s+mehr\s+als|verabschieden\s+Sie\s+sich|schluss\s+mit|"
        r"nie\s+wieder|neu\s+definiert|definiert\s+\w+\s+neu|"
        r"geht\s+über\s+\w+\s+hinaus|revolutionier\w*|"
        r"vergessen\s+Sie|stellen\s+Sie\s+sich\s+vor")),
    ("ja-not-just",
     _c(r"単なる[^。！？\n]{0,20}(?:ではありません|ではない|じゃない)|"
        r"ただの[^。！？\n]{0,20}(?:ではありません|ではない|じゃない)|"
        r"だけでは(?:ありません|ない)|にとどまら(?:ない|ず)|"
        r"はもう不要|とはおさらば|再定義|常識を覆す|革命的|"
        r"想像してみてください|だけでなく|さようなら|を超えた")),
    ("ko-not-just",
     _c(r"단순한\s*[^.!?。\n]{0,20}(?:아닙니다|아니다|아니에요)|"
        r"에\s*그치지\s*않|[와과]\s*작별하세요|작별을\s*고하세요|"
        r"재정의|게임\s*체인저|상상해\s*보세요|"
        r"뿐만\s*아니라|그\s*이상|더\s*이상|혁신적")),
]

# ---------------------------------------------------------------------------
# Sentence-opener patterns (checked at sentence start only)
# ---------------------------------------------------------------------------
OPENERS = [
    ("opener-it-is-not", _c(r"it\s+is\s+not\b|it\s+isn't\b|it's\s+not\b")),
    ("opener-dont-just", _c(r"don't\s+just\b")),
    ("opener-we-are-not", _c(r"we\s+are\s+not\b|we're\s+not\b|we\s+aren't\b")),
    ("opener-stop", _c(r"stop\s+\w+")),
    ("opener-forget", _c(r"forget\b")),
    ("opener-imagine", _c(r"imagine\b")),
    ("opener-picture-this", _c(r"picture\s+this\b")),
    ("opener-in-a-world", _c(r"in\s+a\s+world\s+where\b")),
    ("opener-welcome-new-era",
     _c(r"welcome\s+to\s+(?:a\s+new|the\s+new|a\s+world)\b")),
    ("opener-tired-sick-of", _c(r"(?:tired|sick)\s+of\b")),
    ("opener-ever-wondered", _c(r"ever\s+wonder(?:ed)?\b")),
    ("opener-what-if", _c(r"what\s+if\b")),
    # "At [Company], we ..." — case-sensitive: requires a capitalized name
    ("opener-at-company-we",
     re.compile(r"At\s+[A-Z][\w&.]*(?:\s+[A-Z][\w&.]*){0,3},?\s+we\b")),
]

# ---------------------------------------------------------------------------
# Paragraph patterns (checked over one block of lines, joined)
# ---------------------------------------------------------------------------
# A rule here needs a unit larger than one line. Prose in this repository and
# in most Markdown wraps near column 76, so a dash pair opens on one line and
# closes on the next. Measured over this repository: the line unit found 1 of
# the 9 suspended lists it carries.
#
# The gap class excludes the sentence enders, the semicolon, the pipe, and both
# dashes, so a match stays inside one sentence and inside one table cell. Every
# quantifier is bounded.
BLOCK_GAP = r"[^—–.!?;|。！？]"
# The list separator, in the scripts the rule set covers.
BLOCK_COMMA = r"[,，、]"
BLOCK_PATTERNS = [
    ("dash-pair-list",
     _c(r"[—–]" + BLOCK_GAP + r"{1,200}?" + BLOCK_COMMA +
        BLOCK_GAP + r"{1,200}?" + BLOCK_COMMA + BLOCK_GAP + r"{1,200}?[—–]")),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?！？。؟])\s+")
# Straight quotes only: normalize() folds the curly forms before scan_line
# strips a sentence, so a curly quote never reaches this set. `|` is here so a
# sentence in the first cell of a Markdown table row reaches the OPENERS loop;
# without it every anchored rule missed a specimen quoted inside a table.
LEAD_STRIP = " \t#*->—–-\"'([`0123456789.|"
# The block pass strips the Markdown marker and keeps every dash, because a
# dash is what the block rules match.
BLOCK_LEAD_STRIP = " \t#*->"


def normalize(text):
    return (text.replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"'))


def scan_line(line, lineno, findings):
    norm = normalize(line)
    for name, rx in PATTERNS:
        for m in rx.finditer(norm):
            findings.append((lineno, name, m.group(0).strip()))
    for sentence in SENTENCE_SPLIT.split(norm):
        s = sentence.lstrip(LEAD_STRIP)
        if not s:
            continue
        for name, rx in OPENERS:
            m = rx.match(s)
            if m:
                findings.append((lineno, name, m.group(0).strip()))


def iter_blocks(lines):
    """Group lines into paragraphs, blank lines separating them.

    Yields (joined_text, offsets). `offsets` holds one (start, lineno) pair per
    source line, so a match offset maps back to the line that opens it. Each
    line loses its leading Markdown marker before the join, which keeps a
    quoted or bulleted paragraph on the same footing as a plain one.
    """
    block = []
    for lineno, line in enumerate(lines, 1):
        if line.strip():
            block.append((lineno, line))
            continue
        if block:
            yield _join(block)
        block = []
    if block:
        yield _join(block)


def _join(block):
    parts = []
    offsets = []
    position = 0
    for lineno, line in block:
        piece = line.lstrip(BLOCK_LEAD_STRIP)
        offsets.append((position, lineno))
        position += len(piece) + 1
        parts.append(piece)
    return " ".join(parts), offsets


def _lineno_at(offsets, position):
    found = offsets[0][1]
    for start, lineno in offsets:
        if start > position:
            break
        found = lineno
    return found


def scan_blocks(text, findings):
    for joined, offsets in iter_blocks(text.splitlines()):
        norm = normalize(joined)
        for name, rx in BLOCK_PATTERNS:
            for m in rx.finditer(norm):
                findings.append(
                    (_lineno_at(offsets, m.start()), name, m.group(0).strip())
                )


def scan_text(text):
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        scan_line(line, i, findings)
    scan_blocks(text, findings)
    findings.sort(key=lambda finding: finding[0])
    return findings


def _utf8_streams():
    """Read and report in UTF-8 on every platform.

    A finding quotes the text it matched, and eight of the nine covered
    languages are non-ASCII. Python picks the encoding for a pipe or a console
    from the platform, so on Windows at a legacy code page the quote arrives
    mojibaked, a character the code page has no room for raises
    UnicodeEncodeError, and `--stdin` decodes the draft wrong before a pattern
    ever runs. `errors="replace"` keeps the exit code, the rule name, and the
    line number readable when one character will not render.

    Streams only. The patterns and the 0/1/2 exit contract are untouched.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def main(argv):
    _utf8_streams()
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

    findings = 0
    for path, text in sources:
        for lineno, name, snippet in scan_text(text):
            print(f"{path}:{lineno}: {name}: \"{snippet}\"")
            findings += 1

    print(f"\ncopy_lint: {findings} finding(s)")
    if findings:
        print("FAIL — rewrite each flagged sentence as a direct statement of "
              "what the subject IS or DOES, then re-run. Do not edit this "
              "linter to make copy pass.")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
