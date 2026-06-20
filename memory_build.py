#!/usr/bin/env python3
"""
MLX-powered Memory Builder - CORRECTED VERSION
Uses proper MLX-VLM workflow with apply_chat_template
"""

import sys
import os
import time
import threading
import queue
import json
import tempfile
import glob
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
from remembr.captioners.mlx_llava_captioner import MLXLLaVACaptionerFinalFix

class MLXMemoryBuilderCorrected:
    def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1"):
        print(f"[MLX Memory Builder] Starting with corrected MLX-VLM workflow...")
        print(f"[MLX Memory Builder] Collection: {collection_name}")
        print(f"[MLX Memory Builder] Database IP: {db_ip}")
        
        # Initialize memory
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        print("[MLX Memory Builder] ✓ Memory initialized")
        
        # Initialize corrected MLX LLaVA captioner
        self.captioner = None
        self.init_captioner()
        
        # Data directories
        self.data_dir = Path("/tmp/webots_memory")
        self.data_dir.mkdir(exist_ok=True)
        
        # Processing queue
        self.processing_queue = queue.Queue()
        self.running = True
        
        print("[MLX Memory Builder] ✓ Ready with corrected MLX-VLM workflow")
    
    def init_captioner(self):
        """Initialize corrected MLX LLaVA captioner"""
        print("[MLX Memory Builder] Initializing corrected MLX LLaVA captioner...")
        
        try:
            self.captioner = MLXLLaVACaptionerFinalFix()
            print("[MLX Memory Builder] ✓ Corrected MLX LLaVA captioner ready")
            
        except Exception as e:
            print(f"[MLX Memory Builder] MLX captioner failed: {e}")
            print("[MLX Memory Builder] Falling back to simple captioning")
            self.captioner = None
    
    def generate_simple_caption(self, image_path, position, theta):
        """Generate simple caption without MLX as fallback"""
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
            print(f"[MLX Memory Builder] Error analyzing image: {e}")
            return f"Robot camera view at position ({x:.2f}, {y:.2f}, {z:.2f}) - captured simulation scene"
    
    def process_memory_item(self, data):
        """Process a single memory item using corrected MLX workflow"""
        try:
            image_path = data['image_path']
            position = data['position']
            theta = data['theta']
            timestamp = data['timestamp']
            
            print(f"[MLX Memory Builder] Processing memory item: {image_path}")
            
            # Verify image file exists
            if not os.path.exists(image_path):
                print(f"[MLX Memory Builder] Error: Image file not found: {image_path}")
                caption = f"Robot camera view at position ({position[0]:.2f}, {position[1]:.2f}) - image file missing"
            else:
                # Generate caption using corrected MLX workflow
                if self.captioner:
                    try:
                        print("[MLX Memory Builder] Using corrected MLX LLaVA captioner...")
                        
                        # Verify file is readable
                        file_size = os.path.getsize(image_path)
                        print(f"[MLX Memory Builder] Image file size: {file_size} bytes")
                        
                        # Use file path directly (MLX-VLM can handle this)
                        print(f"[MLX Memory Builder] Processing image: {image_path}")
                        
                        caption = self.captioner.caption_image(image_path)
                        print(f"[MLX Memory Builder] MLX caption: {caption}")
                        
                    except Exception as e:
                        print(f"[MLX Memory Builder] MLX captioning failed: {e}")
                        caption = self.generate_simple_caption(image_path, position, theta)
                        print(f"[MLX Memory Builder] Fallback caption: {caption}")
                else:
                    caption = self.generate_simple_caption(image_path, position, theta)
                    print(f"[MLX Memory Builder] Simple caption: {caption}")
            
            # Create memory item
            memory_item = MemoryItem(
                caption=caption,
                time=timestamp,
                position=position,
                theta=theta
            )
            
            # Insert into memory
            self.memory.insert(memory_item)
            print(f"[MLX Memory Builder] ✓ Memory item inserted at {timestamp:.2f}s")
            
        except Exception as e:
            print(f"[MLX Memory Builder] Error processing memory item: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main processing loop"""
        print("[MLX Memory Builder] Starting processing loop...")
        
        try:
            while self.running:
                try:
                    # Check for new data files
                    data_files = list(self.data_dir.glob("memory_*.json"))
                    
                    if data_files:
                        print(f"[MLX Memory Builder] Found {len(data_files)} files to process")
                    
                    for data_file in data_files:
                        try:
                            print(f"[MLX Memory Builder] Processing file: {data_file}")
                            with open(data_file, 'r') as f:
                                data = json.load(f)
                            
                            # Process the memory item
                            self.process_memory_item(data)
                            
                            # Remove processed file
                            data_file.unlink()
                            print(f"[MLX Memory Builder] Removed processed file: {data_file}")
                            
                        except Exception as e:
                            print(f"[MLX Memory Builder] Error processing file {data_file}: {e}")
                            try:
                                data_file.unlink()
                                print(f"[MLX Memory Builder] Removed corrupted file: {data_file}")
                            except:
                                pass
                    
                    # Sleep briefly to avoid busy waiting
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    print("[MLX Memory Builder] Stopping...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"[MLX Memory Builder] Error in main loop: {e}")
                    time.sleep(1)
        
        finally:
            print("[MLX Memory Builder] Cleaning up...")
        
        print("[MLX Memory Builder] Stopped")

if __name__ == "__main__":
    builder = MLXMemoryBuilderCorrected()
    try:
        builder.run()
    except KeyboardInterrupt:
        print("\n[MLX Memory Builder] Interrupted by user")
























# #!/usr/bin/env python3
# """
# MLX-powered Memory Builder - WORKING VERSION
# Uses direct MLX-VLM generation without chat template
# """

# import sys
# import os
# import time
# import threading
# import queue
# import json
# import tempfile
# import glob
# from pathlib import Path
# from PIL import Image
# import numpy as np

# # Add ReMEmbR to Python path
# remembr_path = "/Users/wen-chungcheng/remembr"
# if remembr_path not in sys.path:
#     sys.path.insert(0, remembr_path)

# # Import ReMEmbR components
# from remembr.memory.memory import MemoryItem
# from remembr.memory.milvus_memory import MilvusMemory
# from remembr.captioners.mlx_llava_captioner import MLXLLaVACaptionerFinalFix

# class MLXMemoryBuilderWorking:
#     def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1"):
#         print(f"[MLX Memory Builder] Starting with working MLX-VLM approach...")
#         print(f"[MLX Memory Builder] Collection: {collection_name}")
#         print(f"[MLX Memory Builder] Database IP: {db_ip}")
        
#         # Initialize memory
#         self.memory = MilvusMemory(collection_name, db_ip=db_ip)
#         print("[MLX Memory Builder] ✓ Memory initialized")
        
#         # Initialize working MLX LLaVA captioner
#         self.captioner = None
#         self.init_captioner()
        
#         # Data directories
#         self.data_dir = Path("/tmp/webots_memory")
#         self.data_dir.mkdir(exist_ok=True)
        
#         # Processing queue
#         self.processing_queue = queue.Queue()
#         self.running = True
        
#         print("[MLX Memory Builder] ✓ Ready with working MLX-VLM approach")
    
#     def init_captioner(self):
#         """Initialize working MLX LLaVA captioner"""
#         print("[MLX Memory Builder] Initializing working MLX LLaVA captioner...")
        
#         try:
#             self.captioner = MLXLLaVACaptionerFinalFix()
#             print("[MLX Memory Builder] ✓ Working MLX LLaVA captioner ready")
            
#         except Exception as e:
#             print(f"[MLX Memory Builder] MLX captioner failed: {e}")
#             print("[MLX Memory Builder] Falling back to simple captioning")
#             self.captioner = None
    
#     def generate_simple_caption(self, image_path, position, theta):
#         """Generate simple caption without MLX as fallback"""
#         x, y, z = position
        
#         try:
#             image = Image.open(image_path)
#             width, height = image.size
            
#             # Simple image analysis
#             if abs(x) < 0.1 and abs(y) < 0.1:
#                 return f"Robot at starting position, capturing {width}x{height} camera view of simulation environment"
#             elif x > 0.5:
#                 return f"Robot exploring forward area ({x:.2f}, {y:.2f}), camera shows new territory ahead"
#             elif abs(y) > 0.3:
#                 return f"Robot moved laterally to ({x:.2f}, {y:.2f}), camera captures side view of environment"
#             else:
#                 return f"Robot navigating at ({x:.2f}, {y:.2f}), camera shows detailed simulation environment"
                
#         except Exception as e:
#             print(f"[MLX Memory Builder] Error analyzing image: {e}")
#             return f"Robot camera view at position ({x:.2f}, {y:.2f}, {z:.2f}) - captured simulation scene"
    
#     def process_memory_item(self, data):
#         """Process a single memory item using working MLX approach"""
#         try:
#             image_path = data['image_path']
#             position = data['position']
#             theta = data['theta']
#             timestamp = data['timestamp']
            
#             print(f"[MLX Memory Builder] Processing memory item: {image_path}")
            
#             # Verify image file exists
#             if not os.path.exists(image_path):
#                 print(f"[MLX Memory Builder] Error: Image file not found: {image_path}")
#                 caption = f"Robot camera view at position ({position[0]:.2f}, {position[1]:.2f}) - image file missing"
#             else:
#                 # Generate caption using working MLX approach
#                 if self.captioner:
#                     try:
#                         print("[MLX Memory Builder] Using working MLX LLaVA captioner...")
                        
#                         # Verify file is readable
#                         file_size = os.path.getsize(image_path)
#                         print(f"[MLX Memory Builder] Image file size: {file_size} bytes")
                        
#                         # Use file path directly (MLX-VLM can handle this)
#                         print(f"[MLX Memory Builder] Processing image: {image_path}")
                        
#                         caption = self.captioner.caption_image(image_path)
#                         print(f"[MLX Memory Builder] MLX caption: {caption}")
                        
#                     except Exception as e:
#                         print(f"[MLX Memory Builder] MLX captioning failed: {e}")
#                         caption = self.generate_simple_caption(image_path, position, theta)
#                         print(f"[MLX Memory Builder] Fallback caption: {caption}")
#                 else:
#                     caption = self.generate_simple_caption(image_path, position, theta)
#                     print(f"[MLX Memory Builder] Simple caption: {caption}")
            
#             # Create memory item
#             memory_item = MemoryItem(
#                 caption=caption,
#                 time=timestamp,
#                 position=position,
#                 theta=theta
#             )
            
#             # Insert into memory
#             self.memory.insert(memory_item)
#             print(f"[MLX Memory Builder] ✓ Memory item inserted at {timestamp:.2f}s")
            
#         except Exception as e:
#             print(f"[MLX Memory Builder] Error processing memory item: {e}")
#             import traceback
#             traceback.print_exc()
    
#     def run(self):
#         """Main processing loop"""
#         print("[MLX Memory Builder] Starting processing loop...")
        
#         try:
#             while self.running:
#                 try:
#                     # Check for new data files
#                     data_files = list(self.data_dir.glob("memory_*.json"))
                    
#                     if data_files:
#                         print(f"[MLX Memory Builder] Found {len(data_files)} files to process")
                    
#                     for data_file in data_files:
#                         try:
#                             print(f"[MLX Memory Builder] Processing file: {data_file}")
#                             with open(data_file, 'r') as f:
#                                 data = json.load(f)
                            
#                             # Process the memory item
#                             self.process_memory_item(data)
                            
#                             # Remove processed file
#                             data_file.unlink()
#                             print(f"[MLX Memory Builder] Removed processed file: {data_file}")
                            
#                         except Exception as e:
#                             print(f"[MLX Memory Builder] Error processing file {data_file}: {e}")
#                             try:
#                                 data_file.unlink()
#                                 print(f"[MLX Memory Builder] Removed corrupted file: {data_file}")
#                             except:
#                                 pass
                    
#                     # Sleep briefly to avoid busy waiting
#                     time.sleep(0.1)
                    
#                 except KeyboardInterrupt:
#                     print("[MLX Memory Builder] Stopping...")
#                     self.running = False
#                     break
#                 except Exception as e:
#                     print(f"[MLX Memory Builder] Error in main loop: {e}")
#                     time.sleep(1)
        
#         finally:
#             print("[MLX Memory Builder] Cleaning up...")
        
#         print("[MLX Memory Builder] Stopped")

# if __name__ == "__main__":
#     builder = MLXMemoryBuilderWorking()
#     try:
#         builder.run()
#     except KeyboardInterrupt:
#         print("\n[MLX Memory Builder] Interrupted by user")