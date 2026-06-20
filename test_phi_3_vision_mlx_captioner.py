# #!/usr/bin/env python3
# """
# Test script for the Phi-3-Vision-MLX captioner
# """

# import sys
# import os
# from pathlib import Path
# from PIL import Image
# import tempfile

# # Add ReMEmbR to Python path
# remembr_path = "/Users/wen-chungcheng/remembr"
# if remembr_path not in sys.path:
#     sys.path.insert(0, remembr_path)

# try:
#     from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner, Phi3VisionMLXCaptionerAdvanced
    
#     print("[Test] Testing Phi-3-Vision-MLX captioner...")
    
#     # Test 1: Standard captioner
#     print("\n[Test 1] Testing standard Phi-3-Vision-MLX captioner...")
#     try:
#         captioner = Phi3VisionMLXCaptioner(quantize_model=True)
        
#         # Create a test image
#         test_image = Image.new('RGB', (224, 224), color='blue')
        
#         # Test with PIL Image
#         caption = captioner.caption_image(test_image)
#         print(f"[Test 1] ✓ Success: {caption}")
        
#     except Exception as e:
#         print(f"[Test 1] ✗ Failed: {e}")
    
#     # Test 2: Advanced captioner
#     print("\n[Test 2] Testing advanced Phi-3-Vision-MLX captioner...")
#     try:
#         advanced_captioner = Phi3VisionMLXCaptionerAdvanced(enable_advanced_features=True)
        
#         # Create a test image
#         test_image = Image.new('RGB', (224, 224), color='red')
        
#         # Test with constraints
#         constraints = [(50, "This image shows"), (100, " which appears to be")]
#         caption = advanced_captioner.caption_with_constraints([test_image], constraints)
#         print(f"[Test 2] ✓ Constrained caption: {caption}")
        
#     except Exception as e:
#         print(f"[Test 2] ✗ Failed: {e}")
    
#     # Test 3: Batch processing
#     print("\n[Test 3] Testing batch processing...")
#     try:
#         captioner = Phi3VisionMLXCaptioner()
        
#         # Create multiple test images
#         test_images = [
#             Image.new('RGB', (224, 224), color='blue'),
#             Image.new('RGB', (224, 224), color='red'),
#             Image.new('RGB', (224, 224), color='green')
#         ]
        
#         # Test batch captioning
#         captions = captioner.caption_batch(test_images)
#         print(f"[Test 3] ✓ Batch success: {len(captions)} captions generated")
#         for i, caption in enumerate(captions):
#             print(f"  Image {i+1}: {caption[:100]}...")
        
#     except Exception as e:
#         print(f"[Test 3] ✗ Failed: {e}")
    
#     # Test 4: File path input
#     print("\n[Test 4] Testing file path input...")
#     try:
#         captioner = Phi3VisionMLXCaptioner()
        
#         # Create and save a test image
#         with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#             test_image = Image.new('RGB', (224, 224), color='yellow')
#             test_image.save(temp_file.name, 'JPEG')
#             temp_path = temp_file.name
        
#         caption = captioner.caption_image(temp_path)
#         print(f"[Test 4] ✓ File path success: {caption}")
        
#         # Cleanup
#         os.unlink(temp_path)
        
#     except Exception as e:
#         print(f"[Test 4] ✗ Failed: {e}")
    
#     print("\n[Test] Testing complete!")
    
# except Exception as e:
#     print(f"[Test] Error: {e}")
#     import traceback
#     traceback.print_exc()

























# #!/usr/bin/env python3
# """
# Debug script for Phi-3-Vision-MLX issues
# """

# import sys
# import os
# from pathlib import Path
# from PIL import Image

# # Add paths
# remembr_path = "/Users/wen-chungcheng/remembr"
# phi3_path = "/Users/wen-chungcheng/Phi-3-Vision-MLX"

# if remembr_path not in sys.path:
#     sys.path.insert(0, remembr_path)
# if phi3_path not in sys.path:
#     sys.path.insert(0, phi3_path)

# def test_direct_import():
#     """Test direct import and basic functionality"""
#     print("[Debug] Testing direct phi_3_vision_mlx import...")
    
#     try:
#         import phi_3_vision_mlx as pv
#         print("[Debug] ✓ Import successful")
        
#         # Test setup
#         print("[Debug] Testing setup...")
#         pv._setup()
#         print("[Debug] ✓ Setup successful")
        
#         # Test simple generation
#         print("[Debug] Testing simple generation...")
#         test_image = Image.new('RGB', (64, 64), color='blue')  # Very small image
        
#         response = pv.generate(
#             prompt="What color is this?",
#             images=test_image,
#             max_tokens=10,
#             quantize_model=True,
#             verbose=True
#         )
        
#         print(f"[Debug] ✓ Generation successful: {response}")
#         return True
        
