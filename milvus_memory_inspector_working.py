#!/usr/bin/env python3
"""
Milvus Memory Database Inspector
Lists and displays all memory items in a Milvus collection
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import time

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory import MilvusMemory
from remembr.memory.memory import MemoryItem
from pymilvus import connections, Collection, utility

class MilvusMemoryInspector:
    """Inspector for Milvus memory collections"""
    
    def __init__(self, collection_name="webots_simulation", db_ip="127.0.0.1", db_port=19530):
        self.collection_name = collection_name
        self.db_ip = db_ip
        self.db_port = db_port
        self.memory = None
        
        print(f"[Memory Inspector] Connecting to Milvus...")
        print(f"[Memory Inspector] Collection: {collection_name}")
        print(f"[Memory Inspector] Database: {db_ip}:{db_port}")
        
        # Connect to Milvus
        try:
            connections.connect(host=db_ip, port=db_port)
            print("[Memory Inspector] ✓ Connected to Milvus")
        except Exception as e:
            print(f"[Memory Inspector] ❌ Failed to connect to Milvus: {e}")
            raise
        
        # Check if collection exists
        if not utility.has_collection(collection_name):
            print(f"[Memory Inspector] ❌ Collection '{collection_name}' does not exist")
            print("[Memory Inspector] Available collections:")
            try:
                collections = utility.list_collections()
                for col in collections:
                    print(f"  - {col}")
            except Exception as e:
                print(f"  Error listing collections: {e}")
            raise ValueError(f"Collection '{collection_name}' not found")
        
        # Initialize memory interface
        try:
            self.memory = MilvusMemory(collection_name, db_ip=db_ip, db_port=db_port)
            self.collection = Collection(collection_name)
            self.collection.load()
            print("[Memory Inspector] ✓ Memory interface initialized")
        except Exception as e:
            print(f"[Memory Inspector] ❌ Failed to initialize memory interface: {e}")
            raise
    
    def get_collection_info(self):
        """Get basic information about the collection"""
        try:
            # Get schema information
            schema = self.collection.schema
            
            # Try to get row count using query
            try:
                # Count total records
                count_result = self.collection.query(
                    expr="id != ''",
                    output_fields=["count(*)"],
                    consistency_level="Strong"
                )
                row_count = len(self.collection.query(expr="id != ''", output_fields=["id"], limit=16384))
            except Exception as e:
                print(f"[Memory Inspector] Could not get row count: {e}")
                row_count = "Unknown"
            
            info = {
                'name': self.collection_name,
                'description': schema.description,
                'row_count': row_count,
                'fields': []
            }
            
            # Get field information
            for field in schema.fields:
                field_info = {
                    'name': field.name,
                    'type': str(field.dtype),
                    'description': field.description,
                    'is_primary': field.is_primary
                }
                
                # Add dimension for vector fields
                if hasattr(field, 'params') and field.params:
                    field_info['params'] = field.params
                
                # Add max_length for varchar fields
                if hasattr(field, 'max_length') and field.max_length:
                    field_info['max_length'] = field.max_length
                
                info['fields'].append(field_info)
            
            return info
            
        except Exception as e:
            print(f"[Memory Inspector] Error getting collection info: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_all_items(self, limit=None, output_format='table', save_to_file=None):
        """List all memory items in the collection"""
        try:
            print(f"[Memory Inspector] Retrieving all memory items...")
            
            # Query all items with pagination if needed
            all_results = []
            batch_size = 1000  # Process in batches
            offset = 0
            
            while True:
                try:
                    if limit and len(all_results) >= limit:
                        break
                    
                    # Calculate how many to fetch in this batch
                    current_limit = min(batch_size, limit - len(all_results)) if limit else batch_size
                    
                    # Query batch
                    results = self.collection.query(
                        expr="id != ''",
                        output_fields=["*"],
                        limit=current_limit,
                        offset=offset
                    )
                    
                    if not results:
                        break
                    
                    all_results.extend(results)
                    offset += len(results)
                    
                    print(f"[Memory Inspector] Retrieved {len(all_results)} items so far...")
                    
                    # If we got fewer results than requested, we've reached the end
                    if len(results) < current_limit:
                        break
                    
                except Exception as e:
                    print(f"[Memory Inspector] Error in batch query: {e}")
                    # Try without offset/limit
                    results = self.collection.query(
                        expr="id != ''",
                        output_fields=["*"]
                    )
                    all_results = results
                    break
            
            print(f"[Memory Inspector] ✓ Retrieved {len(all_results)} total items")
            
            if not all_results:
                print("[Memory Inspector] No items found in collection")
                return []
            
            # Convert to MemoryItem objects
            memory_items = []
            for result in all_results:
                try:
                    # Handle time field (could be list or float)
                    time_value = result.get('time', 0.0)
                    if isinstance(time_value, list) and len(time_value) > 0:
                        time_value = time_value[0]
                    
                    memory_item = MemoryItem(
                        caption=result.get('caption', ''),
                        time=float(time_value),
                        position=result.get('position', [0.0, 0.0, 0.0]),
                        theta=result.get('theta', 0.0),
                        audio_caption=result.get('audio_caption', '')
                    )
                    
                    # Add ID for reference
                    memory_item.id = result.get('id', '')
                    
                    memory_items.append(memory_item)
                    
                except Exception as e:
                    print(f"[Memory Inspector] Error converting item: {e}")
                    continue
            
            # Sort by time
            memory_items.sort(key=lambda x: x.time)
            
            # Apply limit after sorting if specified
            if limit:
                memory_items = memory_items[:limit]
            
            # Display results
            if output_format == 'table':
                self.display_table(memory_items)
            elif output_format == 'json':
                self.display_json(memory_items)
            elif output_format == 'detailed':
                self.display_detailed(memory_items)
            
            # Save to file if requested
            if save_to_file:
                self.save_to_file(memory_items, save_to_file)
            
            return memory_items
            
        except Exception as e:
            print(f"[Memory Inspector] Error listing items: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def display_table(self, memory_items):
        """Display items in table format"""
        print(f"\n{'='*140}")
        print(f"Memory Items Table ({len(memory_items)} items)")
        print(f"{'='*140}")
        
        # Header
        print(f"{'ID':<12} {'Time':<12} {'Position':<25} {'Theta':<8} {'Caption':<60} {'Audio':<15}")
        print(f"{'-'*140}")
        
        # Items
        for i, item in enumerate(memory_items, 1):
            try:
                if hasattr(item, 'id'):
                    item_id = item.id[-8:] if len(item.id) > 8 else item.id
                else:
                    item_id = f"#{i}"
                
                time_str = f"{item.time:.1f}s"
                if len(time_str) > 12:
                    time_str = time_str[:12]
                
                # Format position
                pos = item.position
                if isinstance(pos, list) and len(pos) >= 2:
                    pos_str = f"({pos[0]:.2f}, {pos[1]:.2f})"
                    if len(pos) >= 3:
                        pos_str = f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})"
                else:
                    pos_str = str(pos)
                
                if len(pos_str) > 25:
                    pos_str = pos_str[:22] + "..."
                
                # Format theta
                theta_str = f"{item.theta:.2f}"
                
                # Format caption
                caption = item.caption if item.caption else "No caption"
                if len(caption) > 60:
                    caption = caption[:57] + "..."
                
                # Format audio caption
                audio = "Yes" if (hasattr(item, 'audio_caption') and item.audio_caption and item.audio_caption.strip()) else "No"
                
                print(f"{item_id:<12} {time_str:<12} {pos_str:<25} {theta_str:<8} {caption:<60} {audio:<15}")
                
            except Exception as e:
                print(f"Error displaying item {i}: {e}")
        
        print(f"{'-'*140}")
        print(f"Total: {len(memory_items)} items")
    
    def display_json(self, memory_items):
        """Display items in JSON format"""
        print(f"\nMemory Items JSON ({len(memory_items)} items):")
        print("="*60)
        
        items_data = []
        for i, item in enumerate(memory_items):
            item_data = {
                'index': i + 1,
                'id': getattr(item, 'id', f'item_{i+1}'),
                'time': item.time,
                'position': item.position,
                'theta': item.theta,
                'caption': item.caption,
            }
            
            if hasattr(item, 'audio_caption') and item.audio_caption:
                item_data['audio_caption'] = item.audio_caption
            
            items_data.append(item_data)
        
        print(json.dumps(items_data, indent=2))
    
    def display_detailed(self, memory_items):
        """Display items in detailed format"""
        print(f"\nDetailed Memory Items ({len(memory_items)} items):")
        print("="*80)
        
        for i, item in enumerate(memory_items, 1):
            print(f"\n--- Item {i} ---")
            print(f"ID: {getattr(item, 'id', 'N/A')}")
            print(f"Time: {item.time:.3f}s")
            
            # Convert to readable timestamp if possible
            if item.time > 1000000000:  # Looks like a Unix timestamp
                try:
                    dt = datetime.fromtimestamp(item.time)
                    print(f"Timestamp: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    pass
            
            print(f"Position: {item.position}")
            print(f"Theta: {item.theta:.4f} rad ({item.theta * 180 / 3.14159:.1f}°)")
            print(f"Caption: {item.caption}")
            
            if hasattr(item, 'audio_caption') and item.audio_caption and item.audio_caption.strip():
                print(f"Audio Caption: {item.audio_caption}")
    
    def save_to_file(self, memory_items, filename):
        """Save items to file"""
        try:
            filepath = Path(filename)
            
            # Determine format from extension
            if filepath.suffix.lower() == '.json':
                # Save as JSON
                items_data = []
                for i, item in enumerate(memory_items):
                    item_data = {
                        'index': i + 1,
                        'id': getattr(item, 'id', f'item_{i+1}'),
                        'time': item.time,
                        'position': item.position,
                        'theta': item.theta,
                        'caption': item.caption,
                    }
                    
                    if hasattr(item, 'audio_caption') and item.audio_caption:
                        item_data['audio_caption'] = item.audio_caption
                    
                    items_data.append(item_data)
                
                with open(filepath, 'w') as f:
                    json.dump(items_data, f, indent=2)
            
            else:
                # Save as CSV/text
                with open(filepath, 'w') as f:
                    # Header
                    f.write("Index,ID,Time,Position_X,Position_Y,Position_Z,Theta,Caption,Audio_Caption\n")
                    
                    # Data
                    for i, item in enumerate(memory_items, 1):
                        pos = item.position
                        pos_x = pos[0] if len(pos) > 0 else 0
                        pos_y = pos[1] if len(pos) > 1 else 0
                        pos_z = pos[2] if len(pos) > 2 else 0
                        
                        audio_caption = getattr(item, 'audio_caption', '') or ''
                        
                        # Escape quotes in captions
                        caption = item.caption.replace('"', '""') if item.caption else ''
                        audio_caption = audio_caption.replace('"', '""')
                        
                        f.write(f'{i},"{getattr(item, "id", f"item_{i}")}",'
                               f'{item.time},{pos_x},{pos_y},{pos_z},{item.theta},'
                               f'"{caption}","{audio_caption}"\n')
            
            print(f"[Memory Inspector] ✓ Saved {len(memory_items)} items to {filepath}")
            
        except Exception as e:
            print(f"[Memory Inspector] Error saving to file: {e}")
    
    def search_items(self, query, limit=10):
        """Search for items using text query"""
        try:
            print(f"[Memory Inspector] Searching for: '{query}'")
            
            # Use the memory interface for text search
            results = self.memory.search(query, limit=limit)
            
            print(f"[Memory Inspector] ✓ Found {len(results)} matching items")
            
            if results:
                self.display_detailed(results)
            else:
                print("[Memory Inspector] No matching items found")
            
            return results
            
        except Exception as e:
            print(f"[Memory Inspector] Error searching: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='Milvus Memory Database Inspector')
    parser.add_argument('--collection', '-c', default='webots_simulation', 
                       help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', 
                       help='MilvusDB IP address')
    parser.add_argument('--db-port', '-p', type=int, default=19530,
                       help='MilvusDB port')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Limit number of items to display')
    parser.add_argument('--format', '-f', choices=['table', 'json', 'detailed'], 
                       default='table', help='Output format')
    parser.add_argument('--save', '-s', 
                       help='Save results to file')
    parser.add_argument('--search', '-q', 
                       help='Search for items with text query')
    parser.add_argument('--info', action='store_true',
                       help='Show collection information only')
    
    args = parser.parse_args()
    
    print("🔍 Milvus Memory Database Inspector")
    print("="*50)
    
    try:
        # Initialize inspector
        inspector = MilvusMemoryInspector(
            collection_name=args.collection,
            db_ip=args.db_ip,
            db_port=args.db_port
        )
        
        # Show collection info
        if args.info:
            info = inspector.get_collection_info()
            if info:
                print(f"\n📊 Collection Information:")
                print(f"  Name: {info['name']}")
                print(f"  Description: {info['description']}")
                print(f"  Row Count: {info['row_count']}")
                print(f"\n📋 Schema Fields:")
                for field in info['fields']:
                    print(f"  • {field['name']} ({field['type']})")
                    print(f"    Description: {field['description']}")
                    if field['is_primary']:
                        print(f"    ✓ PRIMARY KEY")
                    if 'max_length' in field:
                        print(f"    Max Length: {field['max_length']}")
                    if 'params' in field:
                        print(f"    Params: {field['params']}")
                    print()
            return
        
        # Search or list items
        if args.search:
            inspector.search_items(args.search, limit=args.limit or 10)
        else:
            inspector.list_all_items(
                limit=args.limit,
                output_format=args.format,
                save_to_file=args.save
            )
    
    except KeyboardInterrupt:
        print("\n[Memory Inspector] Interrupted by user")
    except Exception as e:
        print(f"[Memory Inspector] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()