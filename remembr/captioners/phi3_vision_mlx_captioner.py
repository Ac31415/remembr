"""
Phi-3-Vision-MLX captioner for Mac M3 Max - CORRECTED VERSION
Uses the actual phi_3_vision_mlx framework API correctly
"""

import os
import sys
from pathlib import Path
from PIL import Image
import tempfile
import traceback
from remembr.captioners.captioner import Captioner

# Add the Phi-3-Vision-MLX path to ensure we can import it
phi3_path = "/Users/wen-chungcheng/Phi-3-Vision-MLX"
if phi3_path not in sys.path:
    sys.path.insert(0, phi3_path)

try:
    import phi_3_vision_mlx as pv
    PHI3_VISION_MLX_AVAILABLE = True
    print("[Phi-3-Vision-MLX] Framework imported successfully")
except ImportError as e:
    print(f"[Phi-3-Vision-MLX] Import failed: {e}")
    PHI3_VISION_MLX_AVAILABLE = False

class Phi3VisionMLXCaptioner(Captioner):
    """
    Phi-3-Vision-MLX captioner optimized for Mac M3 Max
    Uses the correct phi_3_vision_mlx framework API
    """
    
    def __init__(self, model_name=None, quantize_model=True, quantize_cache=False):
        print(f"[Phi-3-Vision-MLX] Initializing captioner with native Apple Silicon optimization...")
        
        if not PHI3_VISION_MLX_AVAILABLE:
            raise ImportError("phi_3_vision_mlx framework not available")
        
        # CRITICAL FIX: Setup the framework and preload the model
        self.quantize_model = quantize_model
        self.quantize_cache = quantize_cache
        
        try:
            print("[Phi-3-Vision-MLX] Setting up framework...")
            # First, setup the framework (downloads models if needed)
            # pv._setup()
            print("[Phi-3-Vision-MLX] ✓ Framework setup completed")
            
            print("[Phi-3-Vision-MLX] Loading model...")
            # Load the model using the framework's load function
            self.preload = pv.load(
                quantize_model=quantize_model,
                quantize_cache=quantize_cache
            )
            print("[Phi-3-Vision-MLX] ✓ Model preloaded successfully")
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Model loading failed: {e}")
            traceback.print_exc()
            self.preload = None
        
        # Set generation parameters optimized for captioning
        self.generation_args = {
            "max_tokens": 256,
            "verbose": False,
            "preload": self.preload,  # CRITICAL: Pass the preloaded model
            "quantize_model": quantize_model,
            "quantize_cache": quantize_cache,
            "stream": False,  # Disable streaming for captioning
            "apply_chat_template": True
        }
        
        print(f"[Phi-3-Vision-MLX] ✓ Captioner initialized")
        print(f"[Phi-3-Vision-MLX] Model quantization: {quantize_model}")
        print(f"[Phi-3-Vision-MLX] Cache quantization: {quantize_cache}")
    
    def caption(self, images):
        """Generate captions for images using Phi-3-Vision-MLX"""
        if not isinstance(images, list):
            images = [images]
        
        captions = []
        for image in images:
            try:
                caption = self._caption_single_image(image)
                captions.append(caption)
            except Exception as e:
                print(f"[Phi-3-Vision-MLX] Error captioning image: {e}")
                captions.append(f"Phi-3-Vision-MLX caption: Robot camera view - error occurred")
        
        return captions[0] if len(captions) == 1 else captions
    
    def caption_image(self, image):
        """Caption a single image - compatibility method"""
        return self.caption([image])
    
    def _convert_image_for_phi3(self, image):
        """Convert image to the format expected by phi_3_vision_mlx"""
        if isinstance(image, str):
            # If it's a string, check if it's a URL or file path
            if image.startswith(('http://', 'https://')):
                return image  # Return URL directly
            elif os.path.exists(image):
                return image  # Return file path directly
            else:
                print(f"[Phi-3-Vision-MLX] File path does not exist: {image}")
                return None
        elif isinstance(image, Image.Image):
            # CRITICAL FIX: Save PIL Image to temporary file and return path
            try:
                # Create a temporary file
                temp_dir = "/tmp"
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, f"phi3_temp_{id(image)}.png")
                
                # Save the PIL image
                image.save(temp_path, format='PNG')
                print(f"[Phi-3-Vision-MLX] Saved PIL image to temporary file: {temp_path}")
                return temp_path
                
            except Exception as e:
                print(f"[Phi-3-Vision-MLX] Error saving PIL image to temp file: {e}")
                return None
        else:
            print(f"[Phi-3-Vision-MLX] Unsupported image type: {type(image)}")
            return None
    
    def _caption_single_image(self, image):
        """Caption a single image using Phi-3-Vision-MLX"""
        if self.preload is None:
            return "Phi-3-Vision-MLX caption: Model not loaded"
        
        temp_file = None
        try:
            # Convert image to proper format (file path or URL)
            processed_image = self._convert_image_for_phi3(image)
            
            if processed_image is None:
                return "Phi-3-Vision-MLX caption: Image could not be processed"
            
            # Keep track if we created a temp file
            if isinstance(image, Image.Image):
                temp_file = processed_image
            
            print(f"[Phi-3-Vision-MLX] Processing image: {processed_image}")
            
            # Create prompt optimized for robot scene description
            prompt = "Describe what you see in this image in detail. Focus on objects, actions, the environment, and spatial relationships."
            
            print(f"[Phi-3-Vision-MLX] Generating caption...")
            
            # CRITICAL FIX: Pass the file path/URL instead of PIL Image
            output = pv.generate(
                prompt=prompt,
                images=processed_image,  # Now this is a file path or URL
                **self.generation_args
            )
            
            # Clean up the output
            if isinstance(output, str):
                caption = output.strip()
            else:
                caption = str(output).strip()
            
            # Remove any unwanted tokens
            if '<|end|>' in caption:
                caption = caption[:caption.find('<|end|>')]
            
            print(f"[Phi-3-Vision-MLX] Successfully generated caption: {caption[:100]}...")
            return caption
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Generation failed: {e}")
            traceback.print_exc()
            return f"Phi-3-Vision-MLX caption: Robot camera captured a scene in the simulation environment"
        
        finally:
            # Clean up temporary file if we created one
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"[Phi-3-Vision-MLX] Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    print(f"[Phi-3-Vision-MLX] Error cleaning up temp file: {e}")
    
    def test_model(self):
        """Test the model with a simple image"""
        if self.preload is None:
            print("[Phi-3-Vision-MLX] Model not loaded, skipping test")
            return False
            
        try:
            print("[Phi-3-Vision-MLX] Testing model...")
            
            # Create a simple test image
            test_image = Image.new('RGB', (224, 224), color='blue')
            
            # Test with simple prompt using preloaded model
            response = pv.generate(
                prompt="What color is this image?",
                images=test_image,
                max_tokens=10,
                preload=self.preload,
                verbose=False,
                stream=False
            )
            
            print(f"[Phi-3-Vision-MLX] Model test successful: {response}")
            return True
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Model test failed: {e}")
            traceback.print_exc()
            return False
    
    def clear_cache(self):
        """Clear any cached data"""
        if hasattr(self, 'preload') and self.preload is not None:
            try:
                del self.preload
                self.preload = None
            except:
                pass
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.clear_cache()
        
        
class Phi3VisionMLXCaptionerAdvanced(Phi3VisionMLXCaptioner):
    """
    Advanced version with additional features from phi_3_vision_mlx
    """
    
    def __init__(self, model_name=None, use_quantization=True, enable_advanced_features=True):
        super().__init__(model_name, quantize_model=use_quantization)
        
        self.enable_advanced_features = enable_advanced_features
        
        if enable_advanced_features:
            print("[Phi-3-Vision-MLX] Advanced features enabled")
    
    def caption_with_constraints(self, images, constraints=None):
        """Caption with constrained generation for specific formats"""
        if not self.enable_advanced_features:
            return self.caption(images)
        
        try:
            if not isinstance(images, list):
                images = [images]
            
            # Convert images
            processed_images = []
            for image in images:
                processed_image = self._convert_image_for_phi3(image)
                if processed_image is not None:
                    processed_images.append(processed_image)
            
            # Use constrained generation if available
            prompt = "Describe this robot camera view in detail:"
            
            if constraints:
                # Use constrained decoding
                output = pv.constrain(
                    prompt,
                    processed_images[0] if processed_images else None,
                    constraints,
                    quantize_model=self.generation_args["quantize_model"]
                )
            else:
                # Regular generation
                output = pv.generate(
                    prompt,
                    processed_images[0] if processed_images else None,
                    **self.generation_args
                )
            
            return output if isinstance(output, list) else [output]
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Constrained generation failed: {e}")
            return self.caption(images)
    
    def caption_with_choices(self, images, choices="ABCDE", questions=None):
        """Caption with multiple choice selection"""
        if not self.enable_advanced_features:
            return self.caption(images)
        
        try:
            if not isinstance(images, list):
                images = [images]
            
            if questions is None:
                questions = ["What is the main object in this robot camera view?"] * len(images)
            
            # Convert images
            processed_images = []
            for image in images:
                processed_image = self._convert_image_for_phi3(image)
                if processed_image is not None:
                    processed_images.append(processed_image)
            
            # Use choice selection
            results = pv.choose(
                questions[:len(processed_images)],
                processed_images,
                choices=choices
            )
            
            return results if isinstance(results, list) else [results]
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Choice selection failed: {e}")
            return self.caption(images)




























