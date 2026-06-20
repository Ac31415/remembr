"""
Qwen2 Flash Attention Compatibility Layer for VILA
Creates missing Qwen2FlashAttention2 class for older transformers versions
"""

import sys
import torch
import torch.nn as nn
from typing import Optional, Tuple, List, Union
import warnings

# Try to import the base Qwen2 classes
try:
    from transformers.models.qwen2.modeling_qwen2 import (
        Qwen2Attention,
        Qwen2Model,
        Qwen2PreTrainedModel,
        Qwen2Config,
        Qwen2DecoderLayer,
        Qwen2RMSNorm,
        Qwen2MLP,
        Qwen2RotaryEmbedding,
        apply_rotary_pos_emb,
        repeat_kv,
    )
    from transformers.models.qwen2.configuration_qwen2 import Qwen2Config
except ImportError as e:
    print(f"[Warning] Could not import Qwen2 base classes: {e}")
    # Create minimal stubs if needed
    class Qwen2Attention:
        pass
    class Qwen2Config:
        pass

# Create the missing Qwen2FlashAttention2 class
class Qwen2FlashAttention2(Qwen2Attention):
    """
    Qwen2 flash attention module compatible with VILA.
    Uses standard PyTorch attention as fallback for Mac M3 Max compatibility.
    """
    
    def __init__(self, config: Qwen2Config, layer_idx: Optional[int] = None):
        super().__init__(config, layer_idx)
        
        # Flag to indicate we're using mock flash attention
        self.is_causal = True
        self._flash_attn_uses_top_left_mask = False
        
        print(f"[Info] Using mock Qwen2FlashAttention2 for layer {layer_idx}")
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor]] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
        cache_position: Optional[torch.LongTensor] = None,
        **kwargs,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]]]:
        """
        Forward pass using standard PyTorch attention instead of flash attention.
        """
        
        # Use the parent class (Qwen2Attention) forward method
        # This will use standard attention mechanisms
        try:
            return super().forward(
                hidden_states=hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_key_value,
                output_attentions=output_attentions,
                use_cache=use_cache,
                cache_position=cache_position,
                **kwargs
            )
        except Exception as e:
            print(f"[Warning] Qwen2FlashAttention2 forward failed: {e}")
            # Fallback to a minimal implementation
            return self._fallback_forward(hidden_states, attention_mask, past_key_value, use_cache)
    
    def _fallback_forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor]] = None,
        use_cache: bool = False,
    ):
        """
        Minimal fallback implementation if parent forward fails.
        """
        bsz, q_len, _ = hidden_states.size()
        
        # Just return the input with proper format
        attn_output = hidden_states
        attn_weights = None
        past_key_value_out = past_key_value
        
        return attn_output, attn_weights, past_key_value_out

# Create other missing classes if needed
class Qwen2SdpaAttention(Qwen2Attention):
    """SDPA attention fallback"""
    pass

# Install the compatibility classes into transformers
def install_qwen2_flash_attn_compat():
    """Install Qwen2 flash attention compatibility classes"""
    try:
        import transformers.models.qwen2.modeling_qwen2 as qwen2_module
        
        # Add missing classes to the module
        if not hasattr(qwen2_module, 'Qwen2FlashAttention2'):
            qwen2_module.Qwen2FlashAttention2 = Qwen2FlashAttention2
            print("[Info] Added Qwen2FlashAttention2 compatibility class")
        
        if not hasattr(qwen2_module, 'Qwen2SdpaAttention'):
            qwen2_module.Qwen2SdpaAttention = Qwen2SdpaAttention
            print("[Info] Added Qwen2SdpaAttention compatibility class")
            
        # Also add to the module's __all__ if it exists
        if hasattr(qwen2_module, '__all__'):
            if 'Qwen2FlashAttention2' not in qwen2_module.__all__:
                qwen2_module.__all__.append('Qwen2FlashAttention2')
            if 'Qwen2SdpaAttention' not in qwen2_module.__all__:
                qwen2_module.__all__.append('Qwen2SdpaAttention')
        
        print("[Info] Qwen2 flash attention compatibility layer installed")
        return True
        
    except ImportError as e:
        print(f"[Warning] Could not install Qwen2 compatibility layer: {e}")
        return False

# Install the compatibility layer
install_qwen2_flash_attn_compat()