
DOC_NAME := Handbuch_Aktienanalyse
MAIN_TEX := summary

TEX_FLAGS := -output-format=pdf -iteraction=nonestopmode

default: runPdfLatex

view: runPdfLatex
	xdg-open $(MAIN_TEX).pdf

runPdfLatex:
	@echo $(OUT)
	$(OUT)
	@echo $(OUT)
	$(OUT)

OUT := pdflatex $(MAIN_TEX).tex -jobname=$(DOC_NAME)

.PHONY : clean
clean:
	-rm -f *.log *.aux *.dvi *.toc