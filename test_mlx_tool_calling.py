#!/usr/bin/env python3
"""
Quick test script for MLX agent tool calling fix
Tests that the agent properly calls retrieval tools instead of generating empty responses
"""

import sys
sys.path.insert(0, '/Users/wen-chungcheng/remembr')

from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.agents.mlx_remembr_agent import MLXReMEmbRAgent

def test_tool_calling():
    """Test that MLX agent properly calls tools for navigation queries"""
    
    print("🧪 Testing MLX Agent Tool Calling Fix")
    print("="*60)
    
    # Initialize memory and agent
    print("\n📚 Initializing memory and agent...")
    memory = MilvusMemory("webots_sounds_multimodal")
    agent = MLXReMEmbRAgent(model_backend="COMMAND_R")
    agent.set_memory(memory)
    print("✅ Initialization complete")
    
    # Test queries
    test_queries = [
        "Go to where I heard car honking",
        "Take me to where I heard someone screaming", 
        "Navigate to the location of the church bells"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🧭 Testing query: '{query}'")
        print(f"{'='*60}")
        
        try:
            result = agent.query(query)
            
            success = result.position is not None and result.position != []
            
            print(f"\n📊 Result:")
            print(f"  Position: {result.position}")
            print(f"  Text: {result.text[:100] if result.text else 'None'}...")
            print(f"  Success: {'✅ YES' if success else '❌ NO'}")
            
            results.append({
                'query': query,
                'success': success,
                'position': result.position,
                'text': result.text
            })
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"Successful queries: {successful}/{total} ({success_rate:.1f}%)")
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('success', False) else "❌"
        print(f"{i}. {status} {result['query'][:50]}...")
        if result.get('position'):
            print(f"   Position: {result['position']}")
    
    if success_rate > 50:
        print(f"\n🎉 SUCCESS! Tool calling is working properly!")
        return True
    else:
        print(f"\n⚠️  WARNING: Success rate is low. Tool calling may need more tuning.")
        return False

if __name__ == "__main__":
    success = test_tool_calling()
    sys.exit(0 if success else 1)
