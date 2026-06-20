"""
Phi-3-Vision-MLX captioner for Mac M3 Max - UPDATED VERSION
Uses improved prompting based on captioner_node.py
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
    Uses improved prompting based on the original ReMEmbR captioner_node.py
    """
    
    def __init__(self, model_name=None, quantize_model=True, quantize_cache=False):
        print(f"[Phi-3-Vision-MLX] Initializing captioner with native Apple Silicon optimization...")
        
        if not PHI3_VISION_MLX_AVAILABLE:
            raise ImportError("phi_3_vision_mlx framework not available")
        
        # CRITICAL FIX: Setup the framework and preload the model
        self.quantize_model = quantize_model
        self.quantize_cache = quantize_cache
        
        try:
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
        
        # UPDATED: Use the same detailed prompt structure as captioner_node.py
        self.prompt = (
            "Please describe in detail what you see in this image. "
            "Specifically focus on the people, objects, environmental features, "
            "events/activities, and other interesting details. Think step by step "
            "about these details and be very specific."
        ).strip()
        
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
        
        print(f"[Phi-3-Vision-MLX] ✓ Captioner initialized with detailed prompting")
        print(f"[Phi-3-Vision-MLX] Model quantization: {quantize_model}")
        print(f"[Phi-3-Vision-MLX] Cache quantization: {quantize_cache}")
        print(f"[Phi-3-Vision-MLX] Prompt: {self.prompt}")
    
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
    
    def _convert_to_pil_image(self, image):
        """Convert image to the format expected by Phi-3-Vision-MLX (file path or URL)"""
        if isinstance(image, str):
            if image.startswith(('http://', 'https://')):
                return image  # Return URL as-is
            elif os.path.exists(image):
                return image  # Return file path as-is
            else:
                print(f"[Phi-3-Vision-MLX] File path does not exist: {image}")
                return None
        elif isinstance(image, Image.Image):
            # CRITICAL FIX: Save PIL Image to temporary file and return the path
            try:
                # Create a temporary file to save the PIL image
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # Save the PIL image to the temporary file
                image.save(temp_path, 'JPEG', quality=95)
                print(f"[Phi-3-Vision-MLX] Saved PIL image to temporary file: {temp_path}")
                return temp_path
                
            except Exception as e:
                print(f"[Phi-3-Vision-MLX] Error saving PIL image to temp file: {e}")
                return None
        else:
            print(f"[Phi-3-Vision-MLX] Unsupported image type: {type(image)}")
            return None
    
    def _caption_single_image(self, image):
        """Caption a single image using Phi-3-Vision-MLX with proper image format"""
        if self.preload is None:
            return "Phi-3-Vision-MLX caption: Model not loaded"
        
        temp_files_to_cleanup = []
        
        try:
            # Convert image to proper format (file path or URL)
            processed_image = self._convert_to_pil_image(image)
            
            if processed_image is None:
                return "Phi-3-Vision-MLX caption: Image could not be processed"
            
            # Track temporary files for cleanup
            if isinstance(image, Image.Image) and os.path.exists(processed_image):
                temp_files_to_cleanup.append(processed_image)
            
            print(f"[Phi-3-Vision-MLX] Processing image: {processed_image}")
            print(f"[Phi-3-Vision-MLX] Generating caption...")
            
            # Generate caption with file path/URL
            output = pv.generate(
                prompt=self.prompt,
                images=processed_image,  # This should now be a file path or URL
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
            # Clean up temporary files
            for temp_file in temp_files_to_cleanup:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        print(f"[Phi-3-Vision-MLX] Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    print(f"[Phi-3-Vision-MLX] Warning: Could not clean up temp file {temp_file}: {e}")
    
    def caption_batch(self, images, prompts=None):
        """Caption multiple images in batch with proper format handling"""
        try:
            if prompts is None:
                prompts = [self.prompt] * len(images)
            
            temp_files_to_cleanup = []
            
            # Convert all images to proper format (file paths/URLs)
            processed_images = []
            for image in images:
                processed_image = self._convert_to_pil_image(image)
                if processed_image is not None:
                    processed_images.append(processed_image)
                    # Track temp files for cleanup
                    if isinstance(image, Image.Image) and os.path.exists(processed_image):
                        temp_files_to_cleanup.append(processed_image)
            
            if not processed_images:
                return ["Phi-3-Vision-MLX caption: No valid images to process"] * len(images)
            
            print(f"[Phi-3-Vision-MLX] Batch processing {len(processed_images)} images...")
            
            # Process images individually since we need to handle temp file cleanup
            captions = []
            for i, processed_image in enumerate(processed_images):
                try:
                    output = pv.generate(
                        prompt=prompts[i] if i < len(prompts) else self.prompt,
                        images=processed_image,
                        **self.generation_args
                    )
                    
                    if isinstance(output, str):
                        caption = output.strip()
                        if '<|end|>' in caption:
                            caption = caption[:caption.find('<|end|>')]
                        captions.append(caption)
                    else:
                        captions.append(str(output).strip())
                        
                except Exception as e:
                    print(f"[Phi-3-Vision-MLX] Error processing image {i}: {e}")
                    captions.append(f"Phi-3-Vision-MLX caption: Robot camera captured scene {i+1}")
            
            # Clean up temporary files
            for temp_file in temp_files_to_cleanup:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"[Phi-3-Vision-MLX] Warning: Could not clean up temp file {temp_file}: {e}")
            
            print(f"[Phi-3-Vision-MLX] Successfully generated {len(captions)} captions")
            return captions
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Batch generation failed: {e}")
            traceback.print_exc()
            return [f"Phi-3-Vision-MLX caption: Robot camera captured scene {i+1}" for i in range(len(images))]
    
    def test_model(self):
        """Test the model with a simple image"""
        if self.preload is None:
            print("[Phi-3-Vision-MLX] Model not loaded, skipping test")
            return False
            
        try:
            print("[Phi-3-Vision-MLX] Testing model...")
            
            # Create a simple test image and save to temp file
            test_image = Image.new('RGB', (224, 224), color='blue')
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            test_image.save(temp_path, 'JPEG')
            
            # Test with simple prompt using the file path
            response = pv.generate(
                prompt="What color is this image?",
                images=temp_path,  # Use file path instead of PIL Image
                max_tokens=10,
                preload=self.preload,
                verbose=False,
                stream=False
            )
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
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
    Advanced version with additional features and more detailed prompting
    """
    
    def __init__(self, model_name=None, use_quantization=True, enable_advanced_features=True):
        super().__init__(model_name, quantize_model=use_quantization)
        
        self.enable_advanced_features = enable_advanced_features
        
        # UPDATED: More detailed prompts for different scenarios
        self.detailed_prompts = {
            'navigation': (
                "Describe this robot navigation scene in detail. Focus on the layout of the space, "
                "any obstacles, pathways, landmarks, and objects that could be useful for navigation. "
                "Be specific about spatial relationships and environmental features."
            ),
            'exploration': (
                "Describe what the robot is discovering in this exploration scene. Focus on new "
                "objects, environmental features, people, activities, and anything interesting or "
                "unusual. Think step by step about the details you observe."
            ),
            'interaction': (
                "Describe this scene where the robot might interact with objects or people. "
                "Focus on the people present, their activities, objects they're using, and the "
                "overall social or interactive context. Be very specific about details."
            )
        }
        
        if enable_advanced_features:
            print("[Phi-3-Vision-MLX] Advanced features enabled with detailed prompting")
    
    def caption_with_scenario(self, images, scenario='exploration'):
        """Caption with scenario-specific detailed prompts"""
        if not self.enable_advanced_features:
            return self.caption(images)
        
        try:
            if not isinstance(images, list):
                images = [images]
            
            # Use scenario-specific prompt
            scenario_prompt = self.detailed_prompts.get(scenario, self.prompt)
            print(f"[Phi-3-Vision-MLX] Using {scenario} scenario prompt: {scenario_prompt[:50]}...")
            
            # Convert images
            processed_images = []
            for image in images:
                processed_image = self._convert_to_pil_image(image)
                if processed_image is not None:
                    processed_images.append(processed_image)
            
            if not processed_images:
                return ["Phi-3-Vision-MLX caption: No valid images to process"] * len(images)
            
            # Generate with scenario-specific prompt
            captions = []
            for processed_image in processed_images:
                output = pv.generate(
                    prompt=scenario_prompt,
                    images=processed_image,
                    **self.generation_args
                )
                
                if isinstance(output, str):
                    caption = output.strip()
                    if '<|end|>' in caption:
                        caption = caption[:caption.find('<|end|>')]
                    captions.append(caption)
                else:
                    captions.append(str(output).strip())
            
            return captions[0] if len(captions) == 1 else captions
            
        except Exception as e:
            print(f"[Phi-3-Vision-MLX] Scenario captioning failed: {e}")
            return self.caption(images)