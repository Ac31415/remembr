"""
Enhanced debug script to identify the 'int' object has no attribute 'value' error
"""

import sys
import os
import traceback
import warnings
from types import ModuleType

# Add ReMEmbR to path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

# Create an enhanced triton mock that handles the .value access issue
def create_robust_triton_mock():
    """Create a robust triton mock that handles all .value access patterns"""
    
    # Enhanced mock class that can handle any attribute access
    class EnhancedMockType:
        def __init__(self, name="EnhancedMockType", return_value=None):
            self.name = name
            self.return_value = return_value if return_value is not None else self
            # Explicitly set value attribute
            object.__setattr__(self, 'value', self.return_value)
        
        def __getattr__(self, name):
            if name == 'value':
                return self.return_value
            return EnhancedMockType(f"{self.name}.{name}")
        
        def __call__(self, *args, **kwargs):
            return self.return_value
        
        def __getitem__(self, item):
            return EnhancedMockType(f"{self.name}[{item}]")
        
        def __int__(self):
            return 0
        
        def __float__(self):
            return 0.0
        
        def __bool__(self):
            return True
        
        def __str__(self):
            return f"EnhancedMockType({self.name})"
        
        def __repr__(self):
            return f"<EnhancedMockType: {self.name}>"
    
    # Create triton module
    triton_module = ModuleType('triton')
    triton_module.__version__ = "2.1.0"
    
    # Mock functions that return safe values
    def mock_jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def mock_constexpr(value):
        """Enhanced constexpr that wraps any value safely"""
        class SafeConstExpr:
            def __init__(self, val):
                self.val = val
                self.value = val
            
            def __getattr__(self, name):
                if name == 'value':
                    return self.val
                return getattr(self.val, name, EnhancedMockType(f"constexpr.{name}"))
            
            def __call__(self, *args, **kwargs):
                return self.val
            
            def __int__(self):
                try:
                    return int(self.val)
                except:
                    return 0
            
            def __float__(self):
                try:
                    return float(self.val)
                except:
                    return 0.0
        
        return SafeConstExpr(value)
    
    # Set up triton module
    triton_module.jit = mock_jit
    triton_module.cdiv = lambda a, b: (a + b - 1) // b
    triton_module.next_power_of_2 = lambda x: 1 << (max(0, x - 1)).bit_length()
    triton_module.Config = lambda **kwargs: type('MockConfig', (), kwargs)()
    triton_module.autotune = mock_jit
    triton_module.heuristics = EnhancedMockType("heuristics")
    
    # Create triton.language module
    triton_language = ModuleType('triton.language')
    triton_language.__path__ = ['mock_triton_language']
    triton_language.constexpr = mock_constexpr
    
    # Add all language functions
    language_functions = [
        'program_id', 'num_programs', 'arange', 'load', 'store', 'atomic_add',
        'dot', 'sum', 'max', 'min', 'where', 'exp', 'log', 'sqrt', 'sin', 'cos',
        'tan', 'tanh', 'abs', 'floor', 'ceil'
    ]
    
    for func_name in language_functions:
        setattr(triton_language, func_name, EnhancedMockType(func_name))
    
    # Add data types with explicit value handling
    data_types = [
        'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
        'float16', 'float32', 'float64', 'bfloat16'
    ]
    
    for dtype_name in data_types:
        dtype_obj = EnhancedMockType(dtype_name)
        dtype_obj.value = dtype_obj  # Ensure .value returns itself
        setattr(triton_language, dtype_name, dtype_obj)
    
    # Create triton.language.math module
    triton_language_math = ModuleType('triton.language.math')
    math_functions = [
        'abs', 'sin', 'cos', 'tan', 'tanh', 'exp', 'log', 'sqrt', 'floor', 'ceil',
        'acos', 'asin', 'atan', 'atan2', 'sinh', 'cosh', 'asinh', 'acosh', 'atanh'
    ]
    
    for func_name in math_functions:
        setattr(triton_language_math, func_name, EnhancedMockType(f"math.{func_name}"))
    
    triton_language.math = triton_language_math
    
    # Create other triton modules
    triton_ops = ModuleType('triton.ops')
    triton_ops.matmul = EnhancedMockType("ops.matmul")
    
    triton_runtime = ModuleType('triton.runtime')
    triton_runtime.driver = ModuleType('triton.runtime.driver')
    triton_runtime.driver.active = ModuleType('triton.runtime.driver.active')
    
    triton_testing = ModuleType('triton.testing')
    triton_testing.perf_report = EnhancedMockType("testing.perf_report")
    
    triton_compiler = ModuleType('triton.compiler')
    triton_compiler.compile = EnhancedMockType("compiler.compile")
    
    triton_heuristics = ModuleType('triton.heuristics')
    triton_heuristics.matmul = EnhancedMockType("heuristics.matmul")
    
    # Install all modules
    sys.modules['triton'] = triton_module
    sys.modules['triton.language'] = triton_language
    sys.modules['triton.language.math'] = triton_language_math
    sys.modules['triton.ops'] = triton_ops
    sys.modules['triton.runtime'] = triton_runtime
    sys.modules['triton.runtime.driver'] = triton_runtime.driver
    sys.modules['triton.runtime.driver.active'] = triton_runtime.driver.active
    sys.modules['triton.testing'] = triton_testing
    sys.modules['triton.compiler'] = triton_compiler
    sys.modules['triton.heuristics'] = triton_heuristics
    
    print("[Enhanced Debug] Robust triton mock installed")
    return True

