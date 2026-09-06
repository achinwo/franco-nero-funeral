#!/usr/bin/env python3
r"""The captions, read from assets/data/captions.toml.

A caption belongs to a photograph, not to a place on a page. The same
picture may be printed as a mounted plate, reflowed into the family album,
or set beside a tribute, and it says the same thing in each -- so the words
are kept once, against the image file, and every generator that prints that
image asks here for them.

    [caption]
    "plates/plate-desk.png" = "At the desk"

The key is the path of the image file, relative to assets/images/ -- the
same root \graphicspath gives the document, so a key is the file as the
booklet already refers to it, with its extension on. Two kinds of path turn
up in it, and the difference is worth stating because it is the one thing
about this file that is not obvious:

  originals   family_pics/album-04.jpg, personal/album-27.jpg -- a
              photograph as the family sent it. This is the usual case.

  plates      plates/plate-desk.png -- one of the four old prints. Their
              four crops come out of *one* scan, so the scan cannot name a
              photograph; the crop is the photograph, and it is what the
              booklet prints. These are generated files, which nothing else
              in the project keys off, but the caption has to hang on the
              picture that is printed rather than on the sheet it was cut
              from.

Keying on the file rather than on a caption number is what keeps captions
still while the book moves. The album re-flows every time a photograph is
added, and its plates are renumbered when it does; a caption keyed to a
number would follow the number rather than the picture, and quietly end up
under somebody else.

The value is plain text: no LaTeX, and the inline tags textkit understands
(<i>, <b>) if a word wants emphasis. It is converted on the way out by
latex() below, so what the TOML holds is only ever what will be read off
the page.
"""

import pathlib

import textkit

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOML = ROOT / "assets/data/captions.toml"
# Where \includegraphics starts looking, per \graphicspath in main.tex, and
# so what every key in captions.toml is relative to.
IMAGES = ROOT / "assets/images"


def _normal(path):
    """A key in the one shape lookups compare on: relative to assets/images/,
    forward slashes, no './'.

    Callers hold a path in whichever form suits them -- a key out of
    captions.toml, already relative to the image root; an absolute
    pathlib.Path from a directory scan; the repo-relative `imagePath` a
    tribute carries in tributes.toml -- and all three have to land on the
    same key. The repo-relative form is taken as well as the short one
    because it is what tributes.toml already holds, and a caption that
    silently failed to match would be invisible on the page.

    Returns None for a path that is not under assets/images/ at all, which
    is a caption nothing could ever print.
    """
    path = pathlib.PurePosixPath(pathlib.Path(path).as_posix())
    if path.is_absolute():
        try:
            path = path.relative_to(pathlib.PurePosixPath(IMAGES.as_posix()))
        except ValueError:
            return None
    elif path.parts[:2] == ("assets", "images"):
        path = pathlib.PurePosixPath(*path.parts[2:])
    key = path.as_posix()
    return None if not key or key == "." or key.startswith("..") else key


class Captions:
    """The caption file, loaded once and asked many times."""

    def __init__(self, entries, missing, outside):
        self._entries = entries
        # Keys naming a file that is not there, and keys naming somewhere
        # outside assets/images/ altogether. Kept rather than raised on: a
        # mistyped path should be reported, but it is not worth stopping a
        # funeral booklet from building over.
        self.missing = missing
        self.outside = outside

    def raw(self, image):
        """The caption for an image as it was typed, or None."""
        key = _normal(image)
        return self._entries.get(key) if key else None

    def latex(self, image):
        """The caption for an image, set for LaTeX, or None.

        One line, however it was typed: a caption sits under a picture in a
        measure the layout has already settled, and it wraps to fit. A <br/>
        in it would break that measure -- and, in the album, the arithmetic
        that reserved room for it -- so breaks are folded back to spaces.
        """
        text = self.raw(image)
        if text is None:
            return None
        text = textkit.oneline(str(text))
        return text or None

    def items(self):
        """Every caption, as (image path, caption set for LaTeX)."""
        for key in sorted(self._entries):
            text = self.latex(key)
            if text:
                yield key, text

    def unresolved(self):
        """Keys that named nothing under assets/images/.

        Everything the booklet prints lives there, so such a key is a caption
        that can never reach a page -- and, being a caption, its absence is
        invisible. Reported so that it is not.
        """
        return self.outside


def graphics_key(image):
    r"""The name \includegraphics is given for an image, from its path.

    A key is already relative to \graphicspath, so all that separates the
    two is the extension, which the document leaves off so that a plate can
    change format without the section printing it changing with it:
    plates/plate-desk.png is written into the booklet as plates/plate-desk,
    and that is the name a caption has to be filed under for main.tex to
    find it again.
    """
    key = _normal(image)
    return None if key is None else str(pathlib.PurePosixPath(key).with_suffix(""))


def load():
    """Read captions.toml. A missing file is not an error -- it means no
    photograph has been captioned yet, which is where this booklet started."""
    if not TOML.is_file():
        return Captions({}, [], [])

    data = textkit.read_toml(TOML)
    entries, missing, outside = {}, [], []
    for key, text in data.get("caption", {}).items():
        image = _normal(key)
        if image is None:
            outside.append(key)
            continue
        if not (IMAGES / image).is_file():
            missing.append(image)
        entries[image] = text
    return Captions(entries, missing, outside)
