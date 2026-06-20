"""
Enhanced mock flash_attn module for non-CUDA environments (Mac M3 Max)
This provides fallback implementations that use standard PyTorch operations
"""

import torch
import torch.nn.functional as F
import warnings
import sys
from types import ModuleType
from importlib.machinery import ModuleSpec

# Install triton mock first
try:
    exec(open('/Users/wen-chungcheng/remembr/mock_triton.py').read())
except Exception as e:
    print(f"[Warning] Could not load triton mock: {e}")

# Install FP8 quantization mock
try:
    exec(open('/Users/wen-chungcheng/remembr/mock_fp8_quantization.py').read())
except Exception as e:
    print(f"[Warning] Could not load FP8 quantization mock: {e}")
    
# Install FP8 quantization mock
try:
    exec(open('/Users/wen-chungcheng/remembr/mock_fp8_quantization_triton.py').read())
except Exception as e:
    print(f"[Warning] Could not load triton FP8 quantization mock: {e}")

# Mock the flash_attn functions with standard attention
def flash_attn_unpadded_qkvpacked_func(qkv, cu_seqlens, max_s, dropout_p=0.0, softmax_scale=None, causal=False):
    """Mock implementation using standard PyTorch attention"""
    warnings.warn("Using mock flash_attn implementation for Mac compatibility", UserWarning, stacklevel=2)
    
    # Extract q, k, v from packed format
    batch_size = qkv.shape[0]
    seq_len = qkv.shape[1] 
    num_heads = qkv.shape[2]
    head_dim = qkv.shape[3]
    
    q = qkv[:, :, 0, :, :]  # [batch, seq, heads, dim]
    k = qkv[:, :, 1, :, :]
    v = qkv[:, :, 2, :, :]
    
    # Reshape for standard attention
    q = q.transpose(1, 2)  # [batch, heads, seq, dim]
    k = k.transpose(1, 2)
    v = v.transpose(1, 2)
    
    # Standard scaled dot-product attention
    if softmax_scale is None:
        softmax_scale = 1.0 / (head_dim ** 0.5)
    
    scores = torch.matmul(q, k.transpose(-2, -1)) * softmax_scale
    
    if causal:
        mask = torch.triu(torch.ones(seq_len, seq_len, device=qkv.device), diagonal=1).bool()
        scores.masked_fill_(mask.unsqueeze(0).unsqueeze(0), float('-inf'))
    
    attn_weights = F.softmax(scores, dim=-1)
    
    if dropout_p > 0.0:
        attn_weights = F.dropout(attn_weights, p=dropout_p, training=False)
    
    output = torch.matmul(attn_weights, v)
    output = output.transpose(1, 2)  # [batch, seq, heads, dim]
    
    return output

def flash_attn_varlen_qkvpacked_func(*args, **kwargs):
    """Alias for the main function"""
    return flash_attn_unpadded_qkvpacked_func(*args, **kwargs)

def flash_attn_func(q, k, v, dropout_p=0.0, softmax_scale=None, causal=False, **kwargs):
    """Standard flash_attn_func interface"""
    warnings.warn("Using mock flash_attn implementation for Mac compatibility", UserWarning, stacklevel=2)
    
    if softmax_scale is None:
        softmax_scale = 1.0 / (q.shape[-1] ** 0.5)
    
    scores = torch.matmul(q, k.transpose(-2, -1)) * softmax_scale
    
    if causal:
        seq_len = q.shape[-2]
        mask = torch.triu(torch.ones(seq_len, seq_len, device=q.device), diagonal=1).bool()
        scores.masked_fill_(mask.unsqueeze(0).unsqueeze(0), float('-inf'))
    
    attn_weights = F.softmax(scores, dim=-1)
    
    if dropout_p > 0.0:
        attn_weights = F.dropout(attn_weights, p=dropout_p, training=False)
    
    output = torch.matmul(attn_weights, v)
    return output

def flash_attn_varlen_func(*args, **kwargs):
    """Varlen version - simplified fallback"""
    return flash_attn_func(*args, **kwargs)

def _flash_attn_varlen_forward(*args, **kwargs):
    """Forward function for varlen attention"""
    return flash_attn_varlen_func(*args, **kwargs)

def _flash_attn_varlen_backward(*args, **kwargs):
    """Backward function stub"""
    return None

# Mock the bert_padding module
class MockBertPadding:
    @staticmethod
    def unpad_input(x, attention_mask):
        """Mock unpad_input"""
        return x, None, None, x.shape[1]
    
    @staticmethod
    def pad_input(x, indices, batch_size, seq_len):
        """Mock pad_input"""
        return x
    
    @staticmethod
    def index_first_axis(x, indices):
        """Mock index_first_axis"""
        return x

