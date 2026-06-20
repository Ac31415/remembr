"""
Mock FP8 quantization modules for Mac M3 Max compatibility
"""

import sys
import torch
import torch.nn as nn
from types import ModuleType
from importlib.machinery import ModuleSpec
import warnings

def create_mock_module(name, parent_name=None):
    """Create a properly structured mock module"""
    module = ModuleType(name)
    
    # Create proper module spec
    spec = ModuleSpec(name, None)
    spec.origin = "mock"
    spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
    module.__spec__ = spec
    module.__name__ = name
    module.__file__ = "<mock>"
    module.__package__ = parent_name if parent_name else name.split('.')[0]
    module.__path__ = [f"mock_{name}"] if not parent_name else []
    
    return module

# Mock FP8 quantization functions
class MockFP8Quantizer:
    """Mock FP8 quantizer that returns original values"""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, x, *args, **kwargs):
        warnings.warn("Using mock FP8 quantization for Mac compatibility", UserWarning, stacklevel=2)
        return x
    
    def quantize(self, x, *args, **kwargs):
        return x
    
    def dequantize(self, x, *args, **kwargs):
        return x

# Mock FP8 functions that return original tensors
def mock_fp8_quantize(x, *args, **kwargs):
    """Mock FP8 quantize function"""
    warnings.warn("Using mock FP8 quantization for Mac compatibility", UserWarning, stacklevel=2)
    return x

