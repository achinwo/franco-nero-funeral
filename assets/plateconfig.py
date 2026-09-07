#!/usr/bin/env python3
r"""Read one setting out of assets/data/plates.toml, for make-plates.sh.

    python3 assets/plateconfig.py <plate> <key>

Prints the value and nothing else, so a shell script can take it with
`$(...)`. An unset or empty value prints nothing and exits 0 -- that is a
setting the caller is expected to have a default for, not a fault. A key
naming a file that is not there exits non-zero with a message on stderr,
because that one *is* a fault: it means somebody pointed a plate at a
photograph that has since been renamed, and the alternative to stopping is a
cover silently built from the wrong picture.

`source` values come back as a path relative to assets/images/, which is
where make-plates.sh does its work, so they can be handed straight to
ImageMagick.

This exists because make-plates.sh is a shell script and the config is TOML,
which shell cannot read. It is deliberately one value per call: a handful of
subprocesses on a script that already spends thirty seconds in ImageMagick
costs nothing, and it keeps the shell free of parsing.
"""

import pathlib
import sys

import textkit

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOML = ROOT / "assets/data/plates.toml"
IMAGES = ROOT / "assets/images"


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: plateconfig.py <plate> <key>")
    plate, key = sys.argv[1], sys.argv[2]

    if not TOML.is_file():
        # No config at all is not an error: every caller has a default, and
        # the booklet built for months before this file existed.
        return

    settings = textkit.read_toml(TOML).get(plate)
    if settings is None:
        sys.exit(f"plateconfig: {TOML.name} has no [{plate}] section")

    value = str(settings.get(key, "")).strip()
    if not value:
        return

    if key == "source" and not (IMAGES / value).is_file():
        sys.exit(f"plateconfig: [{plate}] source = {value!r} -- "
                 f"no such file under assets/images/")

    print(value)


if __name__ == "__main__":
    main()
