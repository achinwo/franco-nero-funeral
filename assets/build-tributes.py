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
    order = 20                 # descending; ties keep the order of the file
    title = "Our Tribute to Grandpa"
    from  = "Talia & Tyshawn"  # optional; printed as "from Talia & Tyshawn"
    imagePath = "assets/..."   # optional; a photograph to set the letter around
    dropcap = true             # optional, false by default; opens the letter
                               # on a two-line initial
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

When a heuristic picks the wrong line -- a short paragraph that happens to
end in a comma, a prayer that is not the last thing in the letter -- the
family (or whoever is typing the tribute in) can say so directly by wrapping
that part in <para>, <signoff> or <prayer> tags. Only those three tag names
are recognised; anything else is left as ordinary text for the heuristics
above to read, on the theory that a typo in a tag name should not silently
swallow a line. Tags are stripped in the process, so nothing named after
them ever reaches the PDF.

<i>...</i> and <b>...</b> work inline, anywhere within a line, for the odd
italicised or bold word or phrase -- Arsenal, say, or a name the writer
wants to stand out. <br/> (or <br>, or <br />) breaks the line where it
stands, for the few places a paragraph is really a list: the lines of an
address, or a verse. One at the very start or end of a paragraph is
dropped, having no line to break.

Tributes run on down the page, separated by a drawn divider rather than a
page break: these are long letters, and one that ends two lines into a page
would leave the rest of it looking like an oversight. Where a particular
tribute does want the turn, <pagebreak/> takes it. Written between two
paragraphs it breaks the page there; written at the very top of a body it
starts that tribute on a page of its own, title and all, and the divider
that would have introduced it is dropped -- the page turn is the division.

Lines are paragraphs. A tribute typed as one line per sentence would come out
as one paragraph per sentence, which is the writer's decision to make and not
this script's to second-guess.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
import unicodedata

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
PHOTOS = ROOT / "assets/images/plates/tributes"

# A photograph is fitted inside this box, in millimetres, whichever way round
# it is: a portrait comes out narrow, a landscape wide, and both take about
# the same bite out of the page. The height is the number that matters -- it
# is roughly eleven lines of the 9pt setting, and text has to flow past it
# before the tribute ends, or the divider and the next title would set
# alongside a photograph instead of under it.
PHOTO_W = 40.0
PHOTO_H = 38.0
PHOTO_PIXELS = 1200   # long edge; ~600dpi at the size these print

# A two-line initial needs two lines of its own paragraph to sit against.
# The tribute measure holds about eighty characters of 9pt text, so a first
# paragraph shorter than two of those is set with no initial at all: the
# alternative is an initial with nothing beside its lower half, and the
# paragraph *after* it starting at the margin and setting straight through
# the letter. (A tribute with a photograph runs on a narrower measure and
# reaches two lines sooner, so this is the safe number for both.)
DROPCAP_CHARS = 160

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
            print(f"build-tributes: dropping {ch!r} ({name}) -- "
                  "pdflatex has no glyph for it", file=sys.stderr)
    return "".join(kept)


INLINE_TAGS = {"i": "textit", "b": "textbf"}
# Either an <i>/<b> pair or a line break. <br>, <br/> and <br /> are all
# taken, because all three are what people type.
INLINE_RE = re.compile(r"<(%s)>(.*?)</\1>|<br\s*/?>" % "|".join(INLINE_TAGS),
                       re.DOTALL)


