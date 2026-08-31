# Build main.tex when latexmk is run with no arguments
@default_files = ('main.tex');

# Everything (PDF, .aux, .log, .fls, .synctex.gz) lands in ./build
# Keeping aux_dir equal to out_dir means plain -output-directory covers both,
# so $emulate_aux is not needed (and with it on, latexmk copies the .pdf and
# .synctex.gz back into the project root).
$out_dir = 'build';
$aux_dir = 'build';

$pdf_mode = 1;      # pdflatex (4 = lualatex, 5 = xelatex)

# -synctex=1 so forward/reverse search works from the editor;
# -file-line-error so LaTeX Workshop can parse errors into the Problems panel
set_tex_cmds('-synctex=1 -interaction=nonstopmode -file-line-error %O %S');

# Also remove these on `latexmk -c`
$clean_ext = 'synctex.gz fdb_latexmk fls run.xml bbl';
