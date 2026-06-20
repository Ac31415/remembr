Ac31415: based on the provided scripts, explain how the Memory Building Phase works line by line and block by block in great details

GitHub Copilot: # Memory Building Phase: Detailed Line-by-Line Explanation

## Overview
The Memory Building Phase is a multimodal system that captures, processes, and stores robot experiences combining visual and audio data. Let me break down how it works in detail.

---

## Part 1: Launch Script (launch_multimodal_memory_working.sh)

### Initialization Block
```bash
#!/bin/bash
echo "🤖 Launching Enhanced Multimodal Memory Builder"
echo "============================================="
```
- **Purpose**: Sets bash interpreter and displays startup banner
- **Function**: User feedback that system is initializing

### MilvusDB Verification
```bash
if ! nc -z 127.0.0.1 19530; then
    echo "❌ MilvusDB not running. Please start MilvusDB first:"
    exit 1
fi
```
- **`nc -z 127.0.0.1 19530`**: Network check to port 19530
- **Purpose**: Verifies MilvusDB vector database is running
- **Critical**: System cannot store memories without database

### MLX Compatibility Check
```bash
python -c "
import mlx.core as mx
try:
    a = mx.array([1.0, 2.0])
    b = mx.array([3.0, 4.0])
    c = mx.matmul(a.reshape(1, 2), b.reshape(2, 1))
    mx.eval(c)
except Exception as e:
    print(f'⚠️ MLX compatibility issue: {e}')
"
```
- **Purpose**: Tests MLX framework operations
- **Tests**: Array creation, reshaping, matrix multiplication
- **Why Important**: MLX powers the visual captioning models

### Dependency Installation
```bash
if ! python -c "import mlx_vlm" 2>/dev/null; then
    pip install mlx-vlm --no-deps
    pip install "opencv-python>=4.12.0.88"
fi
```
- **`--no-deps`**: Prevents version conflicts with existing packages
- **Strategy**: Install only what's needed incrementally
- **Protects**: numpy and transformers from unwanted upgrades

### Environment Setup
```bash
export PYTHONPATH="/Users/wen-chungcheng/remembr:/Users/wen-chungcheng/ACT:$PYTHONPATH"
```
- **Purpose**: Adds custom module paths to Python's search path
- **remembr**: ReMEmbR framework modules
- **ACT**: Audio Captioning Transformer model

### Parameter Configuration
```bash
COLLECTION_NAME="webots_multimodal_$(date +%Y%m%d_%H%M%S)"
DB_IP="127.0.0.1"
AUDIO_DEVICE="BlackHole"
AUDIO_BACKEND="ACT"
VISUAL_BACKEND="PHI3"
```
- **COLLECTION_NAME**: Timestamped database collection for unique sessions
- **DB_IP**: MilvusDB connection address
- **AUDIO_DEVICE**: Virtual audio device for system audio capture
- **AUDIO_BACKEND**: Chooses between ACT (captioning) or AUDIOSET (tagging)
- **VISUAL_BACKEND**: Chooses between PHI3, FASTVLM, or GEMMA models

### Argument Parsing Loop
```bash
while [[ $# -gt 0 ]]; do
    case $1 in
        --collection) COLLECTION_NAME="$2"; shift 2 ;;
        --audio-backend) AUDIO_BACKEND="$2"; shift 2 ;;
        --visual-backend) VISUAL_BACKEND="$2"; shift 2 ;;
        --no-audio) NO_AUDIO="--no-audio"; shift ;;
    esac
done
```
- **Purpose**: Allows runtime customization of parameters
- **`shift 2`**: Consumes option and its value
- **`shift`**: Consumes flag-only options

---

## Part 2: Python Memory Builder (memory_build_enhanced_multimodal.py)

### Import and Path Setup
```python
remembr_path = "/Users/wen-chungcheng/remembr"
act_path = "/Users/wen-chungcheng/ACT"
audioset_tagging_cnn_path = "/Users/wen-chungcheng/audioset_tagging_cnn"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)
```
- **`sys.path.insert(0, path)`**: Adds to front of search path (highest priority)
- **Purpose**: Ensures custom modules are found before system modules

