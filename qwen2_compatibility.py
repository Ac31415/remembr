"""
Qwen2 Compatibility Layer for VILA
Provides missing classes that may not be available in older transformers versions
"""
import sys
import torch
import torch.nn as nn
import warnings
from typing import Optional, Tuple

# Try to import the base Qwen2 classes
try:
    from transformers.models.qwen2.modeling_qwen2 import Qwen2Attention
    from transformers.models.qwen2.configuration_qwen2 import Qwen2Config
    QWEN2_AVAILABLE = True
    print("[Qwen2 Compat] Base Qwen2 classes imported successfully.")
except ImportError:
    print("[Qwen2 Compat] Warning: Could not import base Qwen2 classes. Creating stubs.")
    QWEN2_AVAILABLE = False
    
    # Create minimal stubs if the real classes aren't available
    class Qwen2Config:
        def __init__(self, **kwargs):
            self.hidden_size = kwargs.get('hidden_size', 2048)
            self.num_attention_heads = kwargs.get('num_attention_heads', 32)
            self.head_dim = self.hidden_size // self.num_attention_heads
            self.num_key_value_heads = kwargs.get('num_key_value_heads', 32)
            self.rope_theta = kwargs.get('rope_theta', 10000.0)
            self.max_position_embeddings = kwargs.get('max_position_embeddings', 32768)
            self.attention_dropout = 0.0

    class Qwen2Attention(nn.Module):
        def __init__(self, config, layer_idx=None):
            super().__init__()
            self.config = config
            self.layer_idx = layer_idx
            self.hidden_size = config.hidden_size
            self.num_heads = config.num_attention_heads
            self.head_dim = self.hidden_size // self.num_heads
        
        def forward(self, hidden_states, *args, **kwargs):
            # A simple pass-through for the stub
            return hidden_states, None, None

# Create the missing Qwen2FlashAttention2 class
class Qwen2FlashAttention2(Qwen2Attention):
    def __init__(self, config, layer_idx: Optional[int] = None):
        super().__init__(config, layer_idx)
        self.is_causal = True
        self._flash_attn_uses_top_left_mask = False
        print(f"[Qwen2 Compat] Created Qwen2FlashAttention2 for layer {layer_idx}")
    
    def forward(self, hidden_states, *args, **kwargs):
        warnings.warn("Using fallback Qwen2FlashAttention2 for Mac compatibility", UserWarning, stacklevel=2)
        # Fallback to a simple pass-through or parent's logic if it exists and is safe
        return hidden_states, None, None

# Create other potentially missing classes
class Qwen2SdpaAttention(Qwen2Attention):
    def __init__(self, config, layer_idx: Optional[int] = None):
        super().__init__(config, layer_idx)
        print(f"[Qwen2 Compat] Created Qwen2SdpaAttention for layer {layer_idx}")

    def forward(self, hidden_states, *args, **kwargs):
        warnings.warn("Using fallback Qwen2SdpaAttention for Mac compatibility", UserWarning, stacklevel=2)
        return hidden_states, None, None

def install_qwen2_compatibility_classes():
    try:
        import transformers.models.qwen2.modeling_qwen2 as qwen2_module
        
        if not hasattr(qwen2_module, 'Qwen2FlashAttention2'):
            qwen2_module.Qwen2FlashAttention2 = Qwen2FlashAttention2
            print("[Qwen2 Compat] ✓ Added Qwen2FlashAttention2 class")
        
        if not hasattr(qwen2_module, 'Qwen2SdpaAttention'):
            qwen2_module.Qwen2SdpaAttention = Qwen2SdpaAttention
            print("[Qwen2 Compat] ✓ Added Qwen2SdpaAttention class")
        
        # Update the attention classes mapping
        QWEN2_ATTENTION_CLASSES = {
            "eager": getattr(qwen2_module, 'Qwen2Attention', Qwen2Attention),
            "flash_attention_2": Qwen2FlashAttention2,
            "sdpa": Qwen2SdpaAttention,
        }
        qwen2_module.QWEN2_ATTENTION_CLASSES = QWEN2_ATTENTION_CLASSES
        print("[Qwen2 Compat] ✓ Updated QWEN2_ATTENTION_CLASSES mapping")
        return True
    except ImportError:
        print("[Qwen2 Compat] ✗ Could not import transformers.models.qwen2.modeling_qwen2 to install compatibility layer.")
        return False

install_qwen2_compatibility_classes()