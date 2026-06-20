import sys
sys.path.insert(0, "/Users/wen-chungcheng/remembr")

from PIL import Image

# Create tiny test image
test_image = Image.new('RGB', (32, 32), color='blue')  # Very small

try:
    from remembr.captioners.phi3_vision_mlx_captioner import Phi3VisionMLXCaptioner
    
    print("[Test] Creating captioner with minimal settings...")
    captioner = Phi3VisionMLXCaptioner(quantize_model=True)
    
    print("[Test] Testing with tiny image...")
    caption = captioner.caption_image(test_image)
    print(f"[Test] Success: {caption}")
    
except Exception as e:
    print(f"[Test] Failed: {e}")
    import traceback
    traceback.print_exc()
