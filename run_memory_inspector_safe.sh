#!/bin/bash

echo "🔧 Configuring Apple Silicon M3 Max environment for Milvus..."

# Apple Silicon threading optimizations
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Disable problematic optimizations
export MKL_DYNAMIC=false
export MKL_ENABLE_INSTRUCTIONS=SSE4_2

# Python threading
export PYTHONUNBUFFERED=1

echo "✓ Environment configured for Apple Silicon"
echo "🚀 Running Milvus Memory Inspector..."

python milvus_memory_inspector_multimodal.py "$@"