#!/usr/bin/env python3
"""
Phi-3-Vision-MLX Memory Builder - Native Apple Silicon optimization
Uses the phi_3_vision_mlx framework for optimal performance on Mac M3 Max
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
from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner, Phi3VisionMLXCaptionerAdvanced

class Phi3VisionMLXMemoryBuilder:
    def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1", advanced_mode=False):
        print(f"[Phi-3-Vision-MLX Memory Builder] Starting with native Apple Silicon optimization...")
        print(f"[Phi-3-Vision-MLX Memory Builder] Collection: {collection_name}")
        print(f"[Phi-3-Vision-MLX Memory Builder] Database IP: {db_ip}")
        print(f"[Phi-3-Vision-MLX Memory Builder] Advanced mode: {advanced_mode}")
        
        # Initialize memory
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        print("[Phi-3-Vision-MLX Memory Builder] ✓ Memory initialized")
        
        # Initialize Phi-3-Vision-MLX captioner
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
        
        print("[Phi-3-Vision-MLX Memory Builder] ✓ Ready with native Apple Silicon acceleration")
    
    def init_captioner(self):
        """Initialize Phi-3-Vision-MLX captioner"""
        print("[Phi-3-Vision-MLX Memory Builder] Initializing Phi-3-Vision-MLX captioner...")
        
        try:
            if self.advanced_mode:
                self.captioner = Phi3VisionMLXCaptionerAdvanced(
                    use_quantization=True,
                    enable_advanced_features=True
                )
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Advanced Phi-3-Vision-MLX captioner ready")
            else:
                self.captioner = Phi3VisionMLXCaptioner(
                    quantize_model=True,
                    quantize_cache=False
                )
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Standard Phi-3-Vision-MLX captioner ready")
            
            # Test the captioner
            if self.captioner.test_model():
                print("[Phi-3-Vision-MLX Memory Builder] ✓ Captioner test successful")
            else:
                print("[Phi-3-Vision-MLX Memory Builder] ⚠ Captioner test failed, but continuing...")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Captioner initialization failed: {e}")
            print("[Phi-3-Vision-MLX Memory Builder] Falling back to simple captioning")
            self.captioner = None
    
    def generate_simple_caption(self, image_path, position, theta):
        """Generate simple caption without Phi-3-Vision-MLX as fallback"""
        x, y, z = position
        
        try:
            image = Image.open(image_path)
            width, height = image.size
            
            # Simple image analysis
            if abs(x) < 0.1 and abs(y) < 0.1:
                return f"Robot at starting position, capturing {width}x{height} camera view of simulation environment"
            elif x > 0.5:
                return f"Robot exploring forward area ({x:.2f}, {y:.2f}), camera shows new territory ahead"
            elif abs(y) > 0.3:
                return f"Robot moved laterally to ({x:.2f}, {y:.2f}), camera captures side view of environment"
            else:
                return f"Robot navigating at ({x:.2f}, {y:.2f}), camera shows detailed simulation environment"
                
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Error analyzing image: {e}")
            return f"Robot camera view at position ({x:.2f}, {y:.2f}, {z:.2f}) - captured simulation scene"
    
    def process_memory_item(self, data):
        """Process a single memory item using Phi-3-Vision-MLX"""
        try:
            image_path = data['image_path']
            position = data['position']
            theta = data['theta']
            timestamp = data['timestamp']
            
            print(f"[Phi-3-Vision-MLX Memory Builder] Processing memory item: {image_path}")
            
            # Verify image file exists
            if not os.path.exists(image_path):
                print(f"[Phi-3-Vision-MLX Memory Builder] Error: Image file not found: {image_path}")
                caption = f"Robot camera view at position ({position[0]:.2f}, {position[1]:.2f}) - image file missing"
            else:
                # Generate caption using Phi-3-Vision-MLX
                if self.captioner:
                    try:
                        print("[Phi-3-Vision-MLX Memory Builder] Using Phi-3-Vision-MLX captioner...")
                        
                        # Verify file is readable
                        file_size = os.path.getsize(image_path)
                        print(f"[Phi-3-Vision-MLX Memory Builder] Image file size: {file_size} bytes")
                        
                        start_time = time.time()
                        caption = self.captioner.caption_image(image_path)
                        end_time = time.time()
                        
                        print(f"[Phi-3-Vision-MLX Memory Builder] Phi-3-Vision-MLX caption generated in {end_time - start_time:.2f}s: {caption}")
                        
                    except Exception as e:
                        print(f"[Phi-3-Vision-MLX Memory Builder] Phi-3-Vision-MLX captioning failed: {e}")
                        caption = self.generate_simple_caption(image_path, position, theta)
                        print(f"[Phi-3-Vision-MLX Memory Builder] Fallback caption: {caption}")
                else:
                    caption = self.generate_simple_caption(image_path, position, theta)
                    print(f"[Phi-3-Vision-MLX Memory Builder] Simple caption: {caption}")
            
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
            
            print(f"[Phi-3-Vision-MLX Memory Builder] ✓ Memory item {self.processed_count} inserted at {timestamp:.2f}s")
            print(f"[Phi-3-Vision-MLX Memory Builder] Average processing time: {avg_time_per_item:.2f}s per item")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Error processing memory item: {e}")
            traceback.print_exc()
    
    def process_batch_items(self, batch_data):
        """Process multiple memory items in batch for better efficiency"""
        if not self.captioner or not hasattr(self.captioner, 'caption_batch'):
            # Fall back to individual processing
            for data in batch_data:
                self.process_memory_item(data)
            return
        
        try:
            print(f"[Phi-3-Vision-MLX Memory Builder] Processing batch of {len(batch_data)} items...")
            
            # Extract images and verify they exist
            valid_items = []
            image_paths = []
            
            for data in batch_data:
                if os.path.exists(data['image_path']):
                    valid_items.append(data)
                    image_paths.append(data['image_path'])
            
            if not valid_items:
                print("[Phi-3-Vision-MLX Memory Builder] No valid images in batch")
                return
            
            # Generate captions in batch
            start_time = time.time()
            captions = self.captioner.caption_batch(image_paths)
            end_time = time.time()
            
            print(f"[Phi-3-Vision-MLX Memory Builder] Batch captions generated in {end_time - start_time:.2f}s")
            
            # Create and insert memory items
            for i, (data, caption) in enumerate(zip(valid_items, captions)):
                memory_item = MemoryItem(
                    caption=caption,
                    time=data['timestamp'],
                    position=data['position'],
                    theta=data['theta']
                )
                
                self.memory.insert(memory_item)
                self.processed_count += 1
                
                print(f"[Phi-3-Vision-MLX Memory Builder] ✓ Batch item {i+1}/{len(captions)} inserted")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX Memory Builder] Batch processing failed: {e}")
            # Fall back to individual processing
            for data in batch_data:
                self.process_memory_item(data)
    
    def run(self):
        """Main processing loop with batch optimization"""
        print("[Phi-3-Vision-MLX Memory Builder] Starting processing loop...")
        
        batch_size = 5  # Process in batches for better efficiency
        batch_timeout = 2.0  # Max time to wait for batch to fill
        
        try:
            while self.running:
                try:
                    # Check for new data files
                    data_files = list(self.data_dir.glob("memory_*.json"))
                    
                    if data_files:
                        print(f"[Phi-3-Vision-MLX Memory Builder] Found {len(data_files)} files to process")
                        
                        # Load data from files
                        batch_data = []
                        processed_files = []
                        
                        for data_file in data_files[:batch_size]:  # Limit batch size
                            try:
                                print(f"[Phi-3-Vision-MLX Memory Builder] Loading file: {data_file}")
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
                        
                        # Process the batch
                        if batch_data:
                            if len(batch_data) > 1 and self.captioner and hasattr(self.captioner, 'caption_batch'):
                                self.process_batch_items(batch_data)
                            else:
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
                    print(f"[Phi-3-Vision-MLX Memory Builder] Error in main loop: {e}")
                    time.sleep(1)
        
        finally:
            print("[Phi-3-Vision-MLX Memory Builder] Cleaning up...")
            self.print_performance_stats()
        
        print("[Phi-3-Vision-MLX Memory Builder] Stopped")
    
    def print_performance_stats(self):
        """Print performance statistics"""
        elapsed_time = time.time() - self.start_time
        if self.processed_count > 0:
            avg_time = elapsed_time / self.processed_count
            print(f"\n[Phi-3-Vision-MLX Memory Builder] Performance Statistics:")
            print(f"  Total items processed: {self.processed_count}")
            print(f"  Total time: {elapsed_time:.2f}s")
            print(f"  Average time per item: {avg_time:.2f}s")
            print(f"  Processing rate: {self.processed_count / elapsed_time:.2f} items/s")
        else:
            print(f"\n[Phi-3-Vision-MLX Memory Builder] No items processed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phi-3-Vision-MLX Memory Builder')
    parser.add_argument('--collection', '-c', default='webots_simulation', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--advanced', '-a', action='store_true', help='Use advanced captioner features')
    
    args = parser.parse_args()
    
    print("🤖 Phi-3-Vision-MLX Memory Builder")
    print("Native Apple Silicon Acceleration with phi_3_vision_mlx")
    print("="*60)
    
    builder = Phi3VisionMLXMemoryBuilder(
        collection_name=args.collection,
        db_ip=args.db_ip,
        advanced_mode=args.advanced
    )
    
    try:
        builder.run()
    except KeyboardInterrupt:
        print("\n[Phi-3-Vision-MLX Memory Builder] Interrupted by user")