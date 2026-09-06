#!/usr/bin/env python3
r"""Build the family album pages of the Photographs section.

Reads every image in assets/images/family_pics/, normalises each one for
print, solves a justified-rows layout across as many pages as it takes, and
writes assets/images/plates/family-album.tex for 07-photobook.tex to \input.

Drop a photograph into family_pics/ and re-run assets/make-plates.sh: the
album re-flows on its own. Nothing downstream needs editing.

Layout
------
Justified rows, the arrangement a photo book uses for mixed shapes: images
keep their own aspect ratio (nothing is cropped to fit a cell), and every
picture in a row shares one height chosen so the row spans the text width
exactly. A grid of fixed cells would have to crop, and these are family
photographs -- cropping them is not a decision a script should make.
"""

import itertools
import pathlib
import sys

import captions as captionfile
import photoset

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/images/family_pics"
OUT = ROOT / "assets/images/plates/family"
TEX = ROOT / "assets/images/plates/family-album.tex"
# Everything already in the booklet, so a copy of the cover photograph
# dropped into family_pics/ is recognised and skipped rather than printed
# twice. Two directories rather than one: his own photographs, and the four
# scans the plates are cut from, were moved out of images/ into personal/,
# and a check that only read the loose files above them would have gone
# quietly empty -- which is the worst way for a guard like this to fail.
IN_USE = (ROOT / "assets/images", ROOT / "assets/images/personal")

# --- page geometry, in mm; must match the geometry package in main.tex -----
TEXT_W = 120.0
TEXT_H = 180.0
GUTTER = 3.0
RULE = 0.106          # 0.3pt frame, which \fbox adds outside the image
# Held back from the measure so that a row solved to span it exactly cannot
# be tipped over it by the rounding in the two decimal places the widths are
# written to. A row that overruns \linewidth by a thousandth of a millimetre
# does not warn: the gutter between two photographs is a legal place to
# break a line, so TeX quietly sets the rest of the row underneath, and the
# page is suddenly a row taller than the arithmetic here believes.
EPSILON = 0.1
HEAD_RESERVE = 16.0   # the "The Family Album" head on the first album page

# A page is three rows deep, so a row wants to be about a third of it. The
# arithmetic says 55mm; 52 is set instead because of what the shapes do at
# the margin. At 55 a portrait beside a landscape (55mm) beats three
# portraits (54mm) almost every time, and the album comes out 21 rows, which
# is one more than six pages of three will hold -- it ends on two half-empty
# pages. At 52 the three-across rows win often enough to make it 20, which
# is exactly six pages of three after the opening page, and nothing is left
# over. Four photographs across was tried and abandoned: the faces on an A5
# page are 27mm wide and stop being readable.
TARGET_H = 52.0
MAX_H = 78.0          # a short last row is centred rather than blown up
ROW_MIN, ROW_MAX = 2, 3
WINDOW = 6            # how far ahead compose() may look for a shape it needs

# Slack a page may put between its rows before it stops spreading them and
# centres the block instead. Four millimetres on top of the gutter is air;
# much more and the rows stop reading as a grid.
MAX_EXTRA = 4.0
# Held back from the page in the arithmetic below, to cover what LaTeX adds
# between one row and the next (\lineskip, \parskip, the 0.3pt frame \fbox
# draws outside each photograph) that this script does not model. Without it
# a page computed to fill exactly would spill its last row onto the next one.
SAFETY = 3.0
# \topskip, the glue TeX puts above the first box on a page, as read back
# from the document with \showthe\topskip. A row of photographs is far
# taller than it, so a page opening on one gets none of it -- but \vspace*
# opens with a zero-height rule, which is shorter than it, so a page opening
# on that gets all 11pt. A page wanting a top margin asks for that much less
# of it; a page wanting none asks for nothing at all, and gets nothing.
TOPSKIP = 3.87

