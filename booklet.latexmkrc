# Imposition pass. latexmk reads ./.latexmkrc first and any -r file on top of
# it, so $out_dir, $pdf_mode, set_tex_cmds and the tributes custom dependency
# all carry over from there and only the two things that actually differ are
# set here.
#
#     latexmk && latexmk -r booklet.latexmkrc
#
# The first command builds the booklet, the second imposes it. They are two
# commands rather than one because booklet.tex reads a PDF that latexmk has no
# rule to make -- it appears in the .fls as a plain input file, so latexmk will
# notice when it changes and re-impose, but it will not build it for you.

@default_files = ('booklet.tex');

# Without this the booklet.tex run would inherit $jobname from .latexmkrc and
# write build/franco_nero_funeral.pdf -- the file it is reading. booklet.tex
# refuses to run under that name, so the mistake is caught either way, but it
# is set correctly here so the mistake does not arise.
$jobname = 'franco_nero_funeral_booklet';