# Install the robust triton mock
create_robust_triton_mock()

# Install flash_attn mock
print("[Debug] Installing flash_attn mock...")
try:
    exec(open(os.path.join(remembr_path, 'mock_flash_attn.py')).read())
except Exception as e:
    print(f"[Warning] Flash attn mock issue: {e}")

# Apply patches
from unittest.mock import patch
import torch

def fixed_get_imports(filename):
    from transformers.dynamic_module_utils import get_imports
    imports = get_imports(filename)
    if not torch.cuda.is_available() and "flash_attn" in imports:
        imports.remove("flash_attn")
    if not torch.cuda.is_available() and "ring_flash_attn" in imports:
        imports.remove("ring_flash_attn")
    return imports

# Enhanced error tracking with monkey patching
original_getattribute = object.__getattribute__

def track_value_access(obj, name):
    """Track .value access on objects"""
    if name == 'value' and isinstance(obj, int):
        print(f"[Debug] .value accessed on int: {obj}")
        print(f"[Debug] Type: {type(obj)}")
        print(f"[Debug] Stack trace:")
        for line in traceback.format_stack()[-5:]:
            print(f"  {line.strip()}")
        return obj  # Return the int itself
    return original_getattribute(obj, name)

# Monkey patch object.__getattribute__ temporarily
object.__getattribute__ = track_value_access

print("[Debug] Enhanced error tracking installed")

# Now try to import step by step
try:
    print("[Debug] Step 1: Importing basic modules...")
    with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
        from remembr.memory.memory import MemoryItem
        from remembr.memory.milvus_memory import MilvusMemory
        from remembr.agents.remembr_agent import ReMEmbRAgent
        print("[Debug] ✓ Basic ReMEmbR imports successful")
        
        print("[Debug] Step 2: Importing VILACaptioner...")
        try:
            from remembr.captioners.vila_captioner import VILACaptioner
            print("[Debug] ✓ VILACaptioner import successful!")
        except Exception as e:
            print(f"[Debug] ✗ VILACaptioner import failed: {e}")
            print(f"[Debug] Error type: {type(e)}")
            traceback.print_exc()
            
except Exception as e:
    print(f"[Debug] Error during import: {e}")
    traceback.print_exc()
finally:
    # Restore original
    object.__getattribute__ = original_getattribute
    print("[Debug] Restored original object.__getattribute__")

print("[Debug] Debug session complete")