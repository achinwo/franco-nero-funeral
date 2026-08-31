#!/bin/sh
# Regenerates every derived image the booklet uses, from the four original
# scans, into assets/images/plates/. Run from anywhere; requires ImageMagick 7.
#
# Two families of output:
#
#   plate-*.png   the photographs as printed in the Photographs section --
#                 cropped to the print, toned to one warm sepia so four
#                 scans of very different age sit together as a set.
#
#   ghost-*.png   A5 page-sized washes for page backgrounds. The fade is
#                 baked into the pixels rather than applied as PDF
#                 transparency, so what the printer's RIP receives is
#                 ordinary opaque artwork with no flattening surprises.
#                 Two strengths: -lo for pages carrying dense liturgy text,
#                 -hi for the sparse pages that can take more.
set -eu

# Resolved before the cd, so the later call to build-album.py still works.
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/images"
mkdir -p plates
SRC="WhatsApp Image 2026-08-19 at 14.24.16"

# -auto-orient matters: scan (1) carries an EXIF rotation that pdflatex
# does not honour, so the rotation has to be baked in here.
crop() { # crop <suffix> <geometry> <name>
  magick "$SRC$1.jpeg" -auto-orient -crop "$2" +repage "plates/_raw-$3.png"
}
crop ""     1030x780+25+15  desk
crop " (1)" 780x1075+150+205 agbada
crop " (2)" 905x1215+15+52   studio
crop " (3)" 875x1235+12+30   ledger

# The set is a mix of untinted silver prints and hand-tinted ones (the blue
# headwrap, the blue-tinted face over the cartons). Flattening everything to
# sepia would throw that away, so the sepia is laid down at 78% and the
# original colour left showing through at 22%.
tone() {
  magick "plates/_raw-$1.png" \
    \( +clone -colorspace Gray -auto-level \
       -sigmoidal-contrast 3x50% \
       +level-colors '#2e2620','#f6f0e6' \) \
    -compose blend -define compose:args=78 -composite \
    -strip "plates/plate-$1.png"
}
for n in desk agbada studio ledger; do tone "$n"; done

# --- page ghosts -----------------------------------------------------------
# A5 at 200dpi. Detail is irrelevant at these strengths; smoothness is not,
# which is why these stay PNG.
W=1165; H=1654

ghost() { # ghost <name> <dark end> <variant>
  name=$1; dark=$2; variant=$3
  # Cover-crop the plate to the page shape, anchored south so that if
  # anything falls off the edge it is the space above his head, not the face.
  #
  # The wash is a warm duotone, not a percentage of the sepia plate over
  # white. Diluting the plate to 7% leaves a neutral grey that reads as a
  # smudge on the page; squeezing the whole tonal range into a narrow warm
  # band instead -- near-white at the top end, tea-stained at the bottom --
  # reads as a faded photograph on aged paper, which is the point.
  magick "plates/plate-$name.png" \
      -resize "${W}x${H}^" -gravity south -extent "${W}x${H}" \
      -colorspace Gray -auto-level +level-colors "$dark",'#FCFAF6' \
      "plates/_wash.png"
  # Mask. A vertical ramp clears the top third of the page, where the
  # section heading sits, and reaches full strength by the time the text
  # block starts -- so the figure arrives whole below the heading rather
  # than being decapitated by the fade. A soft feather down each side keeps
  # the image off the trim edges. No radial vignette: it hollowed the
  # figure out into texture.
  magick -size "${W}x${H}" gradient:black-white \
      -function polynomial "-2.6,3.9,0.0,0" "plates/_v.png"
  magick -size "${H}x${W}" gradient:black-white \
      -function polynomial "-4,4,0,0" -rotate 90 "plates/_h.png"
  magick "plates/_v.png" "plates/_h.png" -compose multiply -composite \
      -blur 0x10 "plates/_m.png"
  magick "plates/_wash.png" "plates/_m.png" \
      -alpha off -compose copy_opacity -composite \
      -background white -alpha remove -alpha off \
      -strip "plates/ghost-$name-$variant.png"
}

# Only the three portrait scans are ghosted. The desk photograph is
# landscape; cover-cropping it to a portrait page throws away the desk, the
# telephone and the shelves and leaves an unreadable fragment of an arm. It
# earns its place full size on the album page instead.
for n in agbada studio ledger; do
  ghost "$n" '#EDE6DA' lo
  ghost "$n" '#D6C9B4' hi
done

rm -f plates/_raw-*.png plates/_wash.png plates/_v.png plates/_h.png plates/_m.png

# --- frontispiece ----------------------------------------------------------
# A full-bleed A5 plate for the opening page of the Photographs section: the
# studio portrait cover-cropped to the page, with a white field burnt into
# the foot for the type to sit on and a gradient dissolving that field back
# into the photograph, so there is no visible edge. The same device as the
# cover, so the two pages rhyme.
#
# The white field is carried in as an image with the ramp copied into its
# alpha channel. The three-image `-composite` mask form does not apply here:
# with -compose over it silently ignores the mask.
FW=1748; FH=2480
# Solid white from 74% of the page down, so the type at the foot sits on a
# clean field rather than on his trousers -- a linear ramp all the way to
# the trim left the caption line at 70% grey and unreadable.
magick -size "${FW}x$((FH * 52 / 100))" xc:black \
       -size "${FW}x$((FH * 22 / 100))" gradient:black-white \
       -size "${FW}x$((FH * 26 / 100))" xc:white \
       -append -resize "${FW}x${FH}!" -blur 0x8 "plates/_scrim.png"
magick "plates/plate-studio.png" \
    -resize "${FW}x${FH}^" -gravity north -extent "${FW}x${FH}" \
    \( -size "${FW}x${FH}" xc:white "plates/_scrim.png" \
       -alpha off -compose copy_opacity -composite \) \
    -compose over -composite -strip "plates/front-studio.png"
rm -f plates/_scrim.png

# --- family album ----------------------------------------------------------
# The modern colour photographs are a separate problem from the four old
# prints: they need no toning, only orientation, downsizing and a layout.
# build-album.py does all three and writes plates/family-album.tex.
python3 "$HERE/build-album.py"