# """
# Phi-3-Vision-MLX captioner for Mac M3 Max - CORRECTED VERSION
# Uses the actual phi_3_vision_mlx framework API correctly
# """

# import os
# import sys
# from pathlib import Path
# from PIL import Image
# import tempfile
# import traceback
# from remembr.captioners.captioner import Captioner

# # Add the Phi-3-Vision-MLX path to ensure we can import it
# phi3_path = "/Users/wen-chungcheng/Phi-3-Vision-MLX"
# if phi3_path not in sys.path:
#     sys.path.insert(0, phi3_path)

# try:
#     import phi_3_vision_mlx as pv
#     PHI3_VISION_MLX_AVAILABLE = True
#     print("[Phi-3-Vision-MLX] Framework imported successfully")
# except ImportError as e:
#     print(f"[Phi-3-Vision-MLX] Import failed: {e}")
#     PHI3_VISION_MLX_AVAILABLE = False

# class Phi3VisionMLXCaptioner(Captioner):
#     """
#     Phi-3-Vision-MLX captioner optimized for Mac M3 Max
#     Uses the correct phi_3_vision_mlx framework API
#     """
    
#     def __init__(self, model_name=None, quantize_model=True, quantize_cache=False):
#         print(f"[Phi-3-Vision-MLX] Initializing captioner with native Apple Silicon optimization...")
        
