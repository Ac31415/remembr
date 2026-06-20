#!/usr/bin/env python3
"""
MLX-powered ReMEmbR Memory Query Script
Uses native Mac acceleration with MLX Command-R
"""

import sys
import os
import argparse
from pathlib import Path

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory import MilvusMemory
from remembr.agents.mlx_remembr_agent import MLXReMEmbRAgent
import time

class MLXReMEmbRQuery:
    def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1"):
        print(f"[MLX Query] Connecting to ReMEmbR with native Mac acceleration...")
        print(f"[MLX Query] Collection: {collection_name}")
        print(f"[MLX Query] Database IP: {db_ip}")
        
        try:
            # Connect to memory database
            self.memory = MilvusMemory(collection_name, db_ip=db_ip)
            print("[MLX Query] ✓ Connected to memory database")
            
            # Initialize MLX agent
            self.agent = MLXReMEmbRAgent()
            self.agent.set_memory(self.memory)
            print("[MLX Query] ✓ MLX ReMEmbR agent initialized")
            
        except Exception as e:
            print(f"[MLX Error] Failed to connect: {e}")
            sys.exit(1)
    
    def query_memory(self, question):
        """Query the memory using MLX acceleration"""
        print(f"\n🔍 Processing query with MLX: '{question}'")
        print("⏳ Querying MLX ReMEmbR agent...")
        
        try:
            start_time = time.time()
            response = self.agent.query(question)
            end_time = time.time()
            
            print(f"✅ Query completed in {end_time - start_time:.2f} seconds")
            return response
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None
    
    def display_response(self, question, response):
        """Display the response"""
        print("\n" + "="*60)
        print("🤖 MLX REMEMBR RESPONSE")
        print("="*60)
        print(f"❓ Question: {question}")
        print("-" * 60)
        
        if response:
            print(f"💬 Response: {response.text}")
            
            if hasattr(response, 'position') and response.position:
                print(f"📍 Relevant Position: {response.position}")
            
            if hasattr(response, 'confidence') and response.confidence:
                print(f"🎯 Confidence: {response.confidence:.2f}")
                
            if hasattr(response, 'reasoning') and response.reasoning:
                print(f"🧠 Reasoning: {response.reasoning}")
                
        else:
            print("❌ No response received")
        
        print("="*60)
    
    def run_interactive_mode(self):
        """Run interactive query mode"""
        print("\n🚀 MLX ReMEmbR Interactive Query Mode")
        print("Native Mac acceleration with MLX framework!")
        print("Ask questions to learn about the robot's experiences.")
        
        while True:
            try:
                question = input("\n🤖 Ask a question (or 'quit' to exit): ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not question:
                    continue
                
                response = self.query_memory(question)
                self.display_response(question, response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

def main():
    parser = argparse.ArgumentParser(description='MLX-powered ReMEmbR Query Tool')
    parser.add_argument('--collection', '-c', default='webots_simulation')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1')
    parser.add_argument('--query', '-q', type=str, help='Single query to execute')
    
    args = parser.parse_args()
    
    print("🤖 MLX ReMEmbR Query Tool")
    print("Native Mac M3 Max Acceleration")
    print("="*50)
    
    # Create the MLX query interface
    query_interface = MLXReMEmbRQuery(
        collection_name=args.collection,
        db_ip=args.db_ip
    )
    
    if args.query:
        # Single query mode
        response = query_interface.query_memory(args.query)
        query_interface.display_response(args.query, response)
    else:
        # Interactive mode
        query_interface.run_interactive_mode()

if __name__ == "__main__":
    main()