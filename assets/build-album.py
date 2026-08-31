#!/usr/bin/env python3
"""Build the family album pages of the Photographs section.

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
HEAD_RESERVE = 16.0   # the "The Family Album" head on the first album page

# Rows aim for this height and close as soon as they are no taller. At 56mm
# a row of three portraits (50mm) closes and a row of two (78mm) does not,
# which is the rhythm the album wants: at four across, the faces on an A5
# page are 27mm wide and stop being readable.
TARGET_H = 56.0
MAX_H = 78.0          # a short last row is centred rather than blown up

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


def rows(photos):
    """Greedy justified rows: keep adding until the row is no taller than
    TARGET_H, which for these mostly-portrait photographs lands on three."""
    packed, row = [], []
    for item in photos:
        row.append(item)
        if height_of(row) <= TARGET_H:
            packed.append(row)
            row = []
    if row:
        packed.append(row)

    # A single photograph stranded on the last row looks like a mistake.
    # Move one down from the row above so the album ends on a pair.
    if len(packed) > 1 and len(packed[-1]) == 1 and len(packed[-2]) > 2:
        packed[-1].insert(0, packed[-2].pop())
    return packed


def height_of(row):
    span = TEXT_W - (len(row) - 1) * GUTTER - len(row) * 2 * RULE
    return span / sum(item[1] for item in row)


def paginate(packed):
    """Order rows so the pages come out evenly filled.

    Left in photo order the rows here run short, short, tall, tall, which
    packs as two thin rows on one page and two deep ones on the next -- the
    first page then ends in 60mm of white that reads as a mistake. Dealing
    tall and short alternately gives every page one of each. The photographs
    have no meaningful sequence (the filenames are timestamps), so ordering
    rows for the page costs nothing.
    """
    by_height = sorted(packed, key=lambda r: -min(height_of(r), MAX_H))
    out, lo, hi = [], 0, len(by_height) - 1
    while lo <= hi:
        out.append(by_height[lo])
        lo += 1
        if lo <= hi:
            out.append(by_height[hi])
            hi -= 1
    return out


def emit(packed):
    lines = ["% Generated by assets/build-album.py -- do not edit by hand.",
             "% Re-run assets/make-plates.sh after changing family_pics/.",
             "%",
             "% Provenance, so a photograph on the page can be traced back to",
             "% the file it came from:"]
    for row in packed:
        for name, _, origin in row:
            lines.append(f"%   {name.rsplit('/', 1)[1]}  <-  {origin}")
    lines.append("")
    used = HEAD_RESERVE
    first = True
    for row in packed:
        h = min(height_of(row), MAX_H)
        if not first and used + h > TEXT_H:
            lines += ["\\newpage", ""]
            used = 0.0
        used += h + GUTTER
        first = False

        cells = []
        for name, aspect, _ in row:
            cells.append(f"  \\albumphoto{{{name}}}{{{h * aspect:.2f}mm}}{{{h:.2f}mm}}")
        lines.append("\\albumrow{%")
        lines.append("%\n  \\albumgap\n".join(cells) + "%")
        lines += ["}", ""]
    TEX.write_text("\n".join(lines) + "\n")


def main():
    kept, dropped = collect()
    if not kept:
        TEX.write_text("% No usable images in assets/images/family_pics/.\n")
        print("build-album: no usable images found", file=sys.stderr)
        return
    packed = paginate(rows(normalise(kept)))
    emit(packed)
    print(f"build-album: {len(kept)} photographs, "
          f"{len(packed)} rows -> {TEX.relative_to(ROOT)}")
    for name, why in dropped:
        print(f"  skipped {name}: {why}")


if __name__ == "__main__":
    main()
