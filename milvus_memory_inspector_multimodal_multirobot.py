#!/usr/bin/env python3
"""
Milvus Memory Database Inspector for Multi-Robot System
Lists and displays all memory items from both ground and aerial robots
"""

import sys
import argparse
import json
import csv
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# Add ReMEmbR to Python path
remembr_path = str(Path(__file__).parent.resolve())
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory_multimodal_multirobot import MilvusMemory
from remembr.memory.memory_multimodal_multirobot import MemoryItem
from pymilvus import connections, Collection, utility

class MilvusMultiRobotMemoryInspector:
    """Inspector for multi-robot Milvus memory collections"""
    
    def __init__(self, collection_name="webots_multirobot", db_ip="127.0.0.1", db_port=19530):
        self.collection_name = collection_name
        self.db_ip = db_ip
        self.db_port = db_port
        
        print(f"\n{'='*60}")
        print(f"🤖🚁 Multi-Robot Milvus Memory Inspector")
        print(f"{'='*60}")
        print(f"Collection: {collection_name}")
        print(f"Database: {db_ip}:{db_port}")
        print(f"{'='*60}\n")
        
        # Connect to Milvus
        try:
            connections.connect(host=db_ip, port=db_port)
            print("✓ Connected to Milvus")
            
            # Check if collection exists
            if utility.has_collection(collection_name):
                self.collection = Collection(collection_name)
                self.collection.load()
                print(f"✓ Loaded collection: {collection_name}")
            else:
                print(f"❌ Collection '{collection_name}' does not exist")
                self.collection = None
                
        except Exception as e:
            print(f"❌ Failed to connect to Milvus: {e}")
            self.collection = None
    
    def get_collection_info(self):
        """Get basic information about the collection"""
        if not self.collection:
            print("No collection loaded")
            return
        
        try:
            num_entities = self.collection.num_entities
            schema = self.collection.schema
            
            print(f"\n{'='*60}")
            print("Collection Information")
            print(f"{'='*60}")
            print(f"Name: {self.collection_name}")
            print(f"Total Entities: {num_entities}")
            print(f"\nSchema Fields:")
            for field in schema.fields:
                print(f"  - {field.name} ({field.dtype})")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"Error getting collection info: {e}")
    
    def list_all_items(self, limit=None, output_format='table', robot_filter=None):
        """List all memory items"""
        if not self.collection:
            print("No collection loaded")
            return []
        
        try:
            # Build expression for robot filtering. "time >= 0" matches every
            # row (since time is a positive unix timestamp); Milvus requires
            # a non-empty filter expression for .query().
            if robot_filter:
                expr = f'robot_id == "{robot_filter}"'
            else:
                expr = "time >= 0"

            # Query all items
            results = self.collection.query(
                expr=expr,
                output_fields=["caption", "audio_caption", "detection_results", "time", "position", "theta", "robot_id", "robot_data"],
                limit=limit if limit else 16384
            )
            
            if not results:
                print("No memory items found")
                return []
            
            print(f"Found {len(results)} memory items")
            if robot_filter:
                print(f"Filtered by robot: {robot_filter}")
            
            # Convert to MemoryItem objects
            memory_items = []
            for result in results:
                # Deserialize detection_results from JSON
                detection_results = {}
                if 'detection_results' in result and result['detection_results']:
                    try:
                        detection_results = json.loads(result['detection_results'])
                    except:
                        detection_results = {}
                
                # Deserialize robot_data from JSON
                robot_data = '{}'
                if 'robot_data' in result and result['robot_data']:
                    robot_data = result['robot_data']  # Keep as string for MemoryItem
                
                # `time` is now a DOUBLE scalar (raw unix seconds, fp64). Old
                # collections may still return a list [t_offset, 0.0] — add the
                # legacy offset back only in that case.
                raw_t = result.get('time', 0.0)
                if isinstance(raw_t, list):
                    raw_t = float(raw_t[0]) if raw_t else 0.0
                    if raw_t < 1_000_000_000:
                        raw_t += 1721761000
                else:
                    raw_t = float(raw_t)

                memory_item = MemoryItem(
                    caption=result.get('caption', ''),
                    time=raw_t,
                    position=result.get('position', [0.0, 0.0, 0.0]),
                    theta=result.get('theta', 0.0),
                    robot_id=result.get('robot_id', 'unknown'),
                    audio_caption=result.get('audio_caption', ''),
                    detection_results=detection_results,
                    robot_data=robot_data
                )
                memory_items.append(memory_item)
            
            # Sort by time
            memory_items.sort(key=lambda x: x.time)
            
            # Display based on format
            if output_format == 'table':
                self.display_table(memory_items)
            elif output_format == 'detailed':
                self.display_detailed(memory_items)
            elif output_format == 'json':
                self.display_json(memory_items)
            elif output_format == 'csv':
                self.display_csv(memory_items)
            
            return memory_items
            
        except Exception as e:
            print(f"Error listing items: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def display_table(self, memory_items):
        """Display items in table format with combined robot summary"""
        table_data = []
        for idx, item in enumerate(memory_items):
            time_str = datetime.fromtimestamp(item.time).strftime('%H:%M:%S')
            
            # Parse robot_data for combined view
            robot_data = item.get_robot_data()
            
            if robot_data and isinstance(robot_data, dict):
                # Combined multi-robot format
                robot_ids = item.robot_id  # Already comma-separated
                
                # Summarize captions from both robots
                captions = []
                for robot_id in ['ground', 'aerial']:
                    if robot_id in robot_data and 'caption' in robot_data[robot_id]:
                        caption_text = robot_data[robot_id]['caption']
                        # Truncate long captions
                        if len(caption_text) > 25:
                            caption_text = caption_text[:22] + "..."
                        captions.append(f"{robot_id[0].upper()}: {caption_text}")
                
                caption_preview = " | ".join(captions) if captions else item.caption[:40]
                
                # Count total detections from all robots
                total_detections = 0
                detection_details = []
                for robot_id in ['ground', 'aerial']:
                    if robot_id in robot_data and 'detection_results' in robot_data[robot_id]:
                        detections = robot_data[robot_id]['detection_results']
                        if detections and detections.get('classes'):
                            count = len(detections['classes'])
                            total_detections += count
                            detection_type = detections.get('detection_type', 'yolo')
                            detection_details.append(f"{robot_id[0].upper()}:{count}({detection_type})")
                
                if detection_details:
                    detect_str = " | ".join(detection_details)
                else:
                    detect_str = "0"
            else:
                # Fallback to single-robot format
                robot_ids = item.robot_id
                caption_preview = item.caption[:40] + "..." if len(item.caption) > 40 else item.caption
                
                if item.detection_results and item.detection_results.get('classes'):
                    detect_count = len(item.detection_results['classes'])
                    detect_type = item.detection_results.get('detection_type', 'yolo')
                    detect_str = f"{detect_count} ({detect_type})"
                else:
                    detect_str = "0"
            
            audio_preview = item.audio_caption[:30] + "..." if len(item.audio_caption) > 30 else item.audio_caption
            
            table_data.append([
                idx + 1,
                robot_ids,
                time_str,
                f"({item.position[0]:.1f}, {item.position[1]:.1f}, {item.position[2]:.1f})",
                caption_preview,
                audio_preview,
                detect_str
            ])
        
        headers = ["#", "Robot", "Time", "Position", "Visual Caption", "Audio Caption", "Detections"]
        print(f"\n{tabulate(table_data, headers=headers, tablefmt='grid')}\n")
    
    def display_detailed(self, memory_items):
        """Display items in detailed format with per-robot breakdown"""
        for idx, item in enumerate(memory_items):
            print(f"\n{'='*60}")
            print(f"Memory Item #{idx + 1}")
            print(f"{'='*60}")
            print(f"Robot IDs: {item.robot_id}")
            print(f"Time: {datetime.fromtimestamp(item.time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Primary Position: ({item.position[0]:.3f}, {item.position[1]:.3f}, {item.position[2]:.3f})")
            print(f"Primary Orientation (theta): {item.theta:.3f} rad")
            
            # Parse robot_data to show per-robot details
            robot_data = item.get_robot_data()
            
            if robot_data and isinstance(robot_data, dict):
                # Show data for each robot
                for robot_id in ['ground', 'aerial']:
                    if robot_id in robot_data:
                        robot_info = robot_data[robot_id]
                        print(f"\n{'-'*60}")
                        print(f"📍 {robot_id.upper()} ROBOT")
                        print(f"{'-'*60}")
                        
                        # Position and orientation
                        if 'position' in robot_info:
                            pos = robot_info['position']
                            print(f"Position: ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                        if 'theta' in robot_info:
                            print(f"Orientation (theta): {robot_info['theta']:.3f} rad")
                        
                        # Visual caption
                        if 'caption' in robot_info:
                            print(f"\nVisual Caption:")
                            print(f"  {robot_info['caption']}")
                        
                        # Detection results
                        if 'detection_results' in robot_info:
                            detections = robot_info['detection_results']
                            if detections and detections.get('classes'):
                                detection_type = detections.get('detection_type', 'unknown')
                                print(f"\nObject Detections ({len(detections['classes'])} objects, type: {detection_type}):")
                                
                                for i, (cls, cls_name, conf, bbox) in enumerate(zip(
                                    detections['classes'],
                                    detections['class_names'],
                                    detections['confidences'],
                                    detections['bounding_boxes']
                                )):
                                    if detection_type == 'yolo-obb':
                                        # OBB has 8 coordinates (4 points)
                                        print(f"  {i+1}. {cls_name} (ID: {cls}, Conf: {conf:.2f})")
                                        print(f"      Oriented Bbox: [{bbox[0]:.1f}, {bbox[1]:.1f}], [{bbox[2]:.1f}, {bbox[3]:.1f}], [{bbox[4]:.1f}, {bbox[5]:.1f}], [{bbox[6]:.1f}, {bbox[7]:.1f}]")
                                    else:
                                        # Regular YOLO has 4 coordinates [x1, y1, x2, y2]
                                        print(f"  {i+1}. {cls_name} (ID: {cls}, Conf: {conf:.2f})")
                                        print(f"      Bbox: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
                            else:
                                print(f"\nNo detections for {robot_id} robot")
            else:
                # Fallback to old format if robot_data not available
                print(f"\nVisual Caption:")
                print(f"  {item.caption}")
                
                if item.detection_results and item.detection_results.get('classes'):
                    print(f"\nObject Detections ({len(item.detection_results['classes'])} objects):")
                    for i, (cls, cls_name, conf, bbox) in enumerate(zip(
                        item.detection_results['classes'],
                        item.detection_results['class_names'],
                        item.detection_results['confidences'],
                        item.detection_results['bounding_boxes']
                    )):
                        print(f"  {i+1}. {cls_name} (ID: {cls}, Conf: {conf:.2f})")
                        print(f"      Bbox: {bbox}")
            
            # Show audio caption if available
            if item.audio_caption:
                print(f"\n🎵 Audio Caption (Shared):")
                print(f"  {item.audio_caption}")
        
        print(f"\n{'='*60}\n")
    
    def display_json(self, memory_items):
        """Display items in JSON format including robot_data"""
        items_dict = []
        for item in memory_items:
            item_dict = {
                'robot_id': item.robot_id,
                'caption': item.caption,
                'audio_caption': item.audio_caption,
                'time': item.time,
                'time_readable': datetime.fromtimestamp(item.time).strftime('%Y-%m-%d %H:%M:%S'),
                'position': item.position,
                'theta': item.theta,
                'detection_results': item.detection_results
            }
            
            # Include robot_data if available
            robot_data = item.get_robot_data()
            if robot_data:
                item_dict['robot_data'] = robot_data
            
            items_dict.append(item_dict)
        
        print(json.dumps(items_dict, indent=2))
    
    def display_csv(self, memory_items):
        """Display items in CSV format with per-robot breakdown"""
        # Check if items have combined robot data
        if memory_items and hasattr(memory_items[0], 'robot_data') and memory_items[0].robot_data:
            # Combined format header
            print("robot_id,time,ground_pos_x,ground_pos_y,ground_pos_z,ground_theta,ground_caption,ground_detections,"
                  "aerial_pos_x,aerial_pos_y,aerial_pos_z,aerial_theta,aerial_caption,aerial_detections,audio_caption")
            
            for item in memory_items:
                robot_data = item.get_robot_data()
                time_str = datetime.fromtimestamp(item.time).strftime('%Y-%m-%d %H:%M:%S')
                
                if robot_data and isinstance(robot_data, dict):
                    # Extract ground data
                    ground_data = robot_data.get('ground', {})
                    ground_pos = ground_data.get('position', [0, 0, 0])
                    ground_theta = ground_data.get('theta', 0)
                    ground_caption = ground_data.get('caption', '').replace('"', '""')
                    ground_detections = 0
                    if 'detection_results' in ground_data and ground_data['detection_results'].get('classes'):
                        ground_detections = len(ground_data['detection_results']['classes'])
                    
                    # Extract aerial data
                    aerial_data = robot_data.get('aerial', {})
                    aerial_pos = aerial_data.get('position', [0, 0, 0])
                    aerial_theta = aerial_data.get('theta', 0)
                    aerial_caption = aerial_data.get('caption', '').replace('"', '""')
                    aerial_detections = 0
                    if 'detection_results' in aerial_data and aerial_data['detection_results'].get('classes'):
                        aerial_detections = len(aerial_data['detection_results']['classes'])
                    
                    print(f"{item.robot_id},"
                          f"{time_str},"
                          f"{ground_pos[0]:.3f},{ground_pos[1]:.3f},{ground_pos[2]:.3f},{ground_theta:.3f},"
                          f'"{ground_caption}",{ground_detections},'
                          f"{aerial_pos[0]:.3f},{aerial_pos[1]:.3f},{aerial_pos[2]:.3f},{aerial_theta:.3f},"
                          f'"{aerial_caption}",{aerial_detections},'
                          f'"{item.audio_caption}"')
                else:
                    # Fallback for old format
                    print(f"{item.robot_id},"
                          f"{time_str},"
                          f"{item.position[0]:.3f},{item.position[1]:.3f},{item.position[2]:.3f},{item.theta:.3f},"
                          f'"{item.caption}",0,'
                          f"0,0,0,0,\"\",0,"
                          f'"{item.audio_caption}"')
        else:
            # Simple format for single-robot items
            print("robot_id,time,position_x,position_y,position_z,theta,caption,audio_caption,detection_count,detection_type")
            for item in memory_items:
                detection_count = 0
                detection_type = ""
                if item.detection_results:
                    detection_count = len(item.detection_results.get('classes', []))
                    detection_type = item.detection_results.get('detection_type', '')
                
                print(f"{item.robot_id},"
                      f"{datetime.fromtimestamp(item.time).strftime('%Y-%m-%d %H:%M:%S')},"
                      f"{item.position[0]:.3f},"
                      f"{item.position[1]:.3f},"
                      f"{item.position[2]:.3f},"
                      f"{item.theta:.3f},"
                      f'"{item.caption}",'
                      f'"{item.audio_caption}",'
                      f"{detection_count},"
                      f"{detection_type}")
    
    def reset_collection(self):
        """Reset the collection"""
        try:
            if utility.has_collection(self.collection_name):
                print(f"⚠️  Dropping collection: {self.collection_name}")
                utility.drop_collection(self.collection_name)
                print(f"✓ Collection dropped successfully")
            else:
                print(f"Collection '{self.collection_name}' does not exist")
        except Exception as e:
            print(f"Error resetting collection: {e}")

def main():
    parser = argparse.ArgumentParser(description='Multi-Robot Milvus Memory Inspector')
    parser.add_argument('-c', '--collection', type=str, default='webots_multirobot',
                       help='Collection name (default: webots_multirobot)')
    parser.add_argument('--db-ip', type=str, default='127.0.0.1',
                       help='Milvus database IP (default: 127.0.0.1)')
    parser.add_argument('--db-port', type=int, default=19530,
                       help='Milvus database port (default: 19530)')
    parser.add_argument('--recent', type=int,
                       help='Show only the N most recent items')
    parser.add_argument('--format', type=str, choices=['table', 'detailed', 'json', 'csv'],
                       default='table',
                       help='Output format (default: table)')
    parser.add_argument('--robot', type=str, choices=['ground', 'aerial'],
                       help='Filter by robot ID')
    parser.add_argument('--info', action='store_true',
                       help='Show collection information')
    parser.add_argument('--reset', action='store_true',
                       help='Reset (drop) the collection')
    
    args = parser.parse_args()
    
    inspector = MilvusMultiRobotMemoryInspector(
        collection_name=args.collection,
        db_ip=args.db_ip,
        db_port=args.db_port
    )
    
    if args.reset:
        confirm = input(f"Are you sure you want to reset collection '{args.collection}'? (yes/no): ")
        if confirm.lower() == 'yes':
            inspector.reset_collection()
        return
    
    if args.info:
        inspector.get_collection_info()
    
    # List items
    inspector.list_all_items(
        limit=args.recent,
        output_format=args.format,
        robot_filter=args.robot
    )

if __name__ == "__main__":
    main()
