"""
Targeted debug script to identify the 'int' object has no attribute 'value' error
Uses a different approach without patching built-in types
"""

import sys
import os
import traceback
import warnings
import importlib
from types import ModuleType

# Add ReMEmbR to path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

# Install robust triton mock
exec(open(os.path.join(remembr_path, 'mock_triton.py')).read())

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

# Create a comprehensive error handler
def debug_import_with_detailed_traceback():
    """Import with detailed error tracking"""
    try:
        print("[Debug] Step 1: Importing basic modules...")
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            from remembr.memory.memory import MemoryItem
            from remembr.memory.milvus_memory import MilvusMemory
            from remembr.agents.remembr_agent import ReMEmbRAgent
            print("[Debug] ✓ Basic ReMEmbR imports successful")
            
            print("[Debug] Step 2: Trying to import VILACaptioner...")
            
            # Try to import step by step to isolate the issue
            try:
                print("[Debug] 2.1: Importing VILACaptioner module...")
                from remembr.captioners import vila_captioner
                print("[Debug] ✓ VILACaptioner module imported")
                
                print("[Debug] 2.2: Accessing VILACaptioner class...")
                VILACaptioner = vila_captioner.VILACaptioner
                print("[Debug] ✓ VILACaptioner class accessed")
                
                print("[Debug] ✓ VILACaptioner import successful!")
                return True
                
            except AttributeError as e:
                print(f"[Debug] ✗ AttributeError in VILACaptioner: {e}")
                print(f"[Debug] Error details: {type(e).__name__}: {str(e)}")
                
                # Print the full traceback
                print("[Debug] Full traceback:")
                traceback.print_exc()
                
                # Try to identify where the .value access occurs
                tb = traceback.extract_tb(e.__traceback__)
                for frame in tb:
                    print(f"[Debug] Frame: {frame.filename}:{frame.lineno} in {frame.name}")
                    print(f"[Debug] Code: {frame.line}")
                
                return False
                
            except Exception as e:
                print(f"[Debug] ✗ Other error in VILACaptioner: {e}")
                print(f"[Debug] Error type: {type(e)}")
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"[Debug] Error during basic imports: {e}")
        traceback.print_exc()
        return False

# Enhanced triton mock with .value debugging
def create_enhanced_triton_mock():
    """Create enhanced triton mock with better debugging"""
    
    class DebugMockTritonType:
        def __init__(self, name="DebugMockTritonType"):
            self.name = name
            self._value = self  # Set default value to self
            print(f"[Debug] Created DebugMockTritonType: {name}")
        
        def __getattr__(self, name):
            print(f"[Debug] Accessing attribute '{name}' on {self.name}")
            if name == 'value':
                print(f"[Debug] Returning .value for {self.name}: {self._value}")
                return self._value
            return DebugMockTritonType(f"{self.name}.{name}")
        
        def __call__(self, *args, **kwargs):
            print(f"[Debug] Calling {self.name} with args={args}, kwargs={kwargs}")
            return self._value
        
        def __str__(self):
            return f"DebugMockTritonType({self.name})"
        
        def __repr__(self):
            return f"<DebugMockTritonType: {self.name}>"
    
    # Override the existing triton mock with debug version
    import triton.language
    
    # Replace data types with debug versions
    for dtype_name in ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float16', 'float32', 'float64', 'bfloat16']:
        debug_dtype = DebugMockTritonType(dtype_name)
        setattr(triton.language, dtype_name, debug_dtype)
    
    print("[Debug] Enhanced triton mock with debugging installed")

# Install enhanced triton mock
create_enhanced_triton_mock()

# Run the debug import
print("[Debug] Starting targeted import debugging...")
success = debug_import_with_detailed_traceback()

if success:
    print("[Debug] ✓ Import successful!")
else:
    print("[Debug] ✗ Import failed - check details above")

print("[Debug] Debug session complete")



























# """
# Simple debug approach to identify the .value attribute access issue
# """

# import sys
# import os
# import traceback

# # Add ReMEmbR to path
# remembr_path = "/Users/wen-chungcheng/remembr"
# if remembr_path not in sys.path:
#     sys.path.insert(0, remembr_path)

# # Install mocks
# print("[Debug] Installing mocks...")
# exec(open(os.path.join(remembr_path, 'mock_triton.py')).read())
# exec(open(os.path.join(remembr_path, 'mock_flash_attn.py')).read())

# # Monkey patch the specific modules that might be causing issues
# import torch

# # Create a custom AttributeError handler that gives more info
# original_getattribute = getattr

# def debug_getattribute(obj, name):
#     """Debug version of getattribute"""
#     try:
#         return original_getattribute(obj, name)
#     except AttributeError as e:
#         if name == 'value' and isinstance(obj, int):
#             print(f"[Debug] FOUND IT! .value accessed on int: {obj}")
#             print(f"[Debug] Stack trace of the error:")
#             traceback.print_stack()
#             print(f"[Debug] Original error: {e}")
#             # Return the int itself as a workaround
#             return obj
#         raise

# # Apply the debug wrapper
# import builtins
# builtins.getattr = debug_getattribute

# try:
#     print("[Debug] Testing import with enhanced debugging...")
#     from unittest.mock import patch
    
#     def fixed_get_imports(filename):
#         from transformers.dynamic_module_utils import get_imports
#         imports = get_imports(filename)
#         if not torch.cuda.is_available() and "flash_attn" in imports:
#             imports.remove("flash_attn")
#         if not torch.cuda.is_available() and "ring_flash_attn" in imports:
#             imports.remove("ring_flash_attn")
#         return imports
    
#     with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
#         from remembr.memory.memory import MemoryItem
#         from remembr.memory.milvus_memory import MilvusMemory
#         from remembr.agents.remembr_agent import ReMEmbRAgent
        
#         print("[Debug] Basic imports successful, trying VILA...")
#         from remembr.captioners.vila_captioner import VILACaptioner
#         print("[Debug] SUCCESS! VILACaptioner imported")
        
# except Exception as e:
#     print(f"[Debug] Error caught: {e}")
#     print(f"[Debug] Error type: {type(e)}")
#     traceback.print_exc()
# finally:
#     # Restore original
#     builtins.getattr = original_getattribute
#     print("[Debug] Restored original getattr")