#         if not PHI3_VISION_MLX_AVAILABLE:
#             raise ImportError("phi_3_vision_mlx framework not available")
        
#         # CRITICAL FIX: Setup the framework and preload the model
#         self.quantize_model = quantize_model
#         self.quantize_cache = quantize_cache
        
#         try:
#             print("[Phi-3-Vision-MLX] Setting up framework...")
#             # First, setup the framework (downloads models if needed)
#             # pv._setup()
#             print("[Phi-3-Vision-MLX] ✓ Framework setup completed")
            
#             print("[Phi-3-Vision-MLX] Loading model...")
#             # Load the model using the framework's load function
#             self.preload = pv.load(
#                 quantize_model=quantize_model,
#                 quantize_cache=quantize_cache
#             )
#             print("[Phi-3-Vision-MLX] ✓ Model preloaded successfully")
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Model loading failed: {e}")
#             traceback.print_exc()
#             self.preload = None
        
#         # Set generation parameters optimized for captioning
#         self.generation_args = {
#             "max_tokens": 256,
#             "verbose": False,
#             "preload": self.preload,  # CRITICAL: Pass the preloaded model
#             "quantize_model": quantize_model,
#             "quantize_cache": quantize_cache,
#             "stream": False,  # Disable streaming for captioning
#             "apply_chat_template": True
#         }
        
#         print(f"[Phi-3-Vision-MLX] ✓ Captioner initialized")
#         print(f"[Phi-3-Vision-MLX] Model quantization: {quantize_model}")
#         print(f"[Phi-3-Vision-MLX] Cache quantization: {quantize_cache}")
    
#     def caption(self, images):
#         """Generate captions for images using Phi-3-Vision-MLX"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[Phi-3-Vision-MLX] Error captioning image: {e}")
#                 captions.append(f"Phi-3-Vision-MLX caption: Robot camera view - error occurred")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])
    
#     def _convert_to_pil_image(self, image):
#         """Convert image to PIL Image format"""
#         if isinstance(image, str):
#             if image.startswith(('http://', 'https://')):
#                 return image
#             elif os.path.exists(image):
#                 try:
#                     pil_image = Image.open(image).convert('RGB')
#                     print(f"[Phi-3-Vision-MLX] Successfully loaded image from file: {pil_image.size}")
#                     return pil_image
#                 except Exception as e:
#                     print(f"[Phi-3-Vision-MLX] Error loading image file: {e}")
#                     return None
#             else:
#                 print(f"[Phi-3-Vision-MLX] File path does not exist: {image}")
#                 return None
#         elif isinstance(image, Image.Image):
#             return image
#         else:
#             print(f"[Phi-3-Vision-MLX] Unsupported image type: {type(image)}")
#             return None
    