# Mock version checking functions
def is_flash_attn_2_available():
    """Mock version check - always return True since we're providing mock"""
    return True

def is_flash_attn_greater_or_equal_2_10():
    """Mock version check"""
    return True

def flash_attn_supports_top_left_mask():
    """Mock feature check"""
    return True

# Enhanced mock module creation that handles callable modules
def create_mock_module(name, parent_name=None):
    """Create a properly structured mock module with callable support"""
    module = ModuleType(name)
    
    # Create proper module spec
    spec = ModuleSpec(name, None)
    spec.origin = "mock"
    spec.submodule_search_locations = []
    module.__spec__ = spec
    module.__name__ = name
    module.__file__ = "<mock>"
    module.__package__ = parent_name if parent_name else name.split('.')[0]
    
    # Make the module callable in case it's used as a function
    def _mock_module_call(*args, **kwargs):
        warnings.warn(f"Module {name} called as function - using mock implementation", UserWarning, stacklevel=2)
        return module  # Return the module itself or a mock object
    
    module.__call__ = _mock_module_call
    
    return module

# Create the mock module hierarchy
flash_attn_module = create_mock_module('flash_attn')
flash_attn_module.flash_attn_func = flash_attn_func
flash_attn_module.flash_attn_varlen_func = flash_attn_varlen_func
flash_attn_module.__version__ = "2.5.8"  # Mock version

# Create flash_attn.flash_attn_interface module
flash_attn_interface = create_mock_module('flash_attn.flash_attn_interface', 'flash_attn')
flash_attn_interface.flash_attn_unpadded_qkvpacked_func = flash_attn_unpadded_qkvpacked_func
flash_attn_interface.flash_attn_varlen_qkvpacked_func = flash_attn_varlen_qkvpacked_func
flash_attn_interface._flash_attn_varlen_forward = _flash_attn_varlen_forward
flash_attn_interface._flash_attn_varlen_backward = _flash_attn_varlen_backward

# Create flash_attn.bert_padding module
bert_padding = create_mock_module('flash_attn.bert_padding', 'flash_attn')
bert_padding.unpad_input = MockBertPadding.unpad_input
bert_padding.pad_input = MockBertPadding.pad_input
bert_padding.index_first_axis = MockBertPadding.index_first_axis

# Create flash_attn.losses module (sometimes needed)
losses_module = create_mock_module('flash_attn.losses', 'flash_attn')

# Install the mock modules
sys.modules['flash_attn'] = flash_attn_module
sys.modules['flash_attn.flash_attn_interface'] = flash_attn_interface
sys.modules['flash_attn.bert_padding'] = bert_padding
sys.modules['flash_attn.losses'] = losses_module

# Also install version checking functions in transformers if needed
try:
    import transformers.utils.import_utils
    transformers.utils.import_utils.is_flash_attn_2_available = is_flash_attn_2_available
    transformers.utils.import_utils.is_flash_attn_greater_or_equal_2_10 = is_flash_attn_greater_or_equal_2_10
except ImportError:
    pass

print("[Mock] Enhanced flash_attn modules installed for Mac compatibility")

# Install Qwen2 compatibility layer
try:
    exec(open('/Users/wen-chungcheng/remembr/qwen2_flash_attn_compat.py').read())
except Exception as e:
    print(f"[Warning] Could not load Qwen2 compatibility layer: {e}")
    
    
# Enhanced mock for the 'common' module that VILA needs
# Based on the VILA source code, this module contains FP8 quantization constants
common_module = create_mock_module('common')

# Add FP8 quantization constants based on typical FP8 implementations
common_module.FP8_MAX_VALUE = 448.0  # Typical FP8 E4M3 max value
common_module.SCALE_MIN_THRES = 1e-8  # Minimum scale threshold
common_module.FP8_MIN_VALUE = -448.0  # Typical FP8 E4M3 min value
common_module.FP8_E4M3_MAX = 448.0
common_module.FP8_E5M2_MAX = 57344.0
common_module.FP8_E4M3_MIN = -448.0
common_module.FP8_E5M2_MIN = -57344.0

# Add commonly used FP8 functions
def mock_convert_fp8_to_embit(fp8_type):
    """Mock function to convert FP8 type to embit"""
    if 'e4m3' in str(fp8_type).lower():
        return 8  # 4 exponent + 3 mantissa + 1 sign
    elif 'e5m2' in str(fp8_type).lower():
        return 8  # 5 exponent + 2 mantissa + 1 sign
    else:
        return 8  # Default

def mock_convert_str_to_fp8(fp8_str):
    """Mock function to convert string to FP8 type"""
    if fp8_str == "E4M3":
        return torch.float8_e4m3fn if hasattr(torch, 'float8_e4m3fn') else torch.float16
    elif fp8_str == "E5M2":
        return torch.float8_e5m2 if hasattr(torch, 'float8_e5m2') else torch.float16
    else:
        return torch.float16

