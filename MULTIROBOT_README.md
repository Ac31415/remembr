# Multi-Robot Multimodal Memory System

This system extends the single-robot multimodal memory builder to support **2 robots simultaneously**:

## System Overview

### Robots
1. **Ground Robot (Spot)**: Uses YOLO detection with regular bounding boxes
2. **Aerial Robot (Mavic 2 Pro)**: Uses YOLO-OBB detection with oriented bounding boxes

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-Robot System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐                      ┌──────────────┐      │
│  │ Ground Robot│ ─────────────────────▶│  YOLO        │      │
│  │   (Spot)    │  /tmp/webots_memory_ │  Detection   │      │
│  │             │       _ground/       │  (xyxy bbox) │      │
│  └─────────────┘                      └──────────────┘      │
│                                               │               │
│                                               ▼               │
│  ┌─────────────┐                      ┌──────────────┐      │
│  │Aerial Robot │ ─────────────────────▶│  YOLO-OBB    │      │
│  │ (Mavic 2Pro)│  /tmp/webots_memory_ │  Detection   │      │
│  │             │       _aerial/       │(8-pt polygon)│      │
│  └─────────────┘                      └──────────────┘      │
│                                               │               │
│                                               ▼               │
│                                      ┌─────────────────┐     │
│                                      │ Memory Builder  │     │
│                                      │  (with robot_id)│     │
│                                      └─────────────────┘     │
│                                               │               │
│                                               ▼               │
│                                      ┌─────────────────┐     │
│                                      │ Milvus Database │     │
│                                      │  (Multi-Robot)  │     │
│                                      └─────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
/tmp/webots_memory_ground/     # Ground robot data
  ├── spot_image_*.jpg         # Camera captures
  ├── memory_*.json            # Memory metadata
  ├── nav_command.json         # Navigation commands
  └── robot_status.json        # Robot status

/tmp/webots_memory_aerial/     # Aerial robot data
  ├── mavic_image_*.jpg        # Camera captures
  ├── memory_*.json            # Memory metadata
  ├── nav_command.json         # Navigation commands
  └── robot_status.json        # Robot status
```

## Key Components

### 1. Memory Structure (memory_multimodal_multirobot.py)
- Extended `MemoryItem` with `robot_id` field
- Supports filtering by robot ID
- Groups memories by robot and timestamp

### 2. Milvus Database (milvus_memory_multimodal_multirobot.py)
- Multi-robot schema with `robot_id` VARCHAR field
- `search_by_robot(robot_id)` for per-robot queries
- JSON serialization for detection results

### 3. Memory Builder (memory_build_enhanced_multimodal_multirobot.py)
- **YOLOCaptioner**: Regular YOLO for ground robot
  - Returns: `(caption, detection_dict, annotated_path)`
  - Detection dict: `{classes, bounding_boxes, confidences, class_names, detection_type='yolo'}`
  - Bounding boxes: `[x1, y1, x2, y2]` (xyxy format)
  
- **YOLOOBBCaptioner**: YOLO-OBB for aerial robot
  - Returns: `(caption, detection_dict, annotated_path)`
  - Detection dict: `{classes, bounding_boxes, confidences, class_names, detection_type='yolo-obb'}`
  - Bounding boxes: `[x1, y1, x2, y2, x3, y3, x4, y4]` (4-point polygon)

- Separate processing threads:
  - `ground_visual_processing_thread()` - YOLO for ground
  - `aerial_visual_processing_thread()` - YOLO-OBB for aerial
  - `audio_processing_thread()` - Shared audio (ACT)
  - `memory_integration_thread()` - Combines all data

### 4. Robot Controllers

#### Ground Robot (spot_driver.py)
```python
# Modified sections:
- Added: time, pathlib, PIL imports
- Added: Memory capture initialization in __init__
- Added: capture_image() method
- Added: save_memory_data() method
- Added: capture_memory_periodic() method
- Modified: Main loop to call capture_memory_periodic()
```

#### Aerial Robot (mavic2pro.py)
```python
# Modified sections:
- Added: numpy, pathlib, PIL imports
- Added: Memory capture global variables
- Added: capture_image() function
- Added: save_memory_data() function
- Added: capture_memory_periodic() function
- Modified: Main loop to call capture_memory_periodic()
```

## Usage

### 1. Launch Multi-Robot Memory Builder

```bash
# Basic launch
./launch_multimodal_memory_multirobot.sh --collection my_multirobot_session

