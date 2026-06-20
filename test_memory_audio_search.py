#!/usr/bin/env python3
"""
Test script for audio search functionality
"""

import sys
from pathlib import Path

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.agents.mlx_remembr_agent import MLXReMEmbRAgent

def test_audio_search():
    """Test if we can find the clock chime memory"""
    
    print("🧪 Testing audio search functionality...")
    
    # Connect to memory
    memory = MilvusMemory("webots_sounds_multimodal", db_ip="127.0.0.1")
    agent = MLXReMEmbRAgent()
    agent.set_memory(memory)
    
    # Test queries
    test_queries = [
        "take me to where you heard a clock chime",
        "clock chime",
        "chime", 
        "clock",
        "where did you hear a clock",
        "audio clock"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        # Test direct memory search
        memories = memory.search(query, limit=5)
        print(f"   Direct search: {len(memories)} memories found")
        
        for i, mem in enumerate(memories):
            if mem.audio_caption and "clock" in mem.audio_caption.lower():
                print(f"   ✅ Found clock memory {i}: '{mem.audio_caption}' at {mem.position}")
        
        # Test agent query
        try:
            response = agent.query(query)
            if response and response.position:
                print(f"   ✅ Agent found position: {response.position}")
                print(f"   💬 Agent response: {response.text[:100]}...")
            else:
                print(f"   ❌ Agent found no position")
                print(f"   💬 Agent response: {response.text[:100]}..." if response else "No response")
        except Exception as e:
            print(f"   ❌ Agent error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_audio_search()