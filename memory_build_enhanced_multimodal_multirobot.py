#!/usr/bin/env python3
"""
Multi-Robot Enhanced Memory Builder with Audio Captioning
Supports 2 robots:
- Ground robot (Spot) with YOLO detection
- Aerial robot (Mavic 2 Pro) with YOLO-OBB (Oriented Bounding Box) detection
"""

import sys
import os
import time
import threading
import queue
import json
import traceback
import numpy as np
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

# Import ReMEmbR components for multi-robot
from remembr.memory.memory_multimodal_multirobot import MemoryItem
from remembr.memory.milvus_memory_multimodal_multirobot import MilvusMemory
from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner, Phi3VisionMLXCaptionerAdvanced

# Import ACT components
from tools.config_loader import get_config
from tools.utils import *
from tools.file_io import load_pickle_file
from models.TransModel import ACT


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
        
        # Add AudioSet paths to front of sys.path
        audioset_pytorch_path = os.path.join(audioset_path, "pytorch")
        audioset_utils_path = os.path.join(audioset_path, "utils")
        
        # Insert at beginning to take precedence
        sys.path.insert(0, audioset_path)
        sys.path.insert(0, audioset_pytorch_path)
        sys.path.insert(0, audioset_utils_path)
        
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
        
        return audioset_models, audioset_pytorch_utils, audioset_config
        
    finally:
        # Restore original state
        sys.path = original_path
        os.chdir(original_cwd)

# Import AudioSet modules safely
try:
    audioset_modules, audioset_pytorch_utils, audioset_config = import_audioset_modules()
    AUDIOSET_AVAILABLE = True
except Exception as e:
    print(f"[Warning] AudioSet modules not available: {e}")
    AUDIOSET_AVAILABLE = False
    audioset_modules = None
    audioset_pytorch_utils = None
    audioset_config = None


class AudioCaptioningModule:
    """ACT-based audio captioning"""

    def __init__(self, device='mps'):
        print("[AudioCaptioning] Initializing ACT audio captioner")

        original_cwd = os.getcwd()
        act_dir = "/Users/wen-chungcheng/ACT"

        try:
            if not os.path.exists(act_dir):
                raise FileNotFoundError(f"ACT directory not found: {act_dir}")

            os.chdir(act_dir)
            print(f"[AudioCaptioning] Changed to ACT directory: {os.getcwd()}")

            settings_path = os.path.join(act_dir, "settings", "settings.yaml")
            if not os.path.exists(settings_path):
                raise FileNotFoundError(f"ACT settings file not found: {settings_path}")

            sys.path.append(act_dir)
            from tools.config_loader import get_config

            self.config = get_config()
            self.config.mode = 'eval'
            print(f"[AudioCaptioning] Config loaded from {settings_path}")

            self.device = torch.device(device if torch.backends.mps.is_available() else 'cpu')
            print(f"[AudioCaptioning] Using device: {self.device}")

            self.words_list = load_pickle_file(self.config.path.vocabulary)
            self.ntokens = len(self.words_list)
            self.sos_ind = self.words_list.index('<sos>')
            self.eos_ind = self.words_list.index('<eos>')

            from models.TransModel import ACT
            self.model = ACT(self.config, self.ntokens)
            self.model.to(self.device)
            self.model.eval()

            model_path = self.config.path.eval_model
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model'])
                print("[AudioCaptioning] ✓ ACT model loaded successfully")
            else:
                print("[AudioCaptioning] ⚠ Model weights not found, using randomly initialized model")

        except Exception as e:
            print(f"[AudioCaptioning] ❌ Failed to load ACT model: {e}")
            raise
        finally:
            os.chdir(original_cwd)

    def extract_audio_features(self, audio_file):
        """Extract mel-spectrogram features from audio file"""
        try:
            audio, sr = librosa.load(audio_file, sr=self.config.wav.sr, mono=True)

            target_length = 10 * self.config.wav.sr
            if len(audio) <= target_length:
                audio = np.concatenate((audio, np.zeros(target_length - len(audio), dtype=np.float32)))
            else:
                audio = audio[:target_length]

            mel_spec = librosa.feature.melspectrogram(
                y=audio,
                sr=sr,
                n_fft=self.config.wav.window_length,
                hop_length=self.config.wav.hop_length,
                n_mels=self.config.wav.n_mels
            )

            feature = librosa.power_to_db(mel_spec).T.astype(np.float32)
            feature = feature[:-1, :]

            return torch.tensor(feature, dtype=torch.float32).unsqueeze(0).to(self.device)

        except Exception as e:
            print(f"[AudioCaptioning] Error extracting features from {audio_file}: {e}")
            return None

    def generate_caption(self, audio_file):
        """Generate caption for audio file"""
        try:
            audio_features = self.extract_audio_features(audio_file)

            if audio_features is None:
                return "Unable to process audio"

            with torch.no_grad():
                from tools.utils import greedy_decode
                output = greedy_decode(self.model, audio_features, sos_ind=self.sos_ind, eos_ind=self.eos_ind)

            output = output[0, 1:].cpu().numpy()

            caption_words = []
            for idx in output:
                if idx == self.eos_ind:
                    break
                caption_words.append(self.words_list[idx])

            caption_text = ' '.join(caption_words)
            print(f"[AudioCaptioning] Generated caption: {caption_text}")
            return caption_text

        except Exception as e:
            print(f"[AudioCaptioning] Error generating caption: {e}")
            traceback.print_exc()
            return f"Captioning error: {str(e)}"


