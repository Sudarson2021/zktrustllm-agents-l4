#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT_DIR="results/l4_latex_compile_validation"
PDF_DIR="results/l4_report_pdf"
TEX="docs/paper/zktrustllm_agents_l4_journal_draft.tex"
PDF="$PDF_DIR/zktrustllm_agents_l4_journal_draft.pdf"

mkdir -p "$OUT_DIR" "$PDF_DIR"

if ! command -v pdflatex >/dev/null 2>&1; then
  cat > "$OUT_DIR/latex_compile_summary.json" <<JSON
{
  "experiment": "step113_latex_compile_validation",
  "status": "PDFLATEX_NOT_FOUND",
  "latexDraft": "$TEX",
  "compiledPdf": null,
  "message": "pdflatex is not installed or not on PATH."
}
JSON
  echo "pdflatex not found. Install TeX Live first."
  exit 2
fi

echo "[step113] Compiling LaTeX journal draft..."

pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$PDF_DIR" "$TEX" \
  > "$OUT_DIR/pdflatex_pass1_stdout.log" \
  2> "$OUT_DIR/pdflatex_pass1_stderr.log"

pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$PDF_DIR" "$TEX" \
  > "$OUT_DIR/pdflatex_pass2_stdout.log" \
  2> "$OUT_DIR/pdflatex_pass2_stderr.log"

if [ ! -f "$PDF" ]; then
  echo "Expected PDF not found: $PDF"
  exit 3
fi

cat > "$OUT_DIR/latex_compile_summary.json" <<JSON
{
  "experiment": "step113_latex_compile_validation",
  "status": "PASS",
  "latexDraft": "$TEX",
  "compiledPdf": "$PDF",
  "stdoutPass1": "$OUT_DIR/pdflatex_pass1_stdout.log",
  "stderrPass1": "$OUT_DIR/pdflatex_pass1_stderr.log",
  "stdoutPass2": "$OUT_DIR/pdflatex_pass2_stdout.log",
  "stderrPass2": "$OUT_DIR/pdflatex_pass2_stderr.log",
  "researchMeaning": "Validates that the Step 112 LaTeX journal draft can compile into a supervisor-readable PDF."
}
JSON

cat > "$OUT_DIR/latex_compile_summary.md" <<MD
# Step 113 LaTeX Compile Validation

## Result

- Status: **PASS**
- LaTeX draft: \`$TEX\`
- Compiled PDF: \`$PDF\`

## Research Meaning

Step 113 validates that the L4 journal manuscript is not only written as LaTeX source, but can also compile into a PDF for supervisor review and later journal formatting.

## Generated Files

- Summary JSON: \`$OUT_DIR/latex_compile_summary.json\`
- Summary Markdown: \`$OUT_DIR/latex_compile_summary.md\`
- Compiled PDF: \`$PDF\`
MD

echo "[step113] PASS: $PDF"
