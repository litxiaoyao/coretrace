# Reproducible paper build

Run from the repository root:

```bash
bash analysis/compile_paper.sh
```

The default output is `analysis/build_final/main.pdf`. The same directory contains the final LaTeX log, BibTeX output, font inventory, PDF metadata, and a path to the exact source snapshot used for that build. Optional arguments select a different source directory and build directory:

```bash
bash analysis/compile_paper.sh paper analysis/build_review
```

A standard TeX installation uses its normal `pdflatex`, BibTeX and font configuration. The script requires `python3`, `kpsewhich`, `pdftex`, `pdflatex`, `updmap` and `latexmk`; `pdfinfo` and `pdffonts` provide optional inspection output. The script invokes `latexmk -norc -pdf` so a machine-wide Latexmk preference for another engine does not override the paper's pdfLaTeX build.

## Local workspace recovery

The execution image contains a full read-only TeX package tree, but its generated file index, pdfLaTeX format and font maps are missing. The script therefore searches the installed package tree directly and places generated caches under `analysis/tex_runtime/`. A local `updmap` configuration embeds the standard URW Base14 fonts and supplies Computer Modern and AMS outline maps. `microtype` and all original ICML template files remain active and unchanged.

The source snapshot is a new directory for each build. All auxiliary files are written there, avoiding the ambiguity that arose when a pre-existing source auxiliary file and a separate Latexmk output directory were used together. The input manuscript directory is read-only to this build procedure. Old generated build snapshots may be removed after review; they are reproducible intermediates and do not belong in the manuscript source archive.

For a nonstandard TeX source-tree location, set `CORETRACE_TEX_DIST`. To explicitly exercise the isolated cache path, set `CORETRACE_LOCAL_TEX=1`. These variables do not alter the manuscript or the system installation.

## Verified baseline

On 2026-11-24, the unmodified uploaded manuscript was built successfully through the complete Latexmk/BibTeX cycle using:

```bash
bash analysis/compile_paper.sh ../source_upload analysis/build_baseline_verified
```

The resulting PDF has 23 pages and 26 font records. Every font is embedded; no Type 3 bitmap font appears. Body Times/Computer Modern fonts are Type 1; existing vector plots include embedded CID TrueType. The final log contains no undefined citation or reference warning. The evidence is recorded in `analysis/build_baseline_verified/build_validation.json`, `fonts.txt`, `pdfinfo.txt`, and `main.log`.

This baseline proves the recovered build environment. The revised paper must be compiled again and visually reviewed after its final edits.
