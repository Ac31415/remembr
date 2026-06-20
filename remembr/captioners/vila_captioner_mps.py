import torch
import argparse
import re
from io import BytesIO
import os, os.path as osp
import warnings

import requests
from PIL import Image
import numpy as np
from remembr.captioners.captioner import Captioner

from llava.constants import (DEFAULT_IM_END_TOKEN, DEFAULT_IM_START_TOKEN,
                             DEFAULT_IMAGE_TOKEN, IMAGE_PLACEHOLDER,
                             IMAGE_TOKEN_INDEX)
from llava.conversation import SeparatorStyle, conv_templates
from llava.mm_utils import (KeywordsStoppingCriteria, get_model_name_from_path,
                            process_images, tokenizer_image_token)
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init


def image_parser(args):
    out = args.image_file.split(args.sep)
    return out


def load_image(image_file):
    if image_file.startswith("http") or image_file.startswith("https"):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = Image.open(image_file).convert("RGB")
    return image


def load_images(image_files):
    out = []
    for image_file in image_files:
        image = load_image(image_file)
        out.append(image)
    return out


def _check_mps_autocast_support():
    """Check if MPS autocast is supported in this PyTorch version"""
    try:
        with torch.autocast(device_type='mps', dtype=torch.float16, enabled=True):
            pass
        return True
    except (RuntimeError, ValueError):
        return False


