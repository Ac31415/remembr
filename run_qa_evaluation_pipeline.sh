#!/bin/bash

set -euo pipefail

CSV_PATH="${1:-/Users/wen-chungcheng/remembr/qa_single_short_20260421_234457.csv}"
OUTPUT_BASENAME="${2:-qa_evaluation_report.json}"
MILVUS_COLLECTION="${3:-${MILVUS_COLLECTION:-webots_simulation}}"
MODEL_BACKEND="${MODEL_BACKEND:-COMMAND_R}"
JUDGE_BACKEND="${JUDGE_BACKEND:-auto}"
OUTPUT_DIR="${OUTPUT_DIR:-/Users/wen-chungcheng/remembr/qa_results_$(date +%Y%m%d_%H%M%S)}"

mkdir -p "$OUTPUT_DIR"

echo "🎯 QA evaluation pipeline"
echo "CSV: $CSV_PATH"
echo "Answer backend: $MODEL_BACKEND"
echo "Judge backend: $JUDGE_BACKEND"
echo "Milvus collection: $MILVUS_COLLECTION"
echo "Output dir: $OUTPUT_DIR"

if [[ "$OUTPUT_BASENAME" == /* || "$OUTPUT_BASENAME" == *"/"* ]]; then
  OUTPUT_PATH="$OUTPUT_BASENAME"
else
  OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_BASENAME"
fi

python /Users/wen-chungcheng/remembr/qa_evaluation_framework.py \
  --csv-path "$CSV_PATH" \
  --model-backend "$MODEL_BACKEND" \
  --judge-backend "$JUDGE_BACKEND" \
  --milvus-collection "$MILVUS_COLLECTION" \
  --output "$OUTPUT_PATH"

echo "✅ Done"