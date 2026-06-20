#!/bin/bash
# filepath: /Users/wen-chungcheng/remembr/launch_multimodal_memory.sh

# Launch Multimodal Memory Builder for Webots
echo "🤖 Launching Enhanced Multimodal Memory Builder"
echo "============================================="

# Check if MilvusDB is running
echo "Checking MilvusDB connection..."
if ! nc -z 127.0.0.1 19530; then
    echo "❌ MilvusDB not running. Please start MilvusDB first:"
    echo "   docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest"
    exit 1
fi
echo "✅ MilvusDB is running"

# Check MLX compatibility
echo "Checking MLX compatibility..."
python -c "
import mlx.core as mx
import sys
try:
    # Test basic MLX operations
    a = mx.array([1.0, 2.0])
    b = mx.array([3.0, 4.0])
    c = mx.matmul(a.reshape(1, 2), b.reshape(2, 1))
    mx.eval(c)
    print('✅ MLX basic operations working')
except Exception as e:
    print(f'⚠️ MLX compatibility issue: {e}')
    print('Consider using --visual-backend FASTVLM for better stability')
" 2>/dev/null || echo "⚠️ MLX compatibility check failed"

# Replace with this version-aware installation:

# Check if mlx_vlm is installed and handle version conflicts
echo "Checking mlx_vlm installation..."
if ! python -c "import mlx_vlm" 2>/dev/null; then
    echo "Installing mlx_vlm with compatible versions..."
    # Install mlx_vlm without upgrading numpy and transformers
    pip install mlx-vlm --no-deps
    # Install only the new dependencies we actually need
    pip install "opencv-python>=4.12.0.88"
    echo "✅ mlx_vlm installed without version conflicts"
else
    echo "✅ mlx_vlm is already installed"
fi

# Set environment variables
export PYTHONPATH="/Users/wen-chungcheng/remembr:/Users/wen-chungcheng/ACT:$PYTHONPATH"

# Default parameters
COLLECTION_NAME="webots_multimodal_$(date +%Y%m%d_%H%M%S)"
DB_IP="127.0.0.1"
AUDIO_DEVICE="BlackHole"
AUDIO_BACKEND="ACT"  # Add this line

VISUAL_BACKEND="PHI3"  # Add this line


# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --collection)
            COLLECTION_NAME="$2"
            shift 2
            ;;
        --db-ip)
            DB_IP="$2"
            shift 2
            ;;
        --audio-device)
            AUDIO_DEVICE="$2"
            shift 2
            ;;
        --audio-backend)  # Add this case
            AUDIO_BACKEND="$2"
            shift 2
            ;;
        --no-audio)
            NO_AUDIO="--no-audio"
            shift
            ;;
        --advanced)
            ADVANCED="--advanced"
            shift
            ;;
        --visual-backend)
            VISUAL_BACKEND="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --collection NAME       Milvus collection name"
            echo "  --db-ip IP             Database IP address (default: 127.0.0.1)"
            echo "  --audio-device DEVICE  Audio input device (default: BlackHole)"
            echo "  --audio-backend BACKEND Audio captioning backend: ACT or AUDIOSET (default: ACT)"
            echo "  --visual-backend BACKEND Visual backend: PHI3, FASTVLM, GEMMA, or YOLO (default: PHI3)"
            echo "  --no-audio             Disable audio processing"
            echo "  --advanced             Use advanced captioning mode"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--collection NAME] [--db-ip IP] [--audio-device DEVICE] [--audio-backend ACT|AUDIOSET] [--visual-backend PHI3|FASTVLM|GEMMA|YOLO] [--no-audio] [--advanced]"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Collection: $COLLECTION_NAME"
echo "  Database IP: $DB_IP"
echo "  Audio Device: $AUDIO_DEVICE"
echo "  Audio Backend: $AUDIO_BACKEND"  # Add this line
echo "  Visual Backend: $VISUAL_BACKEND"  # Add this line
echo "  Audio Enabled: $([ -z "$NO_AUDIO" ] && echo "Yes" || echo "No")"
echo "  Advanced Mode: $([ -n "$ADVANCED" ] && echo "Yes" || echo "No")"
echo

# Launch the memory builder
echo "🚀 Starting Enhanced Memory Builder..."
cd /Users/wen-chungcheng/remembr

python memory_build_enhanced_multimodal.py \
    --collection "$COLLECTION_NAME" \
    --db-ip "$DB_IP" \
    --audio-device "$AUDIO_DEVICE" \
    --audio-backend "$AUDIO_BACKEND" \
    --visual-backend "$VISUAL_BACKEND" \
    $NO_AUDIO \
    $ADVANCED

echo "Memory builder stopped."