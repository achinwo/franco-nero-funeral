#!/usr/bin/env python3
r"""Set the tributes for the Tributes section.

Reads assets/data/tributes.toml -- the words as the family sent them -- and
writes assets/data/tributes.tex, a run of the macros defined in main.tex, for
08-tribute.tex to \input. Edit the TOML and re-run assets/make-plates.sh (or
this script on its own); nothing downstream needs touching.

The TOML carries text and nothing else: no LaTeX, no markup, no formatting.
Someone typing a tribute into it should not have to know what \& means, so
every special character, curly quote and dash is translated here. Anything
that looks like LaTeX in the source is therefore printed literally, which is
the safe way round for a document nobody will proof-read line by line.

    [[tribute]]
    order = 20                 # ascending; ties keep the order of the file
    title = "Our Tribute to Grandpa"
    from  = "Talia & Tyshawn"  # printed as "from Talia & Tyshawn"
    body  = "..."              # one line per paragraph, blank lines ignored
                               # (a TOML multi-line string, in practice)

(The top-level `title` key is not used. The section head is set in
sections/08-tribute.tex, so that it and the contents page cannot drift apart.)

How a tribute is set
--------------------
A tribute is a letter, and it is laid out like one: a single measure rather
than the two columns the liturgy uses, no indents, air between paragraphs.
Three kinds of line are lifted out of the prose and set differently, by rules
kept deliberately narrow -- a rule that fires when it should not is worse
here than one that quietly does nothing, because the fallback is an ordinary
paragraph, which is never wrong:

  the closing prayer   trailing short lines ending in "Amen", set centred and
                       italic under a short rule, the way the booklet sets
                       every other prayer

  a sign-off           two or more short lines in a row, the first ending in
                       a comma ("With all our love," / "Talia and Tyshawn"),
                       set to the right as it would be on paper

  everything else      a paragraph

Tributes run on down the page, separated by a drawn divider rather than a
page break: these are long letters, and one that ends two lines into a page
would leave the rest of it looking like an oversight.

Lines are paragraphs. A tribute typed as one line per sentence would come out
as one paragraph per sentence, which is the writer's decision to make and not
this script's to second-guess.
"""

import os
import pathlib
import re
import shutil
import sys
import textwrap

try:
    import tomllib
except ModuleNotFoundError:
    # tomllib arrived in 3.11; macOS ships 3.9 and a pyenv shim may pin one
    # older still. Rather than hand-roll a TOML parser -- which would be one
    # more thing that can be subtly wrong about a file the family edits --
    # find a newer interpreter and start again in it.
    for _exe in ("python3.13", "python3.12", "python3.11"):
        _found = shutil.which(_exe)
        if _found:
            os.execv(_found, [_found, os.path.abspath(__file__), *sys.argv[1:]])
    sys.exit("build-tributes: needs Python 3.11 or newer (for tomllib)")

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOML = ROOT / "assets/data/tributes.toml"
TEX = ROOT / "assets/data/tributes.tex"

PRAYER_LINE = 72      # a prayer is set in short lines; prose runs longer
PRAYER_LINES = 5      # ... and is a few of them, not a closing paragraph
SIGNOFF_LINE = 44
WRAP = 76             # source line length, for a readable diff

# Title case for a title that arrives shouted, as they tend to. Left alone if
# the writer used their own capitals -- they may have meant them.
MINOR = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
         "nor", "of", "on", "or", "over", "the", "to", "up", "with"}

ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}

# Typographer's marks, once the escaping above has run.
MARKS = {"“": "``", "”": "''", "‘": "`", "’": "'",
         "„": ",,", "—": "---", "–": "--", "…": r"\dots{}",
         " ": "~", "­": "", "...": r"\dots{}"}


