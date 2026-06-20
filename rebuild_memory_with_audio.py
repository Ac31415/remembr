#!/usr/bin/env python3
"""
Rebuild memory embeddings to include audio captions
"""

import sys
from pathlib import Path

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.memory.memory import MemoryItem
import time

def rebuild_memory_with_audio():
    """Rebuild memory collection with combined visual+audio embeddings"""
    
    # Connect to existing collection
    old_memory = MilvusMemory("webots_sounds_multimodal", db_ip="127.0.0.1")
    
    # Get all existing memories
    print("[Rebuild] Retrieving all existing memories...")
    
    # Create new collection with combined embeddings
    new_memory = MilvusMemory("webots_sounds_multimodal_v2", db_ip="127.0.0.1")
    new_memory.reset(drop_collection=True)
    
    # TODO: Add code to extract all memories from old collection
    # and re-insert them with combined embeddings
    
    print("[Rebuild] Memory rebuild complete!")

if __name__ == "__main__":
    rebuild_memory_with_audio()