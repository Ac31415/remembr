#!/usr/bin/env python3
"""
Enhanced Phi-3-Vision-MLX Memory Builder with Audio Captioning
Integrates real-time audio captioning using ACT model alongside visual captioning
"""

import sys
import os
import time
import threading
import queue
import json
import traceback
import numpy as np
import csv
import librosa
import torch
import pyaudio
from pathlib import Path
from PIL import Image
from datetime import datetime
from collections import deque

import subprocess
import tempfile
import shutil
import wave


# Pause/resume flag file for memory builder audio recording control
PAUSE_FLAG_PATH = "/tmp/webots_memory/controller_paused.flag"


def show_disk_space(hf_model_dir="/Volumes/USB DISK/huggingface"):
    """Show available disk space on the drive containing HuggingFace models.
    
    Args:
        hf_model_dir: Path to the HuggingFace models directory on the external drive.
    """
    print(f"\n📊 Disk Space Check for External Drive ({hf_model_dir})")
    print("-" * 60)
    
    if not os.path.isdir(hf_model_dir):
        print(f"  ⚠️  HF model directory not found: {hf_model_dir}")
        print(f"  Note: The --show-disk-space option checks space on the drive where")
        print(f"  HuggingFace models are stored (default: /Volumes/USB DISK/huggingface)")
        print()
        return
    
    # Get disk space info using shutil.disk_usage
    try:
        total, used, free = shutil.disk_usage(hf_model_dir)
        
        # Convert to human-readable
        def human_readable(bytes_val):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f} PB"
        
        total_hr = human_readable(total)
        used_hr = human_readable(used)
        free_hr = human_readable(free)
        capacity_pct = (used / total) * 100
        
        print(f"  Filesystem:    {hf_model_dir}")
        print(f"  Total Size:    {total_hr}")
        print(f"  Used:          {used_hr}")
        print(f"  Available:     {free_hr}")
        print(f"  Capacity:      {capacity_pct:.1f}%")
        
        # Threshold warnings
        free_gb = free / (1024 ** 3)
        if free_gb < 10:
            print(f"\n  ⚠️  WARNING: Less than 10 GB available on external drive!")
        elif free_gb < 50:
            print(f"\n  ⚠️  NOTE: Less than 50 GB available on external drive.")
        
        # Also show total model directory size
        print(f"\n  HF model directory size:")
        try:
            dir_size = sum(
                f.stat().st_size for f in Path(hf_model_dir).rglob('*') if f.is_file()
            )
            print(f"    {hf_model_dir}: {human_readable(dir_size)}")
        except Exception as e:
            print(f"    Could not determine directory size: {e}")
            
    except Exception as e:
        print(f"  ❌ Could not retrieve disk space info: {e}")
    
    print()

# Add paths
remembr_path = "/Users/wen-chungcheng/remembr"
act_path = "/Users/wen-chungcheng/ACT"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)
if act_path not in sys.path:
    sys.path.insert(0, act_path)
    
audioset_tagging_cnn_path = "/Users/wen-chungcheng/audioset_tagging_cnn"
if audioset_tagging_cnn_path not in sys.path:
    sys.path.insert(0, audioset_tagging_cnn_path)

# Import ReMEmbR components
from remembr.memory.memory_multimodal import MemoryItem
from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner, Phi3VisionMLXCaptionerAdvanced

# Import ACT components
from tools.config_loader import get_config
from tools.utils import *
from tools.file_io import load_pickle_file
from models.TransModel import ACT

# # Import AudioSet Tagging CNN components
# from pytorch.models import *
# from pytorch.inference import audio_tagging
# from utils import config as audioset_config

# NEW (with explicit path handling):
# AudioSet imports with path context
def import_audioset_modules():
    """Import AudioSet modules with proper path context"""
    import sys
    import os
    import importlib.util
    
    # Store original path and working directory
    original_path = sys.path.copy()
    original_cwd = os.getcwd()
    
    try:
        # Change to AudioSet directory for relative imports
        audioset_path = "/Users/wen-chungcheng/audioset_tagging_cnn"
        os.chdir(audioset_path)
        print(f"[AudioSet Import] Changed to AudioSet directory: {os.getcwd()}")
        
        # Add AudioSet paths to front of sys.path
        audioset_pytorch_path = os.path.join(audioset_path, "pytorch")
        audioset_utils_path = os.path.join(audioset_path, "utils")
        
        # Insert at beginning to take precedence
        sys.path.insert(0, audioset_path)
        sys.path.insert(0, audioset_pytorch_path)
        sys.path.insert(0, audioset_utils_path)
        
        print(f"[AudioSet Import] sys.path updated with AudioSet paths")
        
        # Import modules directly
        spec = importlib.util.spec_from_file_location("audioset_models", os.path.join(audioset_pytorch_path, "models.py"))
        audioset_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audioset_models)
        
        spec = importlib.util.spec_from_file_location("audioset_pytorch_utils", os.path.join(audioset_pytorch_path, "pytorch_utils.py"))
        audioset_pytorch_utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audioset_pytorch_utils)
        
        spec = importlib.util.spec_from_file_location("audioset_config", os.path.join(audioset_utils_path, "config.py"))
        audioset_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audioset_config)
        
        # Debug: Print available models
        print(f"[AudioSet Import] models module type: {type(audioset_models)}")
        model_classes = []
        for name in dir(audioset_models):
            if not name.startswith('_'):
                attr = getattr(audioset_models, name)
                if isinstance(attr, type) and hasattr(attr, '__init__'):
                    model_classes.append(name)
        
        print(f"[AudioSet Import] Available model classes: {model_classes}")
        
        return audioset_models, audioset_pytorch_utils, audioset_config
        
    finally:
        # Restore original path and working directory
        sys.path = original_path
        os.chdir(original_cwd)

# Import AudioSet modules safely with better error handling
try:
    audioset_models, audioset_pytorch_utils, audioset_config = import_audioset_modules()
    AUDIOSET_AVAILABLE = True
    print("[AudioSet Import] ✓ AudioSet modules imported successfully")
    
    # Debug: Check what models are available
    model_names = [name for name in dir(audioset_models) if not name.startswith('_')]
    print(f"[AudioSet Import] Available model classes: {model_names}")
    
except Exception as e:
    print(f"[AudioSet Import] ❌ Failed to import AudioSet modules: {e}")
    import traceback
    traceback.print_exc()
    audioset_models = None
    audioset_pytorch_utils = None
    audioset_config = None
    AUDIOSET_AVAILABLE = False