#     except Exception as e:
#         print(f"[Debug] ✗ Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return False

# def test_captioner():
#     """Test the captioner class"""
#     print("\n[Debug] Testing captioner class...")
    
#     try:
#         from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner
        
#         print("[Debug] Creating captioner...")
#         captioner = Phi3VisionMLXCaptioner(quantize_model=True, quantize_cache=False)
        
#         print("[Debug] Testing with small image...")
#         test_image = Image.new('RGB', (32, 32), color='red')
        
#         caption = captioner.caption_image(test_image)
#         print(f"[Debug] ✓ Caption: {caption}")
        
#         return True
        
#     except Exception as e:
#         print(f"[Debug] ✗ Captioner error: {e}")
#         import traceback
#         traceback.print_exc()
#         return False

# if __name__ == "__main__":
#     print("🐛 Phi-3-Vision-MLX Debug Script")
#     print("="*50)
    
#     # Test 1: Direct import
#     success1 = test_direct_import()
    
#     # Test 2: Captioner class
#     if success1:
#         success2 = test_captioner()
#     else:
#         print("[Debug] Skipping captioner test due to import failure")
    
#     print("\n" + "="*50)
#     if success1:
#         print("✓ Debug completed - Framework working")
#     else:
#         print("✗ Debug failed - Check installation")
























# #!/usr/bin/env python3
# """
# Debug script to identify the exact source of GPU timeout
# """

# import sys
# import os
# from pathlib import Path
# from PIL import Image
# import time

# # Add paths
# remembr_path = "/Users/wen-chungcheng/remembr"
# phi3_path = "/Users/wen-chungcheng/Phi-3-Vision-MLX"

# if remembr_path not in sys.path:
#     sys.path.insert(0, remembr_path)
# if phi3_path not in sys.path:
#     sys.path.insert(0, phi3_path)

# def test_framework_import():
#     """Test if we can import the framework"""
#     print("[Debug] Testing framework import...")
#     try:
#         import phi_3_vision_mlx as pv
#         print("[Debug] ✓ Framework import successful")
#         return pv
#     except Exception as e:
#         print(f"[Debug] ✗ Framework import failed: {e}")
#         return None

# def test_setup(pv):
#     """Test framework setup"""
#     print("[Debug] Testing framework setup...")
#     try:
#         pv._setup()
#         print("[Debug] ✓ Setup successful")
#         return True
#     except Exception as e:
#         print(f"[Debug] ✗ Setup failed: {e}")
#         return False

# def test_load(pv):
#     """Test model loading"""
#     print("[Debug] Testing model loading...")
#     try:
#         preload = pv.load(quantize_model=True, quantize_cache=False)
#         print("[Debug] ✓ Model loading successful")
#         return preload
#     except Exception as e:
#         print(f"[Debug] ✗ Model loading failed: {e}")
#         return None

# def test_minimal_generation(pv, preload=None):
#     """Test minimal generation"""
#     print("[Debug] Testing minimal generation...")
#     try:
#         # Tiny image
#         test_image = Image.new('RGB', (16, 16), color='blue')
        
#         # Minimal generation
#         if preload:
#             response = pv.generate(
#                 "Color?",
#                 images=test_image,
#                 max_tokens=3,
#                 preload=preload,
#                 verbose=False,
#                 stream=False
#             )
#         else:
#             response = pv.generate(
#                 "Color?", 
#                 images=test_image,
#                 max_tokens=3,
#                 quantize_model=True,
#                 verbose=False,
#                 stream=False
#             )
        
#         print(f"[Debug] ✓ Generation successful: {response}")
#         return True
        
#     except Exception as e:
#         print(f"[Debug] ✗ Generation failed: {e}")
#         import traceback
#         traceback.print_exc()
#         return False

# if __name__ == "__main__":
#     print("🐛 Phi-3-Vision-MLX GPU Timeout Debug")
#     print("="*50)
    
#     # Step 1: Import
#     pv = test_framework_import()
#     if not pv:
#         sys.exit(1)
    
#     # Step 2: Setup
#     setup_ok = test_setup(pv)
#     if not setup_ok:
#         print("[Debug] Continuing without setup...")
    
#     # Step 3: Try loading model
#     preload = test_load(pv)
    
#     # Step 4: Test generation (with and without preload)
#     if preload:
#         print("\n[Debug] Testing with preloaded model...")
#         test_minimal_generation(pv, preload)
    
#     print("\n[Debug] Testing without preloaded model...")
#     test_minimal_generation(pv, None)
    
#     print("\n[Debug] Debug completed")






from phi_3_vision_mlx import generate
generate('What is shown in this image?', '/Users/wen-chungcheng/Downloads/pexels-photo-1108099.jpeg', quantize_model=False, quantize_cache=True)