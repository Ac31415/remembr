# #!/usr/bin/env python3
# """
# Simple test script to debug MLX-VLM image processing
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
#     from mlx_vlm import load, generate
    
#     print("[Test] Loading MLX-VLM model...")
#     model, processor = load("mlx-community/llava-llama-3-8b-v1_1-8bit")
#     print("[Test] ✓ Model loaded successfully")
    
#     # Create a simple test image
#     print("[Test] Creating test image...")
#     test_image = Image.new('RGB', (224, 224), color='red')
    
#     # Save to temporary file
#     with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#         test_image.save(temp_file.name, 'JPEG')
#         temp_path = temp_file.name
    
#     print(f"[Test] Saved test image to: {temp_path}")
    
#     # Test different prompt formats
#     test_cases = [
#         ("Simple prompt", "What do you see?"),
#         ("No special tokens", "Describe this image."),
#         ("Empty prompt", ""),
#         ("Minimal", "Image"),
#     ]
    
#     for name, prompt in test_cases:
#         print(f"\n[Test {name}] Testing prompt: '{prompt}'")
#         try:
#             response = generate(
#                 model, 
#                 processor, 
#                 prompt, 
#                 temp_path, 
#                 max_tokens=20,
#                 temperature=0.1,
#                 verbose=True
#             )
#             print(f"[Test {name}] ✓ Success: {response}")
#         except Exception as e:
#             print(f"[Test {name}] ✗ Failed: {e}")
            
#             # Try to debug the tokenization
#             try:
#                 print(f"[Debug] Checking tokenization for: '{prompt}'")
#                 # This might help us understand what's happening
#                 if hasattr(processor, 'tokenizer'):
#                     tokens = processor.tokenizer(prompt, return_tensors='np')
#                     print(f"[Debug] Tokens shape: {tokens['input_ids'].shape}")
#                     print(f"[Debug] Token IDs: {tokens['input_ids']}")
#             except Exception as debug_e:
#                 print(f"[Debug] Tokenization debug failed: {debug_e}")
    
#     # Cleanup
#     os.unlink(temp_path)
    
# except Exception as e:
#     print(f"[Test] Error: {e}")
#     import traceback
#     traceback.print_exc()























# #!/usr/bin/env python3
# """
# Minimal test script to debug MLX-VLM interface
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
#     from mlx_vlm import load, generate
    
#     print("[Test] Loading MLX-VLM model...")
#     model, processor = load("mlx-community/llava-llama-3-8b-v1_1-8bit")
#     print("[Test] ✓ Model loaded successfully")
    
#     # Create a simple test image (larger than the tiny robot images)
#     print("[Test] Creating test image...")
#     test_image = Image.new('RGB', (224, 224), color='blue')
    
#     # Test the exact interface that should work
#     prompts_to_test = [
#         "Describe this image.",
#         "What do you see?",
#         "What color is this image?",
#     ]
    
#     for i, prompt in enumerate(prompts_to_test, 1):
#         print(f"\n[Test {i}] Testing prompt: '{prompt}'")
#         try:
#             # Try with direct PIL image
#             response = generate(
#                 model, 
#                 processor, 
#                 prompt, 
#                 test_image,
#                 max_tokens=20,
#                 temperature=0.1
#             )
#             print(f"[Test {i}] ✓ Success: {response}")
#             break  # If one works, we're good
            
#         except Exception as e:
#             print(f"[Test {i}] ✗ Failed: {e}")
            
#             # Try saving to file and using file path
#             try:
#                 with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#                     test_image.save(temp_file.name, 'JPEG')
#                     temp_path = temp_file.name
                
#                 print(f"[Test {i}.1] Trying with file path: {temp_path}")
#                 response = generate(
#                     model, 
#                     processor, 
#                     prompt, 
#                     temp_path,
#                     max_tokens=20,
#                     temperature=0.1
#                 )
#                 print(f"[Test {i}.1] ✓ Success with file path: {response}")
#                 os.unlink(temp_path)
#                 break
                
#             except Exception as e2:
#                 print(f"[Test {i}.1] ✗ Failed with file path: {e2}")
#                 if temp_path:
#                     try:
#                         os.unlink(temp_path)
#                     except:
#                         pass
    
# except Exception as e:
#     print(f"[Test] Error: {e}")
#     import traceback
#     traceback.print_exc()




















# #!/usr/bin/env python3
# """
# Test script using the working MLX-VLM approach (no chat template)
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
#     import mlx.core as mx
#     from mlx_vlm import load, generate
    
#     print("[Test] Loading MLX-VLM model with working approach...")
#     model_path = "mlx-community/llava-llama-3-8b-v1_1-8bit"
    
#     # Load model and processor (no config needed)
#     model, processor = load(model_path)
#     print("[Test] ✓ Model and processor loaded successfully")
    
