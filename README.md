# Franco Nero International — order of service

An A5 booklet, 56 pages, set in LaTeX and built with `latexmk`.

```sh
latexmk                                   # -> build/franco_nero_funeral.pdf
latexmk && latexmk -r booklet.latexmkrc   # -> ..._booklet.pdf, A5 2-up on A4
```

`.latexmkrc` names `main.tex` as the only root, sends the PDF and every
auxiliary file to `build/`, and sets `$jobname` so what comes out is named for
the booklet rather than for the root file, so `latexmk` on its own is the whole
build. There
is nothing to install for this step beyond TeX Live: every generated image and
every generated `.tex` is committed, so the booklet builds on a machine with no
ImageMagick and no Python.

## Dependencies

| What | Why | Known good |
|---|---|---|
| TeX Live (full) | `pdflatex`, `latexmk` | TeX Live 2026, pdfTeX 1.40.29, latexmk 4.88 |
| ImageMagick 7 | regenerating the plates in `assets/images/plates/`, and preparing any photograph a tribute carries | 7.1.1-28 |
| Python 3.11+ | the generators in `assets/` read TOML, and need `tomllib` | 3.13.1 |

A full TeX Live install carries every package the booklet loads —
`geometry`, `graphicx`, `xcolor`, `eso-pic`, `tikz`, `soul`, `letterspace`,
`multicol`, `lettrine`, `tcolorbox`, `enumitem`, `hyperref`, `lmodern` — and both cover
faces, `ebgaramond` and `cormorantgaramond`. On a smaller scheme
(`scheme-basic`, `scheme-small`) install those two font packages explicitly:

```sh
tlmgr install ebgaramond cormorantgaramond
```

The cover selects them with `\fontfamily` rather than by loading their `.sty`
files, which works only if their font maps are enabled. `tlmgr` does that when
it installs them; a font copied into the tree by hand will not print.

Python 3.11 is a floor, not a preference: `tomllib` arrived in 3.11, and this
machine's default `python3` is a pyenv 3.9. The scripts handle that
themselves — `assets/textkit.py` looks for `python3.13`, `python3.12` or
`python3.11` on the `PATH` and re-execs the running script into the first one
it finds, and only fails if there is none. Every generator goes through it,
because every one of them reads a `.toml`: the tributes, and the captions
that `build-album.py` and `build-personal.py` lay their pages out around.

## Regenerating the derived files

```sh
sh assets/make-plates.sh    # about 35 seconds
```

One command rebuilds everything the booklet inputs but nobody edits:

- `assets/data/captions.tex` — the captions, for the prints placed by hand
- `assets/images/plates/plate-*.png` — the four old scans, cropped and toned
  to one sepia
- `assets/images/plates/ghost-*.png` — the page-sized washes behind each
  section opening
- `assets/images/plates/front-studio.png` and `front-life.png` — the two
  frontispieces (sources set in `assets/data/plates.toml`)
- `assets/images/plates/cover-sky.*` — the cover: the montage, or whatever
  image `assets/data/plates.toml` names, copied in unchanged
- `assets/images/plates/personal/*.jpg` and `plates/personal-photos.tex` — his
  own photographs, laid out by `assets/build-personal.py`
- `assets/images/plates/family/*.jpg` and `plates/family-album.tex` — the
  family album, laid out by `assets/build-album.py`
- `assets/data/tributes.tex` and `assets/images/plates/tributes/*.jpg` — the
  tributes and their photographs, set by `assets/build-tributes.py`

Run it after changing anything under `assets/images/` or `assets/data/`, then
`latexmk`. `build-tributes.py` is quick enough to run on its own while a
tribute is being edited.

## Sources and generated files

Edit these:

| File | What it feeds |
|---|---|
| `main.tex` | preamble, every shared macro, the section order |
| `booklet.tex` | the imposition — signature size, and the print options |
| `sections/*.tex` | the pages themselves |
| `assets/data/tributes.toml` | the tributes — plain text, no LaTeX; `imagePath` points at a photograph to set the letter around |
| `assets/data/captions.toml` | the caption under each photograph, filed against the image file it belongs to |
| `assets/data/plates.toml` | which image each full-page plate is built from — the cover and the two frontispieces |
| `assets/images/personal/` | photographs of him; drop one in and the first Photographs pages re-flow |
| `assets/images/family_pics/` | drop a photograph in; the album re-flows |
| `assets/images/sky_backdrop.png` | the cover backdrop |
| `assets/images/personal/franco_sitting_green-print.png` | the cover cut-out |
| `assets/images/personal/WhatsApp Image 2026-08-19*.jpeg` | the four original scans |