class AudioCaptioningModule:
    """Audio captioning module using ACT model"""
    
    def __init__(self, device_name="BlackHole", sample_rate=44100, chunk_duration=10.0):
        print("[Audio Module] Initializing ACT model for audio captioning...")
        
        # Audio parameters
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Audio capture setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.device_index = self.find_audio_device(device_name)
        
        # Audio buffer
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # Setup ACT model
        self.setup_act_model()
        
        print("[Audio Module] ✓ Audio captioning module ready")
    
    def find_audio_device(self, device_name):
        """Find audio device by name"""
        print(f"[Audio Module] Looking for audio device: {device_name}")
        
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if (device_name.lower() in device_info['name'].lower() and 
                    device_info['maxInputChannels'] > 0):
                    print(f"[Audio Module] ✓ Found device: {device_info['name']} (index {i})")
                    return i
            except:
                continue
        
        print(f"[Audio Module] Device '{device_name}' not found, using default input")
        try:
            default_device = self.audio.get_default_input_device_info()
            print(f"[Audio Module] ✓ Using default: {default_device['name']}")
            return default_device['index']
        except:
            print("[Audio Module] ❌ No suitable input device found!")
            return None
    
    def setup_act_model(self):
        """Setup ACT model for inference"""
        try:
            # Store original working directory
            original_cwd = os.getcwd()
            
            # Change to ACT directory before loading config
            act_dir = "/Users/wen-chungcheng/ACT"
            if not os.path.exists(act_dir):
                raise FileNotFoundError(f"ACT directory not found: {act_dir}")
            
            os.chdir(act_dir)
            print(f"[Audio Module] Changed to ACT directory: {os.getcwd()}")
            
            # Check for settings file
            settings_path = os.path.join(act_dir, "settings", "settings.yaml")
            if not os.path.exists(settings_path):
                # Create a minimal settings file
                os.makedirs(os.path.join(act_dir, "settings"), exist_ok=True)
                minimal_settings = """
    # Minimal ACT settings for audio captioning
    model:
    name: "ACT"
    vocab_size: 50000
    
    training:
    batch_size: 32
    learning_rate: 0.001

    paths:
    vocabulary: "data/vocabulary.pkl"
    eval_model: "models/act_model.pth"
    """
                with open(settings_path, 'w') as f:
                    f.write(minimal_settings)
                print(f"[Audio Module] Created minimal settings file: {settings_path}")
            
            # Load configuration
            sys.path.append('/Users/wen-chungcheng/ACT')
            from tools.config_loader import get_config
            # from act_config import get_config  # Assuming this is the import path
            self.config = get_config()
            self.config.mode = 'eval'
            
            # Setup device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"[Audio Module] Using device: {self.device}")
            
            # Load vocabulary (create dummy if not exists)
            vocab_path = self.config.path.vocabulary
            if not os.path.exists(vocab_path):
                # Create dummy vocabulary
                dummy_vocab = ['<sos>', '<eos>', '<pad>', '<unk>'] + [f'word_{i}' for i in range(1000)]
                os.makedirs(os.path.dirname(vocab_path), exist_ok=True)
                import pickle
                with open(vocab_path, 'wb') as f:
                    pickle.dump(dummy_vocab, f)
                print(f"[Audio Module] Created dummy vocabulary: {vocab_path}")
            
            # Load vocabulary
            self.words_list = load_pickle_file(self.config.path.vocabulary)
            self.ntokens = len(self.words_list)
            self.sos_ind = self.words_list.index('<sos>')
            self.eos_ind = self.words_list.index('<eos>')
            
            # Initialize and load model
            # from act_model import ACT  # Assuming this is the import path
            from models.TransModel import ACT
            self.model = ACT(self.config, self.ntokens)
            self.model.to(self.device)
            self.model.eval()
            
            # Load model weights (create dummy if not exists)
            model_path = self.config.path.eval_model
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model'])
                print("[Audio Module] ✓ ACT model loaded successfully")
            else:
                print("[Audio Module] ⚠ Model weights not found, using randomly initialized model")
            
            # Change back to original directory
            os.chdir(original_cwd)
            
        except Exception as e:
            # Change back to original directory on error
            try:
                os.chdir(original_cwd)
            except:
                pass
            print(f"[Audio Module] ❌ Failed to load ACT model: {e}")
            raise
    
    def setup_audio_stream(self):
        """Setup audio input stream"""
        if self.device_index is None:
            return False
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            print("[Audio Module] ✓ Audio stream setup successful")
            return True
        except Exception as e:
            print(f"[Audio Module] ❌ Audio stream setup failed: {e}")
            return False
    
    def preprocess_audio_for_act(self, audio_data):
        """Preprocess audio for ACT model inference"""
        target_sr = self.config.wav.sr  # 32000 Hz
        target_length = 10 * target_sr
        
        # Resample if needed
        if self.sample_rate != target_sr:
            audio_data = librosa.resample(audio_data, orig_sr=self.sample_rate, target_sr=target_sr)
        
        # Pad or truncate to exactly 10 seconds
        if len(audio_data) <= target_length:
            audio_data = np.concatenate((audio_data, np.zeros(target_length - len(audio_data), dtype=np.float32)))
        else:
            audio_data = audio_data[:target_length]
        
        # Extract mel-spectrogram features
        feature = librosa.feature.melspectrogram(
            y=audio_data,
            sr=target_sr,
            n_fft=self.config.wav.window_length,
            hop_length=self.config.wav.hop_length,
            n_mels=self.config.wav.n_mels
        )
        
        # Convert to log scale and transpose
        feature = librosa.power_to_db(feature).T.astype(np.float32)
        feature = feature[:-1, :]  # Remove last frame
        
        return torch.tensor(feature, dtype=torch.float32).unsqueeze(0)
    
    def generate_audio_caption(self, audio_data, beam_size=3):
        """Generate caption for audio data using ACT model"""
        try:
            # Preprocess audio
            src = self.preprocess_audio_for_act(audio_data).to(self.device)
            
            # Run inference
            with torch.no_grad():
                if beam_size == 1:
                    output = greedy_decode(self.model, src, sos_ind=self.sos_ind, eos_ind=self.eos_ind)
                else:
                    from tools.beam import beam_decode
                    output = beam_decode(src, self.model, self.sos_ind, self.eos_ind, beam_width=beam_size)
                
                # Decode output to caption
                output = output[0, 1:].cpu().numpy()
                
                # Convert indices to words
                caption_words = []
                for idx in output:
                    if idx == self.eos_ind:
                        break
                    caption_words.append(self.words_list[idx])
                
                caption = ' '.join(caption_words)
                return caption
                
        except Exception as e:
            print(f"[Audio Module] ❌ Error generating caption: {e}")
            return f"[Audio Error: {str(e)}]"
    
    def capture_audio_chunk(self):
        """Capture and return a 10-second audio chunk"""
        if not self.stream:
            return None
        
        try:
            # Read until we have enough data for a 10-second chunk
            while len(self.audio_buffer) < self.chunk_size:
                audio_data = self.stream.read(1024, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_array])
            
            # Extract chunk and update buffer
            chunk = self.audio_buffer[:self.chunk_size].copy()
            self.audio_buffer = self.audio_buffer[self.chunk_size:]
            
            return chunk
            
        except Exception as e:
            print(f"[Audio Module] Error capturing audio: {e}")
            return None
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            
class AudioSetTaggingModule:
    """Audio tagging module using AudioSet CNN models"""
    
    def __init__(self, model_type="Cnn14", checkpoint_path=None, device_name="BlackHole", sample_rate=32000, chunk_duration=10.0):
        print(f"[AudioSet Module] Initializing {model_type} model for audio tagging...")
        
        self.model_type = model_type
        self.checkpoint_path = checkpoint_path or "/Users/wen-chungcheng/audioset_tagging_cnn/Cnn14_mAP=0.431.pth"
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Audio capture setup (same as ACT)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.device_index = self.find_audio_device(device_name)
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # Setup AudioSet model
        self.setup_audioset_model()
        
    def find_audio_device(self, device_name):
        """Find audio device by name"""
        print(f"[AudioSet Module] Looking for audio device: {device_name}")
        
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if (device_name.lower() in device_info['name'].lower() and 
                    device_info['maxInputChannels'] > 0):
                    print(f"[AudioSet Module] ✓ Found device: {device_info['name']} (index {i})")
                    return i
            except:
                continue
        
        print(f"[AudioSet Module] Device '{device_name}' not found, using default input")
        try:
            default_device = self.audio.get_default_input_device_info()
            print(f"[AudioSet Module] ✓ Using default: {default_device['name']}")
            return default_device['index']
        except:
            print("[AudioSet Module] ❌ No suitable input device found!")
            return None
        
    def setup_audioset_model(self):
        """Setup AudioSet model for inference"""
        try:
            if not AUDIOSET_AVAILABLE:
                raise ImportError("AudioSet modules not available")
                
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"[AudioSet Module] Using device: {self.device}")
            
            # Model parameters
            classes_num = audioset_config.classes_num
            self.labels = audioset_config.labels
            
            print(f"[AudioSet Module] Classes: {classes_num}, Labels: {len(self.labels)}")
            
            # Debug: Check what's actually in the models module
            print(f"[AudioSet Module] Models module contents: {[name for name in dir(audioset_models) if not name.startswith('_')]}")
            
            # Check if model exists with different possible names
            model_class = None
            possible_names = [self.model_type, self.model_type.lower(), self.model_type.upper()]
            
            for name in possible_names:
                if hasattr(audioset_models, name):
                    model_class = getattr(audioset_models, name)
                    print(f"[AudioSet Module] Found model class: {name}")
                    break
            
            if model_class is None:
                # List all available classes for debugging
                available = []
                for attr_name in dir(audioset_models):
                    if not attr_name.startswith('_'):
                        attr = getattr(audioset_models, attr_name)
                        if isinstance(attr, type):
                            available.append(attr_name)
                
                print(f"[AudioSet Module] Available model classes: {available}")
                
                # Try common AudioSet model names
                common_names = ['Cnn14', 'Cnn10', 'Cnn6', 'ResNet22', 'ResNet38', 'ResNet54', 'MobileNetV1', 'MobileNetV2']
                for name in common_names:
                    if hasattr(audioset_models, name):
                        model_class = getattr(audioset_models, name)
                        self.model_type = name
                        print(f"[AudioSet Module] Using available model: {name}")
                        break
                
                if model_class is None:
                    # If still no model found, try to look inside the models module for nested classes
                    if hasattr(audioset_models, 'models'):
                        nested_models = audioset_models.models
                        print(f"[AudioSet Module] Checking nested models: {[name for name in dir(nested_models) if not name.startswith('_')]}")
                        
                        for name in common_names:
                            if hasattr(nested_models, name):
                                model_class = getattr(nested_models, name)
                                self.model_type = name
                                print(f"[AudioSet Module] Using nested model: {name}")
                                break
                    
                    if model_class is None:
                        raise AttributeError(f"No suitable model found. Available: {available}")
            
            # Initialize model with proper parameters
            try:
                # Try with all parameters
                self.model = model_class(
                    sample_rate=32000, 
                    window_size=1024, 
                    hop_size=320, 
                    mel_bins=64, 
                    fmin=50, 
                    fmax=14000, 
                    classes_num=classes_num
                )
                print(f"[AudioSet Module] Model initialized with full parameters")
            except Exception as e:
                print(f"[AudioSet Module] Full parameters failed: {e}")
                try:
                    # Try with minimal parameters
                    self.model = model_class(sample_rate=32000, classes_num=classes_num)
                    print(f"[AudioSet Module] Model initialized with minimal parameters")
                except Exception as e2:
                    print(f"[AudioSet Module] Minimal parameters failed: {e2}")
                    try:
                        # Try with no parameters
                        self.model = model_class()
                        print(f"[AudioSet Module] Model initialized with default parameters")
                    except Exception as e3:
                        raise Exception(f"All model initialization attempts failed: {e3}")
            
            # Load checkpoint
            if os.path.exists(self.checkpoint_path):
                print(f"[AudioSet Module] Loading checkpoint: {self.checkpoint_path}")
                checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
                
                # Handle different checkpoint formats
                if 'model' in checkpoint:
                    state_dict = checkpoint['model']
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                else:
                    state_dict = checkpoint
                
                self.model.load_state_dict(state_dict)
                print("[AudioSet Module] ✓ Checkpoint loaded successfully")
            else:
                print(f"[AudioSet Module] ⚠ Checkpoint not found: {self.checkpoint_path}")
                print("[AudioSet Module] Using randomly initialized model")
            
            self.model.to(self.device)
            self.model.eval()
            
            print("[AudioSet Module] ✓ AudioSet model loaded successfully")
            
        except Exception as e:
            print(f"[AudioSet Module] ❌ Failed to load AudioSet model: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_audio_caption(self, audio_data, top_k=5):
        """Generate audio tags using AudioSet model"""
        try:
            # Preprocess audio (resample if needed)
            if len(audio_data) != self.sample_rate * 10:  # Ensure 10 seconds at 32kHz
                audio_data = librosa.resample(audio_data, orig_sr=self.sample_rate, target_sr=32000)
                if len(audio_data) > 32000 * 10:
                    audio_data = audio_data[:32000 * 10]
                elif len(audio_data) < 32000 * 10:
                    audio_data = np.pad(audio_data, (0, 32000 * 10 - len(audio_data)))
            
            # Convert to tensor
            waveform = torch.tensor(audio_data[None, :], dtype=torch.float32).to(self.device)
            
            # Forward pass
            with torch.no_grad():
                batch_output_dict = self.model(waveform, None)
            
            clipwise_output = batch_output_dict['clipwise_output'].data.cpu().numpy()[0]
            sorted_indexes = np.argsort(clipwise_output)[::-1]
            
            # Generate caption from top predictions
            top_tags = []
            for k in range(min(top_k, len(sorted_indexes))):
                if clipwise_output[sorted_indexes[k]] > 0.1:  # Threshold
                    tag = self.labels[sorted_indexes[k]]
                    confidence = clipwise_output[sorted_indexes[k]]
                    top_tags.append(f"{tag} ({confidence:.2f})")
            
            caption = "Audio contains: " + ", ".join(top_tags) if top_tags else "Audio with unidentified sounds"
            return caption
            
        except Exception as e:
            print(f"[AudioSet Module] ❌ Error generating caption: {e}")
            return f"[AudioSet Error: {str(e)}]"
    
    # Same methods as ACT: setup_audio_stream, capture_audio_chunk, cleanup
    
    def setup_audio_stream(self):
        """Setup audio input stream"""
        if self.device_index is None:
            return False
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            print("[Audio Module] ✓ Audio stream setup successful")
            return True
        except Exception as e:
            print(f"[Audio Module] ❌ Audio stream setup failed: {e}")
            return False
        
    def capture_audio_chunk(self):
        """Capture and return a 10-second audio chunk"""
        if not self.stream:
            return None
        
        try:
            # Read until we have enough data for a 10-second chunk
            while len(self.audio_buffer) < self.chunk_size:
                audio_data = self.stream.read(1024, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_array])
            
            # Extract chunk and update buffer
            chunk = self.audio_buffer[:self.chunk_size].copy()
            self.audio_buffer = self.audio_buffer[self.chunk_size:]
            
            return chunk
            
        except Exception as e:
            print(f"[Audio Module] Error capturing audio: {e}")
            return None
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            
            