#     # Create a test image
#     print("[Test] Creating test image...")
#     test_image = Image.new('RGB', (224, 224), color='blue')
    
#     # Test the working workflow - direct generation without chat template
#     prompt = "Describe what you see in this image in detail. Focus on objects, actions, and the environment."
#     image_input = [test_image]  # List of images
    
#     print("[Test] Generating caption with direct prompt (no chat template)...")
    
#     # Generate using direct approach
#     output = generate(
#         model,
#         processor,
#         prompt,      # Direct prompt - no formatting
#         image_input, # Image input as list
#         max_tokens=100,
#         temperature=0.2,
#         verbose=False
#     )
    
#     print(f"[Test] ✓ Success: {output}")
    
# except Exception as e:
#     print(f"[Test] Error: {e}")
#     import traceback
#     traceback.print_exc()
























# #!/usr/bin/env python3
# """
# Test script using direct MLX-VLM approach without any prompt formatting
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
#     import mlx.core as mx
#     from mlx_vlm import load, generate
#     from mlx_vlm.utils import load_config
    
#     print("[Test] Loading MLX-VLM model with direct approach...")
#     model_path = "mlx-community/llava-llama-3-8b-v1_1-8bit"
    
#     # Load model and processor
#     model, processor = load(model_path)
#     config = load_config(model_path)
#     print("[Test] ✓ Model, processor, and config loaded successfully")
    
#     # Create a test image
#     print("[Test] Creating test image...")
#     test_image = Image.new('RGB', (224, 224), color='blue')
    
#     # Save to a temporary file (this approach definitely works)
#     with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#         test_image.save(temp_file.name, 'JPEG')
#         temp_path = temp_file.name
    
#     print(f"[Test] Saved test image to: {temp_path}")
    
#     # CRITICAL: Try the most minimal approach possible
#     try:
#         print("[Test] Attempting minimal generation...")
        
#         # Use the absolute minimal interface
#         output = generate(
#             model,
#             processor,
#             "What color is this?",  # Minimal prompt
#             temp_path,              # File path (not PIL image)
#             max_tokens=10,
#             temperature=0.0,
#             verbose=True
#         )
        
#         print(f"[Test] ✓ Success with minimal approach: {output}")
        
#     except Exception as e:
#         print(f"[Test] Minimal approach failed: {e}")
        
#         # Try even more minimal
#         try:
#             print("[Test] Trying with empty prompt...")
#             output = generate(
#                 model,
#                 processor,
#                 "",
#                 temp_path,
#                 max_tokens=5
#             )
#             print(f"[Test] ✓ Success with empty prompt: {output}")
            
#         except Exception as e2:
#             print(f"[Test] Empty prompt failed: {e2}")
            
#             # Try with single word
#             try:
#                 print("[Test] Trying with single word...")
#                 output = generate(
#                     model,
#                     processor,
#                     "Describe",
#                     temp_path,
#                     max_tokens=5
#                 )
#                 print(f"[Test] ✓ Success with single word: {output}")
                
#             except Exception as e3:
#                 print(f"[Test] Single word failed: {e3}")
#                 print("[Test] All approaches failed - MLX-VLM may have configuration issues")
    
#     # Cleanup
#     os.unlink(temp_path)
    
# except Exception as e:
#     print(f"[Test] Error: {e}")
#     import traceback
#     traceback.print_exc()

























#!/usr/bin/env python3
"""
Test script for the definitive MLX-VLM fix
"""

import sys
import os
from pathlib import Path
from PIL import Image
import tempfile

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

try:
    from remembr.captioners.mlx_llava_captioner import MLXLLaVACaptionerFinalFix
    
    print("[Test] Testing definitive MLX-VLM fix...")
    
    # Initialize captioner
    captioner = MLXLLaVACaptionerFinalFix()
    
    # Create a test image
    print("[Test] Creating test image...")
    test_image = Image.new('RGB', (224, 224), color='blue')
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        test_image.save(temp_file.name, 'JPEG')
        temp_path = temp_file.name
    
    print(f"[Test] Saved test image to: {temp_path}")
    
    # Test with PIL Image (should work)
    print("\n[Test 1] Testing with PIL Image...")
    try:
        caption = captioner.caption_image(test_image)
        print(f"[Test 1] ✓ Success: {caption}")
    except Exception as e:
        print(f"[Test 1] ✗ Failed: {e}")
    
    # Test with file path (should convert to PIL automatically)
    print("\n[Test 2] Testing with file path...")
    try:
        caption = captioner.caption_image(temp_path)
        print(f"[Test 2] ✓ Success: {caption}")
    except Exception as e:
        print(f"[Test 2] ✗ Failed: {e}")
    
    # Cleanup
    os.unlink(temp_path)
    
    print("\n[Test] Testing complete")
    
except Exception as e:
    print(f"[Test] Error: {e}")
    import traceback
    traceback.print_exc()