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

# `sh assets/make-plates.sh` rebuilds everything. `... covers` rebuilds only
# the three full-page plates -- the cover and the two frontispieces -- which
# is the pass that matters while a cover is being iterated on: it is the one
# part of this script driven by assets/data/plates.toml, and skipping the
# scans, the ghosts and the four Python generators takes it from half a
# minute to about a second. .latexmkrc runs it in that mode on its own when
# plates.toml is newer than the plates, so `latexmk` alone is enough to see a
# new cover.
MODE=${1:-all}
case "$MODE" in
  all|covers) ;;
  *) echo "make-plates: unknown mode '$MODE' (expected 'covers' or nothing)" >&2
     exit 2 ;;
esac

# Resolved before the cd, so the later call to build-album.py still works.
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/images"
mkdir -p plates
# Which photograph each full-page plate is built from is set in
# assets/data/plates.toml, not here. plateconfig.py reads one value out of it;
# an unset value prints nothing, so every caller below falls back to what this
# script did before the config existed, and a value naming a missing file
# stops the run rather than quietly building a cover from the wrong picture.
plate() { python3 "$HERE/plateconfig.py" "$1" "$2"; }

if [ "$MODE" = all ]; then
# The four old prints are one scanned sheet each, and they live with the
# rest of his own photographs in personal/ rather than loose in images/.
SRC="personal/WhatsApp Image 2026-08-19 at 14.24.16"

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
fi   # end of the `all'-only work above: the scans, the plates and the ghosts

# --- frontispieces ---------------------------------------------------------
# Full-bleed A5 plates for the pages that open a section on a photograph: one
# portrait cover-cropped to the page, with a white field burnt into the foot
# for the type to sit on and a gradient dissolving that field back into the
# photograph, so there is no visible edge. The same device as the cover, so
# those pages rhyme with it.
#
# The white field is carried in as an image with the ramp copied into its
# alpha channel. The three-image `-composite` mask form does not apply here:
# with -compose over it silently ignores the mask.
FW=1748; FH=2480
front() { # front <source-image> <name> <field-top-pct>
  # Solid white from <field-top> down, so the type at the foot sits on a
  # clean field rather than on his trousers -- a linear ramp all the way to
  # the trim left the caption line at 70% grey and unreadable. The three
  # bands are: photograph untouched, the dissolve, then the field.
  _top=$3
  magick -size "${FW}x$((FH * (_top - 22) / 100))" xc:black \
         -size "${FW}x$((FH * 22 / 100))" gradient:black-white \
         -size "${FW}x$((FH * (100 - _top) / 100))" xc:white \
         -append -resize "${FW}x${FH}!" -blur 0x8 "plates/_scrim.png"
  magick "$1" \
      -resize "${FW}x${FH}^" -gravity north -extent "${FW}x${FH}" \
      \( -size "${FW}x${FH}" xc:white "plates/_scrim.png" \
         -alpha off -compose copy_opacity -composite \) \
      -compose over -composite -strip "plates/front-$2.png"
  rm -f plates/_scrim.png
}
# Which picture each one uses, and where its white field starts, are settled
# in assets/data/plates.toml. The defaults below are what this script used
# before that file existed: the Photographs section opens on the studio
# portrait, and A Life Remembered on the agbada one -- a different photograph
# deliberately, because two sections opening on the same picture reads as a
# shortage of pictures rather than as a motif.
# Assigned first rather than substituted inline: an unset value is empty and
# takes the default after it, but a *bad* value -- a source naming a file that
# is not there -- exits non-zero, and only in an assignment does `set -e` see
# that and stop. Inline, the failure would be swallowed and the frontispiece
# built from nothing.
front_studio_src=$(plate front-studio source)
front_studio_field=$(plate front-studio field)
front_life_src=$(plate front-life source)
front_life_field=$(plate front-life field)

front "${front_studio_src:-plates/plate-studio.png}" \
      studio "${front_studio_field:-74}"
front "${front_life_src:-plates/plate-agbada.png}" \
      life "${front_life_field:-79}"

# --- the closing plate -----------------------------------------------------
# A full-bleed photograph with a whole page of text set over it, which is a
# different problem from the frontispieces: they clear a field at the foot for
# two display lines, and this one has to carry fourteen lines of an italic
# farewell anywhere on the page.
#
# So the picture is veiled rather than cropped away. White is laid over it
# through a ramp -- a quarter strength at the top of the sheet, full strength
# from `clear' down -- so the head and the light above stay a photograph and
# everything below goes pale enough for the booklet's own ink to read on. The
# veil is baked in here for the same reason the ghosts are: what the printer's
# RIP receives is opaque artwork, with no transparency to flatten.
#
# Built the same way front() builds its scrim -- the ramp copied into the
# alpha channel of a white sheet, then composited over -- because the
# three-image `-composite' mask form silently ignores the mask under
# -compose over.
close_life_src=$(plate close-life source)
close_life_veil=$(plate close-life veil)
close_life_clear=$(plate close-life clear)