class FastVLMCaptioner:
    """FastVLM captioner using llava-fastvithd model"""
    
    def __init__(self, model_path="/Users/wen-chungcheng/ml-fastvlm/checkpoints/llava-fastvithd_0.5b_stage3"):
        print("[FastVLM Captioner] Initializing FastVLM model...")
        
        # Add FastVLM to path
        fastvlm_path = "/Users/wen-chungcheng/ml-fastvlm"
        if fastvlm_path not in sys.path:
            sys.path.insert(0, fastvlm_path)
        
        # Import FastVLM components
        from llava.utils import disable_torch_init
        from llava.conversation import conv_templates
        from llava.model.builder import load_pretrained_model
        from llava.mm_utils import tokenizer_image_token, process_images, get_model_name_from_path
        from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
        
        self.model_path = model_path
        self.conv_templates = conv_templates
        self.tokenizer_image_token = tokenizer_image_token
        self.process_images = process_images
        self.get_model_name_from_path = get_model_name_from_path
        self.IMAGE_TOKEN_INDEX = IMAGE_TOKEN_INDEX
        self.DEFAULT_IMAGE_TOKEN = DEFAULT_IMAGE_TOKEN
        self.DEFAULT_IM_START_TOKEN = DEFAULT_IM_START_TOKEN
        self.DEFAULT_IM_END_TOKEN = DEFAULT_IM_END_TOKEN
        
        # Load model
        disable_torch_init()
        model_name = self.get_model_name_from_path(model_path)
        
        try:
            self.tokenizer, self.model, self.image_processor, self.context_len = load_pretrained_model(
                model_path, None, model_name, device="cpu"
            )
            # Try to move to MPS if available
            try:
                self.model = self.model.to("mps")
                self.device = "mps"
            except:
                self.device = "cpu"
            
            self.model.eval()
            print(f"[FastVLM Captioner] ✓ Model loaded on {self.device}")
            
        except Exception as e:
            print(f"[FastVLM Captioner] ❌ Failed to load model: {e}")
            raise
    
    def caption_image(self, image_path, prompt="Describe the image.", conv_mode="qwen_2"):
        """Generate caption for image using FastVLM"""
        try:
            # Construct prompt
            qs = prompt
            if self.model.config.mm_use_im_start_end:
                qs = self.DEFAULT_IM_START_TOKEN + self.DEFAULT_IMAGE_TOKEN + self.DEFAULT_IM_END_TOKEN + '\n' + qs
            else:
                qs = self.DEFAULT_IMAGE_TOKEN + '\n' + qs
            
            conv = self.conv_templates[conv_mode].copy()
            conv.append_message(conv.roles[0], qs)
            conv.append_message(conv.roles[1], None)
            prompt_text = conv.get_prompt()
            
            # Set pad token
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
            self.model.generation_config.pad_token_id = self.tokenizer.pad_token_id
            
            # Tokenize prompt
            input_ids = self.tokenizer_image_token(
                prompt_text, self.tokenizer, self.IMAGE_TOKEN_INDEX, return_tensors='pt'
            ).unsqueeze(0).to(self.device)
            
            # Load and preprocess image
            from PIL import Image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.process_images([image], self.image_processor, self.model.config)[0]
            
            # Generate caption
            with torch.inference_mode():
                output_ids = self.model.generate(
                    input_ids,
                    images=image_tensor.unsqueeze(0).to(self.device, dtype=torch.float16),
                    image_sizes=[image.size],
                    do_sample=False,
                    max_new_tokens=256,
                    use_cache=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
                
                # Decode output
                output_text = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
                
                # Extract just the response part
                if conv.roles[1] in output_text:
                    caption = output_text.split(conv.roles[1])[-1].strip()
                else:
                    caption = output_text
                
                return caption
                
        except Exception as e:
            print(f"[FastVLM Captioner] ❌ Error generating caption: {e}")
            return f"[FastVLM Error: {str(e)}]"
        
        
class GemmaMlxVlmCaptioner:
    """Gemma MLX-VLM captioner using mlx-community/gemma-3n-E2B-it-4bit model"""
    
    def __init__(self, model_name="mlx-community/gemma-3n-E2B-it-4bit"):
        print("[Gemma MLX-VLM Captioner] Initializing Gemma MLX-VLM model...")
        
        self.model_name = model_name
        
        # Check if mlx_vlm is available
        try:
            result = subprocess.run(['python', '-m', 'mlx_vlm.generate', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise ImportError("mlx_vlm module not found")
            print("[Gemma MLX-VLM Captioner] ✓ mlx_vlm module available")
        except Exception as e:
            print(f"[Gemma MLX-VLM Captioner] ❌ mlx_vlm not available: {e}")
            raise ImportError(f"mlx_vlm module not available: {e}")
        
        # Test model availability by trying to load it (downloads if missing)
        try:
            test_result = subprocess.run([
                'python', '-m', 'mlx_vlm.generate',
                '--model', self.model_name,
                '--help'
            ], stdout=None, stderr=subprocess.PIPE, text=True, timeout=600)  # 10 minutes for download, shows progress bar
            
            if test_result.returncode == 0:
                print(f"[Gemma MLX-VLM Captioner] ✓ Model {self.model_name} is accessible")
            else:
                print(f"[Gemma MLX-VLM Captioner] ⚠ Model test returned code {test_result.returncode}")
                
        except Exception as e:
            print(f"[Gemma MLX-VLM Captioner] ⚠ Model test failed: {e}")
        
        print(f"[Gemma MLX-VLM Captioner] ✓ Gemma MLX-VLM captioner ready with model {self.model_name}")
    
    def caption_image(self, image_path, prompt="Describe this image.", max_tokens=100, temperature=0.0):
        """Generate caption for image using Gemma MLX-VLM"""
        try:
            # Verify image exists
            if not os.path.exists(image_path):
                return f"[Gemma MLX-VLM Error: Image not found at {image_path}]"
            
            # Build command
            cmd = [
                'python', '-m', 'mlx_vlm.generate',
                '--model', self.model_name,
                '--max-tokens', str(max_tokens),
                '--temperature', str(temperature),
                '--prompt', prompt,
                '--image', image_path
            ]
            
            print(f"[Gemma MLX-VLM Captioner] Running inference on {os.path.basename(image_path)}...")
            
            # Run inference with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=None
            )
            
            # Replace the output parsing section with:

            if result.returncode == 0:
                # Parse output to extract just the model's response
                output = result.stdout.strip()
                
                if output:
                    # Look for the model's response between markers
                    lines = output.split('\n')
                    
                    # Strategy 1: Look for "Assistant:" marker (used by SmolVLM, Qwen, etc.)
                    for i, line in enumerate(lines):
                        if 'Assistant:' in line:
                            # Extract everything after "Assistant:" on this line
                            response_parts = [line.split('Assistant:', 1)[1].strip()]
                            # Continue collecting until we hit a separator or stats line
                            for j in range(i + 1, len(lines)):
                                l = lines[j].strip()
                                if l.startswith('==========') or 'tokens-per-sec' in l or 'Peak memory:' in l:
                                    break
                                if l:
                                    response_parts.append(l)
                            if response_parts:
                                return ' '.join(response_parts)
                    
                    # Strategy 2: Look for <start_of_turn>model marker (used by some models)
                    model_response_lines = []
                    in_model_response = False
                    
                    for line in lines:
                        if '<start_of_turn>model' in line:
                            in_model_response = True
                            continue
                        elif line.startswith('==========') and in_model_response:
                            # End of model response
                            break
                        elif in_model_response and line.strip():
                            # Skip empty lines and lines that look like metadata
                            if not any(keyword in line.lower() for keyword in ['prompt:', 'generation:', 'peak memory:', 'tokens-per-sec']):
                                model_response_lines.append(line.strip())
                    
                    if model_response_lines:
                        return ' '.join(model_response_lines)
                    
                    # Fallback: extract everything between the first and second "=====" markers
                    start_marker = None
                    end_marker = None
                    
                    for i, line in enumerate(lines):
                        if line.startswith('==========') and start_marker is None:
                            start_marker = i + 1
                        elif line.startswith('==========') and start_marker is not None:
                            end_marker = i
                            break
                    
                    if start_marker is not None and end_marker is not None:
                        response_lines = []
                        for i in range(start_marker, end_marker):
                            line = lines[i].strip()
                            if line and not any(keyword in line.lower() for keyword in ['prompt:', 'generation:', 'peak memory:', 'tokens-per-sec', 'files:']):
                                response_lines.append(line)
                        
                        if response_lines:
                            return ' '.join(response_lines)
                    
                    # Final fallback
                    return output
                else:
                    return "[Gemma MLX-VLM: No output generated]"
            
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"[Gemma MLX-VLM Captioner] ❌ Inference failed: {error_msg}")
                return f"[Gemma MLX-VLM Error: {error_msg}]"
                
        except subprocess.TimeoutExpired:
            print(f"[Gemma MLX-VLM Captioner] ❌ Inference timeout")
            return "[Gemma MLX-VLM Error: Inference timeout]"
        except Exception as e:
            print(f"[Gemma MLX-VLM Captioner] ❌ Error generating caption: {e}")
            return f"[Gemma MLX-VLM Error: {str(e)}]"


class YOLOCaptioner:
    """YOLO-based object detector for visual captioning"""
    
    def __init__(self, model_path="yolo26x.pt", conf_threshold=0.25, iou_threshold=0.45):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model weights (e.g., 'yolo26x.pt', 'yolo26n.pt')
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
        """
        try:
            from ultralytics import YOLO
            print(f"[YOLO Captioner] Loading YOLO model from {model_path}...")
            self.model = YOLO(model_path)
            self.conf_threshold = conf_threshold
            self.iou_threshold = iou_threshold
            print(f"[YOLO Captioner] ✓ Model loaded successfully")
        except Exception as e:
            print(f"[YOLO Captioner] ❌ Failed to load model: {e}")
            raise
    
    def caption_image(self, image_path, prompt=None):
        """
        Generate caption from YOLO detections
        
        Args:
            image_path: Path to image file
            prompt: Unused (kept for interface compatibility)
            
        Returns:
            str: Caption text (when visual_backend != YOLO)
            OR
            tuple: (caption_text, detection_results_dict, annotated_image_path) when visual_backend == YOLO
        """
        try:
            # Run YOLO prediction
            results = self.model(image_path, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
            
            # Extract detection information
            detection_results = {
                'classes': [],
                'bounding_boxes': [],
                'confidences': [],
                'class_names': []
            }
            
            if len(results) > 0:
                result = results[0]
                
                # Extract boxes, classes, and confidences
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    # Get class IDs, names, and confidences
                    class_ids = boxes.cls.int().cpu().tolist()
                    confidences = boxes.conf.cpu().tolist()
                    xyxy = boxes.xyxy.cpu().tolist()  # [[x1, y1, x2, y2], ...]
                    
                    for cls_id, conf, box in zip(class_ids, confidences, xyxy):
                        class_name = result.names[cls_id]
                        detection_results['classes'].append(cls_id)
                        detection_results['class_names'].append(class_name)
                        detection_results['confidences'].append(round(conf, 3))
                        detection_results['bounding_boxes'].append([
                            round(box[0], 2), round(box[1], 2),
                            round(box[2], 2), round(box[3], 2)
                        ])
                    
                    # Generate text caption
                    class_counts = {}
                    for name in detection_results['class_names']:
                        class_counts[name] = class_counts.get(name, 0) + 1
                    
                    caption_parts = [f"{count} {name}" if count > 1 else name 
                                   for name, count in class_counts.items()]
                    caption = "Detected: " + ", ".join(caption_parts)
                    
                    # Save annotated image
                    annotated_path = image_path.replace('.jpg', '_yolo.jpg').replace('.png', '_yolo.png')
                    result.save(filename=annotated_path)
                    
                    print(f"[YOLO Captioner] Detected {len(detection_results['classes'])} objects: {caption}")
                    return caption, detection_results, annotated_path
                else:
                    return "No objects detected", detection_results, image_path
            else:
                return "No objects detected", detection_results, image_path
                
        except Exception as e:
            print(f"[YOLO Captioner] ❌ Error during detection: {e}")
            import traceback
            traceback.print_exc()
            return f"Detection error: {str(e)}", {}, image_path
            

class MultimodalMemoryItem(MemoryItem):
    """Extended memory item with audio caption support"""
    
    def __init__(self, caption="", audio_caption="", time=0.0, position=[0.0, 0.0, 0.0], theta=0.0, detection_results=None, **kwargs):
        # Call parent constructor first
        super().__init__(caption=caption, time=time, position=position, theta=theta, **kwargs)
        # Then set audio caption and detection results
        self.audio_caption = audio_caption
        self.detection_results = detection_results if detection_results is not None else {}
        print(f"[MultimodalMemoryItem] Created with audio_caption: {audio_caption[:50] if audio_caption else 'None'}...")
        if detection_results and detection_results.get('classes'):
            print(f"[MultimodalMemoryItem] Created with {len(detection_results['classes'])} detections")
    
    def to_dict(self):
        """Convert to dictionary with audio caption and detection results"""
        data = super().to_dict()
        data['audio_caption'] = self.audio_caption
        data['detection_results'] = self.detection_results
        print(f"[MultimodalMemoryItem] to_dict() audio_caption: {data.get('audio_caption', 'MISSING')[:50] if data.get('audio_caption') else 'None'}...")
        if self.detection_results and self.detection_results.get('classes'):
            print(f"[MultimodalMemoryItem] to_dict() detection_results: {len(self.detection_results['classes'])} objects")
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary with audio caption and detection results"""
        return cls(
            caption=data.get('caption', ''),
            audio_caption=data.get('audio_caption', ''),
            time=data.get('time', 0.0),
            position=data.get('position', [0.0, 0.0, 0.0]),
            theta=data.get('theta', 0.0),
            detection_results=data.get('detection_results', {})
        )

class EnhancedMemoryBuilder:
    """Enhanced memory builder with multimodal (visual + audio) captioning"""
    
    def __init__(self, collection_name="webots_multimodal", db_ip="127.0.0.1",
                advanced_mode=False, enable_audio=True, audio_device="BlackHole",
                audio_backend="ACT", visual_backend="PHI3",
                audio_clip_dir="/tmp/webots_memory_audio"):  # Add visual_backend / audio_clip_dir parameters
        print(f"[Enhanced Memory Builder] Starting multimodal memory builder...")
        print(f"[Enhanced Memory Builder] Collection: {collection_name}")
        print(f"[Enhanced Memory Builder] Database IP: {db_ip}")
        print(f"[Enhanced Memory Builder] Advanced mode: {advanced_mode}")
        print(f"[Enhanced Memory Builder] Visual backend: {visual_backend}")  # Add this line
        print(f"[Enhanced Memory Builder] Audio enabled: {enable_audio}")
        
        # Initialize memory
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        print("[Enhanced Memory Builder] ✓ Memory initialized")
        
        # Initialize visual captioner
        self.visual_captioner = None
        self.advanced_mode = advanced_mode
        self.visual_backend = visual_backend  # Add this line
        self.init_visual_captioner()  # This method will be modified
        
        # Test the visual captioner
        if self.visual_captioner:
            if not self.test_visual_captioner():
                print("[Enhanced Memory Builder] ⚠️ Visual captioner test failed, disabling")
                self.visual_captioner = None
        
        # Initialize audio captioner
        self.audio_captioner = None
        self.enable_audio = enable_audio
        self.audio_backend = audio_backend  # Add this line
        if enable_audio:
            self.init_audio_captioner(audio_device, audio_backend)  # Modify this line
        
        # Data directories
        self.data_dir = Path("/tmp/webots_memory")
        self.data_dir.mkdir(exist_ok=True)

        # Directory for the raw audio clips that correspond to memory entries.
        # Clips are named with the entry timestamp so the QA generation tool can
        # match them to entries the same way it matches camera frames.
        self.audio_clip_dir = Path(audio_clip_dir)
        try:
            self.audio_clip_dir.mkdir(parents=True, exist_ok=True)
            print(f"[Enhanced Memory Builder] ✓ Audio clip directory: {self.audio_clip_dir}")
        except Exception as e:
            print(f"[Enhanced Memory Builder] ⚠️ Could not create audio clip directory {self.audio_clip_dir}: {e}")
        self.audio_clip_count = 0
        
        # Processing queues
        self.visual_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.memory_queue = queue.Queue()
        
        # Control flags
        self.running = True
        
        # Performance tracking
        self.processed_count = 0
        self.audio_processed_count = 0
        self.start_time = time.time()
        
        print("[Enhanced Memory Builder] ✓ Multimodal memory builder ready")
        
        # Add timestamp synchronization
        self.simulation_start_time = None
        self.system_start_time = time.time()
        
        print("[Enhanced Memory Builder] ✓ Multimodal memory builder ready")
    
    def _pause_session_audio_recording(self):
        """Pause audio recording (stop writing to WAV, keep threads alive)."""
        if self.session_audio_recording and not self.session_audio_paused:
            print("[Enhanced Memory Builder] ⏸️  Pausing session audio recording...")
            if self.session_audio_file:
                self.session_audio_file.close()
                self.session_audio_file = None
            self.session_audio_recording = False
            self.session_audio_paused = True
            print("[Enhanced Memory Builder] ⏸️  Session audio recording paused")
    
    def _resume_session_audio_recording(self):
        """Resume audio recording (start writing to WAV, keep threads alive)."""
        if not self.session_audio_recording and self.session_audio_paused:
            print("[Enhanced Memory Builder] ▶️  Resuming session audio recording...")
            self.session_audio_paused = False
            self._start_session_audio_recording()
            print("[Enhanced Memory Builder] ▶️  Session audio recording resumed")
    
    def _check_pause_flag(self):
        """Check pause flag file and update recording state."""
        if os.path.exists(PAUSE_FLAG_PATH):
            if not self.session_audio_paused:
                self._pause_session_audio_recording()
        else:
            if self.session_audio_paused:
                self._resume_session_audio_recording()
    
    def init_visual_captioner(self):
        """Initialize visual captioner based on backend choice with error handling"""
        print(f"[Enhanced Memory Builder] Initializing {self.visual_backend} visual captioner...")
        
        try:
            if self.visual_backend.upper() == "PHI3":
                if self.advanced_mode:
                    self.visual_captioner = Phi3VisionMLXCaptionerAdvanced(
                        use_quantization=True,
                        enable_advanced_features=True
                    )
                    print("[Enhanced Memory Builder] ✓ Advanced Phi3 visual captioner ready")
                else:
                    self.visual_captioner = Phi3VisionMLXCaptioner(
                        quantize_model=True,
                        quantize_cache=False
                    )
                    print("[Enhanced Memory Builder] ✓ Standard Phi3 visual captioner ready")
            
            elif self.visual_backend.upper() == "FASTVLM":
                self.visual_captioner = FastVLMCaptioner()
                print("[Enhanced Memory Builder] ✓ FastVLM visual captioner ready")
            
            elif self.visual_backend.upper() == "GEMMA-3N":
                self.visual_captioner = GemmaMlxVlmCaptioner()
                print("[Enhanced Memory Builder] ✓ Gemma-3n MLX-VLM visual captioner ready")
            
            elif self.visual_backend.upper() == "YOLO":
                self.visual_captioner = YOLOCaptioner(model_path="yolo26x.pt")
                print("[Enhanced Memory Builder] ✓ YOLO object detector ready")
            
            else:
                # Treat as HuggingFace model ID
                self.visual_captioner = GemmaMlxVlmCaptioner(model_name=self.visual_backend)
                print(f"[Enhanced Memory Builder] ✓ MLX-VLM visual captioner ready (model: {self.visual_backend})")
            
        except Exception as e:
            print(f"[Enhanced Memory Builder] ❌ Visual captioner initialization failed: {e}")
            print(f"[Enhanced Memory Builder] ⚠️ Falling back to simple visual captions")
            self.visual_captioner = None
            
    def test_visual_captioner(self):
        """Test visual captioner with a simple operation"""
        if not self.visual_captioner:
            return False
            
        try:
            # Create a simple test image
            test_image_path = "/tmp/test_image.jpg"
            from PIL import Image
            import numpy as np
            
            # Create a simple 64x64 RGB image
            test_array = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            test_image = Image.fromarray(test_array)
            test_image.save(test_image_path)
            
            # Test captioning
            test_caption = self.visual_captioner.caption_image(test_image_path)
            
            # Clean up
            os.unlink(test_image_path)
            
            # Check if test was successful
            if "[Error:" in test_caption or "LLVM ERROR" in test_caption:
                return False
                
            print(f"[Enhanced Memory Builder] ✅ Visual captioner test successful")
            return True
            
        except Exception as e:
            print(f"[Enhanced Memory Builder] ❌ Visual captioner test failed: {e}")
            return False
    
    def init_audio_captioner(self, audio_device, audio_backend="ACT"):
        """Initialize audio captioner with specified backend"""
        print(f"[Enhanced Memory Builder] Initializing {audio_backend} audio captioner...")
        
        try:
            if audio_backend.upper() == "ACT":
                self.audio_captioner = AudioCaptioningModule(device_name=audio_device)
            elif audio_backend.upper() == "AUDIOSET":
                if not AUDIOSET_AVAILABLE:
                    raise ImportError("AudioSet modules are not available. Please check AudioSet installation.")
                self.audio_captioner = AudioSetTaggingModule(device_name=audio_device)
            else:
                raise ValueError(f"Unknown audio backend: {audio_backend}")
                
            if self.audio_captioner.setup_audio_stream():
                print(f"[Enhanced Memory Builder] ✓ {audio_backend} audio captioner ready")
            else:
                print(f"[Enhanced Memory Builder] ❌ {audio_backend} audio stream setup failed")
                self.audio_captioner = None
                self.enable_audio = False
        except Exception as e:
            print(f"[Enhanced Memory Builder] {audio_backend} audio captioner initialization failed: {e}")
            self.audio_captioner = None
            self.enable_audio = False
    
    def generate_simple_visual_caption(self, image_path, position, theta):
        """Generate simple visual caption as fallback"""
        x, y, z = position
        
        try:
            image = Image.open(image_path)
            width, height = image.size
            
            if abs(x) < 0.1 and abs(y) < 0.1:
                return f"Robot at starting position, capturing {width}x{height} camera view of simulation environment"
            elif x > 0.5:
                return f"Robot exploring forward area ({x:.2f}, {y:.2f}), camera shows new territory ahead"
            elif abs(y) > 0.3:
                return f"Robot moved laterally to ({x:.2f}, {y:.2f}), camera captures side view of environment"
            else:
                return f"Robot navigating at ({x:.2f}, {y:.2f}), camera shows detailed simulation environment"
                
        except Exception as e:
            print(f"[Enhanced Memory Builder] Error analyzing image: {e}")
            return f"Robot camera view at position ({x:.2f}, {y:.2f}, {z:.2f}) - captured simulation scene"
    
    def visual_processing_thread(self):
        """Thread for processing visual data"""
        print("[Enhanced Memory Builder] Starting visual processing thread...")
        
        # Counter for consecutive empty checks (to handle temporary gaps)
        empty_check_count = 0
        max_empty_checks = 30  # Wait up to 3 seconds (30 * 0.1s) before terminating
        
        while self.running:
            try:
                # Check for new visual data files
                data_files = list(self.data_dir.glob("memory_*.json"))
                
                # Handle case when no data files are found
                if not data_files:
                    empty_check_count += 1
                    if empty_check_count >= max_empty_checks:
                        print(f"[Enhanced Memory Builder] No data files found for {max_empty_checks * 0.1:.0f}s. Terminating...")
                        self.running = False
                        break
                    elif empty_check_count % 50 == 0:  # Log every 5 seconds
                        print(f"[Enhanced Memory Builder] Waiting for data files... ({empty_check_count * 0.1:.0f}s)")
                    time.sleep(0.1)
                    continue
                
                # Reset counter when files are found
                empty_check_count = 0
                
                for data_file in data_files:
                    try:
                        with open(data_file, 'r') as f:
                            data = json.load(f)
                        
                        image_path = data['image_path']
                        position = data['position']
                        theta = data['theta']
                        timestamp = data['timestamp']
                        
                        # Initialize simulation start time on first visual data
                        if self.simulation_start_time is None:
                            self.simulation_start_time = timestamp
                            print(f"[Enhanced Memory Builder] Simulation start time set to: {timestamp}")
                        
                        print(f"[Enhanced Memory Builder] Processing visual: {image_path}")
                        
                        # Generate visual caption
                        visual_caption = None
                        detection_results = None
                        
                        if self.visual_captioner and os.path.exists(image_path):
                            try:
                                start_time = time.time()
                                
                                # Add MPS error handling for non-YOLO backends
                                if self.visual_backend.upper() != "YOLO":
                                    import torch
                                    if torch.backends.mps.is_available():
                                        # Clear MPS cache before inference
                                        torch.mps.empty_cache()
                                
                                # Handle YOLO backend differently (returns tuple)
                                if self.visual_backend.upper() == "YOLO":
                                    caption_result = self.visual_captioner.caption_image(image_path)
                                    
                                    # YOLO returns (caption, detection_results, annotated_path)
                                    if isinstance(caption_result, tuple) and len(caption_result) == 3:
                                        visual_caption, detection_results, annotated_image_path = caption_result
                                        
                                        # Replace original frame with annotated version
                                        if annotated_image_path != image_path and os.path.exists(annotated_image_path):
                                            try:
                                                import shutil
                                                shutil.copy2(annotated_image_path, image_path)
                                                print(f"[Enhanced Memory Builder] 📸 Replaced frame with annotated version")
                                                # Clean up temp annotated file
                                                if annotated_image_path != image_path:
                                                    os.remove(annotated_image_path)
                                            except Exception as e:
                                                print(f"[Enhanced Memory Builder] ⚠️ Could not replace frame: {e}")
                                    else:
                                        visual_caption = str(caption_result)
                                        detection_results = {}
                                else:
                                    # Other backends return just caption string
                                    visual_caption = self.visual_captioner.caption_image(image_path)
                                    detection_results = {}
                                
                                end_time = time.time()
                                
                                # Check if caption indicates an error
                                if "[Error:" in visual_caption or "LLVM ERROR" in visual_caption:
                                    raise Exception(f"Model inference error: {visual_caption}")
                                    
                                print(f"[Enhanced Memory Builder] Visual caption generated in {end_time - start_time:.2f}s: {visual_caption}")
                                if detection_results and detection_results.get('classes'):
                                    print(f"[Enhanced Memory Builder] 🎯 Detected {len(detection_results['classes'])} objects")
                                
                            except Exception as e:
                                print(f"[Enhanced Memory Builder] ❌ Visual captioning failed: {e}")
                                print(f"[Enhanced Memory Builder] 🔄 Using fallback simple caption")
                                visual_caption = self.generate_simple_visual_caption(image_path, position, theta)
                                detection_results = {}
                                
                                # Disable the problematic captioner to prevent further errors
                                print(f"[Enhanced Memory Builder] ⚠️ Disabling {self.visual_backend} captioner due to errors")
                                self.visual_captioner = None
                        else:
                            visual_caption = self.generate_simple_visual_caption(image_path, position, theta)
                            detection_results = {}
                        
                        # Convert simulation time to system time for matching
                        # This assumes both systems run at same rate
                        simulation_elapsed = timestamp - self.simulation_start_time
                        estimated_system_time = self.system_start_time + simulation_elapsed
                        
                        print(f"[Enhanced Memory Builder] Time conversion:")
                        print(f"  Simulation time: {timestamp}")
                        print(f"  Simulation elapsed: {simulation_elapsed}")
                        print(f"  Estimated system time: {estimated_system_time}")
                        
                        # Put in memory queue for combination with audio
                        memory_data = {
                            'visual_caption': visual_caption,
                            'detection_results': detection_results,
                            'timestamp': estimated_system_time,  # Use converted timestamp
                            'original_sim_time': timestamp,       # Keep original for reference
                            'position': position,
                            'theta': theta,
                            'type': 'visual'
                        }
                        
                        self.memory_queue.put(memory_data)
                        
                        # Remove processed file
                        data_file.unlink()
                        
                    except Exception as e:
                        print(f"[Enhanced Memory Builder] Error processing visual file {data_file}: {e}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[Enhanced Memory Builder] Error in visual processing thread: {e}")
                time.sleep(1)
        
        print("[Enhanced Memory Builder] Visual processing thread stopped")
    
    def audio_processing_thread(self):
        """Thread for processing audio data"""
        if not self.enable_audio or not self.audio_captioner:
            print("[Enhanced Memory Builder] Audio processing disabled")
            return
        
        print("[Enhanced Memory Builder] Starting audio processing thread...")
        
        while self.running:
            try:
                # Record the audio capture time
                audio_capture_time = time.time()
                
                # Capture 10-second audio chunk
                audio_chunk = self.audio_captioner.capture_audio_chunk()
                
                if audio_chunk is not None:
                    print("[Enhanced Memory Builder] Processing audio chunk...")
                    
                    # Audio timestamp represents the START of the audio period
                    audio_timestamp = audio_capture_time - self.audio_captioner.chunk_duration
                    
                    # Generate audio caption
                    start_time = time.time()
                    audio_caption = self.audio_captioner.generate_audio_caption(audio_chunk)
                    end_time = time.time()
                    
                    print(f"[Enhanced Memory Builder] Audio caption generated in {end_time - start_time:.2f}s: {audio_caption}")
                    print(f"[Enhanced Memory Builder] Audio timestamp: {audio_timestamp}")
                    
                    # Put in memory queue. Carry the raw samples + sample rate so
                    # the integration thread can persist the actual audio clip
                    # alongside the memory entry it gets matched to.
                    memory_data = {
                        'audio_caption': audio_caption,
                        'timestamp': audio_timestamp,
                        'type': 'audio',
                        'audio_samples': audio_chunk,
                        'sample_rate': getattr(self.audio_captioner, 'sample_rate', 44100),
                    }

                    self.memory_queue.put(memory_data)
                    self.audio_processed_count += 1
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[Enhanced Memory Builder] Error in audio processing thread: {e}")
                time.sleep(1)
        
        print("[Enhanced Memory Builder] Audio processing thread stopped")
    
    def memory_integration_thread(self):
        """Thread for integrating and storing multimodal memory items"""
        print("[Enhanced Memory Builder] Starting memory integration thread...")
        
        visual_buffer = {}  # timestamp -> visual_data
        audio_buffer = deque(maxlen=5000)  # Recent audio captions
        
        while self.running:
            try:
                # Get data from memory queue
                try:
                    memory_data = self.memory_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if memory_data['type'] == 'visual':
                    # Store visual data in buffer first, don't process immediately
                    timestamp = memory_data['timestamp']
                    visual_buffer[timestamp] = memory_data
                    print(f"[Enhanced Memory Builder] Visual data buffered for timestamp {timestamp}")
                    
                elif memory_data['type'] == 'audio':
                    # Store audio data in buffer
                    audio_buffer.append(memory_data)
                    print(f"[Enhanced Memory Builder] Audio data buffered: {memory_data['audio_caption'][:50]}...")
                    
                    # Process any pending visual items that can now be matched
                    self.process_pending_visual_items(visual_buffer, audio_buffer)
                    
            except Exception as e:
                print(f"[Enhanced Memory Builder] Error in memory integration thread: {e}")
                time.sleep(1)
        
        # Process any remaining visual items before stopping
        print("[Enhanced Memory Builder] Processing remaining visual items...")
        self.process_pending_visual_items(visual_buffer, audio_buffer)
        print("[Enhanced Memory Builder] Memory integration thread stopped")
        
    def _save_audio_clip(self, samples, sample_rate, entry_time):
        """Write the raw audio samples for a memory entry to a WAV file.

        The clip is named ``audio_clip_<n>_<entry_time>.wav`` so the QA
        generation tool can locate it by the entry timestamp (mirroring how
        camera frames are matched). Audio is stored as mono 16-bit PCM, which is
        universally playable (e.g. macOS ``afplay``) and needs no extra deps.

        Returns the file path on success, or None when there is nothing to write.
        """
        if samples is None:
            return None

        audio = np.asarray(samples, dtype=np.float32).flatten()
        if audio.size == 0:
            return None

        try:
            sample_rate = int(sample_rate)
        except (TypeError, ValueError):
            sample_rate = 44100
        if sample_rate <= 0:
            sample_rate = 44100

        # float [-1, 1] -> 16-bit PCM
        pcm16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)

        filename = f"audio_clip_{self.audio_clip_count}_{float(entry_time):.3f}.wav"
        clip_path = self.audio_clip_dir / filename

        with wave.open(str(clip_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm16.tobytes())

        self.audio_clip_count += 1
        return clip_path

    def process_pending_visual_items(self, visual_buffer, audio_buffer):
        """Process visual items that can be matched with audio"""
        processed_timestamps = []
        
        for timestamp, visual_data in visual_buffer.items():
            # Find matching audio within time window
            matching_audio = None
            time_window = 15.0  # Reduced to 15 seconds window
            
            # Find the best matching audio (closest in time)
            best_match = None
            best_time_diff = float('inf')
            
            print(f"[Enhanced Memory Builder] Looking for audio match for visual timestamp: {timestamp}")
            print(f"[Enhanced Memory Builder] Audio buffer contains {len(audio_buffer)} items")
            
            for i, audio_data in enumerate(audio_buffer):
                time_diff = abs(audio_data['timestamp'] - timestamp)
                print(f"[Enhanced Memory Builder] Audio {i}: timestamp={audio_data['timestamp']}, diff={time_diff:.2f}s")
                
                if time_diff <= time_window and time_diff < best_time_diff:
                    best_match = audio_data
                    best_time_diff = time_diff
                    print(f"[Enhanced Memory Builder] ✓ New best match found: diff={time_diff:.2f}s")
            
            matching_audio = best_match

            # Create multimodal memory item
            audio_caption = matching_audio['audio_caption'] if matching_audio else ""

            # The timestamp stored on the memory entry (original simulation time).
            # Reuse it for the audio clip filename so the QA tool can match them.
            entry_time = visual_data.get('original_sim_time', timestamp)

            # Debug: Print what we're about to store
            print(f"[Enhanced Memory Builder] Creating memory item:")
            print(f"  Timestamp: {timestamp}")
            print(f"  Original sim time: {visual_data.get('original_sim_time', 'N/A')}")
            print(f"  Visual: {visual_data['visual_caption'][:50]}...")
            print(f"  Audio: {audio_caption[:50] if audio_caption else 'None'}...")
            if matching_audio:
                print(f"  ✓ Audio matched with {best_time_diff:.2f}s difference")
            else:
                print(f"  ❌ No audio match found")

            # Persist the actual audio clip for this entry (best effort: a write
            # failure must never prevent the memory item from being stored).
            if matching_audio is not None and matching_audio.get('audio_samples') is not None:
                try:
                    clip_path = self._save_audio_clip(
                        matching_audio['audio_samples'],
                        matching_audio.get('sample_rate', 44100),
                        entry_time,
                    )
                    if clip_path:
                        print(f"[Enhanced Memory Builder]   🔊 Saved audio clip: {clip_path}")
                except Exception as e:
                    print(f"[Enhanced Memory Builder] ⚠️ Failed to save audio clip: {e}")

            memory_item = MultimodalMemoryItem(
                caption=visual_data['visual_caption'],
                audio_caption=audio_caption,
                time=entry_time,  # Use original simulation time
                position=visual_data['position'],
                theta=visual_data['theta'],
                detection_results=visual_data.get('detection_results', {})
            )
            
            # Verify the memory item has the audio caption and detection results
            print(f"[Enhanced Memory Builder] Memory item audio_caption: {getattr(memory_item, 'audio_caption', 'NOT FOUND')[:50] if getattr(memory_item, 'audio_caption', '') else 'EMPTY'}")
            if visual_data.get('detection_results', {}).get('classes'):
                print(f"[Enhanced Memory Builder] Memory item detections: {len(visual_data['detection_results']['classes'])} objects")
            
            # Insert into memory
            self.memory.insert(memory_item)
            self.processed_count += 1
            
            print(f"[Enhanced Memory Builder] ✓ Multimodal memory item {self.processed_count} inserted")
            print(f"[Enhanced Memory Builder]   Visual: {visual_data['visual_caption'][:50]}...")
            if audio_caption:
                print(f"[Enhanced Memory Builder]   Audio: {audio_caption[:50]}...")
            
            processed_timestamps.append(timestamp)
        
        # Remove processed visual items
        for timestamp in processed_timestamps:
            del visual_buffer[timestamp]

    def get_model_size_bytes(self, model_name):
        """Get the disk size in bytes for a model.
        
        Handles:
        - Local paths (absolute or relative)
        - HuggingFace model IDs (looks in ~/.cache/huggingface/hub/ and custom HF model dirs)
        - Special backends: ACT, AUDIOSET, PHI3, FASTVLM, YOLO (scans their directories)
        
        Args:
            model_name: Model name or path string
            
        Returns:
            int: Size in bytes, or 0 if not found
        """
        # All known backends have model files on disk
        special_dirs = {
            "ACT": "/Users/wen-chungcheng/ACT",
            "AUDIOSET": "/Users/wen-chungcheng/audioset_tagging_cnn",
            "PHI3": "/Users/wen-chungcheng/remembr/models/phi3_v_Q",
            "FASTVLM": "/Users/wen-chungcheng/ml-fastvlm/checkpoints/llava-fastvithd_0.5b_stage3",
            "YOLO": "/Users/wen-chungcheng/remembr/yolo26x.pt",
        }
        if model_name.upper() in special_dirs:
            dir_path = Path(special_dirs[model_name.upper()])
            if dir_path.is_file():
                try:
                    return dir_path.stat().st_size
                except (PermissionError, OSError):
                    pass
            elif dir_path.is_dir():
                try:
                    return sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                except (PermissionError, OSError):
                    pass
            return 0
        
        # Check if it's a local path
        candidate_paths = [model_name]
        
        # If it looks like a HF model ID (contains '/' but not a local path), check HF cache locations
        is_hf_id = '/' in model_name and not model_name.startswith('/') and not model_name.startswith('.')
        
        if is_hf_id:
            # Default HF cache: ~/.cache/huggingface/hub/
            default_cache = Path.home() / ".cache" / "huggingface" / "hub"
            cache_folder = model_name.replace('/', '+')
            candidate_paths.append(str(default_cache / cache_folder))
            # Also try models-- prefix variant
            candidate_paths.append(str(default_cache / f"models--{model_name.replace('/', '--')}"))
            
            # Custom HF model directory
            custom_dirs = [
                "/Volumes/USB DISK/huggingface/hub",
                Path.home() / ".cache" / "huggingface" / "hub",
            ]
            for custom_dir in custom_dirs:
                # Layout 1: <custom_dir>/<org>/<model_name> (e.g., .../mlx-community/gemma-3n-E2B-it-4bit)
                candidate_paths.append(str(Path(custom_dir) / model_name))
                # Layout 2: <custom_dir>/<model_name> (e.g., .../gemma-3n-E2B-it-4bit)
                parts = model_name.split('/')
                if len(parts) > 1:
                    candidate_paths.append(str(Path(custom_dir) / parts[-1]))
                # Layout 3: <custom_dir>/models--<org>--<model> (huggingface-cli format)
                candidate_paths.append(str(Path(custom_dir) / f"models--{model_name.replace('/', '--')}"))
        
        # Try each candidate path
        for path in candidate_paths:
            p = Path(path)
            if p.is_dir():
                try:
                    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
                except (PermissionError, OSError):
                    continue
        
        return 0

    def format_size(self, size_bytes):
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def record_session_stats(self):
        """Record session statistics (elapsed time, model names, model sizes) to a CSV file.
        
        Appends a new row each run for later analysis of model combinations.
        """
        stats_file = Path("model_session_stats.csv")
        elapsed_time = time.time() - self.start_time
        
        # Determine visual model name
        visual_model = self.visual_backend
        if hasattr(self, 'visual_captioner') and self.visual_captioner:
            if hasattr(self.visual_captioner, 'model_name'):
                visual_model = self.visual_captioner.model_name
            elif hasattr(self.visual_captioner, 'model_path'):
                visual_model = self.visual_captioner.model_path
        
        # Determine audio model name
        audio_model = self.audio_backend
        if hasattr(self, 'audio_captioner') and self.audio_captioner:
            if hasattr(self.audio_captioner, 'model_name'):
                audio_model = self.audio_captioner.model_name
            elif hasattr(self.audio_captioner, 'model_type'):
                audio_model = self.audio_captioner.model_type
        
        # Calculate model sizes (deduplicated if same model)
        visual_size = self.get_model_size_bytes(visual_model)
        audio_size = self.get_model_size_bytes(audio_model)
        
        # If same model used for both, count it only once
        if visual_model == audio_model:
            total_size = max(visual_size, audio_size)
        else:
            total_size = visual_size + audio_size
        
        # Calculate processing rates
        visual_rate = self.processed_count / elapsed_time if elapsed_time > 0 else 0
        audio_rate = self.audio_processed_count / elapsed_time if elapsed_time > 0 else 0
        
        # Prepare row
        row = {
            'timestamp': datetime.now().isoformat(),
            'collection': self.memory.db_collection_name if hasattr(self.memory, 'db_collection_name') else 'N/A',
            'elapsed_time_s': round(elapsed_time, 2),
            'visual_items': self.processed_count,
            'audio_items': self.audio_processed_count,
            'visual_rate_per_s': round(visual_rate, 4),
            'audio_rate_per_s': round(audio_rate, 4),
            'visual_backend': self.visual_backend,
            'visual_model': visual_model,
            'visual_size_bytes': visual_size,
            'visual_size_human': self.format_size(visual_size),
            'audio_backend': self.audio_backend,
            'audio_model': audio_model,
            'audio_size_bytes': audio_size,
            'audio_size_human': self.format_size(audio_size),
            'total_size_bytes': total_size,
            'total_size_human': self.format_size(total_size),
        }
        
        # Write to CSV (append, create with headers if new)
        fieldnames = list(row.keys())
        file_exists = stats_file.exists() and stats_file.stat().st_size > 0
        
        try:
            with open(stats_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
            print(f"\n[Enhanced Memory Builder] 📊 Session stats saved to {stats_file}")
        except Exception as e:
            print(f"\n[Enhanced Memory Builder] ⚠️ Failed to save session stats: {e}")

    def run(self):
        """Main processing loop with multimodal threads"""
        print("[Enhanced Memory Builder] Starting multimodal processing...")
        
        # Start processing threads
        threads = []
        
        # Visual processing thread
        visual_thread = threading.Thread(target=self.visual_processing_thread, daemon=True)
        visual_thread.start()
        threads.append(visual_thread)
        
        # Audio processing thread
        if self.enable_audio:
            audio_thread = threading.Thread(target=self.audio_processing_thread, daemon=True)
            audio_thread.start()
            threads.append(audio_thread)
        
        # Memory integration thread
        memory_thread = threading.Thread(target=self.memory_integration_thread, daemon=True)
        memory_thread.start()
        threads.append(memory_thread)
        
        try:
            print("[Enhanced Memory Builder] All threads started. Press Ctrl+C to stop...")
            while self.running:
                time.sleep(1)
                
                # Check pause flag for audio recording control
                self._check_pause_flag()
                
                # Print periodic status
                elapsed_time = time.time() - self.start_time
                if elapsed_time > 0:
                    visual_rate = self.processed_count / elapsed_time
                    audio_rate = self.audio_processed_count / elapsed_time if self.enable_audio else 0
                    
                    print(f"[Enhanced Memory Builder] Status: {self.processed_count} visual, {self.audio_processed_count} audio processed")
                    print(f"[Enhanced Memory Builder] Rate: {visual_rate:.2f} visual/s, {audio_rate:.2f} audio/s")
                
        except KeyboardInterrupt:
            print("\n[Enhanced Memory Builder] Stopping...")
            self.running = False
        
        finally:
            # Cleanup
            # Stop session audio recording first
            if self.session_audio_recording:
                self._stop_session_audio_recording()
            
            # Clean up pause flag file
            try:
                if os.path.exists(PAUSE_FLAG_PATH):
                    os.remove(PAUSE_FLAG_PATH)
            except Exception:
                pass
            
            if self.audio_captioner:
                self.audio_captioner.cleanup()
            
            self.print_performance_stats()
            self.record_session_stats()
        
        print("[Enhanced Memory Builder] Stopped")
    
    def print_performance_stats(self):
        """Print performance statistics"""
        elapsed_time = time.time() - self.start_time
        print(f"\n[Enhanced Memory Builder] Performance Statistics:")
        print(f"  Visual items processed: {self.processed_count}")
        print(f"  Audio items processed: {self.audio_processed_count}")
        print(f"  Total time: {elapsed_time:.2f}s")
        if self.processed_count > 0:
            print(f"  Visual processing rate: {self.processed_count / elapsed_time:.2f} items/s")
        if self.audio_processed_count > 0:
            print(f"  Audio processing rate: {self.audio_processed_count / elapsed_time:.2f} items/s")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Multimodal Memory Builder')
    parser.add_argument('--collection', '-c', default='webots_multimodal', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--advanced', '-a', action='store_true', help='Use advanced visual captioner')
    parser.add_argument('--no-audio', action='store_true', help='Disable audio captioning')
    parser.add_argument('--audio-device', default='BlackHole', help='Audio device name')
    parser.add_argument('--audio-backend', default='ACT', choices=['ACT', 'AUDIOSET'], 
                   help='Audio captioning backend (ACT or AUDIOSET)')
    
    parser.add_argument('--visual-backend', default='PHI3',
                    help='Visual captioning backend: PHI3, FASTVLM, GEMMA-3N, YOLO, or a HuggingFace model ID (e.g., mlx-community/MiniCPM-V-4.6-4bit)')
    parser.add_argument('--audio-clip-dir', default='/tmp/webots_memory_audio',
                    help='Directory where per-entry audio clips (.wav) are saved for QA playback')
    parser.add_argument('--show-disk-space', action='store_true',
                    help='Show available disk space on the external drive where HuggingFace models are stored')

    args = parser.parse_args()
    
    # Show disk space and exit (no captioning)
    if args.show_disk_space:
        show_disk_space()
        sys.exit(0)
    
    print("🤖 Enhanced Multimodal Memory Builder")
    print("Visual + Audio Captioning with ReMEmbR Framework")
    print("="*60)
    
    # Modify the builder instantiation:

    builder = EnhancedMemoryBuilder(
        collection_name=args.collection,
        db_ip=args.db_ip,
        advanced_mode=args.advanced,
        enable_audio=not args.no_audio,
        audio_device=args.audio_device,
        audio_backend=args.audio_backend,
        visual_backend=args.visual_backend,  # Add this line
        audio_clip_dir=args.audio_clip_dir
    )
    
    try:
        builder.run()
    except KeyboardInterrupt:
        print("\n[Enhanced Memory Builder] Interrupted by user")