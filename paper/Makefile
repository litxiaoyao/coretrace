LATEXMK ?= latexmk
PDFLATEX ?= pdflatex
BIBTEX ?= bibtex
LATEXFLAGS ?= -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all pdf pdf-pdflatex clean distclean

all: pdf

pdf:
	$(LATEXMK) -pdf $(LATEXFLAGS) main.tex

pdf-pdflatex:
	$(PDFLATEX) $(LATEXFLAGS) main.tex
	$(BIBTEX) main
	$(PDFLATEX) $(LATEXFLAGS) main.tex
	$(PDFLATEX) $(LATEXFLAGS) main.tex

clean:
	$(LATEXMK) -c main.tex

distclean:
	$(LATEXMK) -C main.tex
