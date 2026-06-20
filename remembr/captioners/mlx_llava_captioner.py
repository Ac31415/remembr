# """
# MLX-powered LLaVA captioner with base64 support
# """

# import mlx.core as mx
# from mlx_vlm import load, generate
# from PIL import Image
# import base64
# from io import BytesIO
# from remembr.captioners.captioner import Captioner

# class MLXLLaVACaptionerBase64(Captioner):
#     """MLX-powered LLaVA captioner using base64 encoding for PIL images"""
    
#     def __init__(self, model_name="mlx-community/llava-llama-3-8b-v1_1-8bit"):
#         print(f"[MLX] Initializing LLaVA captioner with model: {model_name}")
        
#         try:
#             self.model, self.processor = load(model_name)
#             print("[MLX] ✓ LLaVA model loaded successfully with mlx-vlm")
            
#             self.generation_args = {
#                 "max_tokens": 512,
#                 "temperature": 0.2,
#                 "repetition_penalty": 1.1,
#                 "verbose": False
#             }
            
#         except Exception as e:
#             print(f"[MLX] Error loading model: {e}")
#             self.model = None
#             self.processor = None
    
#     def _pil_to_base64_url(self, pil_image):
#         """Convert PIL image to base64 data URL"""
#         # Convert to RGB if needed
#         if pil_image.mode != 'RGB':
#             pil_image = pil_image.convert('RGB')
        
#         # Resize if too large
#         max_size = 512
#         if max(pil_image.size) > max_size:
#             ratio = max_size / max(pil_image.size)
#             new_size = tuple(int(dim * ratio) for dim in pil_image.size)
#             pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
#         # Convert to base64
#         buffer = BytesIO()
#         pil_image.save(buffer, format='JPEG', quality=85)
#         img_str = base64.b64encode(buffer.getvalue()).decode()
        
#         return f"data:image/jpeg;base64,{img_str}"
    
#     def _caption_single_image(self, image):
#         """Caption a single image using MLX LLaVA"""
#         if self.model is None or self.processor is None:
#             return "MLX LLaVA caption: Model not available, robot camera captured a scene"
        
#         try:
#             # Handle different image types
#             if isinstance(image, Image.Image):
#                 # Convert PIL image to base64 data URL
#                 image_input = self._pil_to_base64_url(image)
#             elif isinstance(image, str):
#                 # Assume it's already a URL or path
#                 image_input = image
#             else:
#                 return f"MLX LLaVA caption: Unsupported image type {type(image)}"
            
#             # Create the prompt
#             prompt = "USER: <image>\nDescribe what you see in this image in detail. Focus on objects, actions, and the environment.\nASSISTANT:"
            
#             # Generate caption
#             response = generate(
#                 self.model,
#                 self.processor,
#                 image_input,
#                 prompt,
#                 **self.generation_args
#             )
            
#             # Clean up response
#             caption = response.strip()
#             if caption.startswith("ASSISTANT:"):
#                 caption = caption[10:].strip()
            
#             return caption
            
#         except Exception as e:
#             print(f"[MLX] Generation failed: {e}")
#             return f"MLX LLaVA caption: Robot camera captured a scene in the simulation environment"
    
#     def caption(self, images):
#         """Generate captions for images"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[MLX] Error captioning image: {e}")
#                 captions.append(f"MLX LLaVA caption: Robot camera view - error occurred")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])





















"""
MLX-powered LLaVA captioner for Mac M3 Max - FIXED VERSION
Based on mlx-examples/llava codebase
"""

# import mlx.core as mx
# from mlx_vlm import load, generate
# from mlx_vlm.utils import load_config

from remembr.captioners.generate import load_model, load_model_quantized_8bit_fine_tuned, prepare_inputs, generate_text

from PIL import Image
import os
import traceback
from remembr.captioners.captioner import Captioner