# What a caption costs the row it is in. Most of the album is uncaptioned --
# these are faces the family already knows -- but a captioned print needs the
# depth reserving before the rows are paginated, or the page it falls on ends
# up a caption too tall and pushes its last row over the bottom margin.
#
# CHARS_PER_MM is measured off the page rather than derived from the font
# metrics, because what settles the count is not the average character width
# but where the words happen to break: a 72-character caption under a 45mm
# print comes out three lines, which is 0.53 characters to the millimetre at
# \footnotesize and nothing like the 0.75 the metrics alone would suggest.
# The album sets its captions a size smaller, so a few more fit on a line.
# The figure errs low, so a caption is credited with one line more rather
# than one fewer: that costs 3mm of white, where the other way costs a row
# pushed off the bottom of the page.
CAPTION_GAP = 1.4          # mm between a print and its caption
CAPTION_LEAD = 3.0         # mm a line of caption occupies
CAPTION_CHARS_PER_MM = 0.56

MIN_PIXELS = 600      # below this the print would be visibly soft at album size
LONG_EDGE = 1500      # normalised size; ~380dpi at the largest size used here

# Editorial skips, by filename. Exact duplicates are caught automatically by
# content hash below, but near-duplicates -- the same moment shot twice, at
# different zooms -- are not, and they cannot safely be. A perceptual hash
# (dHash over an 8x8 gradient) was tried and does not separate them here: the
# two frames of the couple by the car score 19 bits apart while two plainly
# different photographs score 17, so any threshold that dropped the pair
# would also drop something the family meant to keep. Silently deleting a
# photograph from a funeral booklet is the wrong failure to risk, so the
# judgement is made by eye and recorded here, where it can be reversed by
# deleting a line.
SKIP = {
    "WhatsApp Image 2026-08-31 at 17.05.20.jpeg":
        "near-duplicate of 17.03.51 (same pose, closer crop)",
}

EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp"}


def collect():
    return photoset.collect(SRC, IN_USE, SKIP, MIN_PIXELS, EXTS)


def normalise(kept, captions):
    """The plates, each with whatever caption is filed against its source.

    A caption is looked up by the file the photograph arrived in, not by the
    plate it becomes: the plates are numbered by position and renumbered
    whenever a photograph is added, and a caption that followed the number
    would end up under somebody else. See assets/data/captions.toml.
    """
    prepared = photoset.normalise(kept, OUT, "plates/family", LONG_EDGE)
    return [(name, aspect, origin, captions.latex(path))
            for (name, aspect, origin), (path, _, _) in zip(prepared, kept)]


