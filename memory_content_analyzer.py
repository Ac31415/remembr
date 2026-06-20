#!/usr/bin/env python3
"""
Memory Content Analyzer
Analyzes stored multimodal memories and extracts semantic content
"""

import sys
import os
import json
import re
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
from collections import Counter, defaultdict

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from remembr.memory.milvus_memory_multimodal import MilvusMemory
from remembr.memory.memory_multimodal import MemoryItem

class MemoryContentAnalyzer:
    """Analyze and categorize stored multimodal memories"""
    
    def __init__(self, collection_name: str = "webots_sounds_multimodal", db_ip: str = "127.0.0.1"):
        self.memory = MilvusMemory(collection_name, db_ip=db_ip)
        self.collection_name = collection_name
        
        # Semantic categories for analysis
        self.visual_keywords = {
            'robot': ['robot', 'pioneer', 'vehicle', 'moving', 'navigation'],
            'building': ['building', 'structure', 'house', 'church', 'warehouse', 'tower'],
            'vehicle': ['car', 'bus', 'truck', 'vehicle', 'transportation'],
            'nature': ['tree', 'plant', 'green', 'grass', 'park', 'outdoor'],
            'infrastructure': ['road', 'street', 'light', 'traffic', 'sign', 'fence'],
            'people_objects': ['bench', 'chair', 'table', 'bin', 'trash', 'mailbox'],
            'playground': ['swing', 'slide', 'playground', 'recreation']
        }
        
        self.audio_keywords = {
            'urban_ambient': ['city', 'urban', 'traffic', 'street', 'ambient', 'background'],
            'church_sounds': ['bell', 'church', 'ring', 'chime'],
            'vehicle_sounds': ['car', 'horn', 'engine', 'truck', 'vehicle'],
            'human_sounds': ['voice', 'talking', 'people', 'conversation', 'scream', 'squeal', 'help'],
            'nature_sounds': ['wind', 'water', 'bird', 'natural'],
            'mechanical': ['machine', 'motor', 'mechanical', 'industrial'],
            'emergency': ['crash', 'alarm', 'siren', 'emergency', 'help', 'distress'],
            # NEW: Ambulance-specific category
            'ambulance_siren': ['ambulance', 'ambulance siren', 'medical emergency', 'emergency vehicle', 'medical siren']
        }
        
    def retrieve_all_memories(self, limit: int = None) -> List[MemoryItem]:
        """Retrieve all memories from the database"""
        print(f"📖 Retrieving memories from collection: {self.collection_name}")
        
        try:
            # Get all memories using the inspector's method
            from milvus_memory_inspector_multimodal import MilvusMemoryInspector
            inspector = MilvusMemoryInspector(self.collection_name)
            memories = inspector.list_all_items(limit=limit, output_format='none')
            
            print(f"✅ Retrieved {len(memories)} memories")
            return memories
            
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            return []
    
    def analyze_visual_content(self, caption: str) -> Dict[str, Any]:
        """Analyze visual caption content"""
        if not caption:
            return {'categories': [], 'keywords': [], 'confidence': 0.0}
        
        caption_lower = caption.lower()
        detected_categories = []
        detected_keywords = []
        
        for category, keywords in self.visual_keywords.items():
            category_matches = []
            for keyword in keywords:
                if keyword in caption_lower:
                    category_matches.append(keyword)
                    detected_keywords.append(keyword)
            
            if category_matches:
                detected_categories.append({
                    'category': category,
                    'matches': category_matches,
                    'confidence': len(category_matches) / len(keywords)
                })
        
        # Calculate overall confidence
        total_words = len(caption.split())
        confidence = len(detected_keywords) / max(total_words, 1)
        
        return {
            'categories': detected_categories,
            'keywords': detected_keywords,
            'confidence': min(confidence, 1.0),
            'text_length': len(caption),
            'word_count': total_words
        }
    
    def analyze_audio_content(self, audio_caption: str) -> Dict[str, Any]:
        """Analyze audio caption content"""
        if not audio_caption:
            return {'categories': [], 'keywords': [], 'confidence': 0.0}
        
        audio_lower = audio_caption.lower()
        detected_categories = []
        detected_keywords = []
        
        for category, keywords in self.audio_keywords.items():
            category_matches = []
            for keyword in keywords:
                if keyword in audio_lower:
                    category_matches.append(keyword)
                    detected_keywords.append(keyword)
            
            if category_matches:
                detected_categories.append({
                    'category': category,
                    'matches': category_matches,
                    'confidence': len(category_matches) / len(keywords)
                })
        
        # Calculate overall confidence
        total_words = len(audio_caption.split())
        confidence = len(detected_keywords) / max(total_words, 1)
        
        return {
            'categories': detected_categories,
            'keywords': detected_keywords,
            'confidence': min(confidence, 1.0),
            'text_length': len(audio_caption),
            'word_count': total_words
        }
    
    def cluster_memories_by_location(self, memories: List[MemoryItem], radius: float = 10.0) -> List[Dict]:
        """Cluster memories by spatial proximity"""
        clusters = []
        processed = set()
        
        for i, memory in enumerate(memories):
            if i in processed:
                continue
                
            # Start new cluster
            cluster = {
                'center': memory.position[:2],  # x, y
                'memories': [memory],
                'indices': [i]
            }
            processed.add(i)
            
            # Find nearby memories
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if j in processed:
                    continue
                
                # Calculate distance
                dx = memory.position[0] - other_memory.position[0]
                dy = memory.position[1] - other_memory.position[1]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    cluster['memories'].append(other_memory)
                    cluster['indices'].append(j)
                    processed.add(j)
            
            # Update cluster center (centroid)
            if len(cluster['memories']) > 1:
                x_coords = [m.position[0] for m in cluster['memories']]
                y_coords = [m.position[1] for m in cluster['memories']]
                cluster['center'] = [
                    sum(x_coords) / len(x_coords),
                    sum(y_coords) / len(y_coords)
                ]
            
            clusters.append(cluster)
        
        return clusters
    
    def analyze_temporal_distribution(self, memories: List[MemoryItem]) -> Dict[str, Any]:
        """Analyze temporal distribution of memories"""
        if not memories:
            return {}
        
        timestamps = [m.time for m in memories]
        timestamps.sort()
        
        # Calculate time intervals
        intervals = []
        for i in range(1, len(timestamps)):
            intervals.append(timestamps[i] - timestamps[i-1])
        
        analysis = {
            'total_memories': len(memories),
            'time_span': timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0,
            'average_interval': np.mean(intervals) if intervals else 0,
            'median_interval': np.median(intervals) if intervals else 0,
            'min_interval': min(intervals) if intervals else 0,
            'max_interval': max(intervals) if intervals else 0,
            'first_memory': timestamps[0],
            'last_memory': timestamps[-1]
        }
        
        return analysis
    
    def analyze_multimodal_alignment(self, memories: List[MemoryItem]) -> Dict[str, Any]:
        """Analyze alignment between visual and audio content"""
        alignment_stats = {
            'total_memories': len(memories),
            'visual_only': 0,
            'audio_only': 0,
            'multimodal': 0,
            'empty': 0,
            'visual_quality': [],
            'audio_quality': [],
            'semantic_alignment': []
        }
        
        # MODIFY: Add scenario-aware filtering if context is set
        evaluation_context = getattr(self, '_evaluation_context', None)
        
        if evaluation_context and evaluation_context.get('filter_type') == 'sound_isolation':
            enabled_types = evaluation_context.get('enabled_sound_types', [])
            memories = self.filter_memories_for_scenario(memories, enabled_types)
        
        for memory in memories:
            has_visual = bool(memory.caption and memory.caption.strip())
            has_audio = bool(hasattr(memory, 'audio_caption') and 
                           memory.audio_caption and memory.audio_caption.strip())
            
            if has_visual and has_audio:
                alignment_stats['multimodal'] += 1
                
                # Analyze semantic alignment
                visual_analysis = self.analyze_visual_content(memory.caption)
                audio_analysis = self.analyze_audio_content(memory.audio_caption)
                
                alignment_stats['visual_quality'].append(visual_analysis['confidence'])
                alignment_stats['audio_quality'].append(audio_analysis['confidence'])
                
                # Check for semantic overlap
                visual_categories = {cat['category'] for cat in visual_analysis['categories']}
                audio_categories = {cat['category'] for cat in audio_analysis['categories']}
                
                # Simple alignment check
                alignment_score = 0.0
                if visual_categories and audio_categories:
                    # Both have detected content
                    alignment_score = 0.5
                    
                    # Check for complementary content (audio about environment, visual about objects)
                    if ('urban_ambient' in audio_categories and 
                        any(cat in visual_categories for cat in ['building', 'infrastructure', 'vehicle'])):
                        alignment_score = 0.8
                    
                    # Check for direct matches
                    if 'vehicle' in visual_categories and 'vehicle_sounds' in audio_categories:
                        alignment_score = 0.9
                
                alignment_stats['semantic_alignment'].append(alignment_score)
                
            elif has_visual:
                alignment_stats['visual_only'] += 1
                visual_analysis = self.analyze_visual_content(memory.caption)
                alignment_stats['visual_quality'].append(visual_analysis['confidence'])
                
            elif has_audio:
                alignment_stats['audio_only'] += 1
                audio_analysis = self.analyze_audio_content(memory.audio_caption)
                alignment_stats['audio_quality'].append(audio_analysis['confidence'])
                
            else:
                alignment_stats['empty'] += 1
        
        # Calculate averages
        if alignment_stats['visual_quality']:
            alignment_stats['avg_visual_quality'] = np.mean(alignment_stats['visual_quality'])
        if alignment_stats['audio_quality']:
            alignment_stats['avg_audio_quality'] = np.mean(alignment_stats['audio_quality'])
        if alignment_stats['semantic_alignment']:
            alignment_stats['avg_semantic_alignment'] = np.mean(alignment_stats['semantic_alignment'])
        
        return alignment_stats
    
    def generate_content_analysis_report(self, memories: List[MemoryItem]) -> Dict[str, Any]:
        """Generate comprehensive content analysis report"""
        print("🔍 Analyzing memory content...")
        
        report = {
            'collection_info': {
                'name': self.collection_name,
                'total_memories': len(memories),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        # Temporal analysis
        print("  ⏱️ Analyzing temporal distribution...")
        report['temporal_analysis'] = self.analyze_temporal_distribution(memories)
        
        # Spatial clustering
        print("  🗺️ Clustering memories by location...")
        spatial_clusters = self.cluster_memories_by_location(memories)
        report['spatial_analysis'] = {
            'num_clusters': len(spatial_clusters),
            'cluster_sizes': [len(cluster['memories']) for cluster in spatial_clusters],
            'avg_cluster_size': np.mean([len(cluster['memories']) for cluster in spatial_clusters]) if spatial_clusters else 0,
            'clusters': spatial_clusters
        }
        
        # Content analysis
        print("  📝 Analyzing visual and audio content...")
        visual_categories = Counter()
        audio_categories = Counter()
        
        for memory in memories:
            if memory.caption:
                visual_analysis = self.analyze_visual_content(memory.caption)
                for cat_info in visual_analysis['categories']:
                    visual_categories[cat_info['category']] += 1
            
            if hasattr(memory, 'audio_caption') and memory.audio_caption:
                audio_analysis = self.analyze_audio_content(memory.audio_caption)
                for cat_info in audio_analysis['categories']:
                    audio_categories[cat_info['category']] += 1
        
        report['content_analysis'] = {
            'visual_categories': dict(visual_categories),
            'audio_categories': dict(audio_categories),
            'top_visual_categories': visual_categories.most_common(5),
            'top_audio_categories': audio_categories.most_common(5)
        }
        
        # Multimodal alignment analysis
        print("  🎭 Analyzing multimodal alignment...")
        report['multimodal_analysis'] = self.analyze_multimodal_alignment(memories)
        
        return report
    
    def save_analysis_report(self, report: Dict, output_path: str):
        """Save analysis report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Analysis report saved to: {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze memory content')
    parser.add_argument('--collection', '-c', default='webots_sounds_multimodal', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--output', '-o', default='memory_analysis.json', help='Output file path')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of memories to analyze')
    
    args = parser.parse_args()
    
    print("🔍 Memory Content Analyzer")
    print("="*40)
    
    analyzer = MemoryContentAnalyzer(args.collection, args.db_ip)
    memories = analyzer.retrieve_all_memories(args.limit)
    
    if memories:
        report = analyzer.generate_content_analysis_report(memories)
        analyzer.save_analysis_report(report, args.output)
        
        print(f"\n📊 Analysis Summary:")
        print(f"   Total memories: {len(memories)}")
        print(f"   Spatial clusters: {report['spatial_analysis']['num_clusters']}")
        print(f"   Multimodal memories: {report['multimodal_analysis']['multimodal']}")
        print(f"   Visual only: {report['multimodal_analysis']['visual_only']}")
        print(f"   Audio only: {report['multimodal_analysis']['audio_only']}")
    else:
        print("❌ No memories found to analyze")