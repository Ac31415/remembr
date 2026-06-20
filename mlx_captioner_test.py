#!/usr/bin/env python3
"""
Test the corrected MLX LLaVA captioner
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
    
    print("[Test] Testing corrected MLX LLaVA captioner...")
    
    # Initialize captioner
    captioner = MLXLLaVACaptionerFinalFix()
    
    # Create a test image
    print("[Test] Creating test image...")
    test_image = Image.new('RGB', (224, 224), color='blue')
    
    # Test with PIL Image directly
    print("\n[Test 1] Testing with PIL Image...")
    try:
        caption = captioner.caption_image(test_image)
        print(f"[Test 1] ✓ Success: {caption}")
    except Exception as e:
        print(f"[Test 1] ✗ Failed: {e}")
    
    # Test with file path
    print("\n[Test 2] Testing with file path...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            test_image.save(temp_file.name, 'JPEG')
            temp_path = temp_file.name
        
        caption = captioner.caption_image(temp_path)
        print(f"[Test 2] ✓ Success: {caption}")
        
        # Cleanup
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"[Test 2] ✗ Failed: {e}")
    
    print("\n[Test] Testing complete!")
    
except Exception as e:
    print(f"[Test] Error: {e}")
    import traceback
    traceback.print_exc()