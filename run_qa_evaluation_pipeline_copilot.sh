#!/bin/bash

set -euo pipefail

CSV_PATH="${1:-/Users/wen-chungcheng/remembr/qa_single_short_20260421_234457.csv}"
MODEL_BACKEND="${MODEL_BACKEND:-COMMAND_R}"
JUDGE_BACKEND="${JUDGE_BACKEND:-auto}"
OUTPUT_DIR="${OUTPUT_DIR:-/Users/wen-chungcheng/remembr/qa_results_$(date +%Y%m%d_%H%M%S)}"

mkdir -p "$OUTPUT_DIR"

echo "🎯 QA evaluation pipeline"
echo "CSV: $CSV_PATH"
echo "Answer backend: $MODEL_BACKEND"
echo "Judge backend: $JUDGE_BACKEND"
echo "Output dir: $OUTPUT_DIR"

python /Users/wen-chungcheng/remembr/qa_evaluation_framework.py \
  --csv-path "$CSV_PATH" \
  --model-backend "$MODEL_BACKEND" \
  --judge-backend "$JUDGE_BACKEND" \
  --output "$OUTPUT_DIR/qa_evaluation_report.json"

echo "✅ Done"