#     def _caption_single_image(self, image):
#         """Caption a single image using Phi-3-Vision-MLX"""
#         if self.preload is None:
#             return "Phi-3-Vision-MLX caption: Model not loaded"
        
#         try:
#             # Convert image to proper format
#             processed_image = self._convert_to_pil_image(image)
            
#             if processed_image is None:
#                 return "Phi-3-Vision-MLX caption: Image could not be processed"
            
#             print(f"[Phi-3-Vision-MLX] Processing image type: {type(processed_image)}")
            
#             # Create prompt optimized for robot scene description
#             prompt = "Describe what you see in this image in detail. Focus on objects, actions, the environment, and spatial relationships."
            
#             print(f"[Phi-3-Vision-MLX] Generating caption...")
            
#             # CRITICAL FIX: Use the generate function with preloaded model
#             output = pv.generate(
#                 prompt=prompt,
#                 images=processed_image,
#                 **self.generation_args
#             )
            
#             # Clean up the output
#             if isinstance(output, str):
#                 caption = output.strip()
#             else:
#                 caption = str(output).strip()
            
#             # Remove any unwanted tokens
#             if '<|end|>' in caption:
#                 caption = caption[:caption.find('<|end|>')]
            
#             print(f"[Phi-3-Vision-MLX] Successfully generated caption: {caption[:100]}...")
#             return caption
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Generation failed: {e}")
#             traceback.print_exc()
#             return f"Phi-3-Vision-MLX caption: Robot camera captured a scene in the simulation environment"
    
#     def test_model(self):
#         """Test the model with a simple image"""
#         if self.preload is None:
#             print("[Phi-3-Vision-MLX] Model not loaded, skipping test")
#             return False
            
#         try:
#             print("[Phi-3-Vision-MLX] Testing model...")
            
#             # Create a simple test image
#             test_image = Image.new('RGB', (224, 224), color='blue')
            
#             # Test with simple prompt using preloaded model
#             response = pv.generate(
#                 prompt="What color is this image?",
#                 images=test_image,
#                 max_tokens=10,
#                 preload=self.preload,
#                 verbose=False,
#                 stream=False
#             )
            
#             print(f"[Phi-3-Vision-MLX] Model test successful: {response}")
#             return True
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Model test failed: {e}")
#             traceback.print_exc()
#             return False
    
#     def clear_cache(self):
#         """Clear any cached data"""
#         if hasattr(self, 'preload') and self.preload is not None:
#             try:
#                 del self.preload
#                 self.preload = None
#             except:
#                 pass
    
#     def __del__(self):
#         """Cleanup when object is destroyed"""
#         self.clear_cache()
        
        
# class Phi3VisionMLXCaptionerAdvanced(Phi3VisionMLXCaptioner):
#     """
#     Advanced version with additional features from phi_3_vision_mlx
#     """
    
#     def __init__(self, model_name=None, use_quantization=True, enable_advanced_features=True):
#         super().__init__(model_name, quantize_model=use_quantization)
        
#         self.enable_advanced_features = enable_advanced_features
        
#         if enable_advanced_features:
#             print("[Phi-3-Vision-MLX] Advanced features enabled")
    
#     def caption_with_constraints(self, images, constraints=None):
#         """Caption with constrained generation for specific formats"""
#         if not self.enable_advanced_features:
#             return self.caption(images)
        
#         try:
#             if not isinstance(images, list):
#                 images = [images]
            
#             # Convert images
#             processed_images = []
#             for image in images:
#                 processed_image = self._convert_to_pil_image(image)
#                 if processed_image is not None:
#                     processed_images.append(processed_image)
            
#             # Use constrained generation if available
#             prompt = "Describe this robot camera view in detail:"
            
#             if constraints:
#                 # Use constrained decoding
#                 output = pv.constrain(
#                     prompt,
#                     processed_images[0] if processed_images else None,
#                     constraints,
#                     quantize_model=self.generation_args["quantize_model"]
#                 )
#             else:
#                 # Regular generation
#                 output = pv.generate(
#                     prompt,
#                     processed_images[0] if processed_images else None,
#                     **self.generation_args
#                 )
            
