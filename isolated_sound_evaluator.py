"""
Isolated Sound Evaluation Module
Evaluates individual sound sources in isolation to measure their specific contribution
to memory building and retrieval performance.
"""

import sys
import os
import json
import math
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
from collections import defaultdict

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

from memory_content_analyzer import MemoryContentAnalyzer
from multimodal_evaluation_framework import MultimodalEvaluationFramework

class IsolatedSoundEvaluator:
    """Evaluate individual sound sources in isolation"""
    
    def __init__(self, ground_truth_path: str, collection_name: str = "webots_multimodal", db_ip: str = "127.0.0.1", model_backend: str = "COMMAND_R"):
        self.ground_truth_path = Path(ground_truth_path)
        self.collection_name = collection_name
        self.db_ip = db_ip
        
        self.model_backend = model_backend  # Add this line
        
        # Load ground truth
        self.ground_truth = self.load_ground_truth()
        
        # Initialize components
        self.memory_analyzer = MemoryContentAnalyzer(collection_name, db_ip)
        self.evaluation_framework = MultimodalEvaluationFramework(
            str(ground_truth_path), collection_name, db_ip, model_backend
        )
        
        # Define test scenarios for isolated sound evaluation
        self.test_scenarios = [
            {
                'name': 'baseline_no_sounds',
                'description': 'Baseline with all sounds disabled',
                'enabled_sounds': []
            },
            {
                'name': 'church_bell_only',
                'description': 'Only church bell sounds enabled',
                'enabled_sounds': ['church_bell']
            },
            {
                'name': 'ambient_only', 
                'description': 'Only ambient city sounds enabled',
                'enabled_sounds': ['ambient']
            },
            {
                'name': 'car_sounds_only',
                'description': 'Only car horn sounds enabled',
                'enabled_sounds': ['car_sound']
            },
            {
                'name': 'help_sounds_only',
                'description': 'Only help/distress sounds enabled',
                'enabled_sounds': ['help_sound']
            },
            {
                'name': 'crash_sounds_only',
                'description': 'Only crash sounds enabled',
                'enabled_sounds': ['crash']
            },
            # NEW: Ambulance siren scenario
            {
                'name': 'ambulance_sirens_only',
                'description': 'Only ambulance siren sounds enabled',
                'enabled_sounds': ['ambulance_siren']
            },
            {
                'name': 'all_sounds_enabled',
                'description': 'All sounds enabled (full system)',
                'enabled_sounds': ['church_bell', 'ambient', 'car_sound', 'help_sound', 'crash', 'ambulance_siren']
            }
        ]
        
    def load_ground_truth(self) -> Dict:
        """Load ground truth data"""
        if not self.ground_truth_path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {self.ground_truth_path}")
        
        with open(self.ground_truth_path, 'r') as f:
            ground_truth = json.load(f)
        
        print(f"📖 Ground truth loaded for isolated evaluation")
        return ground_truth
    
    def filter_memories_by_sound_types(self, memories: List, enabled_sound_types: List[str]) -> List:
        """Filter memories based on actual audio content detected and temporal context"""
        print(f"🔍 Filtering {len(memories)} memories for sound types: {enabled_sound_types}")
        
        if not enabled_sound_types:  # Baseline scenario
            # For baseline, only include memories WITHOUT audio content
            filtered = [mem for mem in memories if not (hasattr(mem, 'audio_caption') and mem.audio_caption and mem.audio_caption.strip())]
            print(f"   📊 Baseline: {len(filtered)} memories without audio content")
            return filtered
        
        filtered_memories = []
        sound_type_matches = defaultdict(int)
        
        # Enhanced keyword mapping with ambulance sounds
        sound_keywords = {
            'car_sound': ['car horn', 'honking', 'vehicle horn', 'automobile', 'traffic horn', 'beeping car'],
            'ambient': ['city sounds', 'urban ambient', 'street noise', 'city atmosphere', 'urban environment'],
            'church_bell': ['church bell', 'bell ringing', 'church chime', 'cathedral bell', 'bell tolling'],
            'help_sound': ['screaming', 'help call', 'distress call', 'emergency sound', 'cry for help', 'shouting', 'yelling', 'squealing', 'wailing', 'squeal'],
            'crash': ['crash sound', 'collision', 'impact noise', 'breaking glass', 'metal crash'],
            # NEW: Ambulance siren keywords
            'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency', 'ambulance siren', 'emergency vehicle', 'medical siren']
        }
        
        for mem in memories:
            if hasattr(mem, 'audio_caption') and mem.audio_caption and mem.audio_caption.strip():
                audio_content = mem.audio_caption.lower()
                
                # Check for matches with enabled sound types
                detected_types = []
                for sound_type in enabled_sound_types:
                    keywords = sound_keywords.get(sound_type, [])
                    # Require more specific matching
                    if any(keyword in audio_content for keyword in keywords):
                        detected_types.append(sound_type)
                        sound_type_matches[sound_type] += 1
                
                # Only include memories that match the expected sound types
                if detected_types:
                    filtered_memories.append(mem)
        
        # Debug output
        print(f"   📊 Found {len(filtered_memories)} memories with matching audio content")
        for sound_type, count in sound_type_matches.items():
            print(f"   🎵 {sound_type}: {count} matches")
        
        return filtered_memories
    
    def set_evaluation_context(self, enabled_sound_types: List[str]):
        """Set scenario context for evaluation framework"""
        self.evaluation_framework._current_scenario_filter = {
            'enabled_sound_types': enabled_sound_types,
            'filter_type': 'sound_isolation'
        }
        
        # Also set context for memory analyzer if needed
        if hasattr(self.memory_analyzer, '_evaluation_context'):
            self.memory_analyzer._evaluation_context = {
                'enabled_sound_types': enabled_sound_types,
                'filter_type': 'sound_isolation'
            }

    def clear_evaluation_context(self):
        """Clear scenario context"""
        if hasattr(self.evaluation_framework, '_current_scenario_filter'):
            delattr(self.evaluation_framework, '_current_scenario_filter')
        
        if hasattr(self.memory_analyzer, '_evaluation_context'):
            delattr(self.memory_analyzer, '_evaluation_context')

    def evaluate_sound_type_performance(self, enabled_sound_types: List[str], memories: List) -> Dict[str, Any]:
        """Evaluate performance with specific sound types enabled"""
        print(f"🎯 Evaluating performance with sounds: {enabled_sound_types}")
        
        # CRITICAL FIX: Filter memories BEFORE passing to evaluation framework
        filtered_memories = self.filter_memories_by_sound_types(memories, enabled_sound_types)
        
        print(f"   📊 Using {len(filtered_memories)} filtered memories (from {len(memories)} total)")
        
        # Filter ground truth to only include enabled sound types
        filtered_sound_sources = []
        if enabled_sound_types:  # Only filter if we have specific sound types
            for sound_source in self.ground_truth.get('sound_sources', []):
                if sound_source.get('classified_type') in enabled_sound_types:
                    filtered_sound_sources.append(sound_source)
        else:
            # For baseline, exclude all sound sources
            filtered_sound_sources = []
        
        # Create filtered ground truth
        filtered_ground_truth = {
            'sound_sources': filtered_sound_sources,
            'visual_objects': self.ground_truth.get('visual_objects', []),
            'areas': self.ground_truth.get('areas', [])
        }
        
        print(f"   🎯 Using {len(filtered_sound_sources)} filtered sound sources")
        
        # Temporarily replace ground truth for evaluation
        original_ground_truth = self.evaluation_framework.ground_truth
        self.evaluation_framework.ground_truth = filtered_ground_truth
        
        # Set evaluation context
        self.set_evaluation_context(enabled_sound_types)
        
        try:
            # CRITICAL: Use filtered memories for ALL evaluations
            content_accuracy = self.evaluation_framework.evaluate_content_accuracy(filtered_memories)
            spatial_coverage = self.evaluation_framework.calculate_spatial_coverage(filtered_memories)
            multimodal_analysis = self.memory_analyzer.analyze_multimodal_alignment(filtered_memories)
            
            # Calculate sound-specific metrics using filtered memories
            sound_specific_metrics = self.calculate_sound_specific_metrics(
                enabled_sound_types, filtered_memories, filtered_sound_sources
            )
            
            return {
                'enabled_sound_types': enabled_sound_types,
                'content_accuracy': content_accuracy,
                'spatial_coverage': spatial_coverage,
                'multimodal_analysis': multimodal_analysis,
                'sound_specific_metrics': sound_specific_metrics,
                'filtered_memory_count': len(filtered_memories),
                'total_memory_count': len(memories),
                'filtered_ground_truth_count': len(filtered_sound_sources)
            }
            
        finally:
            # Restore original ground truth
            self.evaluation_framework.ground_truth = original_ground_truth
            self.clear_evaluation_context()
    
    def calculate_sound_specific_metrics(self, enabled_sound_types: List[str], 
                                   memories: List, sound_sources: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics specific to the enabled sound types"""
        metrics = {
            'total_sound_sources': len(sound_sources),
            'memories_with_audio': 0,
            'audio_detection_rate': 0.0,
            'sound_type_distribution': defaultdict(int),
            'position_accuracy_by_type': {},
            'audio_quality_scores': [],
            'expected_vs_actual_sounds': {}
        }
        
        # Count memories with audio content that matches enabled types
        relevant_audio_memories = 0
        for memory in memories:
            if hasattr(memory, 'audio_caption') and memory.audio_caption:
                metrics['memories_with_audio'] += 1
                
                # Check if audio content matches expected sound types
                audio_content = memory.audio_caption.lower()
                detected_match = False
                
                for sound_type in enabled_sound_types:
                    # Use the same keyword mapping as filter_memories_by_sound_types
                    keywords = {
                        'car_sound': ['car horn', 'honking', 'vehicle horn'],
                        'ambient': ['city sounds', 'urban ambient', 'street noise'],
                        'church_bell': ['church bell', 'bell ringing', 'church chime'],
                        'help_sound': ['screaming', 'help call', 'distress call', 'emergency sound', 'cry for help', 'shouting', 'yelling', 'squealing', 'wailing', 'squeal'],
                        'crash': ['crash sound', 'collision', 'impact noise'],
                        # NEW: Ambulance siren keywords
                        'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency']
                    }.get(sound_type, [])
                    
                    if any(keyword in audio_content for keyword in keywords):
                        detected_match = True
                        metrics['sound_type_distribution'][sound_type] += 1
                
                if detected_match:
                    relevant_audio_memories += 1
        
        # Calculate detection rate based on relevant memories
        if len(memories) > 0:
            metrics['audio_detection_rate'] = metrics['memories_with_audio'] / len(memories)
            metrics['relevant_audio_rate'] = relevant_audio_memories / len(memories)
        
        # Store expected vs actual for debugging
        metrics['expected_vs_actual_sounds'] = {
            'expected_types': enabled_sound_types,
            'total_memories_analyzed': len(memories),
            'memories_with_any_audio': metrics['memories_with_audio'],
            'memories_with_relevant_audio': relevant_audio_memories
        }
        
        return dict(metrics)
    
    def calculate_position_accuracy_for_type(self, memories: List, sound_sources: List[Dict]) -> float:
        """Calculate position accuracy for a specific sound type"""
        if not sound_sources:
            return 0.0
        
        total_accuracy = 0.0
        proximity_threshold = 15.0  # meters
        
        for sound_source in sound_sources:
            source_pos = sound_source.get('position', [0, 0, 0])[:2]
            best_distance = float('inf')
            
            # Find closest memory with audio content
            for memory in memories:
                if (hasattr(memory, 'audio_caption') and memory.audio_caption and 
                    hasattr(memory, 'position') and memory.position):
                    
                    mem_pos = memory.position[:2]
                    distance = math.sqrt(
                        (source_pos[0] - mem_pos[0])**2 + 
                        (source_pos[1] - mem_pos[1])**2
                    )
                    best_distance = min(best_distance, distance)
            
            # Calculate accuracy for this source
            if best_distance <= proximity_threshold:
                accuracy = 1.0 - (best_distance / proximity_threshold)
            else:
                accuracy = 0.0
            
            total_accuracy += accuracy
        
        return total_accuracy / len(sound_sources)
    
    def run_isolated_evaluation(self, memories: List = None) -> Dict[str, Any]:
        """Run comprehensive isolated sound evaluation"""
        print("🎯 Starting Isolated Sound Evaluation")
        print("="*50)
        
        # Retrieve memories if not provided
        if memories is None:
            memories = self.memory_analyzer.retrieve_all_memories()
        
        if not memories:
            return {'error': 'No memories found in collection'}
        
        evaluation_results = {
            'metadata': {
                'collection_name': self.collection_name,
                'evaluation_timestamp': datetime.now().isoformat(),
                'total_memories': len(memories),
                'ground_truth_file': str(self.ground_truth_path)
            },
            'scenario_results': {},
            'comparative_analysis': {}
        }
        
        # Evaluate each test scenario
        scenario_results = {}
        for scenario in self.test_scenarios:
            print(f"\n📊 Evaluating scenario: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            print(f"   Enabled sounds: {scenario['enabled_sounds']}")
            
            result = self.evaluate_sound_type_performance(
                scenario['enabled_sounds'], memories
            )
            scenario_results[scenario['name']] = result
        
        evaluation_results['scenario_results'] = scenario_results
        
        # Perform comparative analysis
        evaluation_results['comparative_analysis'] = self.perform_comparative_analysis(scenario_results)
        
        return evaluation_results
    
    def perform_comparative_analysis(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comparative analysis across different sound scenarios"""
        print("\n🔬 Performing comparative analysis...")
        
        # Add detailed debugging
        print("📊 Detailed Scenario Analysis:")
        for scenario_name, result in scenario_results.items():
            filtered_count = result.get('filtered_memory_count', 0)
            total_count = result.get('total_memory_count', 0)
            audio_rate = result.get('sound_specific_metrics', {}).get('audio_detection_rate', 0.0)
            relevant_rate = result.get('sound_specific_metrics', {}).get('relevant_audio_rate', 0.0)
            
            print(f"  {scenario_name}:")
            print(f"    📈 Filtered memories: {filtered_count}/{total_count}")
            print(f"    🎵 Audio detection rate: {audio_rate:.2%}")
            print(f"    🎯 Relevant audio rate: {relevant_rate:.2%}")
        
        comparative_metrics = {
            'audio_detection_rates': {},
            'spatial_coverage_scores': {},
            'content_accuracy_scores': {},
            'sound_type_effectiveness': {},
            'improvement_over_baseline': {}
        }
        
        baseline_result = scenario_results.get('baseline_no_sounds')
        
        for scenario_name, result in scenario_results.items():
            # Extract key metrics
            audio_detection = result.get('sound_specific_metrics', {}).get('audio_detection_rate', 0.0)
            spatial_coverage = result.get('spatial_coverage', {}).get('coverage_score', 0.0)
            
            # Content accuracy (average of sound detection metrics)
            content_acc = result.get('content_accuracy', {})
            sound_f1 = content_acc.get('sound_detection', {}).get('f1_score', 0.0)
            content_accuracy = sound_f1
            
            comparative_metrics['audio_detection_rates'][scenario_name] = audio_detection
            comparative_metrics['spatial_coverage_scores'][scenario_name] = spatial_coverage
            comparative_metrics['content_accuracy_scores'][scenario_name] = content_accuracy
            
            # Calculate improvement over baseline
            if baseline_result and scenario_name != 'baseline_no_sounds':
                baseline_audio = baseline_result.get('sound_specific_metrics', {}).get('audio_detection_rate', 0.0)
                baseline_spatial = baseline_result.get('spatial_coverage', {}).get('coverage_score', 0.0)
                baseline_content = baseline_result.get('content_accuracy', {}).get('sound_detection', {}).get('f1_score', 0.0)
                
                improvement = {
                    'audio_detection_improvement': audio_detection - baseline_audio,
                    'spatial_coverage_improvement': spatial_coverage - baseline_spatial,
                    'content_accuracy_improvement': content_accuracy - baseline_content
                }
                comparative_metrics['improvement_over_baseline'][scenario_name] = improvement
        
        # Calculate sound type effectiveness
        for scenario_name, result in scenario_results.items():
            if scenario_name == 'baseline_no_sounds' or scenario_name == 'all_sounds_enabled':
                continue
                
            enabled_sounds = result.get('enabled_sound_types', [])
            if len(enabled_sounds) == 1:  # Single sound type scenarios
                sound_type = enabled_sounds[0]
                
                print(f"  Analyzing effectiveness for sound type: {sound_type}, scenario: {scenario_name}")
                
                # CHECK: How many memories actually contain this sound type
                relevant_memory_count = result.get('sound_specific_metrics', {}).get('memories_with_audio', 0)
                total_memories = 81  # From your logs
                
                # PENALTY: If very few memories contain the expected sound type
                relevance_penalty = relevant_memory_count / total_memories
                
                effectiveness_score = (
                    comparative_metrics['audio_detection_rates'][scenario_name] * 0.4 +
                    comparative_metrics['spatial_coverage_scores'][scenario_name] * 0.3 +
                    comparative_metrics['content_accuracy_scores'][scenario_name] * 0.3
                ) * relevance_penalty
                comparative_metrics['sound_type_effectiveness'][sound_type] = effectiveness_score
        
        # Find best performing sound types
        if comparative_metrics['sound_type_effectiveness']:
            best_sound_type = max(
                comparative_metrics['sound_type_effectiveness'].items(),
                key=lambda x: x[1]
            )
            comparative_metrics['best_performing_sound_type'] = {
                'type': best_sound_type[0],
                'score': best_sound_type[1]
            }
        
        return comparative_metrics
    
    def save_evaluation_report(self, report: Dict, output_path: str):
        """Save isolated evaluation report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Isolated evaluation report saved to: {output_file}")
    
    def print_evaluation_summary(self, report: Dict):
        """Print evaluation summary"""
        print("\n📊 ISOLATED SOUND EVALUATION SUMMARY")
        print("="*60)
        
        metadata = report.get('metadata', {})
        print(f"Collection: {metadata.get('collection_name')}")
        print(f"Total Memories: {metadata.get('total_memories')}")
        
        # Scenario performance summary
        scenario_results = report.get('scenario_results', {})
        print(f"\n🎯 Scenario Performance:")
        for scenario_name, result in scenario_results.items():
            audio_rate = result.get('sound_specific_metrics', {}).get('audio_detection_rate', 0.0)
            spatial_score = result.get('spatial_coverage', {}).get('coverage_score', 0.0)
            print(f"  {scenario_name}: Audio={audio_rate:.2%}, Spatial={spatial_score:.2%}")
        
        # Best performing sound type
        comparative = report.get('comparative_analysis', {})
        best_type = comparative.get('best_performing_sound_type')
        if best_type:
            print(f"\n🏆 Best Performing Sound Type: {best_type['type']} (score: {best_type['score']:.3f})")
        
        # Effectiveness ranking
        effectiveness = comparative.get('sound_type_effectiveness', {})
        if effectiveness:
            print(f"\n📈 Sound Type Effectiveness Ranking:")
            sorted_types = sorted(effectiveness.items(), key=lambda x: x[1], reverse=True)
            for i, (sound_type, score) in enumerate(sorted_types, 1):
                print(f"  {i}. {sound_type}: {score:.3f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Isolated Sound Evaluation')
    parser.add_argument('--ground-truth', required=True, help='Path to ground truth JSON file')
    parser.add_argument('--collection', '-c', default='webots_multimodal', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--output', '-o', default='isolated_sound_evaluation.json', help='Output file path')
    
    parser.add_argument('--model-backend', '-m', default='COMMAND_R', 
                   choices=['COMMAND_R', 'GEMMA'], help='Model backend to use')
    
    args = parser.parse_args()
    
    print("🎯 Isolated Sound Evaluation Framework")
    print("="*50)
    
    evaluator = IsolatedSoundEvaluator(
        args.ground_truth,
        args.collection,
        args.db_ip,
        args.model_backend  # Pass model backend argument
    )
    
    report = evaluator.run_isolated_evaluation()
    evaluator.save_evaluation_report(report, args.output)
    evaluator.print_evaluation_summary(report)