class FastVLMCaptioner:
    """FastVLM captioner"""
    def __init__(self, model_path="/Users/wen-chungcheng/ml-fastvlm"):
        print(f"[FastVLM Captioner] Initializing with model path: {model_path}")
        sys.path.insert(0, model_path)
        from generate import load_model, generate
        
        print("[FastVLM Captioner] Loading model...")
        self.model, self.processor = load_model("mlx-community/Qwen2.5-VL-3B-Instruct-8bit")
        self.generate_fn = generate
        print("[FastVLM Captioner] ✓ Model loaded successfully")
        
    def caption_image(self, image_path, prompt="Describe this image in detail."):
        try:
            print(f"[FastVLM Captioner] Processing {image_path}")
            
            image = Image.open(image_path).convert('RGB')
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            input_text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
            output = self.generate_fn(
                self.model, self.processor, image, input_text,
                max_tokens=512, temp=0.7, verbose=False
            )
            
            print(f"[FastVLM Captioner] Generated caption: {output}")
            return output.strip()
            
        except Exception as e:
            print(f"[FastVLM Captioner] Error: {e}")
            traceback.print_exc()
            return f"Error generating caption: {str(e)}"


class GemmaMlxVlmCaptioner:
    """Gemma MLX VLM captioner"""
    def __init__(self, model_path="mlx-community/paligemma-3b-mix-448-8bit"):
        print(f"[Gemma MLX VLM Captioner] Initializing with model: {model_path}")
        import mlx.core as mx
        from mlx_vlm import load, generate
        from mlx_vlm.prompt_utils import apply_chat_template
        from mlx_vlm.utils import load_config
        
        self.model, self.processor = load(model_path)
        self.config = load_config(model_path)
        self.generate_fn = generate
        
        print("[Gemma MLX VLM Captioner] ✓ Model loaded successfully")
        
    def caption_image(self, image_path, prompt="caption en"):
        try:
            print(f"[Gemma MLX VLM Captioner] Processing {image_path}")
            
            output = self.generate_fn(
                self.model,
                self.processor,
                image_path,
                prompt,
                max_tokens=512,
                temp=0.7,
                verbose=False
            )
            
            print(f"[Gemma MLX VLM Captioner] Generated caption: {output}")
            return output.strip()
            
        except Exception as e:
            print(f"[Gemma MLX VLM Captioner] Error: {e}")
            traceback.print_exc()
            return f"Error generating caption: {str(e)}"