#             return output if isinstance(output, list) else [output]
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Constrained generation failed: {e}")
#             return self.caption(images)
    
#     def caption_with_choices(self, images, choices="ABCDE", questions=None):
#         """Caption with multiple choice selection"""
#         if not self.enable_advanced_features:
#             return self.caption(images)
        
#         try:
#             if not isinstance(images, list):
#                 images = [images]
            
#             if questions is None:
#                 questions = ["What is the main object in this robot camera view?"] * len(images)
            
#             # Convert images
#             processed_images = []
#             for image in images:
#                 processed_image = self._convert_to_pil_image(image)
#                 if processed_image is not None:
#                     processed_images.append(processed_image)
            
#             # Use choice selection
#             results = pv.choose(
#                 questions[:len(processed_images)],
#                 processed_images,
#                 choices=choices
#             )
            
#             return results if isinstance(results, list) else [results]
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Choice selection failed: {e}")
#             return self.caption(images)




























# """
# Phi-3-Vision-MLX captioner for Mac M3 Max - Native Apple Silicon optimized
# Uses the phi_3_vision_mlx framework for optimal performance
# """

# import os
# import sys
# from pathlib import Path
# from PIL import Image
# import tempfile
# import traceback
# from remembr.captioners.captioner import Captioner

# try:
#     import phi_3_vision_mlx as pv
#     PHI3_VISION_MLX_AVAILABLE = True
#     print("[Phi-3-Vision-MLX] Framework imported successfully")
# except ImportError as e:
#     print(f"[Phi-3-Vision-MLX] Import failed: {e}")
#     print("[Phi-3-Vision-MLX] Please install: pip install phi-3-vision-mlx")
#     PHI3_VISION_MLX_AVAILABLE = False

# class Phi3VisionMLXCaptioner(Captioner):
#     """
#     Phi-3-Vision-MLX captioner optimized for Mac M3 Max
#     Uses the phi_3_vision_mlx framework with native Apple Silicon acceleration
#     """
    
#     def __init__(self, model_name=None, quantize_model=True, quantize_cache=False):
#         print(f"[Phi-3-Vision-MLX] Initializing captioner with native Apple Silicon optimization...")
        
#         # try:
#         #     if force_cpu:
#         #         # Force CPU usage to avoid GPU timeout
#         #         self.device = mx.cpu
#         #         print("[Phi-3-Vision-MLX] Using CPU device to avoid GPU timeout")
#         #     else:
#         #         self.device = mx.default_device()
                
#         #     # Load model with timeout protection
#         #     with mx.stream(mx.gpu if not force_cpu else mx.cpu):
#         #         self.model, self.processor = self._load_model_with_timeout()
                
#         # except Exception as e:
#         #     print(f"[Phi-3-Vision-MLX] GPU loading failed: {e}")
#         #     print("[Phi-3-Vision-MLX] Falling back to CPU...")
#         #     self.device = mx.cpu
#         #     self.model, self.processor = self._load_model_with_timeout()
        
#         if not PHI3_VISION_MLX_AVAILABLE:
#             raise ImportError("phi_3_vision_mlx not available. Please install: pip install phi-3-vision-mlx")
        
#         # Set generation parameters optimized for captioning
#         # self.generation_args = {
#         #     "max_tokens": 256,
#         #     "temperature": 0.2,
#         #     "quantize_model": quantize_model,
#         #     "quantize_cache": quantize_cache,
#         #     "verbose": False
#         # }
        
#         self.generation_args = {
#             "max_tokens": 256,
#             # "temperature": 0.2,
#             "quantize_model": quantize_model,
#             "quantize_cache": quantize_cache,
#             "verbose": False
#         }
        
#         print(f"[Phi-3-Vision-MLX] ✓ Captioner initialized")
#         print(f"[Phi-3-Vision-MLX] Model quantization: {quantize_model}")
#         print(f"[Phi-3-Vision-MLX] Cache quantization: {quantize_cache}")
#         print(f"[Phi-3-Vision-MLX] Native Apple Silicon acceleration enabled")
    
#     def caption(self, images):
#         """Generate captions for images using Phi-3-Vision-MLX"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[Phi-3-Vision-MLX] Error captioning image: {e}")
#                 captions.append(f"Phi-3-Vision-MLX caption: Robot camera view - error occurred")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])
    