close() { # close <source-image> <name> <veil-pct> <clear-pct>
  _src=$1; _name=$2; _veil=$3; _clear=$4
  # The ramp: a quarter of the veil at the top of the sheet, growing to the
  # full figure by <clear> down, and holding it to the foot.
  magick -size "${FW}x$((FH * _clear / 100))" \
         "gradient:gray$((_veil / 4))-gray${_veil}" \
         -size "${FW}x$((FH * (100 - _clear) / 100))" "xc:gray${_veil}" \
         -append -resize "${FW}x${FH}!" -blur 0x12 "plates/_veil-mask.png"
  magick -size "${FW}x${FH}" xc:white "plates/_veil-mask.png" \
      -alpha off -compose copy_opacity -composite "plates/_veil.png"
  magick "$_src" -resize "${FW}x${FH}^" -gravity north \
      -extent "${FW}x${FH}" "plates/_veil.png" \
      -compose over -composite -strip "plates/$_name.png"
  rm -f plates/_veil-mask.png plates/_veil.png
}

if [ -n "$close_life_src" ]; then
  close "$close_life_src" close-life \
        "${close_life_veil:-70}" "${close_life_clear:-32}"
fi

# --- the back cover --------------------------------------------------------
# The portrait behind the words of thanks, and a third kind of full-page plate:
# not a ghost, which clears the top of the sheet for a heading and so fades his
# head away on a page that is text from the first line, and not a frontispiece,
# which burns a white field into the foot -- which is where this one wants him.
#
# So he is placed rather than cover-cropped. The figure is scaled about his
# head to the size assets/data/plates.toml asks for, stood at the foot of the
# sheet with his face where that file puts it, and faded up into clean paper
# above him and in from both sides, so the type on the page never has to reach
# him and no edge of the photograph is ever seen.
#
# Everywhere outside the figure the canvas is edge-replicated rather than
# filled: the mask is nil out there, so what it holds does not matter, but a
# replicated edge cannot leave a seam anywhere the mask is only nearly nil.
back_src=$(plate back-portrait source)

back() { # back <source-image> <name>
  _src=$1; _name=$2
  # A5 at 300dpi, as the cover and the frontispieces rather than as the
  # ghosts: those are washes nobody looks at directly and 200 is plenty for
  # them, while this one is a face, and the eye that is on it will find the
  # steps in a fade laid down at 200.
  BW=1748; BH=2480
  # Every measurement the placement needs, worked out in one pass because they
  # are fractions of each other and shell arithmetic is integers.
  eval "$(awk -v w="$BW" -v h="$BH" \
              -v head="$(plate back-portrait head)" \
              -v hsize="$(plate back-portrait headsize)" \
              -v fx="$(plate back-portrait facex)" \
              -v ftop="$(plate back-portrait facetop)" \
              -v ffoot="$(plate back-portrait facefoot)" 'BEGIN {
    # Scale: his head is (ffoot-ftop)% of the source and wants to be hsize% of
    # the page, so the source is drawn this many pixels wide.
    pw = h * hsize / (ffoot - ftop)
    ox = w / 2 - pw * fx / 100          # his face on the centre line
    top = h * head / 100 - pw * ftop / 100
    # The fade closes a third of a head-height above him, so the last line of
    # type on the page still has clear paper under its descenders, and opens a
    # head-height above that.
    hold = h * head / 100 - h * hsize / 300
    fade = hold - h * hsize / 100
    printf "PW=%d OX=%d TOP=%d FEA=%d FADE=%d HOLD=%d\n",
           pw, ox, top, pw * 0.26, fade, hold
  }')"
  # The wash. Sigmoidal contrast before the tone map, because squeezing the
  # range into a narrow warm band flattens a face: the print is a 1960s studio
  # portrait and the modelling around his eyes is most of what is left of it.
  magick "$_src" -resize "${PW}x" \
      -colorspace Gray -auto-level -sigmoidal-contrast 2x50% \
      +level-colors "$(plate back-portrait ink)",'#FCFAF6' "plates/_b-fig.png"
  # The photograph is stood on a field of its own backdrop -- the mean of its
  # top edge -- rather than on white or on a replication of that edge. Flat is
  # the whole point: there is barely a head's clearance above him in the print,
  # so the fade has to open over ground that is not the photograph, and any
  # ground with detail in it (a replicated edge smears the top row down the
  # page) arrives as streaks exactly where the eye is looking for his face.
  _ground=$(magick "plates/_b-fig.png" -crop "${PW}x8+0+0" +repage \
      -resize '1x1!' -format '%[pixel:p{0,0}]' info:)
  magick -size "${BW}x${BH}" xc:"$_ground" \
      "plates/_b-fig.png" -geometry "+${OX}+${TOP}" \
      -compose over -composite "plates/_b-page.png"
  # Two masks multiplied: up the page, and in from the sides. The side feather
  # is measured off the figure rather than off the sheet -- it has to reach nil
  # by the edges of the photograph, which is what keeps the replicated ground
  # out of sight.
  magick -size "${BW}x${FADE}" xc:black \
         -size "${BW}x$((HOLD - FADE))" gradient:black-white \
         -size "${BW}x$((BH - HOLD))" xc:white -append "plates/_b-v.png"
  magick -size "${BH}x${OX}" xc:black \
         -size "${BH}x${FEA}" gradient:black-white \
         -size "${BH}x$((PW - 2 * FEA))" xc:white \
         -size "${BH}x${FEA}" gradient:white-black \
         -size "${BH}x$((BW - OX - PW))" xc:black \
         -append -rotate -90 "plates/_b-h.png"
  magick "plates/_b-v.png" "plates/_b-h.png" -compose multiply -composite \
      -blur 0x27 "plates/_b-m.png"
  magick "plates/_b-page.png" "plates/_b-m.png" \
      -alpha off -compose copy_opacity -composite \
      -background white -alpha remove -alpha off \
      -strip "plates/$_name.png"
  rm -f plates/_b-*.png
}

