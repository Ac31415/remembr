"""
Mac-native vision captioner using models that actually work on Mac M3 Max
"""

import torch
import warnings
from PIL import Image
import numpy as np
from typing import Optional, Union
import os

class MacNativeCaptioner:
    """
    Mac-native vision captioner using models optimized for Apple Silicon
    """
    
    def __init__(self, args):
        self.args = args
        self.device = self._get_optimal_device()
        self.model = None
        self.processor = None
        self.model_name = "blip2-opt-2.7b"  # Mac-compatible model
        
        print(f"[MacNative] Initializing Mac-optimized captioner on {self.device}")
        self._initialize_model()
    
    def _get_optimal_device(self):
        """Get the best device for Mac M3 Max"""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    
    def _initialize_model(self):
        """Initialize a Mac-compatible vision model"""
        try:
            # Try BLIP-2 first (works well on Mac)
            self._try_blip2()
        except Exception as e:
            print(f"[MacNative] BLIP-2 failed: {e}")
            try:
                # Fallback to BLIP-1
                self._try_blip1()
            except Exception as e2:
                print(f"[MacNative] BLIP-1 failed: {e2}")
                # Final fallback to CLIP-based captioning
                self._try_clip_captioning()
    
    def _try_blip2(self):
        """Try to initialize BLIP-2 (best option for Mac)"""
        try:
            from transformers import Blip2Processor, Blip2ForConditionalGeneration
            
            print("[MacNative] Loading BLIP-2 model...")
            self.processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                "Salesforce/blip2-opt-2.7b",
                torch_dtype=torch.float16 if self.device.type == "mps" else torch.float32,
                device_map="auto" if self.device.type == "cpu" else None
            )
            
            if self.device.type == "mps":
                self.model = self.model.to(self.device)
            
            self.model_name = "blip2-opt-2.7b"
            print("[MacNative] ✓ BLIP-2 model loaded successfully")
            
        except Exception as e:
            print(f"[MacNative] BLIP-2 initialization failed: {e}")
            raise
    
    def _try_blip1(self):
        """Fallback to BLIP-1"""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            print("[MacNative] Loading BLIP-1 model...")
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                torch_dtype=torch.float16 if self.device.type == "mps" else torch.float32
            )
            
            if self.device.type == "mps":
                self.model = self.model.to(self.device)
            
            self.model_name = "blip-image-captioning-base"
            print("[MacNative] ✓ BLIP-1 model loaded successfully")
            
        except Exception as e:
            print(f"[MacNative] BLIP-1 initialization failed: {e}")
            raise
    
    def _try_clip_captioning(self):
        """Final fallback to CLIP-based captioning"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            print("[MacNative] Loading CLIP model for captioning...")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            
            if self.device.type == "mps":
                self.model = self.model.to(self.device)
            
            self.model_name = "clip-vit-base-patch32"
            print("[MacNative] ✓ CLIP model loaded successfully")
            
        except Exception as e:
            print(f"[MacNative] All model loading failed: {e}")
            raise
    
    def caption_image(self, image: Union[Image.Image, np.ndarray, str]) -> str:
        """
        Generate a caption for the given image
        """
        if self.model is None:
            return "Mac-native captioner not initialized"
        
        try:
            # Convert input to PIL Image
            if isinstance(image, str):
                image = Image.open(image)
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Ensure RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Generate caption based on model type
            if "blip2" in self.model_name:
                return self._blip2_caption(image)
            elif "blip" in self.model_name:
                return self._blip1_caption(image)
            elif "clip" in self.model_name:
                return self._clip_caption(image)
            else:
                return "Unknown model type"
                
        except Exception as e:
            print(f"[MacNative] Captioning error: {e}")
            return f"Error generating caption: {str(e)}"
    
    def _blip2_caption(self, image: Image.Image) -> str:
        """Generate caption using BLIP-2"""
        try:
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_length=50)
            
            caption = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return caption.strip()
            
        except Exception as e:
            print(f"[MacNative] BLIP-2 captioning error: {e}")
            return f"BLIP-2 error: {str(e)}"
    
    def _blip1_caption(self, image: Image.Image) -> str:
        """Generate caption using BLIP-1"""
        try:
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                out = self.model.generate(**inputs, max_length=50)
            
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            return caption.strip()
            
        except Exception as e:
            print(f"[MacNative] BLIP-1 captioning error: {e}")
            return f"BLIP-1 error: {str(e)}"
    
    def _clip_caption(self, image: Image.Image) -> str:
        """Generate caption using CLIP (template-based)"""
        try:
            # Predefined caption templates
            templates = [
                "a photo of a robot",
                "a robot in a room",
                "a robotic scene",
                "a robot exploring",
                "a robot navigating",
                "a robot in an environment"
            ]
            
            inputs = self.processor(text=templates, images=image, return_tensors="pt", padding=True).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get the most likely caption
            best_idx = probs.argmax().item()
            return templates[best_idx]
            
        except Exception as e:
            print(f"[MacNative] CLIP captioning error: {e}")
            return f"CLIP error: {str(e)}"
    
    def __repr__(self):
        return f"MacNativeCaptioner(model={self.model_name}, device={self.device})"