#     def _convert_to_pil_image(self, image):
#         """Convert image to PIL Image format"""
#         if isinstance(image, str):
#             if image.startswith(('http://', 'https://')):
#                 return image  # Return URL directly - phi_3_vision_mlx can handle URLs
#             elif os.path.exists(image):
#                 try:
#                     pil_image = Image.open(image).convert('RGB')
#                     print(f"[Phi-3-Vision-MLX] Successfully loaded image from file: {pil_image.size}")
#                     return pil_image
#                 except Exception as e:
#                     print(f"[Phi-3-Vision-MLX] Error loading image file: {e}")
#                     return None
#             else:
#                 print(f"[Phi-3-Vision-MLX] File path does not exist: {image}")
#                 return None
#         elif isinstance(image, Image.Image):
#             return image
#         else:
#             print(f"[Phi-3-Vision-MLX] Unsupported image type: {type(image)}")
#             return None
    
#     def _caption_single_image(self, image):
#         """Caption a single image using Phi-3-Vision-MLX"""
#         try:
#             # Convert image to proper format
#             processed_image = self._convert_to_pil_image(image)
            
#             if processed_image is None:
#                 return "Phi-3-Vision-MLX caption: Image could not be processed"
            
#             print(f"[Phi-3-Vision-MLX] Processing image type: {type(processed_image)}")
            
#             # Create prompt optimized for robot scene description
#             prompt = "Describe what you see in this image in detail. Focus on objects, actions, the environment, and spatial relationships."
            
#             print(f"[Phi-3-Vision-MLX] Generating caption...")
            
#             # Generate caption using phi_3_vision_mlx
#             output = pv.generate(
#                 prompt,
#                 processed_image,
#                 **self.generation_args
#             )
            
#             # Clean up the output
#             if isinstance(output, str):
#                 caption = output.strip()
#             else:
#                 caption = str(output).strip()
            
#             print(f"[Phi-3-Vision-MLX] Successfully generated caption: {caption[:100]}...")
#             return caption
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Generation failed: {e}")
#             traceback.print_exc()
#             return f"Phi-3-Vision-MLX caption: Robot camera captured a scene in the simulation environment"
    
#     def caption_batch(self, images, prompts=None):
#         """Caption multiple images in batch for better efficiency"""
#         try:
#             if prompts is None:
#                 prompts = ["Describe what you see in this image in detail. Focus on objects, actions, and the environment."] * len(images)
            
#             # Convert all images to proper format
#             processed_images = []
#             for image in images:
#                 processed_image = self._convert_to_pil_image(image)
#                 if processed_image is not None:
#                     processed_images.append(processed_image)
            
#             if not processed_images:
#                 return ["Phi-3-Vision-MLX caption: No valid images to process"] * len(images)
            
#             print(f"[Phi-3-Vision-MLX] Batch processing {len(processed_images)} images...")
            
#             # Use batch generation for efficiency
#             outputs = pv.generate(
#                 prompts[:len(processed_images)],
#                 processed_images,
#                 **self.generation_args
#             )
            
#             # Ensure we have a list of outputs
#             if not isinstance(outputs, list):
#                 outputs = [outputs]
            
#             # Clean up outputs
#             captions = []
#             for output in outputs:
#                 if isinstance(output, str):
#                     captions.append(output.strip())
#                 else:
#                     captions.append(str(output).strip())
            
#             print(f"[Phi-3-Vision-MLX] Successfully generated {len(captions)} captions")
#             return captions
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Batch generation failed: {e}")
#             traceback.print_exc()
#             return [f"Phi-3-Vision-MLX caption: Robot camera captured scene {i+1}" for i in range(len(images))]
    
#     def test_model(self):
#         """Test the model with a simple image"""
#         try:
#             print("[Phi-3-Vision-MLX] Testing model...")
            
#             # Create a simple test image
#             test_image = Image.new('RGB', (224, 224), color='blue')
            
#             # Test with simple prompt
#             response = pv.generate(
#                 "What color is this image?",
#                 test_image,
#                 max_tokens=10,
#                 # temperature=0.0
#             )
            
#             print(f"[Phi-3-Vision-MLX] Model test successful: {response}")
#             return True
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Model test failed: {e}")
#             return False
    
#     def clear_cache(self):
#         """Clear any cached data - phi_3_vision_mlx handles memory automatically"""
#         pass
    
#     def __del__(self):
#         """Cleanup when object is destroyed"""
#         self.clear_cache()


# class Phi3VisionMLXCaptionerAdvanced(Phi3VisionMLXCaptioner):
#     """
#     Advanced version with additional features from phi_3_vision_mlx
#     """
    
