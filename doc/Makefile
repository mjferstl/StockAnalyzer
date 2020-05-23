
DOC_NAME := Handbuch_Unternehmensanalyse
MAIN_TEX := summary

TEX_FLAGS := -output-format=pdf -iteraction=nonestopmode -jobname=$(DOC_NAME)

default: runPdfLatex

view: runPdfLatex
	xdg-open $(MAIN_TEX).pdf

runPdfLatex:
	@echo $(OUT)
	$(OUT)
	@echo $(OUT)
	$(OUT)

OUT := pdflatex $(MAIN_TEX).tex $(TEX_FLAGS)

.PHONY : clean
clean:
	-rm -f *.log *.aux *.dvi *.toc tex_files/*.aux