#!/bin/bash
# Multi-Robot Multimodal Memory Builder Launcher

echo "🤖🚁 Launching Multi-Robot Enhanced Multimodal Memory Builder"
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
COLLECTION_NAME="webots_multirobot_$(date +%Y%m%d_%H%M%S)"
DB_IP="127.0.0.1"
AUDIO_DEVICE="BlackHole"
AUDIO_BACKEND="ACT"
GROUND_DATA_DIR="/tmp/webots_memory_ground"
AERIAL_DATA_DIR="/tmp/webots_memory_aerial"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--collection)
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
        --audio-backend)
            AUDIO_BACKEND="$2"
            shift 2
            ;;
        --no-audio)
            NO_AUDIO="true"
            shift
            ;;
        --ground-data-dir)
            GROUND_DATA_DIR="$2"
            shift 2
            ;;
        --aerial-data-dir)
            AERIAL_DATA_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --collection NAME        Milvus collection name (default: timestamped)"
            echo "  --db-ip IP                   Milvus database IP (default: 127.0.0.1)"
            echo "  --audio-device DEVICE        Audio input device (default: BlackHole)"
            echo "  --audio-backend BACKEND      Audio backend: ACT (default: ACT)"
            echo "  --no-audio                   Disable audio captioning"
            echo "  --ground-data-dir DIR        Ground robot data directory (default: /tmp/webots_memory_ground)"
            echo "  --aerial-data-dir DIR        Aerial robot data directory (default: /tmp/webots_memory_aerial)"
            echo "  -h, --help                   Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --collection my_multirobot_session --audio-backend ACT"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Collection: $COLLECTION_NAME"
echo "  Database IP: $DB_IP"
echo "  Audio Device: $AUDIO_DEVICE"
echo "  Audio Backend: $AUDIO_BACKEND"
echo "  Audio Enabled: $([ -z "$NO_AUDIO" ] && echo "Yes" || echo "No")"
echo "  Ground Robot: YOLO detection"
echo "  Aerial Robot: YOLO-OBB detection"
echo "  Ground Data Dir: $GROUND_DATA_DIR"
echo "  Aerial Data Dir: $AERIAL_DATA_DIR"
echo

# Create data directories
mkdir -p "$GROUND_DATA_DIR"
mkdir -p "$AERIAL_DATA_DIR"
echo "✅ Data directories created"

# Launch the memory builder
echo "🚀 Starting Multi-Robot Memory Builder..."
cd /Users/wen-chungcheng/remembr

CMD="python memory_build_enhanced_multimodal_multirobot.py \
    --collection \"$COLLECTION_NAME\" \
    --db-ip \"$DB_IP\" \
    --audio-backend \"$AUDIO_BACKEND\" \
    --audio-device \"$AUDIO_DEVICE\" \
    --ground-data-dir \"$GROUND_DATA_DIR\" \
    --aerial-data-dir \"$AERIAL_DATA_DIR\""

if [ -n "$NO_AUDIO" ]; then
    CMD="$CMD --no-audio"
fi

eval $CMD

echo "Memory builder stopped."