#     def __init__(self, model_name=None, use_quantization=True, enable_advanced_features=True):
#         super().__init__(model_name, quantize_model=use_quantization)
        
#         self.enable_advanced_features = enable_advanced_features
        
#         if enable_advanced_features:
#             print("[Phi-3-Vision-MLX] Advanced features enabled")
    
#     def caption_with_constraints(self, images, constraints=None):
#         """Caption with constrained generation for specific formats"""
#         if not self.enable_advanced_features:
#             return self.caption(images)
        
#         try:
#             if not isinstance(images, list):
#                 images = [images]
            
#             # Convert images
#             processed_images = []
#             for image in images:
#                 processed_image = self._convert_to_pil_image(image)
#                 if processed_image is not None:
#                     processed_images.append(processed_image)
            
#             # Use constrained generation if available
#             prompt = "Describe this robot camera view in detail:"
            
#             if constraints:
#                 # Use constrained decoding
#                 output = pv.constrain(
#                     prompt,
#                     processed_images[0] if processed_images else None,
#                     constraints,
#                     quantize_model=self.generation_args["quantize_model"]
#                 )
#             else:
#                 # Regular generation
#                 output = pv.generate(
#                     prompt,
#                     processed_images[0] if processed_images else None,
#                     **self.generation_args
#                 )
            
#             return output if isinstance(output, list) else [output]
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Constrained generation failed: {e}")
#             return self.caption(images)
    
#     def caption_with_choices(self, images, choices="ABCDE", questions=None):
#         """Caption with multiple choice selection"""
#         if not self.enable_advanced_features:
#             return self.caption(images)
        
#         try:
#             if not isinstance(images, list):
#                 images = [images]
            
#             if questions is None:
#                 questions = ["What is the main object in this robot camera view?"] * len(images)
            
#             # Convert images
#             processed_images = []
#             for image in images:
#                 processed_image = self._convert_to_pil_image(image)
#                 if processed_image is not None:
#                     processed_images.append(processed_image)
            
#             # Use choice selection
#             results = pv.choose(
#                 questions[:len(processed_images)],
#                 processed_images,
#                 choices=choices
#             )
            
#             return results if isinstance(results, list) else [results]
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Choice selection failed: {e}")
#             return self.caption(images)























# """
# Phi-3-Vision-MLX captioner for Mac M3 Max - CORRECTED VERSION
# Uses the actual phi_3_vision_mlx framework API correctly
# """

# import os
# import sys
# from pathlib import Path
# from PIL import Image
# import tempfile
# import traceback
# from remembr.captioners.captioner import Captioner

# # Add the Phi-3-Vision-MLX path
# phi3_path = "/Users/wen-chungcheng/Phi-3-Vision-MLX"
# if phi3_path not in sys.path:
#     sys.path.insert(0, phi3_path)

# try:
#     import phi_3_vision_mlx as pv
#     PHI3_VISION_MLX_AVAILABLE = True
#     print("[Phi-3-Vision-MLX] Framework imported successfully")
# except ImportError as e:
#     print(f"[Phi-3-Vision-MLX] Import failed: {e}")
#     PHI3_VISION_MLX_AVAILABLE = False

# class Phi3VisionMLXCaptioner(Captioner):
#     """
#     Phi-3-Vision-MLX captioner optimized for Mac M3 Max
#     Uses the correct phi_3_vision_mlx framework API
#     """
    
#     def __init__(self, model_name=None, quantize_model=True, quantize_cache=False):
#         print(f"[Phi-3-Vision-MLX] Initializing captioner with native Apple Silicon optimization...")
        
#         if not PHI3_VISION_MLX_AVAILABLE:
#             raise ImportError("phi_3_vision_mlx framework not available")
        
#         # CRITICAL FIX: Preload the model to avoid GPU timeout during generation
#         self.preload = None
#         self.quantize_model = quantize_model
#         self.quantize_cache = quantize_cache
        
#         try:
#             print("[Phi-3-Vision-MLX] Loading model...")
#             # Use the load function from phi_3_vision_mlx
#             self.preload = pv.load(
#                 quantize_model=quantize_model,
#                 quantize_cache=quantize_cache
#             )
#             print("[Phi-3-Vision-MLX] ✓ Model preloaded successfully")
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Model loading failed: {e}")
#             traceback.print_exc()
#             self.preload = None
        
