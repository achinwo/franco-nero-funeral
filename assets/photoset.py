#!/usr/bin/env python3
r"""A directory of photographs, read and prepared for print.

Shared by the two generated photo sections -- build-album.py, which sets the
family album out of assets/images/family_pics/, and build-personal.py, which
sets his own photographs out of assets/images/personal/. Both do the same
three things to a directory before they can lay anything out:

  collect()    take the images that should be printed, and say why the rest
               were left out
  normalise()  bake in the EXIF rotation, downsize, strip the metadata
  row_height() the one piece of geometry both layouts share

What they do afterwards is not shared, because it is not the same problem:
the album justifies two or three prints to the measure and packs the pages
tight, and the personal section mounts one or two much larger prints with
photo corners. Those layouts live in their own scripts.

ImageMagick 7 does the image work; every call goes through sh() so that a
failure comes back as an exception rather than as a silently missing plate.
"""

import hashlib
import subprocess


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True,
                          check=True).stdout.strip()


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


def collect(src, in_use, skip, min_pixels, exts):
    """The photographs in src worth printing, and what was left out.

    Returns (kept, dropped): kept as (path, width, height) with the pixel
    size after rotation, dropped as (name, reason) so the caller can print
    an account of it. A photograph is never dropped silently -- this is a
    funeral booklet, and a family photograph quietly missing from it is a
    worse fault than a page that needed another look.

    in_use is the directories holding everything the booklet prints
    elsewhere: a copy of the cover photograph, or of one of the old scans,
    dropped in here is recognised by content and skipped rather than printed
    twice. skip is the editorial exclusions, by filename, with a reason.
    """
    if not src.is_dir():
        return [], []

    used = {digest(p) for directory in in_use for p in directory.glob("*")
            if p.is_file() and p.suffix.lower() in exts}

    kept, dropped, seen = [], [], set()
    for path in sorted(src.iterdir()):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if path.name in skip:
            dropped.append((path.name, skip[path.name]))
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
        if min(w, h) < min_pixels:
            dropped.append((path.name, f"too small to print ({w}x{h})"))
            continue

        kept.append((path, w, h))
    return kept, dropped


def normalise(kept, out, plates, long_edge, quality=88):
    """Rotate, downsize and strip metadata into the plates directory.

    Returns (plate name, aspect ratio, source filename) per photograph, in
    the order given. The aspect is taken from the original rather than from
    the plate: the resize preserves it, and the original is the number the
    layout was solved against.

    The directory is cleared first. These plates are numbered by position,
    so a photograph added at the front renumbers everything after it and
    leaving stale files behind would print one of them.
    """
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.jpg"):
        stale.unlink()

    prepared = []
    for i, (path, w, h) in enumerate(kept, start=1):
        dest = out / f"{i:02d}.jpg"
        sh("magick", str(path), "-auto-orient",
           "-resize", f"{long_edge}x{long_edge}>",
           "-strip", "-quality", str(quality), str(dest))
        prepared.append((f"{plates}/{dest.stem}", w / h, path.name))
    return prepared


def row_height(aspects, measure, gutter, rule):
    """The height at which a row of these shapes spans the measure exactly.

    Every print in a row shares one height, and the widths that follow from
    it -- height times aspect -- plus the gutters between them and the frame
    each one carries come to the measure. Nothing is cropped to fit: these
    are photographs of a man's life, and cropping them is not a decision a
    script should be making.
    """
    span = measure - (len(aspects) - 1) * gutter - len(aspects) * 2 * rule
    return span / sum(aspects)