def tex(text):
    """Text as the family typed it, as LaTeX will want to read it.

    <i> and <b> may be used inline, anywhere in a line -- including inside
    each other, for a bold phrase with an italic word in it -- and come out
    as \\textit / \\textbf. <br/> breaks the line where it stands. They are
    pulled out before the escaping below runs, so the words inside are still
    escaped and typeset like everything else; only the tags are markup.
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


def spaced(text):
    """Two breaks with nothing between them mean a blank line, which is what
    a <br/> alone on its own line is asking for. LaTeX will not take that as
    a pair of \\\\ -- the second has no line to end -- so it is asked for as
    the space it is, in the leading of whatever size the text is set at."""
    return re.sub(r"(?:\\\\\s*){2,}", lambda m: r"\\[\baselineskip]", text)


def dropcapped(raw, joined):
    """A paragraph rewritten to open on an initial, or None to leave it alone.

    The split is made on the set text rather than on what the family typed,
    so that the escaping, the marks and the inline tags have all already run
    and what goes into the macro is exactly what would have been printed
    anyway. That is safe because the raw text is checked first: a paragraph
    opening on a letter still opens on that same letter once it has been
    through tex(), which touches punctuation and leaves letters alone.

    A paragraph opening on anything else -- a quotation mark, a numeral, the
    date -- gets no initial, and neither does one too short to hold it.
    Splitting an initial out of an opening quote is a job for a typesetter
    with the page in front of them, and an ordinary paragraph is never wrong.
    """
    if not raw or not raw[0].isalpha() or not latin_safe(raw[0]):
        print("build-tributes: no initial -- the first paragraph does not "
              "open on a letter", file=sys.stderr)
        return None
    if len(raw) < DROPCAP_CHARS:
        print(f"build-tributes: no initial -- the first paragraph is "
              f"{len(raw)} characters and a two-line initial needs about "
              f"{DROPCAP_CHARS} to sit against", file=sys.stderr)
        return None
    m = re.match(r"(\w)(\w*)(.*)", joined, re.DOTALL)
    return m and r"\tributedropcap{%s}{%s}%s" % m.groups()


def oneline(text):
    """Text for a tribute's title, which is one line whatever is typed into
    it: \\so letterspaces a title character by character and stops at a \\\\,
    so a break there would take the build down rather than set a title over
    two lines."""
    return re.sub(r"\s*\\\\\s*", " ", tex(text)).strip()


def plain(text):
    """A run of text with no inline tags left in it, escaped for LaTeX."""
    out = "".join(ESCAPES.get(ch, ch) for ch in text)
    for mark, replacement in MARKS.items():
        out = out.replace(mark, replacement)
    # Straight quotes, alternating open and close. Word processors curl these
    # on their own; a phone keyboard does not.
    out = re.sub(r'"([^"]*)"', r"``\1''", out)
    return strip_unsafe(out)


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


TAG_KINDS = ("para", "signoff", "prayer")
# A block-level tag: one of the three above wrapped round its lines, or a
# <pagebreak/> standing on its own. <pagebreak/> is matched here rather than
# among the inline tags because a page break is a thing that happens between
# paragraphs; one written mid-sentence ends the paragraph where it stands.
TAG_RE = re.compile(r"<(%s)>(.*?)</\1>|<pagebreak\s*/?>" % "|".join(TAG_KINDS),
                    re.DOTALL)


def blocks(body):
    """Split a tribute's body into ('kind', lines) blocks.

    <para>, <signoff>, <prayer> and <pagebreak/> tags are pulled out first
    and taken at their word; whatever is left, outside the tags, is read by
    the heuristics in heuristic_blocks(), same as a tribute with no tags at
    all.
    """
    out, pos = [], 0
    for m in TAG_RE.finditer(body):
        out += heuristic_blocks(body[pos:m.start()])
        pos = m.end()
        kind = m.group(1)
        if kind is None:
            out.append(("pagebreak", []))
            continue
        lines = [ln.strip() for ln in m.group(2).strip().splitlines() if ln.strip()]
        if lines:
            out += [("para", [ln]) for ln in lines] if kind == "para" \
                else [(kind, lines)]
    out += heuristic_blocks(body[pos:])
    return out


def heuristic_blocks(body):
    """Split untagged text into ('kind', lines) blocks by the rules in the
    module docstring."""
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


def photograph(source, index):
    """Prepare one tribute's photograph and return (name, width, height).

    These are phone snapshots -- a group on a front step, a selfie -- and they
    sit two pages away from four sepia scans of the 1960s. Toning them a
    little of the way towards the same warm ink is what stops them reading as
    something pasted in from another book; at 45% of the way there the
    colours are all still their own, only quieter, as a photograph goes when
    it has been in an album a long while.
    """
    src = ROOT / source
    if not src.is_file():
        sys.exit(f"build-tributes: no such image: {source}")
    if not shutil.which("magick"):
        sys.exit("build-tributes: a tribute has an imagePath, "
                 "which needs ImageMagick 7 to prepare")

    PHOTOS.mkdir(parents=True, exist_ok=True)
    dest = PHOTOS / f"{index:02d}.jpg"
    # -auto-orient first: a phone writes the rotation into EXIF and pdflatex
    # does not read it, so an upright photograph would print on its side.
    subprocess.run(
        ["magick", str(src), "-auto-orient",
         "-resize", f"{PHOTO_PIXELS}x{PHOTO_PIXELS}>",
         "(", "+clone", "-colorspace", "Gray", "-auto-level",
         "-sigmoidal-contrast", "2x50%",
         "+level-colors", "#3a2f26,#f7f2e8", ")",
         "-compose", "blend", "-define", "compose:args=45", "-composite",
         "-strip", "-quality", "88", str(dest)],
        check=True, capture_output=True)

    w, h = subprocess.run(["magick", str(dest), "-format", "%w %h", "info:"],
                          check=True, capture_output=True,
                          text=True).stdout.split()
    scale = min(PHOTO_W / int(w), PHOTO_H / int(h))
    return f"plates/tributes/{dest.stem}", int(w) * scale, int(h) * scale


def emit(tributes):
    # Numbered by their place in the booklet, so a reordering renames them;
    # clearing the directory first is what keeps yesterday's numbering from
    # being left behind as a file nothing points at.
    for stale in PHOTOS.glob("*.jpg"):
        stale.unlink()

    out = ["% Generated by assets/build-tributes.py -- do not edit by hand.",
           "% Edit assets/data/tributes.toml and re-run assets/make-plates.sh.",
           ""]
    for i, tribute in enumerate(tributes):
        body = blocks(tribute["body"])
        # A tribute opening on <pagebreak/> starts on a fresh page, head and
        # all: the break has to be set above \tributehead, or the title is
        # left stranded at the foot of the page before it. The divider goes
        # with it -- what separates two tributes on one page is a rule, and
        # what separates them across a page turn is the turn.
        if body and body[0][0] == "pagebreak":
            body = body[1:]
            out += [r"\newpage", ""]
        elif i:
            out += [r"\tributedivider", ""]
        attribution = (tribute.get("from") or tribute.get("subtitle", "")).strip()
        out.append(r"\tributehead{%s}{%s}"
                   % (oneline(titlecase(tribute["title"])),
                      (oneline(attribution)) if attribution else ""))
        out.append(r"\begin{tribute}")
        if tribute.get("imagePath", "").strip():
            name, pw, ph = photograph(tribute["imagePath"].strip(), i + 1)
            out.append(r"\tributephoto{%s}{%.1fmm}{%.1fmm}" % (name, pw, ph))
        # Only the first paragraph takes the initial, and only if the tribute
        # asked for one. A letter has one opening.
        opening = bool(tribute.get("dropcap", False))
        for kind, lines in body:
            if kind == "pagebreak":
                out += [r"\newpage", ""]
                continue
            joined = spaced(tex(" ".join(lines)) if kind == "para"
                            else r"\\".join(tex(ln) for ln in lines))
            if kind == "para":
                if opening:
                    opening = False
                    joined = dropcapped(" ".join(lines).lstrip(), joined) or joined
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
                      key=lambda t: t.get("order", 0), reverse=True)

    missing = [t for t in tributes
               if not all(str(t.get(k, "")).strip() for k in ("title", "body"))]
    if missing:
        sys.exit("build-tributes: a tribute is missing its title or its body")

    if not tributes:
        TEX.write_text("% No tributes in assets/data/tributes.toml.\n")
        print("build-tributes: no tributes found", file=sys.stderr)
        return

    emit(tributes)
    print(f"build-tributes: {len(tributes)} tributes "
          f"-> {TEX.relative_to(ROOT)}")
    for tribute in tributes:
        kinds = [kind for kind, _ in blocks(tribute["body"])]
        print(f"  {oneline(titlecase(tribute['title']))}: "
              f"{kinds.count('para')} paragraphs"
              + (", a sign-off" if "signoff" in kinds else "")
              + (", a closing prayer" if "prayer" in kinds else "")
              + (", a photograph" if tribute.get("imagePath") else "")
              + (", an initial" if tribute.get("dropcap") else "")
              + (f", {kinds.count('pagebreak')} page break"
                 f"{'s' if kinds.count('pagebreak') > 1 else ''}"
                 if "pagebreak" in kinds else ""))


if __name__ == "__main__":
    main()