# With audio disabled
./launch_multimodal_memory_multirobot.sh --collection test --no-audio

# Custom data directories
./launch_multimodal_memory_multirobot.sh \
  --collection my_session \
  --ground-data-dir /custom/path/ground \
  --aerial-data-dir /custom/path/aerial

# Full example with all options
./launch_multimodal_memory_multirobot.sh \
  --collection webots_multirobot_demo \
  --db-ip 127.0.0.1 \
  --audio-backend ACT \
  --audio-device BlackHole \
  --ground-data-dir /tmp/webots_memory_ground \
  --aerial-data-dir /tmp/webots_memory_aerial
```

### 2. Inspect Multi-Robot Memories

```bash
# View all memories in table format
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot

# View recent 10 items in detailed format
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot \
  --recent 10 \
  --format detailed

# Filter by ground robot only
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot \
  --robot ground \
  --format table

# Filter by aerial robot and export to CSV
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot \
  --robot aerial \
  --format csv > aerial_memories.csv

# Show collection information
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot \
  --info

# Reset collection (CAUTION: Deletes all data)
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection webots_multirobot \
  --reset
```

### 3. Running the Robots in Webots

1. **Start Ground Robot (Spot)**:
   - Open Webots world with Spot robot
   - Controller: `spot_driver.py`
   - Data saved to: `/tmp/webots_memory_ground/`

2. **Start Aerial Robot (Mavic 2 Pro)**:
   - Open Webots world with Mavic 2 Pro
   - Controller: `mavic2pro.py`
   - Data saved to: `/tmp/webots_memory_aerial/`

3. **Start Memory Builder**:
   ```bash
   ./launch_multimodal_memory_multirobot.sh --collection my_session
   ```

## Detection Results Structure

### Ground Robot (YOLO)
```json
{
  "classes": [0, 15, 62],
  "bounding_boxes": [
    [120.5, 230.1, 350.8, 480.2],  // person
    [400.3, 150.7, 550.9, 280.4],  // bird
    [600.1, 300.5, 720.3, 420.8]   // chair
  ],
  "confidences": [0.95, 0.87, 0.82],
  "class_names": ["person", "bird", "chair"],
  "detection_type": "yolo"
}
```

### Aerial Robot (YOLO-OBB)
```json
{
  "classes": [0, 5],
  "bounding_boxes": [
    [100.2, 150.3, 300.5, 140.1, 310.7, 380.9, 110.4, 390.2],  // 4-point polygon
    [450.1, 200.5, 550.3, 195.7, 555.8, 350.2, 445.6, 355.9]
  ],
  "confidences": [0.92, 0.88],
  "class_names": ["person", "bus"],
  "detection_type": "yolo-obb"
}
```

## Memory Item Structure

```python
@dataclass
class MemoryItem:
    caption: str              # Visual caption from YOLO
    time: float               # Unix timestamp
    position: list            # [x, y, z]
    theta: float              # Orientation angle
    robot_id: str             # "ground" or "aerial"
    audio_caption: str        # Audio caption from ACT
    detection_results: dict   # YOLO/YOLO-OBB detection results
```

## Database Schema

```
Collection: webots_multirobot_*
├── id: VARCHAR(1000) [Primary Key]
├── text_embedding: FLOAT_VECTOR(1024)
├── position: FLOAT_VECTOR(3)
├── theta: FLOAT
├── time: FLOAT_VECTOR(2)
├── caption: VARCHAR(3000)
├── audio_caption: VARCHAR(3000)
├── detection_results: VARCHAR(10000) [JSON]
└── robot_id: VARCHAR(100) [NEW]
```

## Queries

### Python API Examples

```python
from remembr.memory.milvus_memory_multimodal_multirobot import MilvusMemory