class YOLOCaptioner:
    """YOLO-based object detector for ground robot"""
    
    def __init__(self, model_path="trained models/obi_detect/yolo26x-best-custom.pt", conf_threshold=0.25, iou_threshold=0.45):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model weights
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
        
        Returns:
            tuple: (caption_text, detection_results_dict, annotated_image_path)
        """
        try:
            # Run YOLO prediction
            results = self.model(image_path, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
            
            # Extract detection information
            detection_results = {
                'classes': [],
                'bounding_boxes': [],
                'confidences': [],
                'class_names': [],
                'detection_type': 'yolo'  # Mark as regular YOLO
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


class YOLOOBBCaptioner:
    """YOLO-OBB (Oriented Bounding Box) detector for aerial robot"""
    
    def __init__(self, model_path="trained models/obb_detect/yolo26x-obb-custom-trained.pt", conf_threshold=0.25, iou_threshold=0.45):
        """
        Initialize YOLO-OBB detector for oriented bounding boxes
        
        Args:
            model_path: Path to YOLO-OBB model weights
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
        """
        try:
            from ultralytics import YOLO
            print(f"[YOLO-OBB Captioner] Loading YOLO-OBB model from {model_path}...")
            self.model = YOLO(model_path)
            self.conf_threshold = conf_threshold
            self.iou_threshold = iou_threshold
            print(f"[YOLO-OBB Captioner] ✓ Model loaded successfully")
        except Exception as e:
            print(f"[YOLO-OBB Captioner] ❌ Failed to load model: {e}")
            raise
    
    def caption_image(self, image_path, prompt=None):
        """
        Generate caption from YOLO-OBB detections
        
        Returns:
            tuple: (caption_text, detection_results_dict, annotated_image_path)
        """
        try:
            # Run YOLO-OBB prediction
            results = self.model(image_path, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
            
            # Extract detection information
            detection_results = {
                'classes': [],
                'bounding_boxes': [],  # Will contain oriented boxes
                'confidences': [],
                'class_names': [],
                'detection_type': 'yolo-obb'  # Mark as YOLO-OBB
            }
            
            if len(results) > 0:
                result = results[0]
                
                # Extract OBB boxes, classes, and confidences
                if result.obb is not None and len(result.obb) > 0:
                    obb = result.obb
                    
                    # Get class IDs, names, and confidences
                    class_ids = obb.cls.int().cpu().tolist()
                    confidences = obb.conf.cpu().tolist()
                    
                    # Get oriented boxes as 4-point polygons
                    xyxyxyxy = obb.xyxyxyxy.cpu().tolist()  # [[x1,y1,x2,y2,x3,y3,x4,y4], ...]
                    
                    for cls_id, conf, box in zip(class_ids, confidences, xyxyxyxy):
                        class_name = result.names[cls_id]
                        detection_results['classes'].append(cls_id)
                        detection_results['class_names'].append(class_name)
                        detection_results['confidences'].append(round(conf, 3))
                        
                        # Flatten box if nested (handle different YOLO-OBB formats)
                        if isinstance(box[0], (list, tuple)):
                            # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                            box_flat = [coord for point in box for coord in point]
                        else:
                            # Format: [x1,y1,x2,y2,x3,y3,x4,y4]
                            box_flat = box
                        
                        # Store 4-point polygon (rotated box)
                        detection_results['bounding_boxes'].append([
                            round(box_flat[0], 2), round(box_flat[1], 2),  # Point 1
                            round(box_flat[2], 2), round(box_flat[3], 2),  # Point 2
                            round(box_flat[4], 2), round(box_flat[5], 2),  # Point 3
                            round(box_flat[6], 2), round(box_flat[7], 2)   # Point 4
                        ])
                    
                    # Generate text caption
                    class_counts = {}
                    for name in detection_results['class_names']:
                        class_counts[name] = class_counts.get(name, 0) + 1
                    
                    caption_parts = [f"{count} {name}" if count > 1 else name 
                                   for name, count in class_counts.items()]
                    caption = "Detected (OBB): " + ", ".join(caption_parts)
                    
                    # Save annotated image
                    annotated_path = image_path.replace('.jpg', '_yolo_obb.jpg').replace('.png', '_yolo_obb.png')
                    result.save(filename=annotated_path)
                    
                    print(f"[YOLO-OBB Captioner] Detected {len(detection_results['classes'])} objects: {caption}")
                    return caption, detection_results, annotated_path
                else:
                    return "No objects detected (OBB)", detection_results, image_path
            else:
                return "No objects detected (OBB)", detection_results, image_path
                
        except Exception as e:
            print(f"[YOLO-OBB Captioner] ❌ Error during detection: {e}")
            import traceback
            traceback.print_exc()
            return f"Detection error (OBB): {str(e)}", {}, image_path


class MultimodalMemoryItem(MemoryItem):
    """Extended memory item with audio captioning and multi-robot support"""
    def __init__(self, caption, time, position, theta, robot_id, audio_caption=None, detection_results=None, robot_data=None):
        super().__init__(
            caption=caption,
            time=time,
            position=position,
            theta=theta,
            robot_id=robot_id,
            audio_caption=audio_caption,
            detection_results=detection_results,
            robot_data=robot_data
        )


class EnhancedMultiRobotMemoryBuilder:
    def __init__(self, 
                 collection_name="webots_multirobot",
                 db_ip="127.0.0.1",
                 visual_backend="YOLO",
                 audio_backend="ACT",
                 audio_device="BlackHole",
                 enable_audio=True,
                 ground_data_dir="/tmp/webots_memory_ground",
                 aerial_data_dir="/tmp/webots_memory_aerial"):
        
        self.collection_name = collection_name
        self.db_ip = db_ip
        self.visual_backend = visual_backend
        self.audio_backend = audio_backend
        self.audio_device = audio_device
        self.enable_audio = enable_audio
        self.ground_data_dir = Path(ground_data_dir)
        self.aerial_data_dir = Path(aerial_data_dir)
        
        # Create data directories if they don't exist
        self.ground_data_dir.mkdir(parents=True, exist_ok=True)
        self.aerial_data_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[MultiRobotMemoryBuilder] Ground robot data: {self.ground_data_dir}")
        print(f"[MultiRobotMemoryBuilder] Aerial robot data: {self.aerial_data_dir}")
        
        # Initialize memory
        self.memory = MilvusMemory(
            db_collection_name=collection_name,
            db_ip=db_ip
        )
        
        # Queues for different data types
        self.ground_visual_queue = queue.Queue()
        self.aerial_visual_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.memory_queue = queue.Queue()
        
        # Thread control
        self.running = False
        self.threads = []
        
        # Initialize captioners based on backends
        self._initialize_captioners()
        
    def _initialize_captioners(self):
        """Initialize visual and audio captioners"""
        
        # Initialize YOLO for ground robot
        print(f"[MultiRobotMemoryBuilder] Initializing YOLO for ground robot...")
        try:
            self.ground_visual_captioner = YOLOCaptioner(
                model_path="/Users/wen-chungcheng/ultralytics/trained models/obi_detect/yolo26x-best-custom.pt"
            )
        except Exception as e:
            print(f"[MultiRobotMemoryBuilder] ❌ Failed to initialize ground YOLO: {e}")
            raise
        
        # Initialize YOLO-OBB for aerial robot
        print(f"[MultiRobotMemoryBuilder] Initializing YOLO-OBB for aerial robot...")
        try:
            self.aerial_visual_captioner = YOLOOBBCaptioner(
                model_path="/Users/wen-chungcheng/ultralytics/trained models/obb_detect/yolo26x-obb-custom-trained.pt"
            )
        except Exception as e:
            print(f"[MultiRobotMemoryBuilder] ❌ Failed to initialize aerial YOLO-OBB: {e}")
            raise
        
        # Initialize audio captioner if enabled
        if self.enable_audio:
            print(f"[MultiRobotMemoryBuilder] Initializing audio backend: {self.audio_backend}")
            if self.audio_backend == "ACT":
                try:
                    self.audio_captioner = AudioCaptioningModule()
                except Exception as e:
                    print(f"[MultiRobotMemoryBuilder] ❌ Failed to initialize ACT: {e}")
                    self.audio_captioner = None
            else:
                self.audio_captioner = None
        else:
            self.audio_captioner = None
            
    def ground_visual_processing_thread(self):
        """Process visual data from ground robot (Spot)"""
        print("[Ground Visual Thread] Started")
        
        empty_check_count = 0
        max_empty_checks = 300  # 30 seconds
        
        while self.running:
            try:
                # Check for JSON files in ground robot directory
                data_files = sorted(self.ground_data_dir.glob("memory_*.json"))
                
                if not data_files:
                    empty_check_count += 1
                    if empty_check_count >= max_empty_checks:
                        print(f"[Ground Visual Thread] No data files found for {max_empty_checks * 0.1:.0f}s. Terminating...")
                        self.running = False
                        break
                    
                    # Log progress every 5 seconds
                    if empty_check_count % 50 == 0:
                        print(f"[Ground Visual Thread] Waiting for data files... ({empty_check_count * 0.1:.1f}s)")
                    
                    time.sleep(0.1)
                    continue
                
                # Reset counter when files found
                empty_check_count = 0
                
                # Process oldest file
                json_file = data_files[0]
                
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                image_path = data['image_path']
                timestamp = data['timestamp']
                position = data['position']
                theta = data['theta']
                
                # Generate caption with YOLO
                caption, detection_results, annotated_path = self.ground_visual_captioner.caption_image(image_path)
                
                # Replace original image with annotated version
                if annotated_path != image_path and os.path.exists(annotated_path):
                    shutil.move(annotated_path, image_path)
                    print(f"[Ground Visual Thread] Replaced frame with annotated version")
                
                # Queue for memory integration
                self.ground_visual_queue.put({
                    'robot_id': 'ground',
                    'caption': caption,
                    'timestamp': timestamp,
                    'position': position,
                    'theta': theta,
                    'detection_results': detection_results
                })
                
                # Delete processed file
                json_file.unlink()
                
                print(f"[Ground Visual Thread] Processed: {caption[:50]}...")
                
            except Exception as e:
                print(f"[Ground Visual Thread] Error: {e}")
                traceback.print_exc()
                time.sleep(0.5)
    
    def aerial_visual_processing_thread(self):
        """Process visual data from aerial robot (Mavic 2 Pro)"""
        print("[Aerial Visual Thread] Started")
        
        empty_check_count = 0
        max_empty_checks = 300  # 30 seconds
        
        while self.running:
            try:
                # Check for JSON files in aerial robot directory
                data_files = sorted(self.aerial_data_dir.glob("memory_*.json"))
                
                if not data_files:
                    empty_check_count += 1
                    if empty_check_count >= max_empty_checks:
                        print(f"[Aerial Visual Thread] No data files found for {max_empty_checks * 0.1:.0f}s. Terminating...")
                        self.running = False
                        break
                    
                    # Log progress every 5 seconds
                    if empty_check_count % 50 == 0:
                        print(f"[Aerial Visual Thread] Waiting for data files... ({empty_check_count * 0.1:.1f}s)")
                    
                    time.sleep(0.1)
                    continue
                
                # Reset counter when files found
                empty_check_count = 0
                
                # Process oldest file
                json_file = data_files[0]
                
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                image_path = data['image_path']
                timestamp = data['timestamp']
                position = data['position']
                theta = data['theta']
                
                # Generate caption with YOLO-OBB
                caption, detection_results, annotated_path = self.aerial_visual_captioner.caption_image(image_path)
                
                # Replace original image with annotated version
                if annotated_path != image_path and os.path.exists(annotated_path):
                    shutil.move(annotated_path, image_path)
                    print(f"[Aerial Visual Thread] Replaced frame with annotated version")
                
                # Queue for memory integration
                self.aerial_visual_queue.put({
                    'robot_id': 'aerial',
                    'caption': caption,
                    'timestamp': timestamp,
                    'position': position,
                    'theta': theta,
                    'detection_results': detection_results
                })
                
                # Delete processed file
                json_file.unlink()
                
                print(f"[Aerial Visual Thread] Processed: {caption[:50]}...")
                
            except Exception as e:
                print(f"[Aerial Visual Thread] Error: {e}")
                traceback.print_exc()
                time.sleep(0.5)
    
    def audio_processing_thread(self):
        """Process audio data (shared across both robots)"""
        if not self.enable_audio or self.audio_captioner is None:
            print("[Audio Thread] Disabled")
            return
        
        print("[Audio Thread] Started")
        
        # Audio recording settings
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 16000
        RECORD_SECONDS = 5  # Duration of each audio clip
        
        p = pyaudio.PyAudio()
        
        # Find audio device
        device_index = None
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if self.audio_device.lower() in info['name'].lower():
                device_index = i
                break
        
        if device_index is None:
            print(f"[Audio Thread] ❌ Could not find audio device: {self.audio_device}")
            return
        
        print(f"[Audio Thread] Using device: {p.get_device_info_by_index(device_index)['name']}")
        
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            print("[Audio Thread] Recording started")
            
            while self.running:
                try:
                    # Record audio
                    frames = []
                    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                        if not self.running:
                            break
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    
                    if not self.running:
                        break
                    
                    # Save to temporary file
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    import wave
                    wf = wave.open(temp_audio.name, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    
                    # Generate caption
                    caption = self.audio_captioner.generate_caption(temp_audio.name)
                    
                    # Queue for memory integration
                    self.audio_queue.put({
                        'audio_caption': caption,
                        'timestamp': time.time()
                    })
                    
                    print(f"[Audio Thread] Processed: {caption[:50]}...")
                    
                    # Cleanup
                    os.unlink(temp_audio.name)
                    
                except Exception as e:
                    print(f"[Audio Thread] Error during recording: {e}")
                    time.sleep(1)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"[Audio Thread] Error: {e}")
            traceback.print_exc()
        finally:
            p.terminate()
            print("[Audio Thread] Stopped")
    
    def memory_integration_thread(self):
        """Integrate visual and audio data into memory, combining robots by timestamp"""
        print("[Memory Integration Thread] Started")
        
        # Buffers for matching timestamps
        ground_visual_buffer = deque(maxlen=100)
        aerial_visual_buffer = deque(maxlen=100)
        audio_buffer = deque(maxlen=100)
        
        last_insert_time = time.time()
        
        while self.running:
            try:
                # Collect visual data from ground robot
                while not self.ground_visual_queue.empty():
                    ground_visual_buffer.append(self.ground_visual_queue.get())
                
                # Collect visual data from aerial robot
                while not self.aerial_visual_queue.empty():
                    aerial_visual_buffer.append(self.aerial_visual_queue.get())
                
                # Collect audio data
                if self.enable_audio:
                    while not self.audio_queue.empty():
                        audio_buffer.append(self.audio_queue.get())
                
                # Group visual data by timestamp (within 0.5 second window)
                # Find matching ground and aerial data
                for ground_visual in list(ground_visual_buffer):
                    # Find closest aerial visual within 0.5 seconds
                    matching_aerial = None
                    min_time_diff = float('inf')
                    
                    for aerial_visual in list(aerial_visual_buffer):
                        time_diff = abs(aerial_visual['timestamp'] - ground_visual['timestamp'])
                        if time_diff < 0.5 and time_diff < min_time_diff:
                            matching_aerial = aerial_visual
                            min_time_diff = time_diff
                    
                    if matching_aerial:
                        # We have data from both robots at approximately the same time
                        # Find closest audio caption
                        audio_caption = None
                        if audio_buffer:
                            closest_audio = min(audio_buffer, key=lambda x: abs(x['timestamp'] - ground_visual['timestamp']))
                            if abs(closest_audio['timestamp'] - ground_visual['timestamp']) < 10:  # Within 10 seconds
                                audio_caption = closest_audio['audio_caption']
                        
                        # Create combined robot_data
                        robot_data = {
                            'ground': {
                                'position': ground_visual['position'],
                                'theta': ground_visual['theta'],
                                'caption': ground_visual['caption'],
                                'detection_results': ground_visual['detection_results']
                            },
                            'aerial': {
                                'position': matching_aerial['position'],
                                'theta': matching_aerial['theta'],
                                'caption': matching_aerial['caption'],
                                'detection_results': matching_aerial['detection_results']
                            }
                        }
                        
                        # Use average timestamp
                        avg_timestamp = (ground_visual['timestamp'] + matching_aerial['timestamp']) / 2
                        
                        # Use ground robot's position as primary (for spatial queries)
                        primary_position = ground_visual['position']
                        primary_theta = ground_visual['theta']
                        
                        # Combine captions
                        combined_caption = f"Ground: {ground_visual['caption']} | Aerial: {matching_aerial['caption']}"
                        
                        # Combine detection results
                        combined_detections = {
                            'ground': ground_visual['detection_results'],
                            'aerial': matching_aerial['detection_results']
                        }
                        
                        # Create memory item with both robots' data
                        memory_item = MultimodalMemoryItem(
                            caption=combined_caption,
                            time=avg_timestamp,
                            position=primary_position,
                            theta=primary_theta,
                            robot_id='ground,aerial',
                            audio_caption=audio_caption or '',
                            detection_results=combined_detections,
                            robot_data=robot_data
                        )
                        
                        self.memory.insert(memory_item)
                        ground_visual_buffer.remove(ground_visual)
                        aerial_visual_buffer.remove(matching_aerial)
                        last_insert_time = time.time()
                        
                        print(f"[Memory Integration] Inserted combined memory from both robots at {datetime.fromtimestamp(avg_timestamp).strftime('%H:%M:%S')}")
                
                # Check for stale data
                if time.time() - last_insert_time > 60:
                    print("[Memory Integration] No new data for 60s, checking threads...")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[Memory Integration Thread] Error: {e}")
                traceback.print_exc()
                time.sleep(1)
        
        print("[Memory Integration Thread] Stopped")
    
    def start(self):
        """Start all processing threads"""
        print("\n" + "="*60)
        print("🤖 Starting Multi-Robot Enhanced Memory Builder")
        print("="*60)
        print(f"Collection: {self.collection_name}")
        print(f"Database: {self.db_ip}")
        print(f"Ground Robot: YOLO detection")
        print(f"Aerial Robot: YOLO-OBB detection")
        print(f"Audio Backend: {self.audio_backend if self.enable_audio else 'Disabled'}")
        print(f"Ground Data: {self.ground_data_dir}")
        print(f"Aerial Data: {self.aerial_data_dir}")
        print("="*60 + "\n")
        
        self.running = True
        
        # Start threads
        threads = [
            threading.Thread(target=self.ground_visual_processing_thread, daemon=True),
            threading.Thread(target=self.aerial_visual_processing_thread, daemon=True),
            threading.Thread(target=self.audio_processing_thread, daemon=True),
            threading.Thread(target=self.memory_integration_thread, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
            self.threads.append(thread)
        
        print("All threads started. Press Ctrl+C to stop...\n")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop all processing threads"""
        print("Stopping all threads...")
        self.running = False
        
        for thread in self.threads:
            thread.join(timeout=5)
        
        print("All threads stopped.")
        print("Memory builder shutdown complete.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Robot Enhanced Memory Builder')
    parser.add_argument('--collection', type=str, default='webots_multirobot',
                      help='Milvus collection name')
    parser.add_argument('--db-ip', type=str, default='127.0.0.1',
                      help='Milvus database IP address')
    parser.add_argument('--audio-backend', type=str, default='ACT', choices=['ACT'],
                      help='Audio captioning backend')
    parser.add_argument('--audio-device', type=str, default='BlackHole',
                      help='Audio input device name')
    parser.add_argument('--no-audio', action='store_true',
                      help='Disable audio captioning')
    parser.add_argument('--ground-data-dir', type=str, default='/tmp/webots_memory_ground',
                      help='Ground robot data directory')
    parser.add_argument('--aerial-data-dir', type=str, default='/tmp/webots_memory_aerial',
                      help='Aerial robot data directory')
    
    args = parser.parse_args()
    
    builder = EnhancedMultiRobotMemoryBuilder(
        collection_name=args.collection,
        db_ip=args.db_ip,
        visual_backend='YOLO',  # Fixed: YOLO for ground, YOLO-OBB for aerial
        audio_backend=args.audio_backend,
        audio_device=args.audio_device,
        enable_audio=not args.no_audio,
        ground_data_dir=args.ground_data_dir,
        aerial_data_dir=args.aerial_data_dir
    )
    
    builder.start()