class MLXLLaVACaptionerFinalFix(Captioner):
    """MLX-powered LLaVA captioner optimized for Mac M3 Max using proper MLX format"""
    
    def __init__(self, model_name="mlx-community/llava-llama-3-8b-v1_1-8bit"):
        print(f"[MLX] Initializing MLX LLaVA captioner with model: {model_name}")
        
        try:
            # Load the MLX model using mlx-vlm
            # self.model, self.processor = load(model_name)
            # self.model, self.processor = load_model(model_name)
            self.model, self.processor = load_model_quantized_8bit_fine_tuned(model_name)
            
            # self.config = load_config(model_name)
            print("[MLX] ✓ LLaVA model, processor, and config loaded successfully")
            
            # # CRITICAL FIX: Set missing processor attributes to avoid the deprecation warning
            # if not hasattr(self.processor, 'patch_size') or self.processor.patch_size is None:
            #     self.processor.patch_size = 14  # Standard ViT patch size
            #     print("[MLX Fix] Set processor.patch_size = 14")
            
            # if not hasattr(self.processor, 'vision_feature_select_strategy') or self.processor.vision_feature_select_strategy is None:
            #     self.processor.vision_feature_select_strategy = "default"
            #     print("[MLX Fix] Set processor.vision_feature_select_strategy = 'default'")
            
            # Set generation parameters optimized for Mac M3 Max
            self.generation_args = {
                "max_tokens": 512,
                "temperature": 0.2,
                "repetition_penalty": 1.1,
                "verbose": False
            }
            
        except Exception as e:
            print(f"[MLX] Error loading model: {e}")
            self.model = None
            self.processor = None
            self.config = None
    
    def caption(self, images):
        """Generate captions for images using MLX LLaVA"""
        if not isinstance(images, list):
            images = [images]
        
        captions = []
        for image in images:
            try:
                caption = self._caption_single_image(image)
                captions.append(caption)
            except Exception as e:
                print(f"[MLX] Error captioning image: {e}")
                captions.append(f"MLX LLaVA caption: Robot camera view - {str(e)[:50]}")
        
        return captions[0] if len(captions) == 1 else captions
    
    def caption_image(self, image):
        """Caption a single image - compatibility method"""
        return self.caption([image])
    
    def _convert_to_pil_image(self, image):
        """Convert image to PIL Image format - CRITICAL FIX for file path issue"""
        if isinstance(image, str):
            if image.startswith(('http://', 'https://')):
                # It's a URL - this should work fine with MLX-VLM
                return image
            elif os.path.exists(image):
                # CRITICAL FIX: Convert file path to PIL Image to avoid character splitting
                print(f"[MLX] Converting file path to PIL Image to avoid character splitting: {image}")
                try:
                    pil_image = Image.open(image).convert('RGB')
                    print(f"[MLX] Successfully converted to PIL Image: {pil_image.size}")
                    return pil_image
                except Exception as e:
                    print(f"[MLX] Error converting file to PIL: {e}")
                    return None
            else:
                print(f"[MLX] File path does not exist: {image}")
                return None
        elif isinstance(image, Image.Image):
            # Already a PIL image - perfect
            return image
        else:
            print(f"[MLX] Unsupported image type: {type(image)}")
            return None
    
    def _caption_single_image(self, image):
        """Caption a single image using MLX-VLM with correct format"""
        if self.model is None or self.processor is None or self.config is None:
            return "MLX LLaVA caption: Model not available, robot camera captured a scene"
        
        try:
            # CRITICAL FIX: Convert image to proper format to avoid file path character splitting
            processed_image = self._convert_to_pil_image(image)
            
            if processed_image is None:
                return "MLX LLaVA caption: Image could not be processed"
            
            print(f"[MLX] Processing image type: {type(processed_image)}")
            
            # CRITICAL FIX: Use the correct prompt format with <image> token
            # Based on mlx-examples/llava/README.md
            prompt = "USER: <image>\nDescribe what you see in this image in detail. Focus on objects, actions, and the environment.\nASSISTANT:"
            
            print(f"[MLX] Generating caption with correct prompt format...")
            print(f"[MLX] Prompt: {prompt}")
            
            # CRITICAL FIX: Verify processor attributes before generation
            if hasattr(self.processor, 'patch_size') and hasattr(self.processor, 'vision_feature_select_strategy'):
                print(f"[MLX] Processor attributes: patch_size={self.processor.patch_size}, vision_feature_select_strategy={self.processor.vision_feature_select_strategy}")
            else:
                print("[MLX Warning] Processor missing required attributes")
                
            input_ids, pixel_values = prepare_inputs(self.processor, processed_image, prompt)
            
            # CRITICAL FIX: Use the correct MLX-VLM generate function signature
            # Based on mlx-examples/llava/generate.py
            output = generate(
                self.model,
                self.processor,
                prompt,
                processed_image,  # Pass PIL Image or URL directly
                **self.generation_args
            )
            
            # reply = generate_text(
            #     input_ids, pixel_values, self.model, self.processor, max_tokens, temperature
            # )
            
            reply = generate_text(
                input_ids, pixel_values, self.model, self.processor, **self.generation_args
            )
            
            # print(f"[MLX] Successfully generated caption: {output[:100]}...")
            
            # # Clean up the response if needed
            # if output.startswith("ASSISTANT:"):
            #     output = output[10:].strip()
            
            # return output
            
            print(f"[MLX] Successfully generated caption: {reply[:100]}...")
            
            # Clean up the response if needed
            if reply.startswith("ASSISTANT:"):
                reply = reply[10:].strip()
            
            return reply
            
        except Exception as e:
            print(f"[MLX] Generation failed: {e}")
            traceback.print_exc()
            return f"MLX LLaVA caption: Robot camera captured a scene in the simulation environment"
    
    def clear_cache(self):
        """Clear any cached data - MLX handles memory automatically"""
        pass
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.clear_cache()





























