# Franco Nero International — order of service

An A5 booklet, 31 pages, set in LaTeX and built with `latexmk`.

```sh
latexmk                 # -> build/main.pdf, about two seconds
```

`.latexmkrc` names `main.tex` as the only root and sends the PDF and every
auxiliary file to `build/`, so `latexmk` on its own is the whole build. There
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

## Editing in VS Code

`.vscode/settings.json` configures LaTeX Workshop to build with the same
`latexmk` recipe into `build/`, and sets `forceRecipeUsage` so that a
`%! TeX program` magic comment in a source file cannot quietly replace the
recipe with a bare `pdflatex` that writes its output into the project root.

## Also

`REVIEW.md` lists the content problems still outstanding — contradictory
dates, and pages carried over from another family's booklet. They need a
human decision, not a build.
