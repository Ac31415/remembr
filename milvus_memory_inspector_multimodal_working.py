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

from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.memory.memory_multimodal import MemoryItem
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
                max_batches_to_check = 20  # Check up to 20 batches for estimation
                
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
    
    def list_all_items(self, limit=None, output_format='table', save_to_file=None):
        """List all memory items in the collection with improved large collection handling"""
        try:
            print(f"[Memory Inspector] Retrieving all memory items...")
            
            # Milvus has a hard limit of 16384 for offset+limit
            MAX_MILVUS_LIMIT = 16384
            all_results = []
            batch_size = 1000  # Smaller batch size for safety
            
            # First, try to get a count estimate
            try:
                # Get a small sample to check if collection has data
                sample = self.collection.query(
                    expr="id != ''",
                    output_fields=["id"],
                    limit=1
                )
                if not sample:
                    print("[Memory Inspector] Collection is empty")
                    return []
            except Exception as e:
                print(f"[Memory Inspector] Warning: Could not sample collection: {e}")
            
            # Strategy 1: Try to get data in smaller, safer batches
            offset = 0
            consecutive_empty_batches = 0
            max_empty_batches = 3
            
            while consecutive_empty_batches < max_empty_batches:
                try:
                    # Respect user limit
                    if limit and len(all_results) >= limit:
                        break
                    
                    # Ensure we don't exceed Milvus limits
                    if offset >= MAX_MILVUS_LIMIT:
                        print(f"[Memory Inspector] Reached Milvus query limit at offset {offset}")
                        break
                    
                    # Calculate safe batch size
                    remaining_in_limit = MAX_MILVUS_LIMIT - offset
                    current_batch_size = min(batch_size, remaining_in_limit)
                    
                    if limit:
                        remaining_user_limit = limit - len(all_results)
                        current_batch_size = min(current_batch_size, remaining_user_limit)
                    
                    if current_batch_size <= 0:
                        break
                    
                    print(f"[Memory Inspector] Fetching batch: offset={offset}, limit={current_batch_size}")
                    
                    # Query batch with safety limits
                    results = self.collection.query(
                        expr="id != ''",
                        output_fields=["*"],
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
                    
                    # If we have some results, continue with what we have
                    if all_results:
                        print(f"[Memory Inspector] Continuing with {len(all_results)} retrieved items")
                        break
                    
                    # Strategy 2: Try alternative approaches for very large collections
                    try:
                        print("[Memory Inspector] Trying alternative query strategy...")
                        
                        # Try getting results without offset/limit but with a more restrictive expression
                        if limit and limit <= 1000:
                            # For small limits, try a simple query
                            results = self.collection.query(
                                expr="id != ''",
                                output_fields=["*"],
                                limit=min(limit, 1000)
                            )
                            all_results = results
                            break
                        else:
                            # For larger requests, inform user about limitations
                            print(f"[Memory Inspector] Large collection detected (16,000+ items)")
                            print(f"[Memory Inspector] Milvus query limits prevent retrieving all items")
                            print(f"[Memory Inspector] Consider using --limit to specify a smaller number")
                            print(f"[Memory Inspector] Or use --search to find specific items")
                            
                            # Try to get at least some data (first 10,000 items)
                            safe_limit = min(10000, limit if limit else 10000)
                            print(f"[Memory Inspector] Attempting to retrieve first {safe_limit} items...")
                            
                            results = self.collection.query(
                                expr="id != ''",
                                output_fields=["*"],
                                limit=safe_limit
                            )
                            all_results = results
                            break
                            
                    except Exception as e2:
                        print(f"[Memory Inspector] Alternative query also failed: {e2}")
                        
                        # Last resort: try to get just a small sample
                        try:
                            print("[Memory Inspector] Attempting to retrieve small sample...")
                            results = self.collection.query(
                                expr="id != ''",
                                output_fields=["*"],
                                limit=100
                            )
                            all_results = results
                            print(f"[Memory Inspector] Retrieved sample of {len(all_results)} items")
                        except Exception as e3:
                            print(f"[Memory Inspector] All query strategies failed: {e3}")
                            return []
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
        
    def export_to_json(self, filename=None, limit=None, include_embeddings=False, pretty_print=True):
        """
        Export memory contents to a JSON file with enhanced options
        
        Args:
            filename (str): Output filename. If None, auto-generates with timestamp
            limit (int): Maximum number of items to export
            include_embeddings (bool): Whether to include embedding vectors in export
            pretty_print (bool): Whether to format JSON with indentation
        
        Returns:
            str: Path to the exported file
        """
        try:
            print(f"[Memory Inspector] Starting JSON export...")
            
            # Auto-generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"memory_export_{self.collection_name}_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'
            
            filepath = Path(filename)
            
            # Get memory items
            print(f"[Memory Inspector] Retrieving memory items...")
            memory_items = self.list_all_items(limit=limit, output_format='table', save_to_file=None)
            
            if not memory_items:
                print("[Memory Inspector] No items found to export")
                return None
            
            # Prepare export data structure
            export_data = {
                "metadata": {
                    "collection_name": self.collection_name,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_items": len(memory_items),
                    "database": f"{self.db_ip}:{self.db_port}",
                    "includes_embeddings": include_embeddings
                },
                "items": []
            }
            
            # Process each memory item
            for i, item in enumerate(memory_items):
                try:
                    # Basic item data
                    item_data = {
                        "index": i + 1,
                        "id": getattr(item, 'id', f'item_{i+1}'),
                        "timestamp": item.time,
                        "position": {
                            "x": item.position[0] if len(item.position) > 0 else 0.0,
                            "y": item.position[1] if len(item.position) > 1 else 0.0,
                            "z": item.position[2] if len(item.position) > 2 else 0.0,
                            "raw": item.position
                        },
                        "orientation": {
                            "theta_radians": item.theta,
                            "theta_degrees": item.theta * 180 / 3.14159
                        },
                        "content": {
                            "visual_caption": item.caption or "",
                            "audio_caption": getattr(item, 'audio_caption', '') or ""
                        }
                    }
                    
                    # Add human-readable timestamp if it looks like Unix time
                    if item.time > 1000000000:
                        try:
                            dt = datetime.fromtimestamp(item.time)
                            item_data["readable_timestamp"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                            item_data["date"] = dt.strftime('%Y-%m-%d')
                            item_data["time_of_day"] = dt.strftime('%H:%M:%S')
                        except:
                            pass
                    
                    # Add embedding data if requested (requires querying Milvus directly)
                    if include_embeddings:
                        try:
                            # Query the collection to get embedding data
                            result = self.collection.query(
                                expr=f'id == "{item_data["id"]}"',
                                output_fields=["text_embedding"],
                                limit=1
                            )
                            if result and len(result) > 0:
                                item_data["text_embedding"] = result[0].get('text_embedding', [])
                        except Exception as e:
                            print(f"[Memory Inspector] Warning: Could not retrieve embedding for item {i+1}: {e}")
                            item_data["text_embedding"] = []
                    
                    export_data["items"].append(item_data)
                    
                except Exception as e:
                    print(f"[Memory Inspector] Error processing item {i+1}: {e}")
                    continue
            
            # Write JSON file
            print(f"[Memory Inspector] Writing JSON to {filepath}...")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, f, ensure_ascii=False)
            
            # File size info
            file_size = filepath.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            print(f"[Memory Inspector] ✓ JSON export completed successfully!")
            print(f"[Memory Inspector]   File: {filepath}")
            print(f"[Memory Inspector]   Items exported: {len(export_data['items'])}")
            print(f"[Memory Inspector]   File size: {size_mb:.2f} MB")
            print(f"[Memory Inspector]   Includes embeddings: {include_embeddings}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"[Memory Inspector] ❌ Error exporting to JSON: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def import_from_json(self, filename, clear_existing=False):
        """
        Import memory contents from a JSON file
        
        Args:
            filename (str): JSON file to import from
            clear_existing (bool): Whether to clear existing collection before import
        
        Returns:
            bool: Success status
        """
        try:
            filepath = Path(filename)
            
            if not filepath.exists():
                print(f"[Memory Inspector] ❌ JSON file not found: {filepath}")
                return False
            
            print(f"[Memory Inspector] Importing from JSON: {filepath}")
            
            # Read JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate JSON structure
            if 'items' not in import_data:
                print("[Memory Inspector] ❌ Invalid JSON format: missing 'items' key")
                return False
            
            items = import_data['items']
            print(f"[Memory Inspector] Found {len(items)} items to import")
            
            # Show import info
            if 'metadata' in import_data:
                metadata = import_data['metadata']
                print(f"[Memory Inspector] Source collection: {metadata.get('collection_name', 'unknown')}")
                print(f"[Memory Inspector] Export timestamp: {metadata.get('export_timestamp', 'unknown')}")
            
            # Clear existing data if requested
            if clear_existing:
                print("[Memory Inspector] Clearing existing collection...")
                if not self.reset_collection(reset_option=True):
                    print("[Memory Inspector] ❌ Failed to clear existing collection")
                    return False
            
            # Import items
            success_count = 0
            error_count = 0
            
            for i, item_data in enumerate(items):
                try:
                    # Extract data from JSON structure
                    position = item_data.get('position', {})
                    if isinstance(position, dict):
                        pos_list = [
                            position.get('x', 0.0),
                            position.get('y', 0.0),
                            position.get('z', 0.0)
                        ]
                    else:
                        pos_list = position.get('raw', [0.0, 0.0, 0.0])
                    
                    orientation = item_data.get('orientation', {})
                    theta = orientation.get('theta_radians', 0.0)
                    
                    content = item_data.get('content', {})
                    visual_caption = content.get('visual_caption', '')
                    audio_caption = content.get('audio_caption', '')
                    
                    timestamp = item_data.get('timestamp', time.time())
                    
                    # Create MemoryItem
                    memory_item = MemoryItem(
                        caption=visual_caption,
                        time=timestamp,
                        position=pos_list,
                        theta=theta,
                        audio_caption=audio_caption
                    )
                    
                    # Insert into memory
                    self.memory.insert(memory_item)
                    success_count += 1
                    
                    if (success_count + error_count) % 100 == 0:
                        print(f"[Memory Inspector] Processed {success_count + error_count} items...")
                    
                except Exception as e:
                    print(f"[Memory Inspector] Error importing item {i+1}: {e}")
                    error_count += 1
                    continue
            
            print(f"[Memory Inspector] ✓ Import completed!")
            print(f"[Memory Inspector]   Successfully imported: {success_count} items")
            print(f"[Memory Inspector]   Errors: {error_count} items")
            print(f"[Memory Inspector]   Success rate: {success_count/(success_count+error_count)*100:.1f}%")
            
            return success_count > 0
            
        except Exception as e:
            print(f"[Memory Inspector] ❌ Error importing from JSON: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='Milvus Memory Database Inspector')
    parser.add_argument('--collection', '-c', default='webots_simulation', 
                       help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', 
                       help='MilvusDB IP address')
    parser.add_argument('--db-port', '-p', type=int, default=19530,
                       help='MilvusDB port')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Limit number of items to display (recommended for large collections)')
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
                       help='Show only the N most recent items (faster for large collections)')
    
    # Fixed JSON export/import arguments
    parser.add_argument('--export-json', nargs='?', const='', metavar='FILENAME',
                       help='Export all memory contents to JSON file (auto-generates filename if not specified)')
    parser.add_argument('--include-embeddings', action='store_true',
                       help='Include embedding vectors in JSON export (larger file size)')
    parser.add_argument('--compact-json', action='store_true',
                       help='Export JSON without pretty printing (smaller file size)')
    parser.add_argument('--import-json', metavar='FILENAME',
                       help='Import memory contents from JSON file')
    parser.add_argument('--clear-before-import', action='store_true',
                       help='Clear existing collection before importing JSON')
    
    args = parser.parse_args()
    
    # Validate reset arguments
    if args.reset and args.no_reset:
        print("❌ Error: Cannot specify both --reset and --no-reset")
        sys.exit(1)
    
    print("🔍 Milvus Memory Database Inspector")
    print("="*50)
    
    try:
        # Initialize inspector
        inspector = MilvusMemoryInspector(
            collection_name=args.collection,
            db_ip=args.db_ip,
            db_port=args.db_port
        )
        
        # Handle JSON import
        if args.import_json:
            print(f"\n📥 JSON Import Operation")
            success = inspector.import_from_json(
                args.import_json, 
                clear_existing=args.clear_before_import
            )
            if success:
                print("✅ JSON import completed successfully")
            else:
                print("❌ JSON import failed")
                sys.exit(1)
            return
        
        # Handle JSON export - FIXED
        if args.export_json is not None:
            print(f"\n📤 JSON Export Operation")
            
            # If --export-json is used without filename, args.export_json will be empty string
            filename = args.export_json if args.export_json else None
            
            exported_file = inspector.export_to_json(
                filename=filename,
                limit=args.limit,
                include_embeddings=args.include_embeddings,
                pretty_print=not args.compact_json
            )
            
            if exported_file:
                print(f"✅ JSON export completed: {exported_file}")
            else:
                print("❌ JSON export failed")
                sys.exit(1)
            return
        
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
                if isinstance(info['row_count'], str) and "16,000+" in str(info['row_count']):
                    print(f"\n💡 Large Collection Tips:")
                    print(f"  • Use --limit N to view specific number of items")
                    print(f"  • Use --recent N to see most recent items")
                    print(f"  • Use --search 'query' to find specific items")
                    print(f"  • Use --save file.json to export data")
                    print(f"  • Use --export-json to create comprehensive JSON backup")
            return
        
        # Handle recent items (optimized for large collections)
        if args.recent:
            print(f"\n📅 Showing {args.recent} most recent items")
            # For recent items, we want the highest timestamp values
            # This is more efficient than sorting all items
            limit = args.recent
        else:
            limit = args.limit
        
        # Search or list items
        if args.search:
            inspector.search_items(args.search, limit=limit or 10)
        else:
            # Show warning for large collections without limits
            if not limit and not args.recent:
                print(f"\n⚠️  Large Collection Warning:")
                print(f"   Your collection may have 16,000+ items")
                print(f"   Consider using --limit N or --recent N for better performance")
                print(f"   Use --export-json for complete data export")
                print(f"   Proceeding with default limits...\n")
                limit = 5000  # Set a reasonable default
            
            inspector.list_all_items(
                limit=limit,
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
    
    
# # Export all memory to JSON with auto-generated filename
# python milvus_memory_inspector_multimodal.py --export-json

# # Export specific collection with custom filename
# python milvus_memory_inspector_multimodal.py -c my_collection --export-json my_backup.json

# # Export with embeddings (larger file but complete backup)
# python milvus_memory_inspector_multimodal.py --export-json --include-embeddings

# # Export compact JSON (no pretty printing)
# python milvus_memory_inspector_multimodal.py --export-json --compact-json

# # Import from JSON file
# python milvus_memory_inspector_multimodal.py --import-json my_backup.json

# # Import and clear existing data first
# python milvus_memory_inspector_multimodal.py --import-json my_backup.json --clear-before-import




# # Auto-generate filename
# python milvus_memory_inspector_multimodal.py --export-json

# # Specify custom filename  
# python milvus_memory_inspector_multimodal.py --export-json my_backup.json

# # With other options
# python milvus_memory_inspector_multimodal.py --export-json --include-embeddings --compact-json