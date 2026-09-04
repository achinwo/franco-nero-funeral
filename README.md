# Franco Nero International — order of service

An A5 booklet, 49 pages, set in LaTeX and built with `latexmk`.

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
| Python 3.11+ | `assets/build-tributes.py` needs `tomllib` | 3.13.1 |

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
machine's default `python3` is a pyenv 3.9. `build-tributes.py` handles that
itself — it looks for `python3.13`, `python3.12` or `python3.11` on the `PATH`
and re-execs into the first one it finds, and only fails if there is none.
`build-album.py` needs only 3.7 (for `subprocess.run(capture_output=...)`).

## Regenerating the derived files

```sh
sh assets/make-plates.sh    # about 35 seconds
```

One command rebuilds everything the booklet inputs but nobody edits:

- `assets/images/plates/plate-*.png` — the four old scans, cropped and toned
  to one sepia
- `assets/images/plates/ghost-*.png` — the page-sized washes behind each
  section opening
- `assets/images/plates/front-studio.png` — the frontispiece
- `assets/images/plates/cover-sky.png` — the cover montage
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
| `assets/images/family_pics/` | drop a photograph in; the album re-flows |
| `assets/images/sky_backdrop.png` | the cover backdrop |
| `assets/images/franco_sitting_green-print.png` | the cover cut-out |
| `assets/images/WhatsApp Image 2026-08-19*.jpeg` | the four original scans |

Never edit `assets/images/plates/family-album.tex` or `assets/data/tributes.tex`
by hand. Both say so at the top, and both are overwritten on the next run.

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
folded stack needs, so 49 A5 pages come out as 26 sides — thirteen A4 sheets,
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

The booklet is 49 pages and a fold needs a multiple of four, so three blank
pages are added. `booklet.tex` counts the pages itself, out of the PDF, and
puts those blanks *before* the last page rather than after it — otherwise the
outside of the final sheet comes out blank with the back cover buried a leaf
inside it. Nothing needs editing here when a tribute is added and the page
count changes.

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