### AudioSet Module Import Strategy
```python
def import_audioset_modules():
    original_path = sys.path.copy()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(audioset_path)
        sys.path.insert(0, audioset_path)
        
        spec = importlib.util.spec_from_file_location("audioset_models", 
                                                      os.path.join(audioset_pytorch_path, "models.py"))
        audioset_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audioset_models)
    finally:
        sys.path = original_path
        os.chdir(original_cwd)
```
- **Why Complex**: AudioSet has relative imports that need specific context
- **`spec_from_file_location`**: Direct file import without package structure
- **Finally Block**: Guarantees cleanup even if errors occur
- **State Restoration**: Returns to original directory and path

---

## Part 3: Audio Captioning Module (ACT Backend)

### Initialization
```python
class AudioCaptioningModule:
    def __init__(self, device_name="BlackHole", sample_rate=44100, chunk_duration=10.0):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
```
- **sample_rate=44100**: CD-quality audio (44.1kHz)
- **chunk_duration=10.0**: Processes 10-second segments
- **chunk_size**: Total samples per chunk = 44100 * 10 = 441,000 samples

### Audio Device Discovery
```python
def find_audio_device(self, device_name):
    for i in range(self.audio.get_device_count()):
        device_info = self.audio.get_device_info_by_index(i)
        if (device_name.lower() in device_info['name'].lower() and 
            device_info['maxInputChannels'] > 0):
            return i
```
- **Iterates**: Through all available audio devices
- **Checks**: Name match AND input capability
- **maxInputChannels > 0**: Ensures device can record
- **Fallback**: Uses system default if specified device not found

### ACT Model Setup
```python
def setup_act_model(self):
    original_cwd = os.getcwd()
    os.chdir(act_dir)
    
    self.config = get_config()
    self.config.mode = 'eval'
    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
```
- **Directory Change**: ACT expects to run from its own directory
- **mode='eval'**: Sets model to inference mode (no training)
- **Device Selection**: GPU if available, otherwise CPU

### Vocabulary Loading
```python
self.words_list = load_pickle_file(self.config.path.vocabulary)
self.ntokens = len(self.words_list)
self.sos_ind = self.words_list.index('<sos>')
self.eos_ind = self.words_list.index('<eos>')
```
- **words_list**: Complete vocabulary (e.g., 50,000 words)
- **ntokens**: Used to configure model output layer
- **sos_ind**: Start-of-sequence token for caption generation
- **eos_ind**: End-of-sequence token (stops generation)

### Audio Stream Setup
```python
def setup_audio_stream(self):
    self.stream = self.audio.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=self.sample_rate,
        input=True,
        input_device_index=self.device_index,
        frames_per_buffer=1024
    )
```
- **paFloat32**: 32-bit floating point samples (-1.0 to 1.0)
- **channels=1**: Mono audio (sufficient for speech/environment)
- **input=True**: Configures for recording
- **frames_per_buffer=1024**: Read 1024 samples at a time (23ms chunks)

