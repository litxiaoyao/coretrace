#!/usr/bin/env bash
# Compile an isolated source snapshot with the original ICML template.
# Usage: bash analysis/compile_paper.sh [source-directory] [build-directory]
# Default deliverable: analysis/build_final/main.pdf
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"
source_dir="${1:-$project_dir/paper}"
build_dir="${2:-$script_dir/build_final}"
source_dir="$(cd -- "$source_dir" && pwd)"
mkdir -p -- "$build_dir"
build_dir="$(cd -- "$build_dir" && pwd)"
if [[ ! -f "$source_dir/main.tex" ]]; then
  printf 'Missing main.tex in %s\n' "$source_dir" >&2
  exit 1
fi

# Prefer the normal pdfLaTeX toolchain. Tectonic is a supported fallback and
# uses the same unmodified ICML sources, figures, and bibliography.
compiler=latexmk
if ! command -v latexmk >/dev/null 2>&1 || ! command -v pdflatex >/dev/null 2>&1; then
  compiler=tectonic
  tectonic_bin="${CORETRACE_TECTONIC:-tectonic}"
  if ! command -v "$tectonic_bin" >/dev/null 2>&1; then
    printf 'Need latexmk + pdfLaTeX, or Tectonic (set CORETRACE_TECTONIC).\n' >&2
    exit 1
  fi
fi

# A complete TeX installation uses its own normal format and font maps.
# The workspace image has read-only package sources but missing generated caches.
# Rebuild only those caches locally; never change the template or system tree.
if [[ "$compiler" == latexmk ]] && { [[ "${CORETRACE_LOCAL_TEX:-0}" == 1 ]] || \
   [[ ! -f "$(kpsewhich -format=fmt pdflatex.fmt 2>/dev/null || true)" ]] || \
   [[ ! -f "$(kpsewhich pdftex.map 2>/dev/null || true)" ]]; }; then
  tex_runtime="$script_dir/tex_runtime"
  texmf_dist="${CORETRACE_TEX_DIST:-$(kpsewhich --var-value=TEXMFDIST)}"
  if [[ ! -f "$texmf_dist/tex/latex/base/latex.ltx" ]]; then
    printf 'Cannot locate installed TeX package sources: %s\n' "$texmf_dist" >&2
    exit 1
  fi
  mkdir -p -- "$tex_runtime/web2c" "$tex_runtime/config/web2c" "$tex_runtime/home"
  # Omitting !! permits direct directory lookup when the system ls-R is absent.
  export TEXMF="{$tex_runtime,$texmf_dist}"
  export TEXMFVAR="$tex_runtime"
  export TEXMFCONFIG="$tex_runtime/config"
  export TEXMFHOME="$tex_runtime/home"
  export TEXFORMATS="$tex_runtime/web2c//:"
  export VARTEXFONTS="$tex_runtime/fonts"
  if [[ ! -s "$tex_runtime/web2c/pdflatex.fmt" ]]; then
    (
      cd -- "$tex_runtime/web2c"
      pdftex -ini -etex -interaction=nonstopmode -halt-on-error \
        -jobname=pdflatex pdflatex.ini > format_stdout.txt 2>&1
    )
  fi
  if [[ ! -s "$tex_runtime/fonts/map/pdftex/updmap/pdftex.map" ]]; then
    cat > "$tex_runtime/config/web2c/updmap.cfg" <<'MAPS'
dvipsPreferOutline true
LW35 URWkb
dvipsDownloadBase35 true
pdftexDownloadBase14 true
Map cm.map
Map cmextra.map
Map cyrillic.map
Map euler.map
Map latxfont.map
Map symbols.map
Map charter.map
Map utopia.map
Map pazo.map
Map rsfs.map
MAPS
    updmap --user --cnffile "$tex_runtime/config/web2c/updmap.cfg" \
      --nohash > "$tex_runtime/web2c/updmap_stdout.txt" 2>&1
  fi
fi

# Each run gets a fresh source snapshot. This avoids stale auxiliary files and
# latexmk/BibTeX path ambiguities; only generated directories receive writes.
stage_dir="$(python3 - "$source_dir" "$build_dir" <<'PY'
from pathlib import Path
import shutil, sys, tempfile
source=Path(sys.argv[1]).resolve()
build=Path(sys.argv[2]).resolve()
if source == build or build.is_relative_to(source):
    raise SystemExit('Build directory must be outside the source directory.')
stage=Path(tempfile.mkdtemp(prefix='source_',dir=build))
allowed={'.tex','.bib','.sty','.bst','.cls','.clo','.def','.cfg','.fd',
         '.pdf','.png','.jpg','.jpeg','.eps','.svg'}
for item in source.rglob('*'):
    if not item.is_file() or item.suffix.lower() not in allowed:
        continue
    rel=item.relative_to(source)
    if any(part.startswith('.') for part in rel.parts):
        continue
    if len(rel.parts)==1 and item.suffix.lower() in {'.pdf','.png','.jpg','.jpeg','.eps','.svg'}:
        continue
    target=stage/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(item,target)
print(stage)
PY
)"

status=0
(
  cd -- "$stage_dir"
  if [[ "$compiler" == latexmk ]]; then
    latexmk -norc -pdf -interaction=nonstopmode -halt-on-error \
      -file-line-error main.tex > compile_stdout.txt 2>&1
  else
    "$tectonic_bin" --keep-logs --keep-intermediates main.tex \
      > compile_stdout.txt 2>&1
  fi
) || status=$?
for artifact in main.pdf main.log main.aux main.bbl main.blg main.fls compile_stdout.txt; do
  if [[ -f "$stage_dir/$artifact" ]]; then
    cp -- "$stage_dir/$artifact" "$build_dir/$artifact"
  fi
done
printf '%s\n' "$stage_dir" > "$build_dir/source_snapshot.txt"
if [[ "$status" != 0 ]]; then
  tail -60 "$build_dir/compile_stdout.txt" >&2
  exit "$status"
fi
# Independent conceptual panels can reference identical embedded artwork.
# Deduplicate PDF objects without rasterizing pages or changing their content.
# PyMuPDF is already a figure-rendering dependency; a TeX-only build may omit it.
python3 - "$build_dir/main.pdf" <<'PY'
from pathlib import Path
import sys
try:
    import fitz
except ImportError:
    raise SystemExit(0)
path = Path(sys.argv[1])
optimized = path.with_name("main.optimized.pdf")
with fitz.open(path) as document:
    original_text = [page.get_text() for page in document]
    document.save(optimized, garbage=4, deflate=True)
with fitz.open(optimized) as document:
    if [page.get_text() for page in document] != original_text:
        optimized.unlink()
        raise SystemExit("PDF resource cleanup changed page text; original retained.")
optimized.replace(path)
PY
if command -v pdffonts >/dev/null 2>&1; then
  pdffonts "$build_dir/main.pdf" > "$build_dir/fonts.txt"
fi
if command -v pdfinfo >/dev/null 2>&1; then
  pdfinfo "$build_dir/main.pdf" > "$build_dir/pdfinfo.txt"
fi
printf 'Compiled PDF: %s/main.pdf\n' "$build_dir"
printf 'Build log: %s/main.log\n' "$build_dir"
