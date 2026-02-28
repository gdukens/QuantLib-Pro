# PowerShell LaTeX Compilation Script for QuantLib Pro Scientific Paper
# This script compiles the LaTeX document with bibliography support

Write-Host "Compiling QuantLib Pro Scientific Paper..." -ForegroundColor Green

# First compilation
Write-Host "Step 1/4: Initial LaTeX compilation..." -ForegroundColor Yellow
pdflatex quantlib_pro_scientific_paper.tex

# Generate bibliography
Write-Host "Step 2/4: Processing bibliography..." -ForegroundColor Yellow
bibtex quantlib_pro_scientific_paper

# Second compilation (to resolve citations)
Write-Host "Step 3/4: Second LaTeX compilation..." -ForegroundColor Yellow
pdflatex quantlib_pro_scientific_paper.tex

# Third compilation (to resolve references)
Write-Host "Step 4/4: Final LaTeX compilation..." -ForegroundColor Yellow
pdflatex quantlib_pro_scientific_paper.tex

# Clean up auxiliary files (optional)
Write-Host "Cleaning up auxiliary files..." -ForegroundColor Cyan
Remove-Item -Force -ErrorAction SilentlyContinue *.aux, *.bbl, *.blg, *.log, *.out, *.toc, *.lof, *.lot

Write-Host "Complete! Output: quantlib_pro_scientific_paper.pdf" -ForegroundColor Green