def tex(text):
    """Text as the family typed it, as LaTeX will want to read it."""
    out = "".join(ESCAPES.get(ch, ch) for ch in text)
    for mark, replacement in MARKS.items():
        out = out.replace(mark, replacement)
    # Straight quotes, alternating open and close. Word processors curl these
    # on their own; a phone keyboard does not.
    out = re.sub(r'"([^"]*)"', r"``\1''", out)
    return re.sub(r"[ \t]+", " ", out).strip()


def titlecase(title):
    if title != title.upper():
        return title

    def cap(word, first):
        parts = word.lower().split("-")
        return "-".join(
            p.capitalize() if (first and i == 0) or p not in MINOR else p
            for i, p in enumerate(parts))

    words = title.split()
    return " ".join(cap(w, i == 0 or i == len(words) - 1)
                    for i, w in enumerate(words))


def blocks(body):
    """Split a tribute's body into ('kind', lines) blocks."""
    lines = [ln.strip() for ln in body.strip().splitlines()]
    lines = [ln for ln in lines if ln]

    prayer = []
    if lines and re.search(r"\bAmen[.!]?$", lines[-1]):
        while (lines and len(lines[-1]) <= PRAYER_LINE
               and len(prayer) < PRAYER_LINES):
            prayer.insert(0, lines.pop())

    out, run = [], []
    for line in lines:
        # A sign-off opens on a short line ending in a comma and runs on
        # through the short lines under it.
        if run or (len(line) <= SIGNOFF_LINE and line.endswith(",")):
            if len(line) <= SIGNOFF_LINE:
                run.append(line)
                continue
        out += close(run)
        run = []
        out.append(("para", [line]))
    out += close(run)

    if prayer:
        out.append(("prayer", prayer))
    return out


def close(run):
    """A run of short lines is a sign-off only if there are several of them;
    one on its own is a salutation, or simply a short sentence."""
    if len(run) > 1:
        return [("signoff", run)]
    return [("para", [line]) for line in run]


def emit(tributes):
    out = ["% Generated by assets/build-tributes.py -- do not edit by hand.",
           "% Edit assets/data/tributes.toml and re-run assets/make-plates.sh.",
           ""]
    for i, tribute in enumerate(tributes):
        if i:
            out += [r"\tributedivider", ""]
        out.append(r"\tributehead{%s}{from %s}"
                   % (tex(titlecase(tribute["title"])), tex(tribute["from"])))
        out.append(r"\begin{tribute}")
        for kind, lines in blocks(tribute["body"]):
            joined = tex(" ".join(lines)) if kind == "para" \
                else r"\\".join(tex(ln) for ln in lines)
            if kind == "para":
                out += [textwrap.fill(joined, WRAP), ""]
            elif kind == "signoff":
                out += [r"\tributesignoff{%s}" % joined, ""]
            else:
                out += [r"\tributeprayer{%s}" % joined, ""]
        out += [r"\end{tribute}", ""]
    TEX.write_text("\n".join(out).rstrip("\n") + "\n")


def main():
    if not TOML.is_file():
        sys.exit(f"build-tributes: {TOML.relative_to(ROOT)} is missing")
    data = tomllib.loads(TOML.read_text())
    tributes = sorted(data.get("tribute", []),
                      key=lambda t: t.get("order", 0))

    missing = [t for t in tributes
               if not all(t.get(k, "").strip() for k in ("title", "from", "body"))]
    if missing:
        sys.exit("build-tributes: a tribute is missing title, from or body")

    if not tributes:
        TEX.write_text("% No tributes in assets/data/tributes.toml.\n")
        print("build-tributes: no tributes found", file=sys.stderr)
        return

    emit(tributes)
    print(f"build-tributes: {len(tributes)} tributes "
          f"-> {TEX.relative_to(ROOT)}")
    for tribute in tributes:
        kinds = [kind for kind, _ in blocks(tribute["body"])]
        print(f"  {tex(titlecase(tribute['title']))}: "
              f"{kinds.count('para')} paragraphs"
              + (", a sign-off" if "signoff" in kinds else "")
              + (", a closing prayer" if "prayer" in kinds else ""))


if __name__ == "__main__":
    main()
