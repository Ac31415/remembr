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

# Set environment variables
export PYTHONPATH="/Users/wen-chungcheng/remembr:/Users/wen-chungcheng/ACT:$PYTHONPATH"

# Default parameters
COLLECTION_NAME="webots_multimodal_$(date +%Y%m%d_%H%M%S)"
DB_IP="127.0.0.1"
AUDIO_DEVICE="BlackHole"

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
        --no-audio)
            NO_AUDIO="--no-audio"
            shift
            ;;
        --advanced)
            ADVANCED="--advanced"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--collection NAME] [--db-ip IP] [--audio-device DEVICE] [--no-audio] [--advanced]"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Collection: $COLLECTION_NAME"
echo "  Database IP: $DB_IP"
echo "  Audio Device: $AUDIO_DEVICE"
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
    $NO_AUDIO \
    $ADVANCED

echo "Memory builder stopped."