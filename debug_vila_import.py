"""
Debug script to identify where the 'int' object has no attribute 'value' error occurs
"""

import sys
import os
import traceback
import warnings

# Add ReMEmbR to path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

# Install mocks first
print("[Debug] Installing mocks...")
exec(open(os.path.join(remembr_path, 'mock_flash_attn.py')).read())

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

# Enhanced error tracking
class AttributeErrorTracker:
    def __init__(self):
        self.original_getattribute = object.__getattribute__
        self.calls = []
    
    def track_getattribute(self, obj, name):
        # Track all attribute access
        if name == 'value' and isinstance(obj, int):
            print(f"[Debug] WARNING: Accessing .value on int object: {obj}")
            print(f"[Debug] Stack trace:")
            traceback.print_stack()
            # Return the int itself as a fallback
            return obj
        return self.original_getattribute(obj, name)

# Install the tracker
tracker = AttributeErrorTracker()

# Patch int.__getattribute__ to catch the error
original_int_getattribute = int.__getattribute__

def patched_int_getattribute(self, name):
    if name == 'value':
        print(f"[Debug] Caught .value access on int {self}")
        traceback.print_stack()
        return self  # Return the int itself
    return original_int_getattribute(self, name)

# Apply the patch
int.__getattribute__ = patched_int_getattribute

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

# Restore original
int.__getattribute__ = original_int_getattribute
print("[Debug] Debug session complete")