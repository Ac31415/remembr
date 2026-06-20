#!/usr/bin/env python3
"""
Milvus Memory Database Inspector - Updated for webots_simulation schema
Lists and displays all memory items in a Milvus collection
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import time
import numpy as np

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory import MilvusMemory
from remembr.memory.memory import MemoryItem
from pymilvus import connections, Collection, utility

class WebotsMilvusMemoryInspector:
    """Inspector for Webots Milvus memory collections with proper schema handling"""
    
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
        """Get basic information about the collection with better counting"""
        try:
            # Get schema information
            schema = self.collection.schema
            
            # Try multiple strategies to get row count
            row_count = "Unknown"
            
            try:
                # Strategy 1: Try to count with small batches
                print("[Memory Inspector] Estimating collection size...")
                
                # Sample approach: get batches and estimate
                batch_size = 1000
                total_counted = 0
                max_batches_to_check = 16  # Check up to 16 batches (16k limit)
                
                for batch_num in range(max_batches_to_check):
                    try:
                        offset = batch_num * batch_size
                        if offset >= 16384:  # Milvus limit
                            break
                            
                        batch = self.collection.query(
                            expr="id != ''",
                            output_fields=["id"],
                            limit=batch_size,
                            offset=offset
                        )
                        
                        if not batch:
                            break
                        
                        total_counted += len(batch)
                        
                        if len(batch) < batch_size:
                            # This was the last batch
                            row_count = total_counted
                            break
                            
                    except Exception as e:
                        print(f"[Memory Inspector] Batch {batch_num} failed: {e}")
                        break
                
                if row_count == "Unknown" and total_counted > 0:
                    row_count = f"{total_counted}+ (estimated, collection is large)"
                    
            except Exception as e:
                print(f"[Memory Inspector] Could not estimate row count: {e}")
                row_count = "Large collection (16,000+ items)"
            
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
    
    def reset_collection(self, reset_option=None):
        """Reset the memory collection with user confirmation"""
        try:
            # Get current collection info for display
            info = self.get_collection_info()
            current_count = info['row_count'] if info else 0
            
            print(f"\n⚠️  RESET COLLECTION: {self.collection_name}")
            print(f"   Current items: {current_count}")
            print(f"   Database: {self.db_ip}:{self.db_port}")
            print(f"   This will permanently delete ALL memory data!")
            
            # Handle reset confirmation based on option
            if reset_option is True:
                # Explicit reset requested
                confirmed = True
                print("   Reset confirmed via command line argument")
            elif reset_option is False:
                # Explicit no-reset requested
                print("   Reset cancelled via command line argument")
                return False
            else:
                # Interactive confirmation
                while True:
                    try:
                        response = input("\n   Are you SURE you want to reset this collection? (yes/NO): ").strip()
                        if response.lower() in ['yes']:
                            confirmed = True
                            break
                        elif response.lower() in ['no', 'n', '']:
                            confirmed = False
                            break
                        else:
                            print("   Please type 'yes' to confirm or 'no' to cancel")
                    except (EOFError, KeyboardInterrupt):
                        print("\n   Reset cancelled by user")
                        confirmed = False
                        break
            
            if not confirmed:
                print("   Reset operation cancelled")
                return False
            
            # Perform the reset
            print("\n[Memory Inspector] Performing collection reset...")
            start_time = time.time()
            
            # Use the memory interface to reset
            self.memory.reset(drop_collection=True)
            
            end_time = time.time()
            
            print(f"[Memory Inspector] ✓ Collection '{self.collection_name}' reset successfully")
            print(f"[Memory Inspector] Reset completed in {end_time - start_time:.2f}s")
            print(f"[Memory Inspector] Collection is now empty and ready for new data")
            
            return True
            
        except Exception as e:
            print(f"[Memory Inspector] ❌ Error resetting collection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_all_items(self, limit=None, output_format='table', save_to_file=None, sort_by_time=True):
        """List all memory items in the collection with proper schema handling"""
        try:
            print(f"[Memory Inspector] Retrieving memory items...")
            
            # Milvus has a hard limit of 16384 for offset+limit
            MAX_MILVUS_LIMIT = 16384
            all_results = []
            batch_size = 1000  # Smaller batch size for safety
            
            # Determine which fields to retrieve based on schema
            # Only get scalar fields, not vector fields for display
            output_fields = ["id", "caption", "theta"]
            
            # Check if time and position fields exist and handle them carefully
            try:
                # Test query to see what fields are actually available
                test_result = self.collection.query(
                    expr="id != ''",
                    output_fields=["*"],
                    limit=1
                )
                if test_result:
                    available_fields = list(test_result[0].keys())
                    print(f"[Memory Inspector] Available fields: {available_fields}")
                    
                    # Filter to only scalar fields we can display
                    output_fields = []
                    for field in available_fields:
                        # Skip vector fields (they're too large to display)
                        if field not in ['text_embedding']:
                            output_fields.append(field)
                    
                    print(f"[Memory Inspector] Using output fields: {output_fields}")
                    
            except Exception as e:
                print(f"[Memory Inspector] Could not determine available fields: {e}")
                output_fields = ["*"]
            
            # Strategy 1: Try to get data in smaller, safer batches
            offset = 0
            consecutive_empty_batches = 0
            max_empty_batches = 3
            
            # Set reasonable default limit if none provided
            if not limit:
                limit = 1000  # Default to 1000 for large collections
                print(f"[Memory Inspector] No limit specified, using default: {limit}")
            
            while consecutive_empty_batches < max_empty_batches and len(all_results) < limit:
                try:
                    # Ensure we don't exceed Milvus limits
                    if offset >= MAX_MILVUS_LIMIT:
                        print(f"[Memory Inspector] Reached Milvus query limit at offset {offset}")
                        break
                    
                    # Calculate safe batch size
                    remaining_in_limit = MAX_MILVUS_LIMIT - offset
                    remaining_user_limit = limit - len(all_results)
                    current_batch_size = min(batch_size, remaining_in_limit, remaining_user_limit)
                    
                    if current_batch_size <= 0:
                        break
                    
                    print(f"[Memory Inspector] Fetching batch: offset={offset}, limit={current_batch_size}")
                    
                    # Query batch with safety limits
                    results = self.collection.query(
                        expr="id != ''",
                        output_fields=output_fields,
                        limit=current_batch_size,
                        offset=offset
                    )
                    
                    if not results:
                        consecutive_empty_batches += 1
                        print(f"[Memory Inspector] Empty batch {consecutive_empty_batches}/{max_empty_batches}")
                    else:
                        consecutive_empty_batches = 0
                        all_results.extend(results)
                        print(f"[Memory Inspector] Retrieved {len(all_results)} items so far...")
                    
                    offset += current_batch_size
                    
                except Exception as e:
                    print(f"[Memory Inspector] Error in batch query at offset {offset}: {e}")
                    break
            
            print(f"[Memory Inspector] ✓ Retrieved {len(all_results)} total items")
            
            if not all_results:
                print("[Memory Inspector] No items found in collection")
                return []
            
            # Convert to memory items with proper schema handling
            memory_items = []
            for result in all_results:
                try:
                    memory_item = self._convert_result_to_memory_item(result)
                    if memory_item:
                        memory_items.append(memory_item)
                        
                except Exception as e:
                    print(f"[Memory Inspector] Error converting item: {e}")
                    continue
            
            # Sort by time if requested and time field is available
            if sort_by_time and memory_items and hasattr(memory_items[0], 'time'):
                try:
                    memory_items.sort(key=lambda x: x.time if hasattr(x, 'time') else 0)
                except Exception as e:
                    print(f"[Memory Inspector] Could not sort by time: {e}")
            
            print(f"[Memory Inspector] Converted {len(memory_items)} items to MemoryItem objects")
            
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
    
    def _convert_result_to_memory_item(self, result):
        """Convert Milvus result to MemoryItem with proper schema handling"""
        try:
            # Extract ID
            item_id = result.get('id', '')
            
            # Extract caption
            caption = result.get('caption', '')
            if isinstance(caption, list):
                caption = caption[0] if caption else ''
            
            # Extract theta (rotation)
            theta = result.get('theta', 0.0)
            if isinstance(theta, list):
                theta = theta[0] if theta else 0.0
            
            # Extract time - this is a vector field with dim=2
            time_value = 0.0
            if 'time' in result:
                time_field = result['time']
                if isinstance(time_field, list) and len(time_field) >= 1:
                    # Take the first element of the time vector
                    time_value = float(time_field[0])
                elif isinstance(time_field, (int, float)):
                    time_value = float(time_field)
            
            # Extract position - this is a vector field with dim=3
            position = [0.0, 0.0, 0.0]
            if 'position' in result:
                pos_field = result['position']
                if isinstance(pos_field, list) and len(pos_field) >= 3:
                    position = [float(pos_field[0]), float(pos_field[1]), float(pos_field[2])]
                elif isinstance(pos_field, list) and len(pos_field) >= 2:
                    position = [float(pos_field[0]), float(pos_field[1]), 0.0]
            
            # Create MemoryItem
            memory_item = MemoryItem(
                caption=caption,
                time=time_value,
                position=position,
                theta=float(theta),
                # audio_caption=""  # Not in this schema
            )
            
            # Add ID for reference
            memory_item.id = item_id
            
            return memory_item
            
        except Exception as e:
            print(f"[Memory Inspector] Error in _convert_result_to_memory_item: {e}")
            print(f"[Memory Inspector] Raw result: {result}")
            return None
    
    def display_table(self, memory_items):
        """Display items in table format optimized for webots schema"""
        print(f"\n{'='*160}")
        print(f"Webots Memory Items Table ({len(memory_items)} items)")
        print(f"{'='*160}")
        
        # Header
        print(f"{'ID':<15} {'Time':<15} {'Position':<30} {'Theta':<10} {'Caption':<80}")
        print(f"{'-'*160}")
        
        # Items
        for i, item in enumerate(memory_items, 1):
            try:
                # Format ID
                if hasattr(item, 'id'):
                    item_id = item.id[-12:] if len(item.id) > 12 else item.id
                else:
                    item_id = f"#{i}"
                
                # Format time
                time_str = f"{item.time:.3f}s"
                if len(time_str) > 15:
                    time_str = time_str[:15]
                
                # Format position
                pos = item.position
                if isinstance(pos, list) and len(pos) >= 3:
                    pos_str = f"({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})"
                elif isinstance(pos, list) and len(pos) >= 2:
                    pos_str = f"({pos[0]:.3f}, {pos[1]:.3f}, 0.000)"
                else:
                    pos_str = str(pos)
                
                if len(pos_str) > 30:
                    pos_str = pos_str[:27] + "..."
                
                # Format theta
                theta_str = f"{item.theta:.4f}"
                
                # Format caption
                caption = item.caption if item.caption else "No caption"
                if len(caption) > 80:
                    caption = caption[:77] + "..."
                
                print(f"{item_id:<15} {time_str:<15} {pos_str:<30} {theta_str:<10} {caption:<80}")
                
            except Exception as e:
                print(f"Error displaying item {i}: {e}")
        
        print(f"{'-'*160}")
        print(f"Total: {len(memory_items)} items")
        
        # Show statistics
        if memory_items:
            times = [item.time for item in memory_items if hasattr(item, 'time')]
            if times:
                print(f"Time range: {min(times):.3f}s to {max(times):.3f}s")
                
            positions = [item.position for item in memory_items if hasattr(item, 'position') and item.position]
            if positions:
                print(f"Position range: X[{min(p[0] for p in positions):.3f}, {max(p[0] for p in positions):.3f}] "
                      f"Y[{min(p[1] for p in positions):.3f}, {max(p[1] for p in positions):.3f}]")
    
    def display_json(self, memory_items):
        """Display items in JSON format"""
        print(f"\nWebots Memory Items JSON ({len(memory_items)} items):")
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
            
            # Convert numpy arrays to lists for JSON serialization
            if isinstance(item_data['position'], np.ndarray):
                item_data['position'] = item_data['position'].tolist()
            
            items_data.append(item_data)
        
        print(json.dumps(items_data, indent=2))
    
    def display_detailed(self, memory_items):
        """Display items in detailed format"""
        print(f"\nDetailed Webots Memory Items ({len(memory_items)} items):")
        print("="*100)
        
        for i, item in enumerate(memory_items, 1):
            print(f"\n--- Item {i} ---")
            print(f"ID: {getattr(item, 'id', 'N/A')}")
            print(f"Time: {item.time:.6f}s")
            
            # Convert to readable timestamp if it looks like Unix time
            if item.time > 1000000000:
                try:
                    dt = datetime.fromtimestamp(item.time)
                    print(f"Readable Time: {dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                except:
                    pass
            
            # Position details
            if hasattr(item, 'position') and item.position:
                pos = item.position
                if isinstance(pos, list) and len(pos) >= 3:
                    print(f"Position: X={pos[0]:.6f}, Y={pos[1]:.6f}, Z={pos[2]:.6f}")
                    # Calculate distance from origin
                    distance = (pos[0]**2 + pos[1]**2 + pos[2]**2)**0.5
                    print(f"Distance from origin: {distance:.6f}")
                else:
                    print(f"Position: {pos}")
            
            # Rotation details
            print(f"Theta: {item.theta:.6f} rad ({item.theta * 180 / 3.14159:.2f}°)")
            
            # Caption
            print(f"Caption: {item.caption}")
            
            # Show first few words for long captions
            if len(item.caption) > 100:
                words = item.caption.split()
                if len(words) > 15:
                    print(f"Preview: {' '.join(words[:15])}...")
    
    def save_to_file(self, memory_items, filename):
        """Save items to file with proper schema handling"""
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
                        'time': float(item.time),
                        'position': item.position,
                        'theta': float(item.theta),
                        'caption': item.caption,
                    }
                    
                    # Convert numpy arrays to lists for JSON serialization
                    if isinstance(item_data['position'], np.ndarray):
                        item_data['position'] = item_data['position'].tolist()
                    
                    items_data.append(item_data)
                
                with open(filepath, 'w') as f:
                    json.dump(items_data, f, indent=2)
            
            else:
                # Save as CSV/text
                with open(filepath, 'w') as f:
                    # Header
                    f.write("Index,ID,Time,Position_X,Position_Y,Position_Z,Theta,Caption\n")
                    
                    # Data
                    for i, item in enumerate(memory_items, 1):
                        pos = item.position
                        pos_x = pos[0] if len(pos) > 0 else 0
                        pos_y = pos[1] if len(pos) > 1 else 0
                        pos_z = pos[2] if len(pos) > 2 else 0
                        
                        # Escape quotes in caption
                        caption = item.caption.replace('"', '""') if item.caption else ''
                        
                        f.write(f'{i},"{getattr(item, "id", f"item_{i}")}",'
                               f'{item.time},{pos_x},{pos_y},{pos_z},{item.theta},'
                               f'"{caption}"\n')
            
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
    parser = argparse.ArgumentParser(description='Webots Milvus Memory Database Inspector')
    parser.add_argument('--collection', '-c', default='webots_simulation', 
                       help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', 
                       help='MilvusDB IP address')
    parser.add_argument('--db-port', '-p', type=int, default=19530,
                       help='MilvusDB port')
    parser.add_argument('--limit', '-l', type=int, default=100,
                       help='Limit number of items to display (default: 100 for large collections)')
    parser.add_argument('--format', '-f', choices=['table', 'json', 'detailed'], 
                       default='table', help='Output format')
    parser.add_argument('--save', '-s', 
                       help='Save results to file')
    parser.add_argument('--search', '-q', 
                       help='Search for items with text query')
    parser.add_argument('--info', action='store_true',
                       help='Show collection information only')
    parser.add_argument('--reset', action='store_true',
                       help='Reset memory collection (clear all data)')
    parser.add_argument('--no-reset', action='store_true',
                       help='Skip reset confirmation (for scripts)')
    parser.add_argument('--recent', type=int, metavar='N',
                       help='Show only the N most recent items (fastest for large collections)')
    parser.add_argument('--no-sort', action='store_true',
                       help='Do not sort by time (faster for large collections)')
    
    args = parser.parse_args()
    
    # Validate reset arguments
    if args.reset and args.no_reset:
        print("❌ Error: Cannot specify both --reset and --no-reset")
        sys.exit(1)
    
    print("🤖 Webots Milvus Memory Database Inspector")
    print("="*55)
    
    try:
        # Initialize inspector
        inspector = WebotsMilvusMemoryInspector(
            collection_name=args.collection,
            db_ip=args.db_ip,
            db_port=args.db_port
        )
        
        # Handle reset operation first
        if args.reset:
            print(f"\n🔄 Reset Operation Requested")
            reset_option = True  # Explicit reset
            success = inspector.reset_collection(reset_option)
            if success:
                print("\n✅ Collection reset completed successfully")
                print("   The collection is now empty and ready for new data")
            else:
                print("\n❌ Collection reset failed or was cancelled")
                sys.exit(1)
            return
        
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
                
                # Show recommendations for large collections
                if isinstance(info['row_count'], str) and ("16,000+" in str(info['row_count']) or "Large" in str(info['row_count'])):
                    print(f"\n💡 Large Collection Tips:")
                    print(f"  • Use --limit N to view specific number of items (default: 100)")
                    print(f"  • Use --recent N to see most recent items")
                    print(f"  • Use --search 'query' to find specific items")
                    print(f"  • Use --save file.json to export data")
                    print(f"  • Use --no-sort for faster queries on large datasets")
            return
        
        # Handle recent items (optimized for large collections)
        if args.recent:
            print(f"\n📅 Showing {args.recent} most recent items")
            limit = args.recent
        else:
            limit = args.limit
        
        # Search or list items
        if args.search:
            inspector.search_items(args.search, limit=limit or 10)
        else:
            # Show warning for very large requests
            if limit > 5000:
                print(f"\n⚠️  Large Query Warning:")
                print(f"   Requesting {limit} items from a large collection")
                print(f"   This may take a while and use significant memory")
                response = input("   Continue? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("   Query cancelled")
                    return
            
            inspector.list_all_items(
                limit=limit,
                output_format=args.format,
                save_to_file=args.save,
                sort_by_time=not args.no_sort
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