# """
# MLX-powered LLaVA captioner for Mac M3 Max - WORKING VERSION
# Uses mlx-community/llava-llama-3-8b-v1_1-8bit with direct prompt handling (no chat template)
# """

# import mlx.core as mx
# from mlx_vlm import load, generate
# from PIL import Image
# import requests
# from io import BytesIO
# import base64
# import tempfile
# import os
# from remembr.captioners.captioner import Captioner

# class MLXLLaVACaptionerFinalFix(Captioner):
#     """MLX-powered LLaVA captioner optimized for Mac M3 Max - bypasses chat template requirement"""
    
#     def __init__(self, model_name="mlx-community/llava-llama-3-8b-v1_1-8bit"):
#         print(f"[MLX] Initializing working LLaVA captioner with model: {model_name}")
        
#         try:
#             # Load the MLX model using mlx-vlm
#             self.model, self.processor = load(model_name)
#             print("[MLX] ✓ LLaVA model and processor loaded successfully")
            
#             # Set generation parameters optimized for Mac M3 Max
#             self.generation_args = {
#                 "max_tokens": 512,
#                 "temperature": 0.2,
#                 "repetition_penalty": 1.1,
#                 "verbose": False
#             }
            
#         except Exception as e:
#             print(f"[MLX] Error loading model: {e}")
#             self.model = None
#             self.processor = None
    
#     def caption(self, images):
#         """Generate captions for images using MLX LLaVA"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[MLX] Error captioning image: {e}")
#                 captions.append(f"MLX LLaVA caption: Robot camera view - {str(e)[:50]}")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])
    
#     def _caption_single_image(self, image):
#         """Caption a single image using direct MLX-VLM generation (no chat template)"""
#         if self.model is None or self.processor is None:
#             return "MLX LLaVA caption: Model not available, robot camera captured a scene"
        
#         temp_path = None
#         try:
#             # Handle different input types
#             if isinstance(image, str):
#                 # If it's already a file path, use it directly
#                 if os.path.exists(image):
#                     print(f"[MLX] Using image file path: {image}")
#                     image_input = [image]
#                 else:
#                     print(f"[MLX] File path does not exist: {image}")
#                     return "MLX LLaVA caption: Image file not found"
#             elif isinstance(image, Image.Image):
#                 # MLX-VLM can handle PIL Image objects directly
#                 image_input = [image]
#                 print(f"[MLX] Using PIL Image directly: {image.size}")
#             else:
#                 print(f"[MLX] Unsupported image type: {type(image)}")
#                 return "MLX LLaVA caption: Unsupported image type"
            
#             # CRITICAL FIX: Use direct prompt without chat template
#             prompt = "Describe what you see in this image in detail. Focus on objects, actions, and the environment."
            
#             print(f"[MLX] Generating caption with direct prompt...")
#             print(f"[MLX] Image input: {type(image_input[0])}")
            
#             # CRITICAL FIX: Generate directly without chat template
#             output = generate(
#                 self.model,
#                 self.processor,
#                 prompt,      # Direct prompt - no formatting needed
#                 image_input, # Image input as list
#                 **self.generation_args
#             )
            
#             print(f"[MLX] Successfully generated caption: {output[:100]}...")
#             return output
            
#         except Exception as e:
#             print(f"[MLX] Generation failed: {e}")
#             import traceback
#             traceback.print_exc()
#             return f"MLX LLaVA caption: Robot camera captured a scene in the simulation environment"
#         finally:
#             # Clean up temporary file if created
#             if temp_path and os.path.exists(temp_path):
#                 try:
#                     os.unlink(temp_path)
#                     print(f"[MLX] Cleaned up temporary file: {temp_path}")
#                 except Exception as cleanup_error:
#                     print(f"[MLX] Error cleaning up temp file: {cleanup_error}")
    
