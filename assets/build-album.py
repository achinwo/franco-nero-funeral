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

import hashlib
import itertools
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/images/family_pics"
OUT = ROOT / "assets/images/plates/family"
TEX = ROOT / "assets/images/plates/family-album.tex"
# Everything already in the booklet, so a copy of the cover photograph
# dropped into family_pics/ is recognised and skipped rather than printed
# twice.
IN_USE = ROOT / "assets/images/"

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


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def digest(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def oriented_size(path):
    """Pixel size after EXIF rotation is applied.

    -auto-orient matters: several of these came off a phone with an EXIF
    rotation flag, and pdflatex does not honour it -- an unrotated portrait
    would be laid out as a landscape and come out sideways.
    """
    w, h = sh("magick", str(path), "-auto-orient",
              "-format", "%w %h", "info:").split()
    return int(w), int(h)


def collect():
    if not SRC.is_dir():
        return [], []

    # Hashes of the images the booklet already uses elsewhere.
    used = {digest(p) for p in IN_USE.glob("*")
            if p.is_file() and p.suffix.lower() in EXTS}

    kept, dropped, seen = [], [], set()
    for path in sorted(SRC.iterdir()):
        if not path.is_file() or path.suffix.lower() not in EXTS:
            continue
        if path.name in SKIP:
            dropped.append((path.name, SKIP[path.name]))
            continue

        d = digest(path)
        if d in used:
            dropped.append((path.name, "already used elsewhere in the booklet"))
            continue
        if d in seen:
            dropped.append((path.name, "duplicate of an earlier file"))
            continue
        seen.add(d)

        try:
            w, h = oriented_size(path)
        except subprocess.CalledProcessError:
            dropped.append((path.name, "unreadable"))
            continue
        if min(w, h) < MIN_PIXELS:
            dropped.append((path.name, f"too small to print ({w}x{h})"))
            continue

        kept.append((path, w, h))
    return kept, dropped


def normalise(kept):
    """Rotate, downsize and strip metadata into plates/family/."""
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.jpg"):
        stale.unlink()

    out = []
    for i, (path, w, h) in enumerate(kept, start=1):
        dest = OUT / f"{i:02d}.jpg"
        sh("magick", str(path), "-auto-orient",
           "-resize", f"{LONG_EDGE}x{LONG_EDGE}>",
           "-strip", "-quality", "88", str(dest))
        out.append((f"plates/family/{dest.stem}", w / h, path.name))
    return out


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
    span = TEXT_W - EPSILON - (len(row) - 1) * GUTTER - len(row) * 2 * RULE
    return span / sum(item[1] for item in row)


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
        h = row_height(row)
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
            for name, _, origin in row:
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
        heights = [row_height(row) for row in page]
        gaps = len(page) - 1
        slack = avail - sum(heights) - GUTTER * gaps
        gap = GUTTER + (min(slack / gaps, MAX_EXTRA) if gaps and slack > 0 else 0.0)
        top = max(avail - sum(heights) - gap * gaps, 0.0) / 2

        if top > TOPSKIP:
            lines.append(f"\\vspace*{{{top - TOPSKIP:.2f}mm}}")
        for row, h in zip(page, heights):
            if row is not page[0]:
                lines.append(f"\\vspace{{{gap:.2f}mm}}")
            cells = [f"  \\albumphoto{{{name}}}{{{h * aspect:.2f}mm}}{{{h:.2f}mm}}"
                     for name, aspect, _ in row]
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
    pages = paginate(compose(normalise(kept)))
    emit(pages)
    print(f"build-album: {len(kept)} photographs, "
          f"{sum(len(p) for p in pages)} rows, {len(pages)} pages "
          f"-> {TEX.relative_to(ROOT)}")
    for name, why in dropped:
        print(f"  skipped {name}: {why}")


if __name__ == "__main__":
    main()
