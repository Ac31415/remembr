#!/usr/bin/env python3
"""
Phi-3-Vision-MLX Memory Builder - UPDATED VERSION
Enhanced with improved prompting and better integration
"""

import sys
import os
import time
import threading
import queue
import json
import traceback
from pathlib import Path
from PIL import Image
import numpy as np

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

# Import ReMEmbR components
from remembr.memory.memory import MemoryItem
from remembr.memory.milvus_memory import MilvusMemory
from remembr.captioners.phi3_vision_mlx_captioner_langchain_langgraph import Phi3VisionMLXCaptioner, Phi3VisionMLXCaptionerAdvanced

class Phi3VisionMLXMemoryBuilder:
    def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1", advanced_mode=False):
        print(f"[Phi-3-Vision-MLX Memory Builder] Starting with enhanced prompting and native Apple Silicon optimization...")
        print(f"[Phi-3-Vision-MLX Memory Builder] Collection: {collection_name}")
        print(f"[Phi-3-Vision-MLX Memory Builder] Database IP: {db_ip}")
        print(f"[Phi-3-Vision-MLX Memory Builder] Advanced mode: {advanced_mode}")
        
        # Initialize memory
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        print("[Phi-3-Vision-MLX Memory Builder] ✓ Memory initialized")
        
        # Initialize Phi-3-Vision-MLX captioner with enhanced prompting
        self.captioner = None
        self.advanced_mode = advanced_mode
        self.init_captioner()
        
        # Data directories
        self.data_dir = Path("/tmp/webots_memory")
        self.data_dir.mkdir(exist_ok=True)
        
        # Processing queue
        self.processing_queue = queue.Queue()
        self.running = True
        
        # Performance tracking
        self.processed_count = 0
        self.start_time = time.time()
        
        # Scenario detection for adaptive prompting
        self.scenario_detector = {
            'exploration': lambda pos: abs(pos[0]) > 0.3 or abs(pos[1]) > 0.3,
            'navigation': lambda pos: abs(pos[0]) < 0.3 and abs(pos[1]) < 0.3,
            'interaction': lambda pos: True  # Default fallback
        }
        
        print("[Phi-3-Vision-MLX Memory Builder] ✓ Ready with enhanced prompting and native Apple Silicon acceleration")
    
    def init_captioner(self):
        """Initialize Phi-3-Vision-MLX captioner with enhanced prompting"""
        print("[Phi-3-Vision-MLX Memory Builder] Initializing enhanced Phi-3-Vision-MLX captioner...")
        
        try:
            if self.advanced_mode:
                self.captioner = Phi3VisionMLXCaptionerAdvanced(
                    use_quantization=True,
                    enable_advanced_features=True
                )
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Advanced Phi-3-Vision-MLX captioner with scenario-specific prompts ready")
            else:
                self.captioner = Phi3VisionMLXCaptioner(
                    quantize_model=True,
                    quantize_cache=False
                )
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Enhanced Phi-3-Vision-MLX captioner with detailed prompts ready")
            
            # Test the captioner
            if self.captioner.test_model():
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Enhanced captioner test successful")
            else:
                print("[Phi-3-Vision-MLX Memory Builder] ⚠ Enhanced captioner test failed, but continuing...")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced captioner initialization failed: {e}")
            print("[Phi-3-Vision-MLX Memory Builder] Falling back to simple captioning")
            self.captioner = None
    
    def detect_scenario(self, position):
        """Detect scenario based on robot position for adaptive prompting"""
        for scenario, detector in self.scenario_detector.items():
            if detector(position):
                return scenario
        return 'exploration'  # Default
    
    def generate_enhanced_simple_caption(self, image_path, position, theta):
        """Generate enhanced simple caption matching captioner_node.py style"""
        x, y, z = position
        
        try:
            image = Image.open(image_path)
            width, height = image.size
            
            # Enhanced caption with more detail - matching captioner_node.py style
            if abs(x) < 0.1 and abs(y) < 0.1:
                return (f"Robot positioned at starting location, camera capturing {width}x{height} view "
                       f"of the simulation environment. The scene shows the initial exploration area "
                       f"with various objects and environmental features visible in the camera frame.")
            elif x > 0.5:
                return (f"Robot actively exploring forward into new territory at position ({x:.2f}, {y:.2f}). "
                       f"Camera shows detailed view of previously unexplored environment with objects, "
                       f"pathways, and spatial features that provide navigation context for future reference.")
            elif abs(y) > 0.3:
                return (f"Robot executing lateral movement to position ({x:.2f}, {y:.2f}), camera capturing "
                       f"side perspective of the environment. The view includes environmental features, "
                       f"spatial relationships, and objects that help define the layout of this area.")
            else:
                return (f"Robot navigating through simulation environment at coordinates ({x:.2f}, {y:.2f}). "
                       f"Camera provides detailed documentation of the scene including objects, environmental "
                       f"features, spatial arrangements, and contextual details important for navigation memory.")
                
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Error analyzing image: {e}")
            return (f"Robot camera documentation at position ({x:.2f}, {y:.2f}, {z:.2f}). "
                   f"Scene captured shows simulation environment with various objects and features "
                   f"providing spatial and contextual information for navigation and exploration tasks.")
    
    def process_memory_item(self, data):
        """Process a single memory item using enhanced Phi-3-Vision-MLX"""
        try:
            image_path = data['image_path']
            position = data['position']
            theta = data['theta']
            timestamp = data['timestamp']
            
            print(f"[Phi-3-Vision-MLX Memory Builder] Processing memory item with enhanced prompting: {image_path}")
            
            # Verify image file exists
            if not os.path.exists(image_path):
                print(f"[Phi-3-Vision-MLX Memory Builder] Error: Image file not found: {image_path}")
                caption = self.generate_enhanced_simple_caption(image_path, position, theta)
            else:
                # Generate caption using enhanced Phi-3-Vision-MLX
                if self.captioner:
                    try:
                        print("[Phi-3-Vision-MLX Memory Builder] Using enhanced Phi-3-Vision-MLX captioner...")
                        
                        # Verify file is readable
                        file_size = os.path.getsize(image_path)
                        print(f"[Phi-3-Vision-MLX Memory Builder] Image file size: {file_size} bytes")
                        
                        # Detect scenario for adaptive prompting if using advanced mode
                        if self.advanced_mode and hasattr(self.captioner, 'caption_with_scenario'):
                            scenario = self.detect_scenario(position)
                            print(f"[Phi-3-Vision-MLX Memory Builder] Detected scenario: {scenario}")
                            
                            start_time = time.time()
                            caption = self.captioner.caption_with_scenario(image_path, scenario=scenario)
                            end_time = time.time()
                            
                            print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced scenario-specific caption generated in {end_time - start_time:.2f}s")
                        else:
                            start_time = time.time()
                            caption = self.captioner.caption_image(image_path)
                            end_time = time.time()
                            
                            print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced detailed caption generated in {end_time - start_time:.2f}s")
                        
                        print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced caption: {caption}")
                        
                    except Exception as e:
                        print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced captioning failed: {e}")
                        caption = self.generate_enhanced_simple_caption(image_path, position, theta)
                        print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced fallback caption: {caption}")
                else:
                    caption = self.generate_enhanced_simple_caption(image_path, position, theta)
                    print(f"[Phi-3-Vision-MLX Memory Builder] Enhanced simple caption: {caption}")
            
            # Create memory item
            memory_item = MemoryItem(
                caption=caption,
                time=timestamp,
                position=position,
                theta=theta
            )
            
            # Insert into memory
            self.memory.insert(memory_item)
            self.processed_count += 1
            
            # Performance tracking
            elapsed_time = time.time() - self.start_time
            avg_time_per_item = elapsed_time / self.processed_count if self.processed_count > 0 else 0
            
            print(f"[Phi-3-Vision-MLX Memory Builder] ✓ Enhanced memory item {self.processed_count} inserted at {timestamp:.2f}s")
            print(f"[Phi-3-Vision-MLX Memory Builder] Average processing time: {avg_time_per_item:.2f}s per item")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Error processing memory item: {e}")
            traceback.print_exc()
    
    def run(self):
        """Main processing loop with enhanced batch optimization"""
        print("[Phi-3-Vision-MLX Memory Builder] Starting enhanced processing loop...")
        
        batch_size = 3 if self.advanced_mode else 5  # Smaller batches for advanced mode
        batch_timeout = 2.0
        
        try:
            while self.running:
                try:
                    # Check for new data files
                    data_files = list(self.data_dir.glob("memory_*.json"))
                    
                    if data_files:
                        print(f"[Phi-3-Vision-MLX Memory Builder] Found {len(data_files)} files to process with enhanced methods")
                        
                        # Load data from files
                        batch_data = []
                        processed_files = []
                        
                        for data_file in data_files[:batch_size]:
                            try:
                                print(f"[Phi-3-Vision-MLX Memory Builder] Loading file for enhanced processing: {data_file}")
                                with open(data_file, 'r') as f:
                                    data = json.load(f)
                                
                                batch_data.append(data)
                                processed_files.append(data_file)
                                
                            except Exception as e:
                                print(f"[Phi-3-Vision-MLX Memory Builder] Error loading file {data_file}: {e}")
                                try:
                                    data_file.unlink()
                                    print(f"[Phi-3-Vision-MLX Memory Builder] Removed corrupted file: {data_file}")
                                except:
                                    pass
                        
                        # Process the batch with enhanced methods
                        if batch_data:
                            for data in batch_data:
                                self.process_memory_item(data)
                            
                            # Remove processed files
                            for data_file in processed_files:
                                try:
                                    data_file.unlink()
                                    print(f"[Phi-3-Vision-MLX Memory Builder] Removed processed file: {data_file}")
                                except Exception as e:
                                    print(f"[Phi-3-Vision-MLX Memory Builder] Error removing file: {e}")
                    
                    # Sleep briefly to avoid busy waiting
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    print("[Phi-3-Vision-MLX Memory Builder] Stopping...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"[Phi-3-Vision-MLX Memory Builder] Error in enhanced main loop: {e}")
                    time.sleep(1)
        
        finally:
            print("[Phi-3-Vision-MLX Memory Builder] Cleaning up enhanced processing...")
            self.print_performance_stats()
        
        print("[Phi-3-Vision-MLX Memory Builder] Enhanced processing stopped")
    
    def print_performance_stats(self):
        """Print enhanced performance statistics"""
        elapsed_time = time.time() - self.start_time
        if self.processed_count > 0:
            avg_time = elapsed_time / self.processed_count
            print(f"\n[Phi-3-Vision-MLX Memory Builder] Enhanced Performance Statistics:")
            print(f"  Total items processed: {self.processed_count}")
            print(f"  Total time: {elapsed_time:.2f}s")
            print(f"  Average time per item: {avg_time:.2f}s")
            print(f"  Processing rate: {self.processed_count / elapsed_time:.2f} items/s")
            print(f"  Enhanced prompting mode: {'Advanced' if self.advanced_mode else 'Standard'}")
        else:
            print(f"\n[Phi-3-Vision-MLX Memory Builder] No items processed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Phi-3-Vision-MLX Memory Builder')
    parser.add_argument('--collection', '-c', default='webots_simulation', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--advanced', '-a', action='store_true', help='Use advanced captioner with scenario-specific prompts')
    
    args = parser.parse_args()
    
    print("🤖 Enhanced Phi-3-Vision-MLX Memory Builder")
    print("Detailed Prompting + Native Apple Silicon Acceleration")
    print("="*60)
    
    builder = Phi3VisionMLXMemoryBuilder(
        collection_name=args.collection,
        db_ip=args.db_ip,
        advanced_mode=args.advanced
    )
    
    try:
        builder.run()
    except KeyboardInterrupt:
        print("\n[Enhanced Phi-3-Vision-MLX Memory Builder] Interrupted by user")