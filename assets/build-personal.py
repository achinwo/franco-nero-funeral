#!/usr/bin/env python3
r"""Build the pages of his own photographs, in the Photographs section.

Reads every image in assets/images/personal/, normalises each one for print,
sizes one or two prints to a row across as many pages as it takes, and writes
assets/images/plates/personal-photos.tex for 07-photobook.tex to \input.

Drop a photograph of him into personal/ and re-run assets/make-plates.sh:
these pages re-flow on their own. Nothing downstream needs editing.

The family album, next door, does the same job for family_pics/ and does it
differently, and the difference is the point. The album is forty-odd group
photographs and it sets them small, three across in a plain hairline frame,
the way a photo book sets a contact sheet: they are a crowd, and they read as
one. These are photographs of one man. They are set two to a row at twice the
size, mounted with the photo corners the composed page uses for the four old
prints, and captioned -- which is what makes a page of them read as an album
somebody kept rather than as a gallery.

What is not printed
-------------------
personal/ holds his photographs and also the artwork cut from them: the four
scanned sheets the sepia plates come out of, and the cover cut-out. Those are
already in the booklet -- as the plates, the two frontispieces, every page
ghost and the cover itself -- so printing the sources again would be printing
the same pictures twice, once finished and once raw. They are named in SKIP
below with the reason, in the same place and the same form as the album's
editorial skips, so the judgement is visible and can be reversed by deleting
a line.
"""

import pathlib
import sys

import captions as captionfile
import photoset

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/images/personal"
OUT = ROOT / "assets/images/plates/personal"
TEX = ROOT / "assets/images/plates/personal-photos.tex"
# Everything the booklet prints from elsewhere. personal/ itself is not in
# this list, for the obvious reason: it is what is being printed.
IN_USE = (ROOT / "assets/images",)

# --- page geometry, in mm; must match the geometry package in main.tex -----
TEXT_W = 120.0
TEXT_H = 180.0
GUTTER = 5.0          # \personalgutter, between two prints in a row
# The frame \mountedprint draws is a 0.3pt tikz stroke on the boundary of the
# image, so half of it -- 0.15pt -- falls outside.
RULE = 0.053
# The measure the rows are solved against, held back from the text width. A
# mounted print is not a flush-left grid: the four old prints on the composed
# page opposite run to 82% and 89% of the measure, and these want the same
# air round them. It also covers the rounding in the two decimal places the
# widths are written to, so a row can never overrun \linewidth.
MEASURE = 112.0
# No head over these pages, and so nothing to hold back from the first of
# them. They run straight on from the three prints 07-photobook.tex composes
# by hand -- the same photographs of the same man, and a head between them
# would announce a second gallery where there is only one continuing.
HEAD_RESERVE = 0.0

# A print is capped rather than blown up to span the measure. Two portraits
# solved to fill 112mm come to 79mm tall, and two of those rows will not sit
# on a page under a head; capped at 70 they do, and the pair comes out 49mm
# wide with 7mm of air down each side, which is the proportion the composed
# page sets its pair at.
MAX_H = 70.0
# A print alone in its row is set much larger -- tall enough that no row of
# two can share the page with it, so it takes one of its own and is centred
# on it. An odd number of photographs is what makes one, and the alternative
# tried first was to allow it a little more height than a pair: at 88mm it
# came out 65mm wide in the middle of an empty page and read as a photograph
# nobody had found a place for. Set as a plate it reads as one given a page,
# which is the same gesture the frontispiece makes and is the right way for
# a run of his portraits to end.
MAX_H_SOLO = 118.0
ROW_MAX = 2

# What a caption costs the row it is in, at \footnotesize. As in
# build-album.py, the depth has to be reserved before the rows are
# paginated, or a captioned row pushes its page over the bottom margin.
# These prints are twice the album's size and take the larger caption face,
# so a line is deeper and fewer characters go on it.
#
# CHARS_PER_MM is measured off the page rather than derived from the font
# metrics, because what decides the count is not the average character width
# but where the words happen to break: a 72-character caption set under a
# 45mm print comes out three lines, which is 0.53 characters to the
# millimetre and nothing like the 0.75 the metrics alone would suggest. The
# figure below is rounded down from that, so the estimate errs towards
# crediting a caption with one line more than it needs -- that costs 4mm of
# white, where crediting it with one fewer costs a row pushed off the page.
CAPTION_GAP = 2.2
CAPTION_LEAD = 3.6
CAPTION_CHARS_PER_MM = 0.50

# Slack a page may put between its rows before it stops spreading them and
# centres the block instead.
MAX_EXTRA = 8.0
SAFETY = 3.0          # what LaTeX adds between rows that this does not model
TOPSKIP = 3.87        # as build-album.py; see the note there

MIN_PIXELS = 600
LONG_EDGE = 1800      # these print at twice the album's size

# Not photographs of him but the artwork cut from them -- see the note at the
# top of this file.
SKIP = {
    "WhatsApp Image 2026-08-19 at 14.24.16.jpeg":
        "the scan plate-desk is cut from",
    "WhatsApp Image 2026-08-19 at 14.24.16 (1).jpeg":
        "the scan plate-agbada is cut from",
    "WhatsApp Image 2026-08-19 at 14.24.16 (2).jpeg":
        "the scan plate-studio is cut from",
    "WhatsApp Image 2026-08-19 at 14.24.16 (3).jpeg":
        "the scan plate-ledger is cut from",
    "franco_sitting_green.png":
        "the full-size original of the cover cut-out",
    "franco_sitting_green-print.png":
        "the cover cut-out, printed on the cover",
    "franco_nero.png":
        "a cut-out with no background, which needs a page built round it",
}

EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp"}


def collect():
    return photoset.collect(SRC, IN_USE, SKIP, MIN_PIXELS, EXTS)


def normalise(kept, captions):
    """The plates, each with whatever caption is filed against its source.

    Looked up by the file the photograph arrived in rather than by the plate
    it becomes: the plates are numbered by position, and a caption that
    followed the number would end up under somebody else the moment a
    photograph was added. See assets/data/captions.toml.
    """
    prepared = photoset.normalise(kept, OUT, "plates/personal", LONG_EDGE)
    return [(name, aspect, origin, captions.latex(path))
            for (name, aspect, origin), (path, _, _) in zip(prepared, kept)]


def compose(photos):
    """Two prints to a row, in the order they arrived.

    No shape-matching here, unlike the album. Every one of these is a
    portrait or close to square -- they are photographs of one man, not of
    rooms full of people -- so there is no landscape to pair a portrait with
    and nothing for a search over shapes to find. Taking them in order keeps
    a photograph next to the one it came in with, which is the only ordering
    anybody looking at these would expect.
    """
    return [photos[i:i + ROW_MAX] for i in range(0, len(photos), ROW_MAX)]


def row_height(row):
    """The print height for a row: solved to span the measure, then capped.

    The cap is what keeps these from filling the page edge to edge. A row
    held under it is set at that height and centred, which is how a mounted
    print wants to sit -- with paper round it.
    """
    solved = photoset.row_height([item[1] for item in row],
                                 MEASURE, GUTTER, RULE)
    return min(solved, MAX_H if len(row) > 1 else MAX_H_SOLO)


def caption_depth(row, height):
    """What the captions in a row add below the prints, in mm."""
    lines = 0
    for _, aspect, _, caption in row:
        if caption:
            per_line = max(1, int(height * aspect * CAPTION_CHARS_PER_MM))
            lines = max(lines, -(-len(caption) // per_line))
    return CAPTION_GAP + lines * CAPTION_LEAD if lines else 0.0


def row_extent(row):
    h = row_height(row)
    return h + caption_depth(row, h)


def paginate(rows):
    """Rows into pages, in the order they were composed."""
    pages, page, used = [], [], HEAD_RESERVE
    for row in rows:
        h = row_extent(row)
        if page and used + GUTTER + h > TEXT_H - SAFETY:
            pages.append(page)
            page, used = [], 0.0
        used += (GUTTER if page else 0.0) + h
        page.append(row)
    if page:
        pages.append(page)
    return pages


def emit(pages):
    lines = ["% Generated by assets/build-personal.py -- do not edit by hand.",
             "% Re-run assets/make-plates.sh after changing personal/.",
             "%",
             "% Provenance, so a photograph on the page can be traced back to",
             "% the file it came from:"]
    for page in pages:
        for row in page:
            for name, _, origin, _ in row:
                lines.append(f"%   {name.rsplit('/', 1)[1]}  <-  {origin}")
    lines.append("")

    for index, page in enumerate(pages):
        if index:
            lines += [r"\newpage", ""]

        # The rows are spread down the page rather than left to sit at the
        # top of it, and what a short page cannot spend that way is split
        # top and bottom so it reads as a centred block. The same treatment
        # the album pages get, with a freer hand: there are two rows to a
        # page here rather than three, so there is more to give away and a
        # wider gap between two mounted prints still reads as deliberate.
        avail = TEXT_H - SAFETY - (HEAD_RESERVE if not index else 0.0)
        heights = [row_height(row) for row in page]
        extents = [row_extent(row) for row in page]
        gaps = len(page) - 1
        slack = avail - sum(extents) - GUTTER * gaps
        gap = GUTTER + (min(slack / gaps, MAX_EXTRA) if gaps and slack > 0 else 0.0)
        top = max(avail - sum(extents) - gap * gaps, 0.0) / 2

        if top > TOPSKIP:
            lines.append(f"\\vspace*{{{top - TOPSKIP:.2f}mm}}")
        for row, h in zip(page, heights):
            if row is not page[0]:
                lines.append(f"\\vspace{{{gap:.2f}mm}}")
            cells = [
                f"  \\personalphotocap{{{name}}}{{{h * aspect:.2f}mm}}"
                f"{{{caption}}}" if caption else
                f"  \\personalphoto{{{name}}}{{{h * aspect:.2f}mm}}"
                for name, aspect, _, caption in row]
            lines.append("\\personalrow{%")
            lines.append("%\n  \\personalgap\n".join(cells) + "%")
            lines.append("}")
        lines.append("")
    TEX.write_text("\n".join(lines) + "\n")


def main():
    kept, dropped = collect()
    if not kept:
        TEX.write_text("% No usable images in assets/images/personal/.\n")
        print("build-personal: no usable images found", file=sys.stderr)
        return
    pages = paginate(compose(normalise(kept, captionfile.load())))
    emit(pages)
    captioned = sum(1 for page in pages for row in page
                    for *_, caption in row if caption)
    print(f"build-personal: {len(kept)} photographs, "
          f"{sum(len(p) for p in pages)} rows, {len(pages)} pages"
          + (f", {captioned} captioned" if captioned else "")
          + f" -> {TEX.relative_to(ROOT)}")
    for name, why in dropped:
        print(f"  skipped {name}: {why}")


if __name__ == "__main__":
    main()
