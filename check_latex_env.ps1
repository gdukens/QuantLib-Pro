# LaTeX Environment Check for QuantLib Pro Scientific Paper
# This script checks if necessary LaTeX packages and tools are available

Write-Host "QuantLib Pro Scientific Paper - LaTeX Environment Check" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if pdflatex is available
Write-Host "`nChecking LaTeX installation..." -ForegroundColor Yellow
try {
    $pdflatexVersion = pdflatex --version | Select-Object -First 1
    Write-Host "✓ pdflatex found: $pdflatexVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ pdflatex not found. Please install a LaTeX distribution." -ForegroundColor Red
    Write-Host "  Recommended: TeX Live, MiKTeX, or MacTeX" -ForegroundColor Yellow
}

# Check if bibtex is available  
Write-Host "`nChecking BibTeX..." -ForegroundColor Yellow
try {
    $bibtexVersion = bibtex --version | Select-Object -First 1
    Write-Host "✓ bibtex found: $bibtexVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ bibtex not found. Usually included with LaTeX distributions." -ForegroundColor Red
}

# Check if required files exist
Write-Host "`nChecking required files..." -ForegroundColor Yellow

$requiredFiles = @(
    "quantlib_pro_scientific_paper.tex",
    "references.bib"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing: $file" -ForegroundColor Red
    }
}

# File size information
Write-Host "`nFile information:" -ForegroundColor Yellow
if (Test-Path "quantlib_pro_scientific_paper.tex") {
    $texSize = (Get-Item "quantlib_pro_scientific_paper.tex").Length
    $texLines = (Get-Content "quantlib_pro_scientific_paper.tex").Count
    Write-Host "  Main paper: $texLines lines, $([math]::Round($texSize/1KB, 1)) KB" -ForegroundColor Cyan
}

if (Test-Path "references.bib") {
    $bibSize = (Get-Item "references.bib").Length  
    $bibEntries = (Select-String -Path "references.bib" -Pattern "@").Count
    Write-Host "  Bibliography: $bibEntries entries, $([math]::Round($bibSize/1KB, 1)) KB" -ForegroundColor Cyan
}

# Compilation readiness
Write-Host "`nCompilation readiness:" -ForegroundColor Yellow
$canCompile = (Get-Command pdflatex -ErrorAction SilentlyContinue) -and 
              (Get-Command bibtex -ErrorAction SilentlyContinue) -and
              (Test-Path "quantlib_pro_scientific_paper.tex") -and
              (Test-Path "references.bib")

if ($canCompile) {
    Write-Host "✓ Ready to compile! Run .\compile_paper.ps1" -ForegroundColor Green
} else {
    Write-Host "✗ Missing requirements. See above for details." -ForegroundColor Red
}

Write-Host "`nPaper Statistics:" -ForegroundColor Yellow
if (Test-Path "quantlib_pro_scientific_paper.tex") {
    $content = Get-Content "quantlib_pro_scientific_paper.tex" -Raw
    $sections = ($content | Select-String -AllMatches "\\section\{").Matches.Count
    $equations = ($content | Select-String -AllMatches "\\begin\{equation\}").Matches.Count  
    $algorithms = ($content | Select-String -AllMatches "\\begin\{algorithm\}").Matches.Count
    $tables = ($content | Select-String -AllMatches "\\begin\{table\}").Matches.Count
    
    Write-Host "  Sections: $sections" -ForegroundColor Cyan
    Write-Host "  Equations: $equations" -ForegroundColor Cyan  
    Write-Host "  Algorithms: $algorithms" -ForegroundColor Cyan
    Write-Host "  Tables: $tables" -ForegroundColor Cyan
}

Write-Host "`nFor help, see PAPER_README.md" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Green