#         # Set generation parameters optimized for captioning
#         self.generation_args = {
#             "max_tokens": 256,
#             "temperature": 0.2,
#             "verbose": False,
#             "preload": self.preload,  # CRITICAL: Pass the preloaded model
#             "quantize_model": quantize_model,
#             "quantize_cache": quantize_cache
#         }
        
#         print(f"[Phi-3-Vision-MLX] ✓ Captioner initialized")
#         print(f"[Phi-3-Vision-MLX] Model quantization: {quantize_model}")
#         print(f"[Phi-3-Vision-MLX] Cache quantization: {quantize_cache}")
    
#     def caption(self, images):
#         """Generate captions for images using Phi-3-Vision-MLX"""
#         if not isinstance(images, list):
#             images = [images]
        
#         captions = []
#         for image in images:
#             try:
#                 caption = self._caption_single_image(image)
#                 captions.append(caption)
#             except Exception as e:
#                 print(f"[Phi-3-Vision-MLX] Error captioning image: {e}")
#                 captions.append(f"Phi-3-Vision-MLX caption: Robot camera view - error occurred")
        
#         return captions[0] if len(captions) == 1 else captions
    
#     def caption_image(self, image):
#         """Caption a single image - compatibility method"""
#         return self.caption([image])
    
#     def _convert_to_pil_image(self, image):
#         """Convert image to PIL Image format"""
#         if isinstance(image, str):
#             if image.startswith(('http://', 'https://')):
#                 return image
#             elif os.path.exists(image):
#                 try:
#                     pil_image = Image.open(image).convert('RGB')
#                     print(f"[Phi-3-Vision-MLX] Successfully loaded image from file: {pil_image.size}")
#                     return pil_image
#                 except Exception as e:
#                     print(f"[Phi-3-Vision-MLX] Error loading image file: {e}")
#                     return None
#             else:
#                 print(f"[Phi-3-Vision-MLX] File path does not exist: {image}")
#                 return None
#         elif isinstance(image, Image.Image):
#             return image
#         else:
#             print(f"[Phi-3-Vision-MLX] Unsupported image type: {type(image)}")
#             return None
    
#     def _caption_single_image(self, image):
#         """Caption a single image using Phi-3-Vision-MLX"""
#         if self.preload is None:
#             return "Phi-3-Vision-MLX caption: Model not loaded"
        
#         try:
#             # Convert image to proper format
#             processed_image = self._convert_to_pil_image(image)
            
#             if processed_image is None:
#                 return "Phi-3-Vision-MLX caption: Image could not be processed"
            
#             print(f"[Phi-3-Vision-MLX] Processing image type: {type(processed_image)}")
            
#             # Create prompt optimized for robot scene description
#             prompt = "Describe what you see in this image in detail. Focus on objects, actions, the environment, and spatial relationships."
            
#             print(f"[Phi-3-Vision-MLX] Generating caption...")
            
#             # CRITICAL FIX: Use the correct API signature from phi_3_vision_mlx
#             output = pv.generate(
#                 prompt=prompt,
#                 images=processed_image,  # Note: 'images' parameter name
#                 **self.generation_args
#             )
            
#             # Clean up the output
#             if isinstance(output, str):
#                 caption = output.strip()
#             else:
#                 caption = str(output).strip()
            
#             print(f"[Phi-3-Vision-MLX] Successfully generated caption: {caption[:100]}...")
#             return caption
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Generation failed: {e}")
#             traceback.print_exc()
#             return f"Phi-3-Vision-MLX caption: Robot camera captured a scene in the simulation environment"
    
#     def test_model(self):
#         """Test the model with a simple image"""
#         try:
#             print("[Phi-3-Vision-MLX] Testing model...")
            
#             # Create a simple test image
#             test_image = Image.new('RGB', (224, 224), color='blue')
            
#             # Test with simple prompt
#             response = pv.generate(
#                 prompt="What color is this image?",
#                 images=test_image,
#                 max_tokens=10,
#                 temperature=0.0,
#                 preload=self.preload
#             )
            
#             print(f"[Phi-3-Vision-MLX] Model test successful: {response}")
#             return True
            
#         except Exception as e:
#             print(f"[Phi-3-Vision-MLX] Model test failed: {e}")
#             traceback.print_exc()
#             return False
    
#     def clear_cache(self):
#         """Clear any cached data"""
#         if self.preload is not None:
#             try:
#                 del self.preload
#                 self.preload = None
#             except:
#                 pass
    
#     def __del__(self):
#         """Cleanup when object is destroyed"""
#         self.clear_cache()