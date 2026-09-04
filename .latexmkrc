# Build main.tex when latexmk is run with no arguments
@default_files = ('main.tex');

# Everything (PDF, .aux, .log, .fls, .synctex.gz) lands in ./build
# Keeping aux_dir equal to out_dir means plain -output-directory covers both,
# so $emulate_aux is not needed (and with it on, latexmk copies the .pdf and
# .synctex.gz back into the project root).
$out_dir = 'build';
$aux_dir = 'build';

# The root file stays main.tex -- every section carries a "%! TeX root"
# comment pointing at it -- but what comes out is the booklet itself, and it
# is handed to a printer under that name rather than as somebody's main.pdf.
# Every auxiliary file takes the jobname too, which is why .gitignore matches
# on extension rather than on 'main.*'.
$jobname = 'franco_nero_funeral';

$pdf_mode = 1;      # pdflatex (4 = lualatex, 5 = xelatex)

# -synctex=1 so forward/reverse search works from the editor;
# -file-line-error so LaTeX Workshop can parse errors into the Problems panel
set_tex_cmds('-synctex=1 -interaction=nonstopmode -file-line-error %O %S');

# assets/data/tributes.tex is not written by hand: assets/build-tributes.py
# generates it from assets/data/tributes.toml, which is the file the family
# actually edits. Declaring that as a custom dependency is what keeps the two
# in step -- latexmk already knows tributes.tex is an input of the booklet,
# and now it knows where that file comes from, so it reruns the script
# whenever the TOML is the newer of the two and rebuilds on the result.
#
# This is why `latexmk` on its own is still the whole build. It also means an
# editor that runs latexmk on save needs to know nothing about the script:
# sections/08-tribute.tex opens the TOML so it is listed in the .fls, the
# editor watches it, and saving it starts a build that begins here.
#
# python3 rather than a specific version: the script re-execs itself into a
# newer interpreter if the one it lands in has no tomllib.
add_cus_dep('toml', 'tex', 0, 'build_tributes');
sub build_tributes {
    return system('python3', 'assets/build-tributes.py');
}

# Also remove these on `latexmk -c`
$clean_ext = 'synctex.gz fdb_latexmk fls run.xml bbl';

# booklet.tex is a second root -- the imposition that lays two A5 pages on an
# A4 sheet -- and it reads build/franco_nero_funeral.pdf. Naming it here would
# hand it the $jobname above, so pdflatex would write its output over the file
# it is reading. booklet.tex refuses to ship a page under that name, but by
# then pdflatex has already opened and truncated the booklet's .log, which
# leaves latexmk remembering a failure it then will not build past. Cheaper to
# stop before any of that happens. (booklet.latexmkrc names the file itself,
# and does not match: it ends in .latexmkrc.)
if (grep { m{(^|/)booklet(\.tex)?$} } @ARGV) {
    die "latexmk: build the imposition as `latexmk -r booklet.latexmkrc',\n"
      . "         which sets the jobname it has to be written out under.\n";
}
