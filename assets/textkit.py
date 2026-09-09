#!/usr/bin/env python3
r"""Turning text the family typed into text LaTeX will set.

Shared by the three generators -- build-tributes.py, build-captions.py and
build-album.py -- because all three read the same kind of file: plain words,
typed by somebody who should not have to know what \& means. Every special
character, curly quote and dash is translated here, and anything that looks
like LaTeX in the source is printed literally, which is the safe way round
for a document nobody will proof-read line by line.

A few inline tags are understood, anywhere within a line:

    <i>...</i>   italic          <b>...</b>   bold
    <s>...</s>   struck through  (<del>, <strike> and <strikethrough> too)
    <br/>        break the line  (<br> and <br /> are taken too)

They are pulled out before the escaping runs, so the words inside them are
still escaped and typeset like everything else; only the tags are markup.

The module is imported, not run. It lives beside the scripts that use it, so
`python3 assets/build-tributes.py` finds it on sys.path with nothing to set
up.
"""

import os
import pathlib
import re
import shutil
import sys
import unicodedata

# The name of whichever script imported this, for the warnings below: a line
# saying a character was dropped is worth little if it does not say which
# generator dropped it.
PROG = pathlib.Path(sys.argv[0]).stem or "textkit"


def warn(message):
    print(f"{PROG}: {message}", file=sys.stderr)