### Audio Preprocessing
```python
def preprocess_audio_for_act(self, audio_data):
    target_sr = self.config.wav.sr  # 32000 Hz
    target_length = 10 * target_sr
    
    if self.sample_rate != target_sr:
        audio_data = librosa.resample(audio_data, 
                                      orig_sr=self.sample_rate, 
                                      target_sr=target_sr)
```
- **Resampling**: Converts 44.1kHz → 32kHz (ACT's expected rate)
- **librosa.resample**: High-quality resampling with anti-aliasing
- **target_length**: Ensures exactly 10 seconds (320,000 samples)

### Padding/Truncation
```python
if len(audio_data) <= target_length:
    audio_data = np.concatenate((audio_data, 
                                 np.zeros(target_length - len(audio_data))))
else:
    audio_data = audio_data[:target_length]
```
- **Short Audio**: Pads with zeros (silence) to 10 seconds
- **Long Audio**: Truncates to first 10 seconds
- **Purpose**: Model expects fixed-length input

### Mel-Spectrogram Extraction
```python
feature = librosa.feature.melspectrogram(
    y=audio_data,
    sr=target_sr,
    n_fft=self.config.wav.window_length,
    hop_length=self.config.wav.hop_length,
    n_mels=self.config.wav.n_mels
)
```
- **Mel-spectrogram**: Frequency representation mimicking human hearing
- **n_fft**: FFT window size (typically 1024 or 2048)
- **hop_length**: Step between windows (overlap for smoothness)
- **n_mels**: Number of mel frequency bands (typically 64 or 128)

### Log-Scale Conversion
```python
feature = librosa.power_to_db(feature).T.astype(np.float32)
feature = feature[:-1, :]
```
- **power_to_db**: Converts to decibel scale (log scale)
- **.T**: Transpose to (time, frequency) format
- **[:-1, :]**: Removes last time frame (boundary artifact)

### Caption Generation
```python
def generate_audio_caption(self, audio_data, beam_size=3):
    src = self.preprocess_audio_for_act(audio_data).to(self.device)
    
    with torch.no_grad():
        if beam_size == 1:
            output = greedy_decode(self.model, src, sos_ind, eos_ind)
        else:
            output = beam_decode(src, self.model, sos_ind, eos_ind, 
                               beam_width=beam_size)
```
- **torch.no_grad()**: Disables gradient computation (inference only)
- **greedy_decode**: Fastest, picks most likely word each step
- **beam_decode**: Better quality, explores top-k alternatives
- **beam_size=3**: Keeps 3 best hypotheses at each step

### Caption Decoding
```python
output = output[0, 1:].cpu().numpy()

caption_words = []
for idx in output:
    if idx == self.eos_ind:
        break
    caption_words.append(self.words_list[idx])

caption = ' '.join(caption_words)
```
- **[0, 1:]**: First batch item, skip SOS token
- **Loop Until EOS**: Builds caption word by word
- **words_list[idx]**: Converts token indices to words
- **join**: Combines words into sentence

### Audio Chunk Capture
```python
def capture_audio_chunk(self):
    while len(self.audio_buffer) < self.chunk_size:
        audio_data = self.stream.read(1024, exception_on_overflow=False)
        audio_array = np.frombuffer(audio_data, dtype=np.float32)
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_array])
    
    chunk = self.audio_buffer[:self.chunk_size].copy()
    self.audio_buffer = self.audio_buffer[self.chunk_size:]
```
- **Accumulates**: Small chunks until full 10-second window
- **exception_on_overflow=False**: Drops frames if system is busy (prevents crashes)
- **Buffer Management**: Extracts chunk, keeps remainder for next cycle
- **copy()**: Prevents reference issues

---

## Part 4: AudioSet Tagging Module

### Model Initialization Strategy
```python
def setup_audioset_model(self):
    possible_names = [self.model_type, self.model_type.lower(), 
                     self.model_type.upper()]
    
    for name in possible_names:
        if hasattr(audioset_models, name):
            model_class = getattr(audioset_models, name)
            break
```
- **Case-Insensitive Search**: Handles different naming conventions
- **hasattr**: Checks if attribute exists
- **getattr**: Retrieves the class object
- **Fallback Logic**: Tries common model names if specified one fails

### Model Parameter Handling
```python
try:
    self.model = model_class(
        sample_rate=32000, window_size=1024, hop_size=320,
        mel_bins=64, fmin=50, fmax=14000, classes_num=classes_num
    )
except:
    try:
        self.model = model_class(sample_rate=32000, classes_num=classes_num)
    except:
        self.model = model_class()
```
- **Progressive Fallback**: Tries full params → minimal params → defaults
- **Defensive**: Handles models with different constructor signatures
- **classes_num**: Number of AudioSet categories (527 classes)

### Checkpoint Loading
```python
checkpoint = torch.load(self.checkpoint_path, map_location=self.device)

if 'model' in checkpoint:
    state_dict = checkpoint['model']
elif 'state_dict' in checkpoint:
    state_dict = checkpoint['state_dict']
else:
    state_dict = checkpoint

self.model.load_state_dict(state_dict)
```
- **map_location**: Loads model to correct device (CPU/GPU)
- **Key Variations**: Different training frameworks save differently
- **load_state_dict**: Loads trained weights into model

### Audio Tag Generation
```python
def generate_audio_caption(self, audio_data, top_k=5):
    waveform = torch.tensor(audio_data[None, :]).to(self.device)
    
    with torch.no_grad():
        batch_output_dict = self.model(waveform, None)
    
    clipwise_output = batch_output_dict['clipwise_output'].data.cpu().numpy()[0]
    sorted_indexes = np.argsort(clipwise_output)[::-1]
```
- **[None, :]**: Adds batch dimension (1, samples)
- **clipwise_output**: Probabilities for all 527 classes
- **argsort[::-1]**: Sorts indices by probability (descending)

### Top-K Selection
```python
top_tags = []
for k in range(min(top_k, len(sorted_indexes))):
    if clipwise_output[sorted_indexes[k]] > 0.1:
        tag = self.labels[sorted_indexes[k]]
        confidence = clipwise_output[sorted_indexes[k]]
        top_tags.append(f"{tag} ({confidence:.2f})")

caption = "Audio contains: " + ", ".join(top_tags)
```
- **Threshold 0.1**: Only includes confident predictions
- **Formatting**: Includes confidence scores for transparency
- **Natural Language**: Converts tags into readable sentence

---

## Part 5: Visual Captioning Backends

### PHI3 Vision Backend
```python
if self.visual_backend.upper() == "PHI3":
    if self.advanced_mode:
        self.visual_captioner = Phi3VisionMLXCaptionerAdvanced(
            use_quantization=True,
            enable_advanced_features=True
        )
    else:
        self.visual_captioner = Phi3VisionMLXCaptioner(
            quantize_model=True,
            quantize_cache=False
        )
```
- **quantize_model=True**: Reduces model to 4-bit precision (4x smaller)
- **Advanced Features**: Context accumulation, multi-turn reasoning
- **Trade-off**: Speed vs. quality

### FastVLM Backend
```python
from llava.model.builder import load_pretrained_model

self.tokenizer, self.model, self.image_processor, self.context_len = \
    load_pretrained_model(model_path, None, model_name, device="cpu")

try:
    self.model = self.model.to("mps")
    self.device = "mps"
except:
    self.device = "cpu"
```
- **MPS**: Apple's Metal Performance Shaders (GPU acceleration on Mac)
- **Fallback**: Uses CPU if MPS unavailable
- **Four Components**: Tokenizer, model, image processor, context length

### Gemma MLX-VLM Backend
```python
class GemmaMlxVlmCaptioner:
    def caption_image(self, image_path, prompt, max_tokens=100):
        cmd = [
            'python', '-m', 'mlx_vlm.generate',
            '--model', self.model_name,
            '--max-tokens', str(max_tokens),
            '--prompt', prompt,
            '--image', image_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
```
- **Subprocess Approach**: Runs as external command
- **Isolation**: Prevents MLX errors from crashing main process
- **Timeout**: Prevents hanging on problematic images

### Output Parsing
```python
lines = output.split('\n')
model_response_lines = []
in_model_response = False

for line in lines:
    if '<start_of_turn>model' in line:
        in_model_response = True
        continue
    elif line.startswith('==========') and in_model_response:
        break
    elif in_model_response and line.strip():
        if not any(keyword in line.lower() for keyword in 
                  ['prompt:', 'generation:', 'tokens-per-sec']):
            model_response_lines.append(line.strip())
```
- **State Machine**: Tracks when inside model response
- **Filtering**: Removes metadata lines
- **Extraction**: Gets only the actual caption text

---

## Part 6: Multimodal Memory Item

### Extended Memory Class
```python
class MultimodalMemoryItem(MemoryItem):
    def __init__(self, caption="", audio_caption="", time=0.0, 
                 position=[0.0, 0.0, 0.0], theta=0.0, **kwargs):
        super().__init__(caption=caption, time=time, position=position, 
                        theta=theta, **kwargs)
        self.audio_caption = audio_caption
```
- **Inheritance**: Extends base MemoryItem class
- **audio_caption**: New field for audio information
- **super().__init__**: Calls parent class initialization
- **\*\*kwargs**: Allows additional fields to be passed through

### Serialization
```python
def to_dict(self):
    data = super().to_dict()
    data['audio_caption'] = self.audio_caption
    return data
```
- **super().to_dict()**: Gets visual, position, time fields
- **Adds**: Audio caption to dictionary
- **Purpose**: Prepares for JSON/database storage

---

## Part 7: Enhanced Memory Builder Main Class

### Initialization
```python
class EnhancedMemoryBuilder:
    def __init__(self, collection_name, db_ip, advanced_mode, 
                 enable_audio, audio_device, audio_backend, visual_backend):
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        self.visual_captioner = None
        self.audio_captioner = None
```
- **MilvusMemory**: Vector database connection
- **Deferred Initialization**: Captioners set up separately (error handling)

### Visual Captioner Test
```python
def test_visual_captioner(self):
    test_array = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    test_image = Image.fromarray(test_array)
    test_image.save(test_image_path)
    
    test_caption = self.visual_captioner.caption_image(test_image_path)
    
    if "[Error:" in test_caption or "LLVM ERROR" in test_caption:
        return False
```
- **Random Image**: Simple test case
- **64x64**: Small size for fast testing
- **Error Detection**: Checks for MLX/model errors
- **Purpose**: Prevents crashes during actual operation

### Simple Visual Caption Fallback
```python
def generate_simple_visual_caption(self, image_path, position, theta):
    x, y, z = position
    
    if abs(x) < 0.1 and abs(y) < 0.1:
        return "Robot at starting position, capturing camera view"
    elif x > 0.5:
        return f"Robot exploring forward area ({x:.2f}, {y:.2f})"
```
- **Rule-Based**: Uses position to generate description
- **Fallback**: Used when ML models fail
- **Context-Aware**: Different messages for different locations

---

## Part 8: Processing Threads

### Visual Processing Thread
```python
def visual_processing_thread(self):
    while self.running:
        data_files = list(self.data_dir.glob("memory_*.json"))
        
        if not data_files:
            print("No data files found. Terminating...")
            self.running = False
            break
```
- **Polling**: Checks for new files periodically
- **glob("memory_*.json")**: Pattern matching for memory files
- **Termination Logic**: Stops when no work remains

### Timestamp Synchronization
```python
if self.simulation_start_time is None:
    self.simulation_start_time = timestamp
    print(f"Simulation start time set to: {timestamp}")

simulation_elapsed = timestamp - self.simulation_start_time
estimated_system_time = self.system_start_time + simulation_elapsed
```
- **First File**: Sets baseline timestamp
- **Elapsed Calculation**: How much simulation time has passed
- **Time Conversion**: Maps simulation time → system time
- **Purpose**: Synchronizes with audio (which uses system time)

### Visual Caption Generation with Error Handling
```python
try:
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    
    visual_caption = self.visual_captioner.caption_image(image_path)
    
    if "[Error:" in visual_caption or "LLVM ERROR" in visual_caption:
        raise Exception(f"Model inference error: {visual_caption}")
        
except Exception as e:
    print(f"Visual captioning failed: {e}")
    visual_caption = self.generate_simple_visual_caption(image_path, 
                                                         position, theta)
    self.visual_captioner = None
```
- **MPS Cache Clear**: Prevents memory accumulation on Apple Silicon
- **Error String Detection**: Catches model failures
- **Graceful Degradation**: Falls back to simple captions
- **Disable on Error**: Prevents repeated failures

### Memory Queue Structure
```python
memory_data = {
    'visual_caption': visual_caption,
    'timestamp': estimated_system_time,
    'original_sim_time': timestamp,
    'position': position,
    'theta': theta,
    'type': 'visual'
}

self.memory_queue.put(memory_data)
```
- **Dictionary Format**: Easy to serialize/deserialize
- **Dual Timestamps**: System time (for matching) + sim time (for storage)
- **Type Tag**: Identifies as visual data
- **Queue**: Thread-safe communication between threads

### Audio Processing Thread
```python
def audio_processing_thread(self):
    while self.running:
        audio_capture_time = time.time()
        audio_chunk = self.audio_captioner.capture_audio_chunk()
        
        if audio_chunk is not None:
            audio_timestamp = audio_capture_time - self.audio_captioner.chunk_duration
```
- **Capture Time**: Records when capture completes
- **Timestamp Adjustment**: Subtracts chunk duration to get start time
- **Reason**: Audio represents previous 10 seconds, not current moment

### Audio Caption Generation
```python
start_time = time.time()
audio_caption = self.audio_captioner.generate_audio_caption(audio_chunk)
end_time = time.time()

print(f"Audio caption generated in {end_time - start_time:.2f}s: {audio_caption}")
```
- **Timing**: Monitors performance
- **Feedback**: Shows what was detected
- **Purpose**: Helps debug audio quality issues

---

## Part 9: Memory Integration Thread

### Buffer Management
```python
def memory_integration_thread(self):
    visual_buffer = {}  # timestamp -> visual_data
    audio_buffer = deque(maxlen=5000)  # Recent audio captions
```
- **visual_buffer**: Dict for O(1) timestamp lookup
- **audio_buffer**: Deque with automatic size limit
- **maxlen=5000**: Keeps ~14 hours of audio at 10s intervals
- **Purpose**: Hold data until matching pair found

### Data Type Routing
```python
memory_data = self.memory_queue.get(timeout=1.0)

if memory_data['type'] == 'visual':
    visual_buffer[timestamp] = memory_data
    print(f"Visual data buffered for timestamp {timestamp}")
    
elif memory_data['type'] == 'audio':
    audio_buffer.append(memory_data)
    self.process_pending_visual_items(visual_buffer, audio_buffer)
```
- **timeout=1.0**: Prevents indefinite blocking
- **Visual**: Store and wait for audio
- **Audio**: Triggers matching process
- **Strategy**: Audio is trigger because it's less frequent

### Pending Visual Item Processing
```python
def process_pending_visual_items(self, visual_buffer, audio_buffer):
    processed_timestamps = []
    
    for timestamp, visual_data in visual_buffer.items():
        matching_audio = None
        time_window = 15.0
```
- **Iteration**: Checks all pending visual items
- **time_window**: Tolerance for timestamp matching
- **15 seconds**: Generous buffer for async capture timing

### Best Match Selection
```python
best_match = None
best_time_diff = float('inf')

for audio_data in audio_buffer:
    time_diff = abs(audio_data['timestamp'] - timestamp)
    
    if time_diff <= time_window and time_diff < best_time_diff:
        best_match = audio_data
        best_time_diff = time_diff
```
- **Linear Search**: Checks all audio items
- **Closest Match**: Minimizes time difference
- **Within Window**: Only considers nearby timestamps
- **Updates**: Keeps track of best candidate

### Memory Item Creation
```python
audio_caption = matching_audio['audio_caption'] if matching_audio else ""

memory_item = MultimodalMemoryItem(
    caption=visual_data['visual_caption'],
    audio_caption=audio_caption,
    time=visual_data.get('original_sim_time', timestamp),
    position=visual_data['position'],
    theta=visual_data['theta']
)
```
- **Conditional Caption**: Empty string if no audio match
- **original_sim_time**: Uses simulation time for storage
- **Complete Context**: Visual + audio + spatial information

### Database Insertion
```python
self.memory.insert(memory_item)
self.processed_count += 1

print(f"✓ Multimodal memory item {self.processed_count} inserted")
print(f"   Visual: {visual_data['visual_caption'][:50]}...")
if audio_caption:
    print(f"   Audio: {audio_caption[:50]}...")
```
- **insert()**: Stores in MilvusDB vector database
- **Counter**: Tracks progress
- **Truncated Output**: First 50 chars for readability
- **Conditional**: Only shows audio if present

### Buffer Cleanup
```python
processed_timestamps.append(timestamp)

for timestamp in processed_timestamps:
    del visual_buffer[timestamp]
```
- **Tracking**: Remembers what was processed
- **Deletion**: Removes from buffer to prevent reprocessing
- **Memory Management**: Prevents buffer growth

---

## Part 10: Robot Controller Integration

### Memory Data Capture (from controller)
```python
if self.should_capture():
    current_time = time.time()
    position = self.get_robot_position()
    theta = self.get_robot_orientation()
    image_path = self.capture_image()
    audio_info = self.capture_audio_info()
    
    if image_path:
        self.save_memory_data(image_path, position, theta, 
                             current_time, audio_info)
```
- **should_capture()**: Rate limiting (e.g., every 1 second)
- **Coordinates**: Captures current pose
- **Image**: Camera snapshot
- **Synchronized**: All data has same timestamp

### Memory Data File Format
```python
memory_data = {
    'image_path': image_path,
    'position': position,
    'theta': theta,
    'timestamp': timestamp,
    'audio_info': audio_info,
    'capture_count': self.capture_count,
    'robot_type': 'Pioneer 3-AT',
    'session_start_time': self.start_time,
    'auto_mode': self.auto_mode,
    'navigation_active': self.navigation_mode
}

with open(memory_path, 'w') as f:
    json.dump(memory_data, f, indent=2)
```
- **JSON Format**: Human-readable, easy to parse
- **Metadata**: Context about robot state
- **File-Based**: Loose coupling between controller and builder
- **Atomic**: Each memory is independent file

---

## Summary: Complete Data Flow

1. **Robot Controller** captures image + sensor data → saves JSON file
2. **Visual Thread** detects file → generates caption → queues with timestamp
3. **Audio Thread** continuously captures audio → generates caption → queues with timestamp
4. **Integration Thread** matches visual+audio by timestamp → creates MultimodalMemoryItem
5. **Database** stores memory with visual caption, audio caption, position, orientation

**Key Design Decisions:**
- **Asynchronous**: Three independent threads for parallelism
- **Buffer-Based**: Tolerates timing differences between modalities
- **Graceful Degradation**: Falls back when ML models fail
- **File-Based IPC**: Controller and builder loosely coupled
- **Timestamp Synchronization**: Maps simulation time to real time for matching