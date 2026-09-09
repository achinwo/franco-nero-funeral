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
# %P rather than %S for the source file: with $pre_tex_code empty the two are
# identical, and when it is set -- which is how the draft watermark is turned
# on, below -- %P is the only substitution latexmk expands it into. With %S
# here the code is silently dropped and the draft flag does nothing at all.
set_tex_cmds('-synctex=1 -interaction=nonstopmode -file-line-error %O %P');

# --- Draft copies ----------------------------------------------------------
# A review copy for the printer, watermarked DRAFT diagonally across every
# page. The switch is here rather than in main.tex so that it cannot be
# committed: a `\draftmode' left set in the source is how a watermark reaches
# the press.
#
#   DRAFT=1 latexmk           one draft build
#   touch DRAFT && latexmk    every build until the file is removed
#
# The file is the one that matters in practice. An editor that builds on save
# -- LaTeX Workshop here -- runs latexmk with its own environment and will not
# see a variable exported in a shell, so `touch DRAFT' is what makes the
# editor produce drafts too. It is in .gitignore.
#
# DRAFT=0 (or no/off/false) is off, so the variable can be left set in a
# profile and turned down without unsetting it.
my $draft = ($ENV{DRAFT} && $ENV{DRAFT} !~ /^(0|no|off|false)$/i) ? 1
          : (-e 'DRAFT')                                         ? 1 : 0;
if ($draft) {
    warn "latexmk: DRAFT build -- every page is watermarked\n";
    $pre_tex_code = '\def\draftmode{}';
}

# Turning the flag on or off changes no file the booklet inputs, so latexmk
# would find everything up to date and hand back the copy it built last time
# -- an unwatermarked PDF from a draft build, or worse, a watermarked one
# after the flag came off. Recording the state next to the output and forcing
# a rebuild when it differs is what keeps the switch honest.
{
    my $stamp = "$out_dir/.draftmode";
    mkdir $out_dir unless -d $out_dir;
    my $was = (-e $stamp) ? 1 : 0;
    if ($was != $draft) {
        $go_mode = 1;   # same as -g: rebuild rather than trust the timestamps
        if ($draft) { open(my $fh, '>', $stamp) && close($fh); }
        else        { unlink $stamp; }
    }
}

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
# The rule is keyed on the extension, not on the file, so it catches every
# .toml the booklet inputs a .tex beside -- assets/data/captions.toml as well
# as the tributes. latexmk hands the sub the base name it is building, which
# is what picks the script; a .toml this does not recognise is left alone
# rather than run through the wrong generator.
add_cus_dep('toml', 'tex', 0, 'build_from_toml');
sub build_from_toml {
    my ($base) = @_;
    return system('python3', 'assets/build-tributes.py') if $base =~ m{tributes$};
    return system('python3', 'assets/build-captions.py') if $base =~ m{captions$};
    warn "latexmk: no generator knows how to build $base.tex from $base.toml\n";
    return 0;
}

# The full-page plates -- the cover, the two frontispieces, the veiled photo-
# graph that closes the biography and the portrait on the back cover -- are
# built from whatever assets/data/plates.toml names, and that file produces
# images rather than a .tex, so the custom dependency above cannot express it:
# add_cus_dep matches on extension, and there is no plates.tex to hang it on.
# Without something here, changing the cover in the config and running latexmk
# rebuilds nothing at all, because as far as latexmk is concerned the plate on
# disk is unchanged -- which is exactly the trap this block exists to close.
#
# So: if the config is newer than the plates it builds, run the covers-only
# pass before the build. That pass skips the scans, the ghosts and the four
# Python generators, so it costs a few seconds rather than half a minute.
#
# Only when it is stale, which keeps the promise that a fresh clone builds the
# booklet with no ImageMagick and no Python: every plate is committed, so on a
# clone the config is older than what it made and nothing here runs.
#
# What this does NOT catch is a source image replaced in place under the same
# name -- the config has not changed, so nothing looks stale. `touch
# assets/data/plates.toml` says so, or run `sh assets/make-plates.sh covers`.
if (-e 'assets/data/plates.toml') {
    my $conf = (stat 'assets/data/plates.toml')[9];
    my $newest = 0;
    foreach my $plate (glob 'assets/images/plates/cover-sky.* '
                          . 'assets/images/plates/front-* '
                          . 'assets/images/plates/close-life.png '
                          . 'assets/images/plates/back-portrait.png') {
        my $mtime = (stat $plate)[9];
        $newest = $mtime if defined $mtime && $mtime > $newest;
    }
    if ($conf > $newest) {
        warn "latexmk: assets/data/plates.toml is newer than the plates it "
           . "builds; running `make-plates.sh covers'\n";
        system('sh', 'assets/make-plates.sh', 'covers') == 0
            or die "latexmk: the covers pass failed; fix plates.toml and "
                 . "run again\n";
    }
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