def read_toml(path):
    """Parse a TOML file, on an interpreter old enough to lack tomllib.

    tomllib arrived in 3.11; macOS ships 3.9 and a pyenv shim may pin one
    older still. Rather than hand-roll a TOML parser -- which would be one
    more thing that can be subtly wrong about a file the family edits --
    find a newer interpreter and start the calling script again in it.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        for exe in ("python3.13", "python3.12", "python3.11"):
            found = shutil.which(exe)
            if found:
                script = os.path.abspath(sys.argv[0])
                os.execv(found, [found, script, *sys.argv[1:]])
        sys.exit(f"{PROG}: needs Python 3.11 or newer (for tomllib)")
    return tomllib.loads(pathlib.Path(path).read_text())


ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
           "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}

# Typographer's marks, once the escaping above has run.
MARKS = {"“": "``", "”": "''", "‘": "`", "’": "'",
         "„": ",,", "—": "---", "–": "--", "…": r"\dots{}",
         # A non-breaking space and a soft hyphen, written as escapes
         # rather than as themselves: both are invisible in an editor,
         # and an ordinary space pasted over that first key would tie
         # every word in the booklet to the one after it.
         "\xa0": "~", "\xad": "", "...": r"\dots{}"}


def latin_safe(ch):
    """Whether pdflatex, with the T1/Latin Modern setup this booklet uses,
    can be trusted to typeset ch.

    Accented Latin letters -- the accessible face of "Unicode" to someone
    typing a name like Přemysl or Zoë on a phone -- come through fine, along
    with the Latin-1 symbols (£, °, ½, section and paragraph marks). Emoji
    and other pictographic symbols do not: pdflatex has no glyph for them
    and stops the whole build cold rather than leaving a gap, which is a
    worse outcome here than quietly dropping the one character.
    """
    code = ord(ch)
    if code < 0x80 or 0xA0 <= code <= 0xFF:
        return True
    return unicodedata.name(ch, "").startswith(("LATIN ", "COMBINING "))


def strip_unsafe(text):
    kept = []
    for ch in text:
        if latin_safe(ch):
            kept.append(ch)
        else:
            name = unicodedata.name(ch, f"U+{ord(ch):04X}")
            warn(f"dropping {ch!r} ({name}) -- pdflatex has no glyph for it")
    return "".join(kept)


# Four spellings of the strike, because there is no obvious one: <s> is what
# HTML settled on, <del> what it means, and <strike>/<strikethrough> what
# somebody who has not written HTML since 1999 will type. All four are the
# same tag; a writer should not have to guess which one this file knows.
STRIKE_TAGS = ("s", "del", "strike", "strikethrough")

INLINE_TAGS = {"i": "textit", "b": "textbf",
               **{tag: "struck" for tag in STRIKE_TAGS}}
# Either a tag pair or a line break. <br>, <br/> and <br /> are all taken,
# because all three are what people type. Longest name first: the alternation
# is tried in order, so an unsorted list would match the <s> in <strike> and
# then fail on the tag it had half-eaten.
INLINE_RE = re.compile(
    r"<(%s)>(.*?)</\1>|<br\s*/?>"
    % "|".join(sorted(INLINE_TAGS, key=len, reverse=True)), re.DOTALL)


def tex(text):
    """Text as the family typed it, as LaTeX will want to read it.

    <i> and <b> may be used inline, anywhere in a line -- including inside
    each other, for a bold phrase with an italic word in it -- and come out
    as \\textit / \\textbf. <br/> breaks the line where it stands.
    """
    out, pos = [], 0
    for m in INLINE_RE.finditer(text):
        out.append(plain(text[pos:m.start()]))
        out.append(r"\\" if m.group(1) is None
                   else r"\%s{%s}" % (INLINE_TAGS[m.group(1)], tex(m.group(2))))
        pos = m.end()
    out.append(plain(text[pos:]))
    out = re.sub(r"[ \t]+", " ", "".join(out)).strip()
    # A break with no line to break -- one opening or closing the text, as in
    # a paragraph typed "...and we will never forget you.<br/>" -- is an
    # error in LaTeX rather than the blank line it looks like, and the blank
    # line between paragraphs is already there.
    return re.sub(r"^(?:\s*\\\\)+|(?:\\\\\s*)+$", "", out).strip()


def plain(text):
    """A run of text with no inline tags left in it, escaped for LaTeX."""
    out = "".join(ESCAPES.get(ch, ch) for ch in text)
    for mark, replacement in MARKS.items():
        out = out.replace(mark, replacement)
    # Straight quotes, alternating open and close. Word processors curl these
    # on their own; a phone keyboard does not.
    out = re.sub(r'"([^"]*)"', r"``\1''", out)
    return strip_unsafe(out)


BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)


def lines(text):
    """Text split where the writer asked for a line break.

    For the places a break cannot simply become a \\\\ in the output because
    something else has to be done to each line -- a tribute's title, where
    every line is letterspaced separately because \\so will not cross a
    break. Splitting here rather than after tex() means each line is still
    the writer's own words, so anything that reads them (title case, say)
    sees a line rather than a string with a tag in the middle of it.

    Empty pieces are dropped: a break at the very start or end of the text,
    or two in a row, asked for a line that has nothing on it.
    """
    return [piece.strip() for piece in BR_RE.split(text) if piece.strip()]


STRIKE_RE = re.compile(
    r"<(%s)>(.*?)</\1>"
    % "|".join(sorted(STRIKE_TAGS, key=len, reverse=True)), re.DOTALL)


def runs(text):
    """Text split into (struck, piece) runs on the strike tags.

    The companion to lines(): for the places a strike cannot simply become a
    \\struck{...} in the output because something else has to be done to each
    run. A tribute's title is letterspaced with \\so, and no soul command
    survives a \\sout inside it, so there the struck run has to be set beside
    the letterspaced ones rather than within them -- which means knowing where
    it starts and stops before anything else runs.

    Pieces come back as the writer typed them, spaces and all: whoever is
    assembling the runs has to decide which side of a join a space belongs
    on, and that cannot be decided here. Empty pieces are dropped.
    """
    out, pos = [], 0
    for m in STRIKE_RE.finditer(text):
        out.append((False, text[pos:m.start()]))
        out.append((True, m.group(2)))
        pos = m.end()
    out.append((False, text[pos:]))
    return [(struck, piece) for struck, piece in out if piece.strip()]


def oneline(text):
    """Text for somewhere that is one line whatever is typed into it -- a
    title, a caption under a photograph. \\so letterspaces a title character
    by character and stops at a \\\\, so a break there would take the build
    down rather than set the line over two."""
    return re.sub(r"\s*\\\\\s*", " ", tex(text)).strip()
