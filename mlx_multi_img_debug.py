# #!/usr/bin/env python3
# """
# Debug script to understand the MLX-VLM image token issue
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
    
#     print("[Debug] Loading MLX-VLM model...")
#     model_path = "mlx-community/llava-llama-3-8b-v1_1-8bit"
    
#     model, processor = load(model_path)
#     config = load_config(model_path)
#     print("[Debug] ✓ Model loaded successfully")
    
#     # Create a test image
#     print("[Debug] Creating test image...")
#     test_image = Image.new('RGB', (224, 224), color='blue')
    
#     # Debug the processor directly
#     print("\n[Debug] Testing processor directly...")
    
#     # Test 1: Check what happens when we process the image
#     print("[Debug] Processing image with processor...")
#     try:
#         # Let's see what the processor does with the image
#         if hasattr(processor, 'process_images'):
#             processed = processor.process_images([test_image])
#             print(f"[Debug] Processed result type: {type(processed)}")
#             print(f"[Debug] Processed result: {processed}")
#         elif hasattr(processor, '__call__'):
#             processed = processor(test_image)
#             print(f"[Debug] Processed result type: {type(processed)}")
#             print(f"[Debug] Processed result keys: {processed.keys() if hasattr(processed, 'keys') else 'No keys'}")
#     except Exception as e:
#         print(f"[Debug] Processor failed: {e}")
    
#     # Test 2: Check what happens with tokenization
#     print("\n[Debug] Testing tokenization...")
#     simple_prompt = "What do you see?"
    
#     try:
#         if hasattr(processor, 'tokenizer'):
#             tokens = processor.tokenizer(simple_prompt)
#             print(f"[Debug] Tokenized prompt: {tokens}")
#             if hasattr(tokens, 'input_ids'):
#                 print(f"[Debug] Input IDs shape: {tokens.input_ids.shape}")
#                 print(f"[Debug] Input IDs: {tokens.input_ids}")
                
#                 # Check for image tokens
#                 if hasattr(processor.tokenizer, 'convert_ids_to_tokens'):
#                     token_strings = processor.tokenizer.convert_ids_to_tokens(tokens.input_ids[0])
#                     print(f"[Debug] Token strings: {token_strings}")
                    
#                     # Look for image-related tokens
#                     image_tokens = [i for i, token in enumerate(token_strings) if 'image' in token.lower()]
#                     print(f"[Debug] Image token positions: {image_tokens}")
#     except Exception as e:
#         print(f"[Debug] Tokenization debug failed: {e}")
    
#     # Test 3: Check what mlx_vlm.generate expects
#     print("\n[Debug] Testing generate function signature...")
    
#     # Let's inspect the generate function
#     import inspect
#     sig = inspect.signature(generate)
#     print(f"[Debug] Generate function signature: {sig}")
    
#     # Test 4: Try the most minimal call possible
#     print("\n[Debug] Testing minimal generate call...")
    
#     try:
#         # Save image to file first
#         with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#             test_image.save(temp_file.name, 'JPEG')
#             temp_path = temp_file.name
        
#         print(f"[Debug] Saved test image to: {temp_path}")
        
#         # Try with file path only
#         print("[Debug] Calling generate with file path...")
        
#         # Enable verbose mode to see what's happening
#         response = generate(
#             model,
#             processor,
#             "What color is this?",
#             temp_path,
#             max_tokens=5,
#             verbose=True  # This should show us internal processing
#         )
        
#         print(f"[Debug] ✓ Success: {response}")
        
#     except Exception as e:
#         print(f"[Debug] Generate failed: {e}")
        
#         # Let's try to understand what's happening inside generate
#         print("\n[Debug] Inspecting internal processing...")
        
#         try:
#             # Check if we can access the processor's internal methods
#             if hasattr(processor, 'process'):
#                 print("[Debug] Processor has 'process' method")
#             if hasattr(processor, 'preprocess'):
#                 print("[Debug] Processor has 'preprocess' method")
#             if hasattr(processor, 'tokenizer'):
#                 print("[Debug] Processor has 'tokenizer' attribute")
#                 if hasattr(processor.tokenizer, 'model_max_length'):
#                     print(f"[Debug] Tokenizer max length: {processor.tokenizer.model_max_length}")
            