# Add these functions to the common module
common_module.convert_fp8_to_embit = mock_convert_fp8_to_embit
common_module.convert_str_to_fp8 = mock_convert_str_to_fp8

# Add sub-modules
common_module.utils = create_mock_module('common.utils', 'common')
common_module.config = create_mock_module('common.config', 'common')

# Add some utility functions to utils
common_module.utils.get_fp8_max_value = lambda fp8_type: common_module.FP8_MAX_VALUE
common_module.utils.get_scale_min_threshold = lambda: common_module.SCALE_MIN_THRES

# Add some config values
common_module.config.FP8_ENABLED = True
common_module.config.DEFAULT_FP8_TYPE = "E4M3"

# Install the modules
sys.modules['common'] = common_module
sys.modules['common.utils'] = common_module.utils
sys.modules['common.config'] = common_module.config

print("[Mock] Enhanced common module installed for VILA compatibility")
print("[Mock] - Added FP8_MAX_VALUE and other FP8 constants")
print("[Mock] - Added FP8 conversion functions")
print("[Mock] - Added utils and config submodules")

# NEW: Mock the 'division' module that VILA needs
# Based on the VILA source code, this contains FP8 division and quantization functions
division_module = create_mock_module('division')

# Mock division functions based on the VILA realquantize/division.py file
def mock_fp8_division_kernel(*args, **kwargs):
    """Mock FP8 division kernel"""
    warnings.warn("Using mock FP8 division kernel for Mac compatibility", UserWarning, stacklevel=2)
    if args:
        return args[0]  # Return first argument (usually the tensor)
    return None

def mock_stochastic_rounding(*args, **kwargs):
    """Mock stochastic rounding function"""
    warnings.warn("Using mock stochastic rounding for Mac compatibility", UserWarning, stacklevel=2)
    if args:
        return args[0]  # Return first argument unchanged
    return None

def mock_fp8_division(*args, **kwargs):
    """Mock FP8 division function"""
    warnings.warn("Using mock FP8 division for Mac compatibility", UserWarning, stacklevel=2)
    if len(args) >= 2:
        weight, group_size = args[0], args[1]
        # Return weight unchanged with a mock scale
        scale = torch.tensor(1.0) if hasattr(torch, 'tensor') else 1.0
        return weight, scale
    return args[0] if args else None, 1.0

def mock_fp8_division_transpose(*args, **kwargs):
    """Mock FP8 division transpose function"""
    warnings.warn("Using mock FP8 division transpose for Mac compatibility", UserWarning, stacklevel=2)
    if len(args) >= 2:
        weight, group_size = args[0], args[1]
        if hasattr(weight, 'transpose'):
            transposed = weight.transpose(-2, -1)
            scale = torch.tensor(1.0) if hasattr(torch, 'tensor') else 1.0
            return transposed, scale
        else:
            return weight, 1.0
    return args[0] if args else None, 1.0

# Add division functions to the module
division_module.fp8_division_kernel = mock_fp8_division_kernel
division_module._fp8_division_kernel = mock_fp8_division_kernel
division_module.stochastic_rounding = mock_stochastic_rounding
division_module._stochastic_rounding = mock_stochastic_rounding
division_module.fp8_division = mock_fp8_division
division_module.fp8_division_transpose = mock_fp8_division_transpose

# Add constants that might be needed
division_module.SCALE_MIN_THRES = 1e-8
division_module.FP8_MAX_VALUE = 448.0

# Add some classes that might be needed
class MockDivisionConfig:
    def __init__(self, *args, **kwargs):
        self.group_size = kwargs.get('group_size', 128)
        self.bits = kwargs.get('bits', 8)
        self.fp8_type = kwargs.get('fp8_type', 'E4M3')

division_module.DivisionConfig = MockDivisionConfig

# Install the division module
sys.modules['division'] = division_module

print("[Mock] division module installed for VILA compatibility")
print("[Mock] - Added FP8 division kernel and related functions")
print("[Mock] - Added stochastic rounding mock")
print("[Mock] - Added division configuration classes")

# Add debugging to trace exactly where the error is occurring
def debug_import_hook():
    """Add debugging to trace import issues"""
    import builtins
    original_import = builtins.__import__
    
    def debug_import(name, *args, **kwargs):
        try:
            result = original_import(name, *args, **kwargs)
            return result
        except Exception as e:
            print(f"[Debug] Import error for {name}: {e}")
            raise
    
    builtins.__import__ = debug_import

# Enable debugging
debug_import_hook()

print("[Debug] Import debugging enabled - will show detailed error location")