def caption_depth(row, height):
    """What the captions in a row add below the prints, in mm.

    One depth for the whole row rather than one per photograph: the prints
    hang from a common line, so the row is as deep as its deepest caption
    and a page has to reserve that much.
    """
    lines = 0
    for _, aspect, _, caption in row:
        if caption:
            per_line = max(1, int(height * aspect * CAPTION_CHARS_PER_MM))
            lines = max(lines, -(-len(caption) // per_line))
    return CAPTION_GAP + lines * CAPTION_LEAD if lines else 0.0


def row_extent(row):
    """The full depth a row takes on the page: its prints, and any caption
    hanging under them."""
    h = row_height(row)
    return h + caption_depth(row, h)


def compose(photos):
    """Build the rows.

    A row's height is decided by the shapes in it, and only some of the
    combinations are any use: three portraits come to 54mm and a portrait
    beside a landscape to 55mm, but two landscapes come to 41mm and two
    portraits to 83mm. Filling rows in the order the photographs happen to
    arrive takes whatever those shapes give, which is how a page ends up
    either three-fifths full or a row over.

    So rows are composed rather than filled: of the two- and three-photograph
    rows that can be made from the next few, take whichever comes closest to
    TARGET_H. Mixing the shapes is the whole trick -- a landscape set beside
    two portraits is what keeps the rows, and with them the pages, even. The
    window is what keeps a photograph near the ones it arrived with: a search
    over the whole album would sort it by shape, which is not an order
    anybody would want to look through.
    """
    pool, packed = list(photos), []
    while len(pool) > ROW_MAX:
        window = range(min(WINDOW, len(pool)))
        best = min((combo
                    for k in range(ROW_MIN, ROW_MAX + 1)
                    for combo in itertools.combinations(window, k)),
                   key=lambda c: abs(height_of([pool[i] for i in c]) - TARGET_H))
        packed.append([pool[i] for i in best])
        for i in sorted(best, reverse=True):
            pool.pop(i)

    # What is left is a last row of one, two or three. One on its own reads
    # as a photograph nobody found a place for, so it joins the row above --
    # or, if that row is already full, takes one of its three down for company.
    if len(pool) == 1 and packed:
        if len(packed[-1]) < ROW_MAX:
            packed[-1] += pool
        else:
            packed.append([packed[-1].pop()] + pool)
    elif pool:
        packed.append(pool)
    return packed


def height_of(row):
    return photoset.row_height([item[1] for item in row],
                               TEXT_W - EPSILON, GUTTER, RULE)


def row_height(row):
    return min(height_of(row), MAX_H)


def paginate(packed):
    """Rows into pages, in the order the rows were composed.

    The rows now all land near one height, so filling each page in turn is
    enough to keep the pages even -- there is nothing left for a reordering
    to fix, and the album keeps the sequence it arrived in.
    """
    pages, page, used = [], [], HEAD_RESERVE
    for row in packed:
        h = row_extent(row)
        if page and used + GUTTER + h > TEXT_H - SAFETY:
            pages.append(page)
            page, used = [], 0.0
        used += (GUTTER if page else 0.0) + h
        page.append(row)
    if page:
        pages.append(page)

    # One row alone on the last page is the same mistake as one photograph
    # alone on the last row, a page further out.
    if len(pages) > 1 and len(pages[-1]) == 1 and len(pages[-2]) > 2:
        pages[-1].insert(0, pages[-2].pop())
    return pages


def emit(pages):
    lines = ["% Generated by assets/build-album.py -- do not edit by hand.",
             "% Re-run assets/make-plates.sh after changing family_pics/.",
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

        # The rows are set to fill the page rather than to sit at the top of
        # it with the remainder falling out of the bottom, which is what
        # leaves an album page looking half-finished. The slack goes between
        # the rows, up to MAX_EXTRA of it; whatever a short page cannot
        # spend that way is split top and bottom instead, so the last page
        # of the album reads as a centred block rather than a page that ran
        # out. A full page has nothing left to centre and sits flush.
        avail = TEXT_H - SAFETY - (HEAD_RESERVE if not index else 0.0)
        # Two sets of numbers: the extent a row takes on the page, captions
        # and all, which is what the spreading below is solved against, and
        # the height of the prints themselves, which is what goes into the
        # macros.
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
                f"  \\albumphotocap{{{name}}}{{{h * aspect:.2f}mm}}"
                f"{{{h:.2f}mm}}{{{caption}}}" if caption else
                f"  \\albumphoto{{{name}}}{{{h * aspect:.2f}mm}}{{{h:.2f}mm}}"
                for name, aspect, _, caption in row]
            lines.append("\\albumrow{%")
            lines.append("%\n  \\albumgap\n".join(cells) + "%")
            lines.append("}")
        lines.append("")
    TEX.write_text("\n".join(lines) + "\n")


def main():
    kept, dropped = collect()
    if not kept:
        TEX.write_text("% No usable images in assets/images/family_pics/.\n")
        print("build-album: no usable images found", file=sys.stderr)
        return
    pages = paginate(compose(normalise(kept, captionfile.load())))
    emit(pages)
    captioned = sum(1 for page in pages for row in page
                    for *_, caption in row if caption)
    print(f"build-album: {len(kept)} photographs, "
          f"{sum(len(p) for p in pages)} rows, {len(pages)} pages"
          + (f", {captioned} captioned" if captioned else "")
          + f" -> {TEX.relative_to(ROOT)}")
    for name, why in dropped:
        print(f"  skipped {name}: {why}")


if __name__ == "__main__":
    main()