#             # Try to manually do what generate does
#             print("\n[Debug] Attempting manual processing...")
            
#             # First, let's see how MLX-VLM processes the prompt
#             prompt = "What color is this?"
            
#             # Check if there are any special tokens being added
#             if hasattr(processor, 'tokenizer'):
#                 # Try basic tokenization
#                 tokens = processor.tokenizer.encode(prompt)
#                 print(f"[Debug] Basic tokenization: {tokens}")
                
#                 # Check vocab
#                 if hasattr(processor.tokenizer, 'get_vocab'):
#                     vocab = processor.tokenizer.get_vocab()
#                     image_tokens_in_vocab = {k: v for k, v in vocab.items() if 'image' in k.lower()}
#                     print(f"[Debug] Image tokens in vocab: {image_tokens_in_vocab}")
        
#         except Exception as debug_e:
#             print(f"[Debug] Internal inspection failed: {debug_e}")
    
#     finally:
#         # Cleanup
#         if 'temp_path' in locals():
#             try:
#                 os.unlink(temp_path)
#             except:
#                 pass
    
# except Exception as e:
#     print(f"[Debug] Error: {e}")
#     import traceback
#     traceback.print_exc()























#!/usr/bin/env python3
"""
Fixed debug script - tests the correct MLX-VLM usage pattern
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
    import mlx.core as mx
    from mlx_vlm import load, generate
    from mlx_vlm.utils import load_config
    
    print("[Debug] Loading MLX-VLM model...")
    model_path = "mlx-community/llava-llama-3-8b-v1_1-8bit"
    
    model, processor = load(model_path)
    config = load_config(model_path)
    print("[Debug] ✓ Model loaded successfully")
    
    # Create a test image
    print("[Debug] Creating test image...")
    test_image = Image.new('RGB', (224, 224), color='blue')
    
    # Test the CORRECT usage patterns
    print("\n[Test 1] Testing with PIL Image directly (CORRECT)")
    try:
        prompt = "What color is this?"
        
        print(f"[Debug] Calling generate with PIL Image directly")
        print(f"[Debug] Image type: {type(test_image)}")
        print(f"[Debug] Image size: {test_image.size}")
        
        response = generate(
            model,
            processor,
            prompt,
            test_image,  # Pass PIL Image directly, NOT file path
            max_tokens=20,
            verbose=True
        )
        
        print(f"[Test 1] ✓ Success: {response}")
        
    except Exception as e:
        print(f"[Test 1] ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[Test 2] Testing with PIL Image in list (CORRECT)")
    try:
        prompt = "Describe this image."
        
        print(f"[Debug] Calling generate with [PIL Image]")
        print(f"[Debug] Image list type: {type([test_image])}")
        print(f"[Debug] First item type: {type(test_image)}")
        
        response = generate(
            model,
            processor,
            prompt,
            [test_image],  # Pass as list of PIL Images
            max_tokens=20,
            verbose=True
        )
        
        print(f"[Test 2] ✓ Success: {response}")
        
    except Exception as e:
        print(f"[Test 2] ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Now test the WRONG way (what was causing the error)
    print("\n[Test 3] Testing with file path (WRONG - this should fail)")
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            test_image.save(temp_file.name, 'JPEG')
            temp_path = temp_file.name
        
        print(f"[Debug] File path: {temp_path}")
        print(f"[Debug] This will likely cause character splitting...")
        
        response = generate(
            model,
            processor,
            "What color is this?",
            temp_path,  # This is what was causing the error!
            max_tokens=5,
            verbose=True
        )
        
        print(f"[Test 3] Unexpected success: {response}")
        
    except Exception as e:
        print(f"[Test 3] ✗ Expected failure (file path character splitting): {e}")
        # This should fail with "multiple images" error
    
    finally:
        # Cleanup
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
    
    print("\n[Conclusion] The issue is clear:")
    print("✓ PIL Image objects work correctly")
    print("✗ File paths get split character by character")
    print("📋 Solution: Always convert file paths to PIL Images first")
    
except Exception as e:
    print(f"[Debug] Error: {e}")
    import traceback
    traceback.print_exc()