Never edit `assets/images/plates/family-album.tex`,
`assets/images/plates/personal-photos.tex`, `assets/data/tributes.tex` or
`assets/data/captions.tex` by hand. All four say so at the top, and all four
are overwritten on the next run.

## Captions

`assets/data/captions.toml` is the one place a photograph is given its words:

```toml
[caption]
"plates/plate-desk.png" = "At the desk — the shop books, and the telephone"
"personal/album-27.jpg" = "Outside the shop"
```

The key is the image file, relative to `assets/images/` — the same root
`\graphicspath` gives the document. A caption follows its photograph wherever
the booklet prints it, so there is nothing to keep in step by hand and no
caption text anywhere in `sections/`. The value is plain text: type the
apostrophes, quotation marks and dashes you want to see, and `<i>`/`<b>` if a
word wants emphasis.

Most photographs have no caption, which is the normal case — the album is
faces the family already knows. A photograph with no line simply prints
without one.

Two paths appear as keys. Usually it is the original, `personal/album-27.jpg`
or `family_pics/album-04.jpg`. The four old prints are the exception: all
four are cut from a single scanned sheet, so the sheet cannot name one
photograph and the caption hangs on the crop that is printed —
`plates/plate-desk.png`.

Adding a caption changes how much room its page has to leave for the picture,
so run `sh assets/make-plates.sh` after editing this file. (Editing it and
running `latexmk` alone updates the four mounted prints, whose captions are
looked up rather than laid out around, but leaves the generated pages as they
were.)

## The full-page plates

Three plates take a whole A5 sheet, edge to edge: the cover and the two
frontispieces that open a section on a picture. Which image goes into each is
set in `assets/data/plates.toml`, so swapping one is a path and a re-run
rather than an edit to `make-plates.sh`:

```toml
[cover]
source = "personal/cover-from-canva.png"   # empty = build the montage

[front-studio]
source = "plates/plate-studio.png"
field  = 74
```

Paths are relative to `assets/images/`, the same root as `captions.toml`.

**`latexmk` on its own is enough.** `.latexmkrc` notices when `plates.toml` is
newer than the plates it builds and runs a covers-only pass first:

```sh
sh assets/make-plates.sh covers    # ~4s: the three full-page plates, nothing else
sh assets/make-plates.sh           # ~35s: everything
```

The covers pass skips the scans, the ghosts and the four Python generators,
which is what makes it quick enough to sit in front of a build. It only fires
when the config is stale, so a fresh clone still builds with no ImageMagick and
no Python — every plate is committed.

The one case it cannot see is a source image **replaced in place under the same
name**: the config has not changed, so nothing looks stale. `touch
assets/data/plates.toml`, or run the covers pass by hand.

**The cover is used exactly as given.** No crop, no tone, no scrim, no
montage — the file is copied to `plates/cover-sky` unchanged, which is what
makes it usable for artwork finished in another program. Two consequences:

- The page draws it at the full width *and* height of the sheet, so an image
  that is not A5 in proportion is **stretched, not cropped**. Make it
  1748×2480 (A5 at 300dpi) and nothing moves. The script prints the size it
  found and warns if the shape is off by more than 1%.
- It bleeds to the trim on all four sides. Keep anything that must survive
  the guillotine a few millimetres inside the edge.

Leave `source` empty and the cover is built the way it always was, from
`sky_backdrop.png` and the cut-out. The montage code is untouched, so this is
a switch rather than a demolition.

The two frontispieces *are* processed: a portrait is cover-cropped to the page
with a white field burnt into the foot for the type. `field` is where that
field begins, as a percentage down the page — a property of the crop rather
than a house style, so a tightly cropped portrait wants a larger number than a
loose one. Move it if a new picture comes out half dissolved, or with the type
sitting on a shirt.

A `source` naming a file that is not there stops the run. That is deliberate:
the alternative is a cover built silently from the wrong picture.

To render the cover's type alone — for compositing over artwork edited
elsewhere — see the recipe in `build/cover-text.tex`, which carries `main.tex`'s
preamble, inputs `sections/01-cover.tex` unaltered and redefines `\pageghost`
to nothing.

## The Photographs section

Three runs of pictures, in this order:

1. the frontispiece — the studio portrait under a white scrim
2. **his own photographs** — the three old prints `07-photobook.tex` places by
   hand, running straight on into as many pages as `assets/images/personal/`
   needs, all mounted with photo corners and laid out by `build-personal.py`
3. **the family album** — `assets/images/family_pics/`, three across in plain
   hairline frames, laid out by `build-album.py`

Only the album carries a head, and what it marks is the turn from his
pictures to everybody's.

`personal/` holds the artwork cut from those photographs as well as the
photographs themselves — the four scanned sheets and the cover cut-out. Those
are already in the booklet as the plates, the frontispieces, the page ghosts
and the cover, so `build-personal.py` skips them by name, with the reason
given in its `SKIP` table.

One thing to know before replacing the cover backdrop: `make-plates.sh` reads
landmarks out of that file by pixel — its width, and the row where the
cloudscape meets the paper field — and those numbers are written into the
script (`SKYW`, `SKYSEAM`). A new backdrop with the seam in a different place
needs them re-measured, or the mist will dissolve the wrong band of the page.

## Printing it: A5 on A4

```sh
latexmk && latexmk -r booklet.latexmkrc   # -> build/franco_nero_funeral_booklet.pdf
```

The second command imposes the booklet: `booklet.tex` reads the finished A5
PDF back in and lays two pages side by side on each A4 sheet, in the order a
folded stack needs, so 56 A5 pages come out as 28 sides — fourteen A4 sheets,
printed double-sided, folded down the middle and stapled through the fold.

The pages stay A5. Two of them across are 296mm and A4 turned landscape is
297mm, so nothing is scaled and the type is the size it was set;
`noautoscale` in `booklet.tex` is what holds that, because pdfpages would
otherwise grow each page by the last 0.3% to fill its half of the sheet.

Two things to get right at the printer:

- **Duplex on the short edge.** These are landscape sheets folded down their
  vertical centre. On long edge every second sheet comes out upside down. If
  a particular printer flips the other way, uncomment `flip-other-edge` in
  `booklet.tex`.
- **The covers bleed.** A desktop printer cannot reach the edge of an A4
  sheet and will crop a few millimetres off them. A print shop working from a
  larger sheet and trimming does not. Adding `scale=0.94` to the options in
  `booklet.tex` pulls everything inside a desktop printer's margins, at the
  cost of the pages no longer being A5.

A fold needs a multiple of four pages, so `booklet.tex` counts the pages
itself, out of the PDF, and pads to the next multiple. It puts any blanks
*before* the last page rather than after it — otherwise the outside of the
final sheet comes out blank with the back cover buried a leaf inside it. The
booklet is 56 pages at the moment, which is already a multiple of four, so
none are being added; nothing needs editing here when a tribute or a
photograph changes the count.

By default the whole booklet is one signature, which is the saddle stitch an
order of service is bound with. `\bkltsignature` at the top of `booklet.tex`
takes 16, 12 or 8 instead if the bindery wants separate gatherings to sew;
the blank-page arithmetic follows it.

`booklet.latexmkrc` exists because `.latexmkrc` sets `$jobname` for the whole
project, and the imposition pass must not be written out under the booklet's
own name — it reads that file. latexmk reads the directory's rc file first and
a `-r` file on top of it, so everything else (`build/`, pdflatex, the tributes
dependency) carries over and only the jobname and the root file differ. The
two commands stay two commands because `booklet.tex` consumes a PDF latexmk
has no rule to build: it will notice when that PDF changes and re-impose, but
it will not build it for you.

## Editing in VS Code

`.vscode/settings.json` configures LaTeX Workshop to build with the same
`latexmk` recipe into `build/`, and sets `forceRecipeUsage` so that a
`%! TeX program` magic comment in a source file cannot quietly replace the
recipe with a bare `pdflatex` that writes its output into the project root.

There is a second recipe, **booklet (A5 2-up on A4)**, which runs the two
commands above in order. `recipe.default` stays `first`, so the plain
`latexmk` recipe is what builds on save and the booklet recipe only runs when
it is chosen. The viewer stays pointed at `build/franco_nero_funeral.pdf` —
`latex-workshop.latex.jobname` is one setting for the whole project — so the
imposed PDF has to be opened by hand, which is the right way round: the A5
booklet is what you proofread and the A4 sheets are what you send off.

## Also

`REVIEW.md` lists the content problems still outstanding — contradictory
dates, and pages carried over from another family's booklet. They need a
human decision, not a build.