if [ -n "$back_src" ]; then
  back "$back_src" back-portrait
fi

# --- the cover -------------------------------------------------------------
# Either the cover is a file somebody finished elsewhere, or it is the montage
# this script builds. assets/data/plates.toml decides which, and an empty
# `source` means the montage -- so the default is what the cover has always
# been, and pointing at a file is a switch rather than a demolition.
cover_src=$(plate cover source)

if [ -n "$cover_src" ]; then
  # Used exactly as given: no crop, no tone, no scrim. The page draws it at
  # the full width and height of the sheet, so its own proportions are what
  # print -- which is the whole reason for this branch, and also the one way
  # to get a stretched cover, so the shape is checked and reported below.
  #
  # Copied under the source's own extension, and every other cover-sky.*
  # removed first: \includegraphics is given the name without one, so a
  # leftover .png beside a new .jpg would leave TeX to pick between them.
  rm -f plates/cover-sky.*
  cp "$cover_src" "plates/cover-sky.${cover_src##*.}"

  # A5 is 1748x2480 at 300dpi. A cover that is not that shape is stretched to
  # the page rather than cropped, and a stretch of a few per cent is the kind
  # of thing that looks merely a little wrong on screen and unmistakable in
  # print, so it is said out loud rather than left to be noticed.
  cover_wh=$(magick identify -format '%w %h' "$cover_src")
  echo "make-plates: cover taken as-is from $cover_src (${cover_wh% *}x${cover_wh#* })"
  awk -v wh="$cover_wh" 'BEGIN {
    split(wh, d, " ")
    got = d[1] / d[2]
    want = 148 / 210
    if (got < want * 0.99 || got > want * 1.01) {
      printf "make-plates: WARNING -- cover is %.3f wide-to-tall, A5 is %.3f.\n", got, want
      print "make-plates:   the page will stretch it to fit; 1748x2480 fits exactly."
    }
  }' </dev/null
else
  # Whatever a previous run left under another extension: the montage writes
  # cover-sky.png, and a cover-sky.jpg from a custom cover would still be
  # sitting beside it for \includegraphics to choose between.
  rm -f plates/cover-sky.*

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

  magick personal/franco_sitting_green-print.png -trim +repage \
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
fi

if [ "$MODE" = covers ]; then
  exit 0   # the full-page plates are done, and they are all `covers' rebuilds
fi

# --- captions --------------------------------------------------------------
# The words under the photographs. assets/data/captions.toml files a caption
# against the image it belongs to; build-captions.py turns that into the
# definitions main.tex looks up for the prints a person placed by hand, and
# the two layout scripts below read the same file directly, because a
# caption changes how much room its page has to leave for the picture.
# Run first, so that a caption added and a page re-flowed happen together.
python3 "$HERE/build-captions.py"

# --- his own photographs ---------------------------------------------------
# personal/ holds the photographs of him, and the artwork cut from them.
# build-personal.py mounts the photographs two to a row and leaves the
# artwork alone, writing plates/personal-photos.tex.
python3 "$HERE/build-personal.py"

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