class VILACaptionerMPS(Captioner):
    """
    VILA Captioner specifically optimized for Mac M3 Max with MPS backend.
    This version uses Metal Performance Shaders for optimal performance on Apple Silicon.
    """

    def __init__(self, args):
        # Model initialization
        disable_torch_init()
        
        print("[Info] Initializing VILA Captioner with MPS backend for Mac M3 Max")
        
        self.model_name = get_model_name_from_path(args.model_path)
        self.tokenizer, self.model, self.image_processor, self.context_len = load_pretrained_model(
            args.model_path, self.model_name, args.model_base
        )

        # Determine conversation mode
        if "llama-2" in self.model_name.lower():
            conv_mode = "llava_llama_2"
        elif "v1" in self.model_name.lower():
            conv_mode = "llava_v1"
        elif "mpt" in self.model_name.lower():
            conv_mode = "mpt"
        else:
            conv_mode = "llava_v0"

        if args.conv_mode is not None and conv_mode != args.conv_mode:
            print(
                "[WARNING] the auto inferred conversation mode is {}, while `--conv-mode` is {}, using {}".format(
                    conv_mode, args.conv_mode, args.conv_mode
                )
            )
        else:
            args.conv_mode = conv_mode

        self.args = args
        
        # MPS-specific device setup
        self.device = self._get_mps_device()
        print(f"[Info] Using device: {self.device}")
        
        # Move model to MPS device
        if hasattr(self.model, 'to'):
            self.model = self.model.to(self.device)
            print(f"[Info] Model moved to {self.device}")
        
        # Set model to evaluation mode for inference
        self.model.eval()
        
        # MPS-specific optimizations
        self._setup_mps_optimizations()
    
    def _get_mps_device(self):
        """Get the best available device, prioritizing MPS for Mac M3 Max"""
        if torch.backends.mps.is_available():
            return torch.device('mps')
        elif torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')
    
    def _setup_mps_optimizations(self):
        """Setup MPS-specific optimizations"""
        if self.device.type == 'mps':
            # Enable MPS optimizations
            print("[Info] Setting up MPS optimizations for Mac M3 Max")
            
            # Set appropriate data types for MPS
            self.compute_dtype = torch.float16  # MPS supports float16 well
            
            # Check if MPS autocast is supported
            self.use_mps_autocast = _check_mps_autocast_support()
            if not self.use_mps_autocast:
                print("[Warning] MPS autocast not supported in this PyTorch version, using manual casting")
            
            # Enable memory efficient attention if available
            if hasattr(torch.backends.mps, 'is_memory_efficient_attention_available'):
                if torch.backends.mps.is_memory_efficient_attention_available():
                    print("[Info] MPS memory efficient attention enabled")
            
            # Set MPS memory allocation strategy
            if hasattr(torch.mps, 'set_per_process_memory_fraction'):
                torch.mps.set_per_process_memory_fraction(0.8)  # Reserve 80% for model
                print("[Info] MPS memory allocation optimized")
        else:
            self.compute_dtype = torch.float32
            self.use_mps_autocast = False

    def caption(self, images: list[Image.Image]):
        """
        Generate captions for images using MPS-optimized inference.
        """
        args = self.args
        
        # Prepare the query
        qs = args.query
        image_token_se = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN
        
        if IMAGE_PLACEHOLDER in qs:
            if self.model.config.mm_use_im_start_end:
                qs = re.sub(IMAGE_PLACEHOLDER, image_token_se, qs)
            else:
                qs = re.sub(IMAGE_PLACEHOLDER, DEFAULT_IMAGE_TOKEN, qs)
        else:
            if DEFAULT_IMAGE_TOKEN not in qs:
                if self.model.config.mm_use_im_start_end:
                    qs = (image_token_se + "\n") * len(images) + qs
                else:
                    qs = (DEFAULT_IMAGE_TOKEN + "\n") * len(images) + qs

        # Setup conversation
        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], qs)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        # MPS-optimized inference with proper autocast handling
        if self.device.type == 'mps' and self.use_mps_autocast:
            # Use MPS autocast if supported
            with torch.autocast(device_type='mps', dtype=self.compute_dtype, enabled=True):
                return self._inference_forward(images, prompt, args)
        elif self.device.type == 'cuda':
            # Use CUDA autocast
            with torch.autocast(device_type='cuda', dtype=torch.float16, enabled=True):
                return self._inference_forward(images, prompt, args)
        else:
            # Manual casting for MPS without autocast support or CPU
            return self._inference_forward_manual_cast(images, prompt, args)
    
    def _inference_forward(self, images, prompt, args):
        """Forward pass with autocast enabled"""
        # Process images and move to device
        images_tensor = process_images(images, self.image_processor, self.model.config)
        images_tensor = images_tensor.to(self.device, dtype=self.compute_dtype)
        
        # Tokenize and move to device
        input_ids = tokenizer_image_token(prompt, self.tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt")
        input_ids = input_ids.unsqueeze(0).to(self.device)

        # Setup stopping criteria
        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], args.query)
        conv.append_message(conv.roles[1], None)
        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, self.tokenizer, input_ids)

        # Generate
        with torch.inference_mode():
            output_ids = self.model.generate(
                input_ids,
                images=[images_tensor],
                do_sample=True if args.temperature > 0 else False,
                temperature=args.temperature,
                top_p=args.top_p,
                num_beams=args.num_beams,
                max_new_tokens=args.max_new_tokens,
                use_cache=True,
                stopping_criteria=[stopping_criteria],
                pad_token_id=self.tokenizer.eos_token_id
            )

        return self._decode_output(output_ids, stop_str)
    
    def _inference_forward_manual_cast(self, images, prompt, args):
        """Forward pass with manual casting for MPS without autocast support"""
        print("[Info] Using manual casting for MPS compatibility")
        
        # Process images and move to device with manual casting
        images_tensor = process_images(images, self.image_processor, self.model.config)
        
        # Manual casting to appropriate dtype
        if self.device.type == 'mps':
            images_tensor = images_tensor.to(self.device, dtype=self.compute_dtype)
        else:
            images_tensor = images_tensor.to(self.device)
        
        # Tokenize and move to device
        input_ids = tokenizer_image_token(prompt, self.tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt")
        input_ids = input_ids.unsqueeze(0).to(self.device)

        # Setup stopping criteria
        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], args.query)
        conv.append_message(conv.roles[1], None)
        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, self.tokenizer, input_ids)

        # Generate with manual memory management
        with torch.inference_mode():
            # Clear cache before inference
            if self.device.type == 'mps':
                torch.mps.empty_cache()
            
            output_ids = self.model.generate(
                input_ids,
                images=[images_tensor],
                do_sample=True if args.temperature > 0 else False,
                temperature=args.temperature,
                top_p=args.top_p,
                num_beams=args.num_beams,
                max_new_tokens=args.max_new_tokens,
                use_cache=True,
                stopping_criteria=[stopping_criteria],
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Clear cache after inference
            if self.device.type == 'mps':
                torch.mps.empty_cache()

        return self._decode_output(output_ids, stop_str)
    
    def _decode_output(self, output_ids, stop_str):
        """Decode the output tokens"""
        outputs = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
        outputs = outputs.strip()
        if outputs.endswith(stop_str):
            outputs = outputs[:-len(stop_str)]
        outputs = outputs.strip()
        return outputs
    
    def clear_cache(self):
        """Clear MPS cache to free memory"""
        if self.device.type == 'mps':
            torch.mps.empty_cache()
        elif self.device.type == 'cuda':
            torch.cuda.empty_cache()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.clear_cache()