#     def clear_cache(self):
#         """Clear any cached data - MLX handles memory automatically"""
#         pass
    
#     def __del__(self):
#         """Cleanup when object is destroyed"""
#         self.clear_cache()
























# """
# MLX-powered LLaVA captioner for Mac M3 Max - WORKING VERSION
# Uses mlx-community/llava-llama-3-8b-v1_1-8bit with direct prompt handling (no chat template)
# """

# import mlx.core as mx
# from mlx_vlm import load, generate
# from PIL import Image
# import requests
# from io import BytesIO
# import base64
# import tempfile
# import os
# from remembr.captioners.captioner import Captioner

# class MLXLLaVACaptionerFinalFix(Captioner):
#     """MLX-powered LLaVA captioner optimized for Mac M3 Max - bypasses chat template requirement"""
    
#     def __init__(self, model_name="mlx-community/llava-llama-3-8b-v1_1-8bit"):
#         print(f"[MLX] Initializing working LLaVA captioner with model: {model_name}")
        
#         try:
#             # Load the MLX model using mlx-vlm
#             self.model, self.processor = load(model_name)
#             print("[MLX] ✓ LLaVA model and processor loaded successfully")
            
#             # Set generation parameters optimized for Mac M3 Max
#             self.generation_args = {
#                 "max_tokens": 512,
#                 "temperature": 0.2,
#                 "repetition_penalty": 1.1,
#                 "verbose": False
#             }
            
#         except Exception as e:
#             print(f"[MLX] Error loading model: {e}")
#             self.model = None
#             self.processor = None
    
#     def caption(self, images):
#         """Generate captions for images using MLX LLaVA"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[MLX] Error captioning image: {e}")
#                 captions.append(f"MLX LLaVA caption: Robot camera view - {str(e)[:50]}")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])
    
#     def _caption_single_image(self, image):
#         """Caption a single image using direct MLX-VLM generation (no chat template)"""
#         if self.model is None or self.processor is None:
#             return "MLX LLaVA caption: Model not available, robot camera captured a scene"
        
#         temp_path = None
#         try:
#             # Handle different input types
#             if isinstance(image, str):
#                 # If it's already a file path, use it directly
#                 if os.path.exists(image):
#                     print(f"[MLX] Using image file path: {image}")
#                     image_input = [image]
#                 else:
#                     print(f"[MLX] File path does not exist: {image}")
#                     return "MLX LLaVA caption: Image file not found"
#             elif isinstance(image, Image.Image):
#                 # MLX-VLM can handle PIL Image objects directly
#                 image_input = [image]
#                 print(f"[MLX] Using PIL Image directly: {image.size}")
#             else:
#                 print(f"[MLX] Unsupported image type: {type(image)}")
#                 return "MLX LLaVA caption: Unsupported image type"
            
#             # CRITICAL FIX: Use direct prompt without chat template
#             prompt = "Describe what you see in this image in detail. Focus on objects, actions, and the environment."
            
#             print(f"[MLX] Generating caption with direct prompt...")
#             print(f"[MLX] Image input: {type(image_input[0])}")
            
#             # CRITICAL FIX: Generate directly without chat template
#             output = generate(
#                 self.model,
#                 self.processor,
#                 prompt,      # Direct prompt - no formatting needed
#                 image_input, # Image input as list
#                 **self.generation_args
#             )
            
#             print(f"[MLX] Successfully generated caption: {output[:100]}...")
#             return output
            
#         except Exception as e:
#             print(f"[MLX] Generation failed: {e}")
#             import traceback
#             traceback.print_exc()
#             return f"MLX LLaVA caption: Robot camera captured a scene in the simulation environment"
#         finally:
#             # Clean up temporary file if created
#             if temp_path and os.path.exists(temp_path):
#                 try:
#                     os.unlink(temp_path)
#                     print(f"[MLX] Cleaned up temporary file: {temp_path}")
#                 except Exception as cleanup_error:
#                     print(f"[MLX] Error cleaning up temp file: {cleanup_error}")
    
#     def clear_cache(self):
#         """Clear any cached data - MLX handles memory automatically"""
#         pass
    
#     def __del__(self):
#         """Cleanup when object is destroyed"""
#         self.clear_cache()