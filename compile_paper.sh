#!/bin/bash
# LaTeX Compilation Script for QuantLib Pro Scientific Paper
# This script compiles the LaTeX document with bibliography support

echo "Compiling QuantLib Pro Scientific Paper..."

# First compilation
echo "Step 1/4: Initial LaTeX compilation..."
pdflatex quantlib_pro_scientific_paper.tex

# Generate bibliography
echo "Step 2/4: Processing bibliography..."
bibtex quantlib_pro_scientific_paper

# Second compilation (to resolve citations)
echo "Step 3/4: Second LaTeX compilation..."
pdflatex quantlib_pro_scientific_paper.tex

# Third compilation (to resolve references)
echo "Step 4/4: Final LaTeX compilation..."
pdflatex quantlib_pro_scientific_paper.tex

# Clean up auxiliary files (optional)
echo "Cleaning up auxiliary files..."
rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot

echo "Complete! Output: quantlib_pro_scientific_paper.pdf"