def mock_fp8_quantize_pertensor(x, *args, **kwargs):
    """Mock per-tensor FP8 quantize function"""
    warnings.warn("Using mock FP8 per-tensor quantization for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        # Return (quantized_tensor, scale, zero_point) or similar
        return x, torch.tensor(1.0), torch.tensor(0)
    return x, 1.0, 0

def mock_fp8_quantize_pertensor_transpose(x, *args, **kwargs):
    """Mock per-tensor transpose FP8 quantize function"""
    warnings.warn("Using mock FP8 per-tensor transpose quantization for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        return x.transpose(-2, -1), torch.tensor(1.0), torch.tensor(0)
    return x, 1.0, 0

def mock_fp8_linear_forward(x, scale, weight, weight_scale, bias, *args, **kwargs):
    """Mock FP8 linear forward function"""
    warnings.warn("Using mock FP8 linear forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor) and isinstance(weight, torch.Tensor):
        # Simple linear operation
        result = torch.matmul(x, weight.T)
        if bias is not None:
            result = result + bias
        return result
    return x

def mock_fp8_linear_backward(grad_output, *args, **kwargs):
    """Mock FP8 linear backward function"""
    warnings.warn("Using mock FP8 linear backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

def mock_fp8_add_Ifp_Ifp_Ofp_Og16(x, y, *args, **kwargs):
    """Mock FP8 addition function"""
    warnings.warn("Using mock FP8 addition for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor) and isinstance(y, torch.Tensor):
        result = x + y
        return result, (result, torch.tensor(1.0))
    return x + y, (x + y, 1.0)

def mock_fp8_add_Ifp_Ifp_Ofp_Opt(x, y, *args, **kwargs):
    """Mock FP8 addition optimized function"""
    warnings.warn("Using mock FP8 addition optimized for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor) and isinstance(y, torch.Tensor):
        return x + y
    return x + y

def mock_fp8_division(weight, group_size, bits, scale=None):
    """Mock FP8 division function"""
    warnings.warn("Using mock FP8 division for Mac compatibility", UserWarning, stacklevel=2)
    if scale is None:
        scale = torch.tensor(1.0)
    return weight, scale

def mock_fp8_division_transpose(weight, group_size, bits, scale=None):
    """Mock FP8 division transpose function"""
    warnings.warn("Using mock FP8 division transpose for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(weight, torch.Tensor):
        transposed = weight.transpose(-2, -1)
        if scale is None:
            scale = torch.tensor(1.0)
        return transposed, scale
    if scale is None:
        scale = 1.0
    return weight, scale

def mock_fp8_rmsnorm_forward(x, weight, eps=1e-6):
    """Mock FP8 RMS norm forward function"""
    warnings.warn("Using mock FP8 RMS norm forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        # Simple RMS normalization
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + eps)
        if weight is not None:
            x = x * weight
        return x
    return x

def mock_fp8_rmsnorm_backward(grad_output, *args, **kwargs):
    """Mock FP8 RMS norm backward function"""
    warnings.warn("Using mock FP8 RMS norm backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

def mock_fp8_silu_forward(x, *args, **kwargs):
    """Mock FP8 SiLU forward function"""
    warnings.warn("Using mock FP8 SiLU forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        return x * torch.sigmoid(x)
    return x

def mock_fp8_silu_backward(grad_output, *args, **kwargs):
    """Mock FP8 SiLU backward function"""
    warnings.warn("Using mock FP8 SiLU backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

def mock_fp8_gelu_forward(x, *args, **kwargs):
    """Mock FP8 GELU forward function"""
    warnings.warn("Using mock FP8 GELU forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        return torch.nn.functional.gelu(x)
    return x

def mock_fp8_gelu_backward(grad_output, *args, **kwargs):
    """Mock FP8 GELU backward function"""
    warnings.warn("Using mock FP8 GELU backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

def mock_fp8_mul_forward(x, y, *args, **kwargs):
    """Mock FP8 multiplication forward function"""
    warnings.warn("Using mock FP8 multiplication forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor) and isinstance(y, torch.Tensor):
        return x * y
    return x * y

def mock_fp8_mul_backward(grad_output, *args, **kwargs):
    """Mock FP8 multiplication backward function"""
    warnings.warn("Using mock FP8 multiplication backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

def mock_fp8_transpose(x, *args, **kwargs):
    """Mock FP8 transpose function"""
    warnings.warn("Using mock FP8 transpose for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        return x.transpose(-2, -1)
    return x

def mock_fp8_layernorm_noparam_forward(x, eps=1e-6):
    """Mock FP8 layer norm no param forward function"""
    warnings.warn("Using mock FP8 layer norm no param forward for Mac compatibility", UserWarning, stacklevel=2)
    if isinstance(x, torch.Tensor):
        mean = x.mean(-1, keepdim=True)
        var = x.var(-1, keepdim=True, unbiased=False)
        return (x - mean) / torch.sqrt(var + eps)
    return x

def mock_fp8_layernorm_noparam_backward(grad_output, *args, **kwargs):
    """Mock FP8 layer norm no param backward function"""
    warnings.warn("Using mock FP8 layer norm no param backward for Mac compatibility", UserWarning, stacklevel=2)
    return grad_output

# Mock quantization config classes
class MockQuantizationConfig:
    """Mock quantization configuration"""
    def __init__(self, *args, **kwargs):
        self.coat_fp8_args = kwargs.get('coat_fp8_args', {})
        self.group_size = kwargs.get('group_size', 128)
        self.weight_memory_efficient = kwargs.get('weight_memory_efficient', True)
        
    def __getattr__(self, name):
        return getattr(self.coat_fp8_args, name, None)

class MockFP8CacheWeightModule:
    """Mock FP8 cache weight module"""
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, *args, **kwargs):
        return self

class MockFP8Manager:
    """Mock FP8 manager"""
    def __init__(self, *args, **kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

# Mock quantization functions
def mock_Coat_quantize_bgn(*args, **kwargs):
    """Mock COAT quantize begin function"""
    warnings.warn("Using mock COAT quantize begin for Mac compatibility", UserWarning, stacklevel=2)
    return None

def mock_Coat_quantize_end(*args, **kwargs):
    """Mock COAT quantize end function"""
    warnings.warn("Using mock COAT quantize end for Mac compatibility", UserWarning, stacklevel=2)
    return None

# Create the main FloatPointQuantizeTorch module
fp8_module = create_mock_module('FloatPointQuantizeTorch')

# Add all the mock functions to the module
fp8_module.fp8_quantize = mock_fp8_quantize
fp8_module.fp8_quantize_pertensor = mock_fp8_quantize_pertensor
fp8_module.fp8_quantize_pertensor_transpose = mock_fp8_quantize_pertensor_transpose
fp8_module.fp8_linear_forward = mock_fp8_linear_forward
fp8_module.fp8_linear_backward = mock_fp8_linear_backward
fp8_module.fp8_add_Ifp_Ifp_Ofp_Og16 = mock_fp8_add_Ifp_Ifp_Ofp_Og16
fp8_module.fp8_add_Ifp_Ifp_Ofp_Opt = mock_fp8_add_Ifp_Ifp_Ofp_Opt
fp8_module.fp8_division = mock_fp8_division
fp8_module.fp8_division_transpose = mock_fp8_division_transpose
fp8_module.fp8_rmsnorm_forward = mock_fp8_rmsnorm_forward
fp8_module.fp8_rmsnorm_backward = mock_fp8_rmsnorm_backward
fp8_module.fp8_silu_forward = mock_fp8_silu_forward
fp8_module.fp8_silu_backward = mock_fp8_silu_backward
fp8_module.fp8_gelu_forward = mock_fp8_gelu_forward
fp8_module.fp8_gelu_backward = mock_fp8_gelu_backward
fp8_module.fp8_mul_forward = mock_fp8_mul_forward
fp8_module.fp8_mul_backward = mock_fp8_mul_backward
fp8_module.fp8_transpose = mock_fp8_transpose
fp8_module.fp8_layernorm_noparam_forward = mock_fp8_layernorm_noparam_forward
fp8_module.fp8_layernorm_noparam_backward = mock_fp8_layernorm_noparam_backward
fp8_module.Coat_quantize_bgn = mock_Coat_quantize_bgn
fp8_module.Coat_quantize_end = mock_Coat_quantize_end

# Add configuration classes
fp8_module.QuantizationConfig = MockQuantizationConfig
fp8_module.FP8CacheWeightModule = MockFP8CacheWeightModule
fp8_module.FP8Manager = MockFP8Manager

# Install the module
sys.modules['FloatPointQuantizeTorch'] = fp8_module

print("[Mock] FloatPointQuantizeTorch module installed for Mac compatibility")
print("[Mock] - All FP8 quantization functions mocked with standard PyTorch operations")
print("[Mock] - Configuration classes available")
print("[Mock] - Backward compatibility maintained")