memory = MilvusMemory("webots_multirobot", db_ip="127.0.0.1")

# Search by robot
ground_memories = memory.search_by_robot("ground")
aerial_memories = memory.search_by_robot("aerial")

# Search by text (searches all robots)
results = memory.search_by_text("person walking")

# Search by position (searches all robots)
results = memory.search_by_position((10.0, 5.0, 0.0))

# Search by time
results = memory.search_by_time("14:30:00")
```

## Files Created/Modified

### New Files
- `remembr/memory/memory_multimodal_multirobot.py`
- `remembr/memory/milvus_memory_multimodal_multirobot.py`
- `memory_build_enhanced_multimodal_multirobot.py`
- `launch_multimodal_memory_multirobot.sh`
- `milvus_memory_inspector_multimodal_multirobot.py`
- `MULTIROBOT_README.md` (this file)

### Modified Files
- `spot_driver.py` (ground robot controller)
- `mavic2pro.py` (aerial robot controller)

### Original Files (Not Modified)
- `remembr/memory/memory_multimodal.py`
- `remembr/memory/milvus_memory_multimodal.py`
- `memory_build_enhanced_multimodal.py`
- `launch_multimodal_memory_working.sh`
- `milvus_memory_inspector_multimodal.py`

## Features

✅ **Dual Robot Support**: Ground + Aerial simultaneously
✅ **Robot Identification**: Each memory tagged with robot_id
✅ **YOLO Detection**: Regular bounding boxes for ground robot
✅ **YOLO-OBB Detection**: Oriented bounding boxes for aerial robot
✅ **Shared Audio**: ACT audio captioning across both robots
✅ **Separate Data Folders**: Isolated storage per robot
✅ **Frame Annotation**: Bounding boxes drawn on saved images
✅ **Multi-Robot Inspector**: Filter and query by robot
✅ **JSON Serialization**: Complex detection data stored efficiently

## Troubleshooting

### No data being captured
```bash
# Check data directories exist
ls -la /tmp/webots_memory_ground/
ls -la /tmp/webots_memory_aerial/

# Verify robots are running
# Check Webots console for memory capture messages
```

### YOLO model not found
```bash
# Verify model paths in memory builder
Ground: /Users/wen-chungcheng/ultralytics/trained models/yolo26x.pt
Aerial: /Users/wen-chungcheng/ultralytics/trained models/obb_detect/yolo26x-obb.pt
```

### Database connection issues
```bash
# Check Milvus is running
nc -z 127.0.0.1 19530

# Start Milvus if needed
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest
```

### Collection already exists
```bash
# Reset collection to use new schema
python milvus_memory_inspector_multimodal_multirobot.py \
  --collection old_collection \
  --reset
```

## Dependencies

- Python 3.8+
- Ultralytics YOLO (`ultralytics`)
- Milvus (`pymilvus`)
- LangChain (`langchain`, `langchain-community`, `langchain-huggingface`)
- PyTorch (`torch`)
- NumPy (`numpy`)
- Pillow (`PIL`)
- Librosa (`librosa`)
- PyAudio (`pyaudio`)
- Webots (for robot simulation)

## Performance Notes

- **Capture Interval**: 1 second per robot (configurable)
- **Image Quality**: JPEG 85% quality
- **Detection Threshold**: 0.25 confidence (configurable)
- **Memory Integration**: Timestamps matched within 10 seconds
- **Thread Safety**: Separate queues for each robot

## Next Steps

1. **Start Milvus**: Ensure database is running
2. **Launch Robots**: Start both Spot and Mavic in Webots
3. **Start Memory Builder**: Run launch script with desired collection name
4. **Inspect Memories**: Use inspector to view captured data
5. **Query System**: Use Python API or inspector for robot-specific queries

For questions or issues, refer to the original single-robot documentation or contact the development team.
