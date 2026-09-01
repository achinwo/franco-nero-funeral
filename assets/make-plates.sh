#!/bin/sh
# Regenerates every derived file the booklet inputs -- the images, from the
# four original scans, into assets/images/plates/, and the tributes from the
# copy the family sent. Run from anywhere; requires ImageMagick 7.
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

# --- the cover -------------------------------------------------------------
# The cover is a montage, not a photograph. sky_backdrop.png is A5 stationery:
# a dawn cloudscape over the top three-fifths of the sheet, a hard seam, then
# textured paper. The studio cut-out is stood up in it, so that the man they
# called De Sky Man rises out of the cloud bank instead of out of the blank
# white field the cover used before.
#
# Two decisions drive every number below. The seam sits at 62% of the page,
# a shade above where the backdrop puts it, so that the weather keeps the
# proportion the backdrop was cut to while the type still has a field of its
# own to sit in. And the cloud is composited twice, once
# as the ground and again in front of him, so that real wisps pass over his
# chest; a plain white ramp would have dissolved him into fog, which reads as
# a fault in the printing rather than as weather.
CW=1748; CH=2480                 # A5 at 300dpi, as the frontispiece
CSEAM=$((CH * 62 / 100))         # cloud bank meets paper field
CPH=$((CH - CSEAM))
CFW=$((CW * 90 / 100))           # his width on the page
CFH=$((1784 * CFW / 1221))       # ... and the height that follows from it
COX=$(((CW - CFW) / 2))
CTOP=$((CH * 5 / 100))           # the top of his cap
CIN=$((CH * 44 / 100))           # cloud starts to pass in front of him
COUT=$((CH * 575 / 1000))        # cloud entirely in front

# Landmarks in the backdrop, which is 1240x1748 with its seam on row 1114.
SKYW=1240; SKYSEAM=1114

# The sky, enlarged until the seam falls where we want it and cropped to the
# page. It is a low-resolution asset being asked to cover an A5 sheet at 300
# dpi, which only works because it is cloud: there is no edge in it for the
# upscale to soften.
magick sky_backdrop.png -crop "${SKYW}x${SKYSEAM}+0+0" +repage -filter Lanczos \
    -resize "${CW}x${CSEAM}^" -gravity center -extent "${CW}x${CSEAM}" \
    "plates/_c-sky.png"

# The paper field is mirror-tiled from a band of the backdrop's own stock,
# well clear of the seam. The
# green and blue multipliers take the neutral grey stock to ivory without
# flattening its grain, the way a flat tint would; the same ivory is used for
# the mist below, so the two meet invisibly.
magick sky_backdrop.png -crop "${SKYW}x400+0+1250" +repage -filter Lanczos \
    -resize "${CW}x" -channel G -evaluate multiply 0.985 \
    -channel B -evaluate multiply 0.955 +channel "plates/_c-band.png"
magick "plates/_c-band.png" \( "plates/_c-band.png" -flip \) \
       "plates/_c-band.png" \( "plates/_c-band.png" -flip \) \
    -append -crop "${CW}x${CPH}+0+0" +repage "plates/_c-field.png"

# The page, with the zenith deepened: the backdrop's own sky runs pale all the
# way up, and a cover wants somewhere for the eye to come to rest above his
# head.
magick "plates/_c-sky.png" "plates/_c-field.png" -append \
    \( -size "${CW}x$((CH * 30 / 100))" gradient:'#1F3B57'-'#1F3B5700' \
       -channel A -evaluate multiply 0.14 +channel \) \
    -geometry +0+0 -compose over -composite "plates/_c-base.png"

# Light behind him. It is doing two jobs: the halo the day asks for, and the
# separation the photograph needs, because his cap is a dark teal that would
# otherwise sit flat against a mid-blue sky.
magick -size 1200x1200 radial-gradient:'#FFF6E4FF'-'#FFF6E400' -resize '1500x1100!' \
    -channel A -evaluate multiply 0.65 +channel "plates/_c-glow.png"
magick "plates/_c-base.png" "plates/_c-glow.png" \
    -geometry "+$((COX + 545 * CFW / 1221 - 750))+$((CTOP + 309 * CFW / 1221 - 550))" \
    -composite "plates/_c-lit.png"

magick franco_sitting_green-print.png -trim +repage \
    -filter Lanczos -resize "${CFW}x${CFH}!" "plates/_c-man.png"
magick "plates/_c-lit.png" "plates/_c-man.png" \
    -geometry "+${COX}+${CTOP}" -composite "plates/_c-stood.png"

# The cloud again, in front. The layer is the finished ground carrying a ramp
# in its alpha, so above the ramp nothing changes and below it the page simply
# closes over him -- cloud first, then the paper field, which is why his cut
# lower half never has to be dealt with: it is behind the page.
magick -size "${CW}x${CIN}" xc:black \
       -size "${CW}x$((COUT - CIN))" gradient:black-white \
       -size "${CW}x$((CH - COUT))" xc:white -append -blur 0x18 "plates/_c-m1.png"
magick "plates/_c-base.png" "plates/_c-m1.png" \
    -alpha off -compose copy_opacity -composite "plates/_c-front.png"
magick "plates/_c-stood.png" "plates/_c-front.png" -compose over -composite \
    "plates/_c-inclouds.png"

# The mist that dissolves the seam. Without it the cloud bank ends on a ruled
# line across the page, which is how the backdrop itself is drawn and is the
# one thing about it that looks like stationery.
MA=$((CH * 44 / 100)); MB=$((CH * 608 / 1000))     # mist fades in over MA..MB,
MC=$((CH * 656 / 1000)); MD=$((CH * 793 / 1000))   # holds to MC, gone by MD
magick -size "${CW}x${MA}" xc:black \
       -size "${CW}x$((MB - MA))" gradient:black-white \
       -size "${CW}x$((MC - MB))" xc:white \
       -size "${CW}x$((MD - MC))" gradient:white-black \
       -size "${CW}x$((CH - MD))" xc:black -append -blur 0x24 "plates/_c-m2.png"
magick -size "${CW}x${CH}" xc:'#F3EFE8' "plates/_c-m2.png" \
    -alpha off -compose copy_opacity -composite "plates/_c-mist.png"
magick "plates/_c-inclouds.png" "plates/_c-mist.png" -compose over -composite \
    -strip "plates/cover-sky.png"

rm -f plates/_c-*.png

# --- family album ----------------------------------------------------------
# The modern colour photographs are a separate problem from the four old
# prints: they need no toning, only orientation, downsizing and a layout.
# build-album.py does all three and writes plates/family-album.tex.
python3 "$HERE/build-album.py"

# --- tributes --------------------------------------------------------------
# Prose rather than pictures, but derived artwork all the same: the family
# send assets/data/tributes.toml and build-tributes.py sets it. Run from here
# so that one command still brings everything the booklet inputs up to date;
# it is quick to run on its own while a tribute is being edited.
python3 "$HERE/build-tributes.py"
