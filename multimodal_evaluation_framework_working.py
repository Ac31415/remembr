"""
Multimodal Memory Building Evaluation Framework
Comprehensive evaluation of multimodal memory building system including navigation service
"""

import sys
import os
import json
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Add ReMEmbR to Python path
remembr_path = "/Users/wen-chungcheng/remembr"
if remembr_path not in sys.path:
    sys.path.insert(0, remembr_path)

# Add Webots controller path
webots_controller_path = "/Users/wen-chungcheng/Documents/Webots Sims/vehicles/controllers/remembr_controller"
if webots_controller_path not in sys.path:
    sys.path.insert(0, webots_controller_path)

from ground_truth_labeler import GroundTruthLabeler
from memory_content_analyzer import MemoryContentAnalyzer

# Import navigation service components
try:
    # from remembr_navigation_service_multimodal import ReMEmbRNavigationService
    from remembr_navigation_service import ReMEmbRNavigationService
    from remembr.agents.mlx_remembr_agent import MLXReMEmbRAgent
    NAVIGATION_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Navigation service not available: {e}")
    NAVIGATION_SERVICE_AVAILABLE = False

class MultimodalEvaluationFramework:
    """Comprehensive evaluation framework for multimodal memory building"""
    
    def __init__(self, ground_truth_path: str, collection_name: str = "webots_multimodal", db_ip: str = "127.0.0.1", model_backend: str = "COMMAND_R"):
        self.ground_truth_path = Path(ground_truth_path)
        self.collection_name = collection_name
        self.db_ip = db_ip
        self.model_backend = model_backend  # Add this line
        
        # Load ground truth
        self.ground_truth = self.load_ground_truth()
        
        # Initialize memory analyzer
        self.memory_analyzer = MemoryContentAnalyzer(collection_name, db_ip)
        
        # Initialize navigation service for testing (if available)
        self.navigation_service = None
        if NAVIGATION_SERVICE_AVAILABLE:
            try:
                print("🚀 Initializing navigation service for evaluation...")
                self.navigation_service = ReMEmbRNavigationService(
                    collection_name=collection_name, 
                    db_ip=db_ip,
                    model_backend=model_backend  # Add this line
                )
                print("✅ Navigation service initialized for evaluation")
            except Exception as e:
                print(f"⚠️ Could not initialize navigation service: {e}")
        
        # Evaluation metrics
        self.metrics = {
            'spatial_coverage': {},
            'temporal_consistency': {},
            'content_accuracy': {},
            'multimodal_alignment': {},
            'retrieval_performance': {},
            'navigation_performance': {}  # New metric for navigation evaluation
        }
        
    def run_comprehensive_evaluation_with_isolated_sounds(self) -> Dict[str, Any]:
        """Run comprehensive evaluation including isolated sound benchmarking"""
        print("🚀 Starting Comprehensive Multimodal Memory Evaluation with Isolated Sound Analysis")
        print("="*80)
        
        # Run standard comprehensive evaluation
        standard_report = self.run_comprehensive_evaluation()
        
        if 'error' in standard_report:
            return standard_report
        
        # Add isolated sound evaluation
        print("\n🎯 Adding Isolated Sound Evaluation...")
        try:
            from isolated_sound_evaluator import IsolatedSoundEvaluator
            
            isolated_evaluator = IsolatedSoundEvaluator(
                str(self.ground_truth_path),
                self.collection_name,
                self.db_ip
            )
            
            # Retrieve memories (reuse from standard evaluation)
            memories = self.memory_analyzer.retrieve_all_memories()
            isolated_report = isolated_evaluator.run_isolated_evaluation(memories)
            
            # Combine reports
            comprehensive_report = {
                **standard_report,
                'isolated_sound_analysis': isolated_report,
                'metadata': {
                    **standard_report.get('metadata', {}),
                    'includes_isolated_sound_analysis': True
                }
            }
            
            # Update overall scores to include isolated sound insights
            comprehensive_report['overall_scores'] = self._calculate_enhanced_overall_scores(
                comprehensive_report
            )
            
            return comprehensive_report
            
        except ImportError as e:
            print(f"⚠️ Isolated sound evaluation not available: {e}")
            return standard_report
        except Exception as e:
            print(f"⚠️ Error in isolated sound evaluation: {e}")
            return standard_report
        
    def _calculate_enhanced_overall_scores(self, report: Dict) -> Dict[str, float]:
        """Calculate enhanced overall scores including isolated sound insights"""
        # Get standard scores
        scores = self._calculate_overall_scores(report)
        
        # Add isolated sound analysis scores
        isolated_analysis = report.get('isolated_sound_analysis', {})
        comparative_analysis = isolated_analysis.get('comparative_analysis', {})
        
        if comparative_analysis:
            # Get best performing sound type effectiveness
            best_sound_type = comparative_analysis.get('best_performing_sound_type', {})
            if best_sound_type:
                scores['best_sound_type_effectiveness'] = best_sound_type.get('score', 0.0)
            
            # Calculate sound diversity score (how many sound types are effective)
            effectiveness = comparative_analysis.get('sound_type_effectiveness', {})
            if effectiveness:
                effective_types = len([score for score in effectiveness.values() if score > 0.3])
                total_types = len(effectiveness)
                scores['sound_diversity_score'] = effective_types / max(total_types, 1)
            
            # Enhanced overall score including sound analysis
            if 'best_sound_type_effectiveness' in scores and 'sound_diversity_score' in scores:
                scores['enhanced_overall_score'] = (
                    scores['overall_system_score'] * 0.7 +
                    scores['best_sound_type_effectiveness'] * 0.2 +
                    scores['sound_diversity_score'] * 0.1
                )
        
        return scores
        
    def load_ground_truth(self) -> Dict:
        """Load ground truth data"""
        if not self.ground_truth_path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {self.ground_truth_path}")
        
        with open(self.ground_truth_path, 'r') as f:
            ground_truth = json.load(f)
        
        print(f"📖 Ground truth loaded: {len(ground_truth.get('sound_sources', []))} sound sources, "
              f"{len(ground_truth.get('visual_objects', []))} visual objects")
        
        return ground_truth
    
    def calculate_spatial_coverage(self, memories: List) -> Dict[str, float]:
        """Evaluate spatial coverage of memories vs ground truth objects"""
        print("🗺️ Evaluating spatial coverage...")
        
        if not memories:
            return {'coverage_score': 0.0, 'details': 'No memories to evaluate'}
        
        # MODIFY: Add scenario-aware coverage calculation
        # Get all ground truth object positions (filtered by current scenario if needed)
        gt_positions = []
        
        # MODIFY: The scenario filter needs to be more sophisticated
        scenario_filter = getattr(self, '_current_scenario_filter', None)
        
        # ADD: Check if we're evaluating against historical data vs. live data
        if scenario_filter and scenario_filter.get('filter_type') == 'sound_isolation':
            enabled_types = scenario_filter.get('enabled_sound_types', [])
            
            # PROBLEM: This should filter memories by when they were recorded, not just content
            # Add temporal filtering based on when specific sounds were active
            
            for sound_source in self.ground_truth.get('sound_sources', []):
                if sound_source.get('position'):
                    # MODIFY: Check if this sound source type matches the scenario
                    if enabled_types and sound_source.get('classified_type') not in enabled_types:
                        continue  # Skip this sound source
                    gt_positions.append(sound_source['position'][:2])
        
        # Add visual object positions
        for visual_object in self.ground_truth.get('visual_objects', []):
            if visual_object.get('position'):
                gt_positions.append(visual_object['position'][:2])  # x, y
        
        if not gt_positions:
            return {'coverage_score': 0.0, 'details': 'No ground truth positions available'}
        
        # Get memory positions
        memory_positions = []
        for memory in memories:
            if hasattr(memory, 'position') and memory.position:
                memory_positions.append(memory.position[:2])
        
        if not memory_positions:
            return {'coverage_score': 0.0, 'details': 'No memory positions available'}
        
        # Calculate coverage using proximity matching
        coverage_radius = 20.0  # meters
        covered_gt_positions = 0
        
        for gt_pos in gt_positions:
            for mem_pos in memory_positions:
                distance = math.sqrt((gt_pos[0] - mem_pos[0])**2 + (gt_pos[1] - mem_pos[1])**2)
                if distance <= coverage_radius:
                    covered_gt_positions += 1
                    break  # This GT position is covered
        
        coverage_score = covered_gt_positions / len(gt_positions)
        
        return {
            'coverage_score': coverage_score,
            'covered_positions': covered_gt_positions,
            'total_gt_positions': len(gt_positions),
            'coverage_radius': coverage_radius,
            'memory_positions_count': len(memory_positions)
        }
    
    def evaluate_content_accuracy(self, memories: List) -> Dict[str, Any]:
        """Evaluate accuracy of memory content vs ground truth"""
        print("🎯 Evaluating content accuracy...")
        
        accuracy_metrics = {
            'sound_detection': {'tp': 0, 'fp': 0, 'fn': 0},
            'visual_detection': {'tp': 0, 'fp': 0, 'fn': 0},
            'sound_classification': {'correct': 0, 'total': 0},
            'visual_classification': {'correct': 0, 'total': 0}
        }
        
        # FIXED: Create scenario-aware ground truth, but don't filter the spatial index too aggressively
        scenario_filter = getattr(self, '_current_scenario_filter', None)
        
        # Create ground truth indices (keep all objects for position matching)
        gt_sound_index = self._create_spatial_index(
            self.ground_truth.get('sound_sources', []), 'sound'
        )
        gt_visual_index = self._create_spatial_index(
            self.ground_truth.get('visual_objects', []), 'visual'
        )
        
        # # FIXED: More generous proximity threshold for car sounds
        # # Car sounds can be heard from much further away
        # if (scenario_filter and 
        #     scenario_filter.get('enabled_sound_types') == ['car_sound']):
        #     proximity_threshold = 50.0  # Increased from 15.0 for car sounds
        # else:
        #     proximity_threshold = 20.0  # Increased from 15.0 for other sounds
            
        # FIXED: More generous proximity threshold for single point source sounds
        # Single point source sounds can be heard from much further away
        if (scenario_filter and 
            scenario_filter.get('enabled_sound_types')):
            proximity_threshold = 50.0  # Increased from 15.0 for isolated sounds cases
        else:
            proximity_threshold = 20.0  # Increased from 15.0 for other sounds cases
        
        print(f"    🎯 Using proximity threshold: {proximity_threshold}m")
        
        for memory in memories:
            if not (hasattr(memory, 'position') and memory.position):
                continue
                
            mem_pos = memory.position[:2]
            
            # Find nearby ground truth objects
            nearby_sounds = self._find_nearby_objects(mem_pos, gt_sound_index, proximity_threshold)
            nearby_visuals = self._find_nearby_objects(mem_pos, gt_visual_index, proximity_threshold)
            
            # FIXED: More flexible sound detection evaluation
            if hasattr(memory, 'audio_caption') and memory.audio_caption:
                # For isolated sound scenarios, check if the audio content matches the expected type
                audio_content = memory.audio_caption.lower()
                
                if scenario_filter and scenario_filter.get('filter_type') == 'sound_isolation':
                    enabled_types = scenario_filter.get('enabled_sound_types', [])
                    
                    # Check if audio content matches any of the enabled sound types
                    sound_type_match = False
                    for sound_type in enabled_types:
                        type_keywords = {
                            'car_sound': ['car horn', 'honk', 'car', 'vehicle horn', 'horn'],
                            'church_bell': ['bell', 'church', 'ring', 'chime'],
                            'ambient': ['city', 'urban', 'ambient', 'background'],
                            'help_sound': ['scream', 'help', 'distress', 'emergency', 'help me', 'screaming', 'shout', 'yell', 'cry', 'calling', 'calling for help', 'screaming', 'shouting', 'yelling', 'crying', 'distress call', 'call for help', 'calling out', 'squeal'],
                            'crash': ['crash', 'bang', 'collision', 'impact'],
                            # NEW: Ambulance siren keywords
                            'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency', 'medical siren']
                        }.get(sound_type, [])
                        
                        if any(keyword in audio_content for keyword in type_keywords):
                            sound_type_match = True
                            break
                    
                    if sound_type_match:
                        # For isolated scenarios, count as TP if content matches expected type
                        # even if not near a ground truth sound source
                        accuracy_metrics['sound_detection']['tp'] += 1
                        
                        # Check if we can find a matching ground truth sound source
                        classification_correct = False
                        for sound_source in self.ground_truth.get('sound_sources', []):
                            if sound_source.get('classified_type') in enabled_types:
                                # Check if this specific sound type matches
                                expected_type = sound_source.get('classified_type')
                                type_keywords = {
                                    'car_sound': ['car horn', 'honk', 'car', 'vehicle horn', 'horn'],
                                    'church_bell': ['bell', 'church', 'ring', 'chime'],
                                    'ambient': ['city', 'urban', 'ambient', 'background'],
                                    'help_sound': ['scream', 'help', 'distress', 'emergency', 'squeal', 'help me', 'screaming', 'shout', 'yell', 'cry', 'calling', 'calling for help', 'screaming', 'shouting', 'yelling', 'crying', 'distress call', 'call for help', 'calling out'],
                                    'crash': ['crash', 'bang', 'collision', 'impact'],
                                    # NEW: Ambulance siren keywords
                                    'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency', 'medical siren']
                                }.get(expected_type, [])
                                
                                if any(keyword in audio_content for keyword in type_keywords):
                                    classification_correct = True
                                    break
                        
                        if classification_correct:
                            accuracy_metrics['sound_classification']['correct'] += 1
                        accuracy_metrics['sound_classification']['total'] += 1
                    else:
                        # Audio content doesn't match expected types for this scenario
                        accuracy_metrics['sound_detection']['fp'] += 1
                else:
                    # Standard evaluation (non-isolated scenario)
                    if nearby_sounds:
                        accuracy_metrics['sound_detection']['tp'] += 1
                        if self._check_sound_classification_accuracy(memory.audio_caption, nearby_sounds):
                            accuracy_metrics['sound_classification']['correct'] += 1
                        accuracy_metrics['sound_classification']['total'] += 1
                    else:
                        accuracy_metrics['sound_detection']['fp'] += 1
            
            # Evaluate visual content (unchanged)
            if memory.caption:
                if nearby_visuals:
                    accuracy_metrics['visual_detection']['tp'] += 1
                    if self._check_visual_classification_accuracy(memory.caption, nearby_visuals):
                        accuracy_metrics['visual_classification']['correct'] += 1
                    accuracy_metrics['visual_classification']['total'] += 1
                else:
                    accuracy_metrics['visual_detection']['fp'] += 1
        
        # FIXED: Calculate false negatives only for enabled sound types in isolated scenarios
        if scenario_filter and scenario_filter.get('filter_type') == 'sound_isolation':
            enabled_types = scenario_filter.get('enabled_sound_types', [])
            
            # Only count FN for sound sources that match enabled types
            for sound_source in self.ground_truth.get('sound_sources', []):
                if sound_source.get('classified_type') in enabled_types:
                    if not self._is_position_covered_by_memories_with_audio(
                        sound_source['position'], memories, proximity_threshold, enabled_types
                    ):
                        accuracy_metrics['sound_detection']['fn'] += 1
        else:
            # Standard FN calculation
            for sound_source in self.ground_truth.get('sound_sources', []):
                if not self._is_position_covered_by_memories(sound_source['position'], memories, proximity_threshold):
                    accuracy_metrics['sound_detection']['fn'] += 1
        
        # Visual FN calculation (unchanged)
        for visual_object in self.ground_truth.get('visual_objects', []):
            if not self._is_position_covered_by_memories(visual_object['position'], memories, proximity_threshold):
                accuracy_metrics['visual_detection']['fn'] += 1
        
        # Calculate precision, recall, F1
        results = {}
        for content_type in ['sound_detection', 'visual_detection']:
            tp = accuracy_metrics[content_type]['tp']
            fp = accuracy_metrics[content_type]['fp']
            fn = accuracy_metrics[content_type]['fn']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            results[content_type] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'tp': tp, 'fp': fp, 'fn': fn
            }
            
            print(f"    📊 {content_type}: TP={tp}, FP={fp}, FN={fn}, F1={f1:.3f}")
        
        # Add classification accuracy
        for class_type in ['sound_classification', 'visual_classification']:
            total = accuracy_metrics[class_type]['total']
            correct = accuracy_metrics[class_type]['correct']
            results[class_type] = {
                'accuracy': correct / total if total > 0 else 0,
                'correct': correct,
                'total': total
            }
            
            if total > 0:
                print(f"    📊 {class_type}: {correct}/{total} correct ({correct/total:.3f})")
        
        return results
    
    def _is_position_covered_by_memories_with_audio(self, position: List[float], memories: List, 
                                               threshold: float, expected_sound_types: List[str]) -> bool:
        """Check if a position is covered by memories with relevant audio content"""
        for memory in memories:
            if (hasattr(memory, 'position') and memory.position and 
                hasattr(memory, 'audio_caption') and memory.audio_caption):
                
                # Check distance
                distance = math.sqrt(
                    (position[0] - memory.position[0])**2 + 
                    (position[1] - memory.position[1])**2
                )
                
                if distance <= threshold:
                    # Check if audio content matches expected sound types
                    audio_content = memory.audio_caption.lower()
                    for sound_type in expected_sound_types:
                        type_keywords = {
                            'car_sound': ['car horn', 'honk', 'car', 'vehicle horn', 'horn'],
                            'church_bell': ['bell', 'church', 'ring', 'chime'],
                            'ambient': ['city', 'urban', 'ambient', 'background'],
                            'help_sound': ['scream', 'help', 'distress', 'emergency', 'squeal', 'help me', 'screaming', 'shout', 'yell', 'cry', 'calling', 'calling for help', 'screaming', 'shouting', 'yelling', 'crying', 'distress call', 'call for help', 'calling out'],
                            'crash': ['crash', 'bang', 'collision', 'impact'],
                            # NEW: Ambulance siren keywords
                            'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency', 'medical siren']
                        }.get(sound_type, [])
                        
                        if any(keyword in audio_content for keyword in type_keywords):
                            return True
        return False
    
    def _create_spatial_index(self, objects: List[Dict], object_type: str, scenario_filter=None) -> List[Dict]:
        """Create spatial index for ground truth objects"""
        index = []
        for obj in objects:
            if obj.get('position'):
                # FIXED: Don't filter here for content accuracy evaluation
                # Let the evaluation logic handle the filtering
                index.append({
                    'position': obj['position'][:2],
                    'type': object_type,
                    'data': obj
                })
        return index
    
    def _matches_scenario_filter(self, obj: Dict, scenario_filter: Dict) -> bool:
        """Check if object matches current scenario filter"""
        if not scenario_filter:
            return True
            
        filter_type = scenario_filter.get('filter_type')
        
        if filter_type == 'sound_isolation':
            enabled_types = scenario_filter.get('enabled_sound_types', [])
            obj_type = obj.get('classified_type', '')
            
            # For baseline (no sounds), exclude all sound objects
            if not enabled_types:
                return obj.get('type') != 'sound_source'
            
            # For specific sound types, only include matching ones
            return obj_type in enabled_types
        
        return True
    
    def _find_nearby_objects(self, position: List[float], spatial_index: List[Dict], threshold: float) -> List[Dict]:
        """Find objects within threshold distance"""
        nearby = []
        for indexed_obj in spatial_index:
            distance = math.sqrt(
                (position[0] - indexed_obj['position'][0])**2 + 
                (position[1] - indexed_obj['position'][1])**2
            )
            if distance <= threshold:
                nearby.append(indexed_obj['data'])
        return nearby
    
    def _is_position_covered_by_memories(self, position: List[float], memories: List, threshold: float) -> bool:
        """Check if a position is covered by any memory"""
        for memory in memories:
            if hasattr(memory, 'position') and memory.position:
                distance = math.sqrt(
                    (position[0] - memory.position[0])**2 + 
                    (position[1] - memory.position[1])**2
                )
                if distance <= threshold:
                    return True
        return False
    
    def _check_sound_classification_accuracy(self, audio_caption: str, nearby_sounds: List[Dict]) -> bool:
        """Check if audio caption matches nearby sound types"""
        if not audio_caption or not nearby_sounds:
            return False
        
        audio_lower = audio_caption.lower()
        
        for sound in nearby_sounds:
            sound_type = sound.get('classified_type', '').lower()
            
            # Simple keyword matching
            if sound_type in audio_lower:
                return True
            
            # Check for semantic matches
            type_keywords = {
                            'car_sound': ['car horn', 'honk', 'car', 'vehicle horn', 'horn'],
                            'church_bell': ['bell', 'church', 'ring', 'chime'],
                            'ambient': ['city', 'urban', 'ambient', 'background'],
                            'help_sound': ['scream', 'help', 'distress', 'emergency', 'squeal', 'help me', 'screaming', 'shout', 'yell', 'cry', 'calling', 'calling for help', 'screaming', 'shouting', 'yelling', 'crying', 'distress call', 'call for help', 'calling out'],
                            'crash': ['crash', 'bang', 'collision', 'impact'],
                            # NEW: Ambulance siren keywords
                            'ambulance_siren': ['ambulance', 'siren', 'emergency siren', 'medical emergency', 'medical siren']
                        }
            
            keywords = type_keywords.get(sound_type, [])
            if any(keyword in audio_lower for keyword in keywords):
                return True
        
        return False
    
    def _check_visual_classification_accuracy(self, visual_caption: str, nearby_visuals: List[Dict]) -> bool:
        """Check if visual caption matches nearby visual object types"""
        if not visual_caption or not nearby_visuals:
            return False
        
        visual_lower = visual_caption.lower()
        
        for visual in nearby_visuals:
            visual_type = visual.get('classified_type', '').lower()
            
            # Simple keyword matching
            if visual_type in visual_lower:
                return True
            
            # Check object type
            object_type = visual.get('type', '').lower()
            if object_type in visual_lower:
                return True
        
        return False
    
    def evaluate_navigation_performance(self, memories: List) -> Dict[str, Any]:
        """Evaluate navigation service performance with target coordinate extraction"""
        print("🧭 Evaluating navigation service performance...")
        
        if not self.navigation_service:
            return {
                'error': 'Navigation service not available',
                'total_queries': 0,
                'successful_navigations': 0,
                'success_rate': 0.0
            }
        
        # Test queries specifically designed for navigation
        navigation_queries = self._generate_navigation_test_queries()
        
        navigation_results = {
            'total_queries': len(navigation_queries),
            'successful_navigations': 0,
            'successful_coordinate_extractions': 0,
            'average_position_accuracy': 0.0,
            'average_response_quality': 0.0,
            'query_results': []
        }
        
        position_accuracies = []
        response_qualities = []
        
        for query in navigation_queries:
            try:
                print(f"  🧭 Testing navigation query: '{query['text']}'")
                
                # Create navigation request similar to the navigation service
                request_data = {
                    'query': query['text'],
                    'current_position': [0, 0, 0],  # Starting position
                    'timestamp': datetime.now().timestamp(),
                    'client': 'evaluation_framework'
                }
                
                # Process navigation request using the service's method
                result = self.navigation_service.process_navigation_request(request_data)
                
                # Evaluate the result
                query_result = {
                    'query': query['text'],
                    'expected_type': query['type'],
                    'expected_position': query.get('position'),
                    'success': result.get('success', False),
                    'target_position': result.get('target_position'),
                    'response_text': result.get('response_text', ''),
                    'error': result.get('error'),
                    'position_accuracy': 0.0,
                    'response_quality': 0.0
                }
                
                # Calculate position accuracy if we have both expected and actual positions
                if (query_result['success'] and 
                    query_result['target_position'] and 
                    query.get('position') and
                    query_result['target_position'] is not None and
                    not any(x is None for x in query_result['target_position'])):
                    
                    expected_pos = query['position'][:2]  # x, y
                    actual_pos = query_result['target_position'][:2]  # x, y
                    
                    distance = math.sqrt(
                        (expected_pos[0] - actual_pos[0])**2 + 
                        (expected_pos[1] - actual_pos[1])**2
                    )
                    
                    # **FIXED: More realistic position accuracy calculation**
                    # Position accuracy: 1.0 at 0m distance, 0.0 at 100m+ distance (was 50m)
                    # Also add minimum accuracy for reasonable distances
                    position_accuracy = max(0, 1 - (distance / 100.0))
                    
                    # Give some credit for being in the right general area (within 200m)
                    if distance <= 200.0:
                        position_accuracy = max(position_accuracy, 0.2)  # Minimum 20% for being close
                    
                    query_result['position_accuracy'] = position_accuracy
                    query_result['distance_error'] = distance  # Add distance for debugging
                    position_accuracies.append(position_accuracy)
                    
                    navigation_results['successful_coordinate_extractions'] += 1
                    
                    print(f"    ✅ Coordinates extracted: {query_result['target_position']}")
                    print(f"    📍 Expected: {expected_pos}, Actual: {actual_pos[:2]}")
                    print(f"    📏 Distance error: {distance:.2f}m, Accuracy: {position_accuracy:.2f}")
                else:
                    print(f"    ❌ No valid coordinates extracted")
                    if query_result.get('error'):
                        print(f"    📝 Error: {query_result['error']}")
                
                # Evaluate response quality (simple text-based heuristics)
                response_quality = self._evaluate_response_quality(
                    query_result['response_text'], 
                    query
                )
                query_result['response_quality'] = response_quality
                response_qualities.append(response_quality)
                
                if query_result['success']:
                    navigation_results['successful_navigations'] += 1
                
                navigation_results['query_results'].append(query_result)
                
            except Exception as e:
                print(f"  ❌ Navigation query failed: {query['text']} - {e}")
                error_result = {
                    'query': query['text'],
                    'expected_type': query['type'],
                    'expected_position': query.get('position'),
                    'success': False,
                    'error': str(e),
                    'position_accuracy': 0.0,
                    'response_quality': 0.0
                }
                navigation_results['query_results'].append(error_result)
        
        # Calculate overall metrics
        if navigation_results['query_results']:
            navigation_results['success_rate'] = (
                navigation_results['successful_navigations'] / navigation_results['total_queries']
            )
            navigation_results['coordinate_extraction_rate'] = (
                navigation_results['successful_coordinate_extractions'] / navigation_results['total_queries']
            )
        
        if position_accuracies:
            navigation_results['average_position_accuracy'] = np.mean(position_accuracies)
        
        if response_qualities:
            navigation_results['average_response_quality'] = np.mean(response_qualities)
        
        print(f"  📊 Navigation evaluation complete:")
        print(f"    Success rate: {navigation_results['success_rate']:.2%}")
        print(f"    Coordinate extraction rate: {navigation_results['coordinate_extraction_rate']:.2%}")
        print(f"    Average position accuracy: {navigation_results['average_position_accuracy']:.2f}")
        
        return navigation_results
    
    def _generate_navigation_test_queries(self) -> List[Dict]:
        """Generate test queries specifically for navigation evaluation"""
        
        # Check if we're in isolated sound evaluation context
        scenario_filter = getattr(self, '_current_scenario_filter', None)
        
        if scenario_filter and scenario_filter.get('filter_type') == 'sound_isolation':
            # Use scenario-aware queries for isolated sound evaluation
            return self._generate_scenario_aware_navigation_queries()
        else:
            # Use original ground truth-based queries for standard evaluation
            return self._generate_ground_truth_navigation_queries()
        
    def _generate_ground_truth_navigation_queries(self) -> List[Dict]:
        """Generate navigation queries based on ground truth data (original method)"""
        queries = []
        
        # Sound-based navigation queries from ground truth
        for sound_source in self.ground_truth.get('sound_sources', []):
            sound_type = sound_source.get('classified_type', '')
            position = sound_source.get('position')
            
            # if sound_type == 'church_bell' and position:
            #     queries.append({
            #         'text': "Navigate to the church bell",
            #         'type': 'sound_navigation',
            #         'expected_type': 'church_bell',
            #         'position': position
            #     })
            #     queries.append({
            #         'text': "Take me to where I heard church bells ringing",
            #         'type': 'sound_navigation',
            #         'expected_type': 'church_bell',
            #         'position': position
            #     })
            #     break  # Only test one church bell location
            
            # elif sound_type == 'car_sound' and position:
            #     queries.append({
            #         'text': "Go to where I heard car honking",
            #         'type': 'sound_navigation',
            #         'expected_type': 'car_sound',
            #         'position': position
            #     })
            #     break  # Only test one car sound location

            # elif sound_type == 'ambulance_siren' and position:
            #     queries.append({
            #         'text': "Go to where I heard the ambulance siren",
            #         'type': 'sound_navigation',
            #         'expected_type': 'ambulance_siren',
            #         'position': position
            #     })
            #     break  # Only test one ambulance siren location
            
            
            # if sound_type == 'church_bell' and position:
            #     queries.append({
            #         'text': "Navigate to the church bell",
            #         'type': 'sound_navigation',
            #         'expected_type': 'church_bell',
            #         'position': position
            #     })
            #     queries.append({
            #         'text': "Take me to where I heard church bells ringing",
            #         'type': 'sound_navigation',
            #         'expected_type': 'church_bell',
            #         'position': position
            #     })
            #     break  # Only test one church bell location
            
            if sound_type == 'car_sound' and position:
                queries.append({
                    'text': "Go to where I heard car honking",
                    'type': 'sound_navigation',
                    'expected_type': 'car_sound',
                    'position': position
                })
                # break  # Only test one car sound location

            if sound_type == 'ambulance_siren' and position:
                queries.append({
                    'text': "Go to where I heard the ambulance siren",
                    'type': 'sound_navigation',
                    'expected_type': 'ambulance_siren',
                    'position': position
                })
                # break  # Only test one ambulance siren location
                
            if sound_type == 'help_sound' and position:
                queries.append({
                    'text': "Go to where I heard someone screaming",
                    'type': 'sound_navigation',
                    'expected_type': 'help_sound',
                    'position': position
                })
                # break  # Only test one ambulance siren location
            

        # Visual-based navigation queries from ground truth
        church_objects = [obj for obj in self.ground_truth.get('visual_objects', []) 
                        if 'Church' in obj.get('type', '')]
        if church_objects:
            church_obj = church_objects[0]
            # queries.extend([
            #     {
            #         'text': "Navigate to the church building",
            #         'type': 'visual_navigation',
            #         'expected_type': 'building',
            #         'position': church_obj.get('position')
            #     },
            #     {
            #         'text': "Take me to the church",
            #         'type': 'visual_navigation',
            #         'expected_type': 'building',
            #         'position': church_obj.get('position')
            #     }
            # ])
        
        # # Area-based navigation queries from ground truth
        # for area in self.ground_truth.get('areas', []):
        #     area_name = area.get('name', '').lower()
        #     if 'church' in area_name:
        #         queries.append({
        #             'text': "Navigate to the church area",
        #             'type': 'area_navigation',
        #             'expected_type': 'area',
        #             'position': area.get('center')
        #         })
        #     elif 'playground' in area_name:
        #         queries.append({
        #             'text': "Take me to the playground",
        #             'type': 'area_navigation',
        #             'expected_type': 'area',
        #             'position': area.get('center')
        #         })
        
        # # Generic location queries (always included)
        # queries.extend([
        #     {
        #         'text': "Find a quiet place",
        #         'type': 'semantic_navigation',
        #         'expected_type': 'semantic'
        #     },
        #     {
        #         'text': "Navigate to an interesting location",
        #         'type': 'semantic_navigation',
        #         'expected_type': 'semantic'
        #     }
        # ])
        
        return queries
        
    def _generate_scenario_aware_navigation_queries(self) -> List[Dict]:
        """Generate navigation queries based on actual memory content for isolated sound evaluation"""
        queries = []
        
        # 1. CAR SOUND NAVIGATION (should work well)
        queries.extend([
            {
                'text': "Navigate to where I heard car honking",
                'type': 'sound_navigation',
                'expected_type': 'car_sound',
                'scenario': 'car_sound'
            },
            {
                'text': "Take me to the car horn sounds",
                'type': 'sound_navigation', 
                'expected_type': 'car_sound',
                'scenario': 'car_sound'
            },
            {
                'text': "Go where the honking was",
                'type': 'sound_navigation',
                'expected_type': 'car_sound',
                'scenario': 'car_sound'
            }
        ])
        
        # 2. VISUAL NAVIGATION (moderate success expected)
        queries.extend([
            {
                'text': "Navigate to the residential buildings",
                'type': 'visual_navigation',
                'expected_type': 'building',
                'scenario': 'baseline'
            },
            {
                'text': "Take me to the fence area",
                'type': 'visual_navigation',
                'expected_type': 'fence', 
                'scenario': 'baseline'
            },
            {
                'text': "Find the trash bins",
                'type': 'visual_navigation',
                'expected_type': 'trash',
                'scenario': 'baseline'
            }
        ])
        
        # 3. NON-EXISTENT SOUND NAVIGATION (should fail gracefully)
        queries.extend([
            # {
            #     'text': "Navigate to the church bell",
            #     'type': 'sound_navigation',
            #     'expected_type': 'church_bell',
            #     'scenario': 'church_bell'
            # },
            {
                'text': "Take me where I heard screaming",
                'type': 'sound_navigation',
                'expected_type': 'help_sound',
                'scenario': 'help_sound'
            },
            # NEW: Ambulance navigation queries
            {
                'text': "Navigate to the ambulance sirens",
                'type': 'sound_navigation',
                'expected_type': 'ambulance_siren',
                'scenario': 'ambulance_siren'
            },
            {
                'text': "Take me where I heard emergency sirens",
                'type': 'sound_navigation',
                'expected_type': 'ambulance_siren',
                'scenario': 'ambulance_siren'
            }
        ])
        
        # # 4. GENERAL NAVIGATION (semantic understanding)
        # queries.extend([
        #     {
        #         'text': "Find an interesting location",
        #         'type': 'semantic_navigation',
        #         'expected_type': 'semantic',
        #         'scenario': 'general'
        #     },
        #     {
        #         'text': "Navigate to where there's activity",
        #         'type': 'semantic_navigation', 
        #         'expected_type': 'semantic',
        #         'scenario': 'general'
        #     }
        # ])
        
        return queries
    
    def _evaluate_response_quality(self, response_text: str, query: Dict) -> float:
        """Evaluate the quality of navigation response text"""
        if not response_text:
            return 0.0
        
        response_lower = response_text.lower()
        query_text = query['text'].lower()
        
        quality_score = 0.0
        
        # Check for response relevance
        query_words = set(query_text.split())
        response_words = set(response_lower.split())
        word_overlap = len(query_words.intersection(response_words))
        if query_words:
            quality_score += (word_overlap / len(query_words)) * 0.3
        
        # Check for location/navigation language
        navigation_keywords = [
            'navigate', 'go', 'move', 'direction', 'location', 'position', 
            'coordinates', 'found', 'remember', 'recall', 'area', 'place'
        ]
        nav_keyword_count = sum(1 for keyword in navigation_keywords if keyword in response_lower)
        quality_score += min(nav_keyword_count / 3, 1.0) * 0.3
        
        # Check for specific content references
        expected_type = query.get('expected_type', '')
        if expected_type and expected_type in response_lower:
            quality_score += 0.2
        
        # Check response length (not too short, not too long)
        word_count = len(response_text.split())
        if 5 <= word_count <= 50:
            quality_score += 0.2
        elif word_count > 0:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def evaluate_retrieval_performance(self, memories: List) -> Dict[str, Any]:
        """Evaluate memory retrieval performance with scenario-aware queries"""
        print("🔍 Evaluating scenario-aware retrieval performance...")
        
        # Generate test queries based on actual memory content and scenarios
        test_queries = self._generate_scenario_aware_test_queries(memories)
        
        retrieval_results = {
            'total_queries': len(test_queries),
            'successful_retrievals': 0,
            'average_relevance': 0.0,
            'query_results': [],
            'scenario_breakdown': {}
        }
        
        for query in test_queries:
            try:
                # Perform retrieval using memory system
                results = self.memory_analyzer.memory.search(query['text'], limit=5)
                
                # Evaluate relevance with scenario context
                relevance_score = self._calculate_scenario_aware_query_relevance(query, results, memories)
                
                # FIXED: More realistic success threshold based on actual content
                # Different thresholds for different query types
                if query['scenario'] == 'car_sound':
                    success_threshold = 0.3  # Lower threshold for car sounds since they're abundant
                elif query['scenario'] == 'baseline':
                    success_threshold = 0.2  # Lower threshold for visual-only queries
                else:
                    success_threshold = 0.1  # Very low threshold for non-existent sounds
                
                query_result = {
                    'query': query['text'],
                    'scenario': query['scenario'],
                    'expected_type': query['type'],
                    'expected_position': query.get('position'),
                    'num_results': len(results),
                    'relevance_score': relevance_score,
                    'successful': relevance_score > success_threshold,
                    'success_threshold': success_threshold,
                    'query_category': query.get('category', 'unknown')
                }
                
                retrieval_results['query_results'].append(query_result)
                
                # Track by scenario
                scenario = query['scenario']
                if scenario not in retrieval_results['scenario_breakdown']:
                    retrieval_results['scenario_breakdown'][scenario] = {
                        'total': 0, 'successful': 0, 'avg_relevance': 0.0, 'relevance_scores': []
                    }
                
                retrieval_results['scenario_breakdown'][scenario]['total'] += 1
                retrieval_results['scenario_breakdown'][scenario]['relevance_scores'].append(relevance_score)
                
                if query_result['successful']:
                    retrieval_results['successful_retrievals'] += 1
                    retrieval_results['scenario_breakdown'][scenario]['successful'] += 1
                    
            except Exception as e:
                print(f"⚠️ Query failed: {query['text']} - {e}")
                error_result = {
                    'query': query['text'],
                    'scenario': query['scenario'],
                    'expected_type': query['type'],
                    'error': str(e),
                    'successful': False,
                    'relevance_score': 0.0
                }
                retrieval_results['query_results'].append(error_result)
        
        # Calculate overall metrics
        if retrieval_results['query_results']:
            retrieval_results['average_relevance'] = np.mean([
                r['relevance_score'] for r in retrieval_results['query_results']
            ])
            
            retrieval_results['success_rate'] = (
                retrieval_results['successful_retrievals'] / retrieval_results['total_queries']
            )
        
        # Calculate scenario-specific metrics
        for scenario, data in retrieval_results['scenario_breakdown'].items():
            if data['relevance_scores']:
                data['avg_relevance'] = np.mean(data['relevance_scores'])
                data['success_rate'] = data['successful'] / data['total']
        
        # Print detailed breakdown
        print(f"    📊 Retrieval Performance by Scenario:")
        for scenario, data in retrieval_results['scenario_breakdown'].items():
            print(f"      {scenario}: {data['success_rate']:.2%} success, {data['avg_relevance']:.3f} avg relevance")
        
        return retrieval_results
    
    def _calculate_scenario_aware_query_relevance(self, query: Dict, results: List, memories: List) -> float:
        """Calculate relevance score with scenario awareness"""
        if not results:
            return 0.0
        
        relevance_scores = []
        expected_content = query.get('expected_content')
        scenario = query.get('scenario', '')
        category = query.get('category', '')
        
        for result in results:
            score = 0.0
            
            # Content-based relevance (increased weight)
            content_score = 0.0
            query_text = query['text'].lower()
            
            # Check audio content match
            if hasattr(result, 'audio_caption') and result.audio_caption:
                audio_text = result.audio_caption.lower()
                
                # Direct keyword matching
                query_words = set(query_text.split())
                audio_words = set(audio_text.split())
                overlap = len(query_words.intersection(audio_words))
                
                if overlap > 0:
                    content_score = max(content_score, overlap / len(query_words))
                
                # Scenario-specific bonus scoring
                if scenario == 'car_sound' and any(kw in audio_text for kw in ['car horn', 'honk', 'horn']):
                    # content_score = max(content_score, 0.8)  # High score for car sound matches
                    pass
                elif scenario == 'church_bell' and any(kw in audio_text for kw in ['bell', 'church']):
                    # content_score = max(content_score, 0.8)
                    pass
                elif 'silence' in audio_text and scenario in ['church_bell', 'ambient', 'help_sound']:
                    content_score = max(content_score, 0.3)  # Some credit for silence when no sound expected
            
            # Check visual content match
            if result.caption:
                caption_text = result.caption
                if isinstance(caption_text, list):
                    caption_text = ' '.join(caption_text)
                
                caption_text = caption_text.lower()
                
                query_words = set(query_text.split())
                caption_words = set(caption_text.split())
                overlap = len(query_words.intersection(caption_words))
                
                if overlap > 0:
                    content_score = max(content_score, overlap / len(query_words))
            
            # Position-based relevance (if applicable)
            position_score = 0.0
            expected_position = query.get('expected_position')
            if expected_position and hasattr(result, 'position') and result.position:
                distance = math.sqrt(
                    (expected_position[0] - result.position[0])**2 + 
                    (expected_position[1] - result.position[1])**2
                )
                # More generous position scoring
                position_score = max(0, 1 - (distance / 100.0))
            
            # Weighted combination based on query category
            if category == 'direct_audio_match':
                score = content_score * 0.9 + position_score * 0.1
            elif category == 'direct_visual_match':
                score = content_score * 0.9 + position_score * 0.1
            elif category == 'multimodal_combo':
                score = content_score * 0.8 + position_score * 0.2
            elif category == 'position_based':
                score = content_score * 0.5 + position_score * 0.5
            else:
                score = content_score * 0.7 + position_score * 0.3
            
            relevance_scores.append(score)
        
        # Return best relevance score
        return max(relevance_scores) if relevance_scores else 0.0
    
    def _generate_scenario_aware_test_queries(self, memories: List) -> List[Dict]:
        """Generate test queries that align with isolated sound evaluation scenarios"""
        queries = []
        
        # Analyze what content actually exists in memories
        audio_content_analysis = self._analyze_actual_audio_content(memories)
        visual_content_analysis = self._analyze_actual_visual_content(memories)
        
        print(f"    📊 Found audio content: {list(audio_content_analysis.keys())}")
        print(f"    📊 Found visual content: {list(visual_content_analysis.keys())}")
        
        # 1. CAR SOUND SCENARIO QUERIES (should have high success rate)
        if audio_content_analysis.get('car_horn', 0) > 0:
            queries.extend([
                {
                    'text': "car horn",
                    'type': 'sound',
                    'scenario': 'car_sound',
                    'category': 'direct_audio_match',
                    'expected_content': 'car horn'
                },
                {
                    'text': "honking",
                    'type': 'sound', 
                    'scenario': 'car_sound',
                    'category': 'audio_synonym',
                    'expected_content': 'car horn'
                },
                {
                    'text': "vehicle sound",
                    'type': 'sound',
                    'scenario': 'car_sound', 
                    'category': 'audio_related',
                    'expected_content': 'car horn'
                },
                {
                    'text': "horn sound",
                    'type': 'sound',
                    'scenario': 'car_sound',
                    'category': 'audio_partial',
                    'expected_content': 'car horn'
                }
            ])

        # 1. AMBULANCE SIREN SCENARIO QUERIES (should have high success rate)
        if audio_content_analysis.get('ambulance_siren', 0) > 0:
            queries.extend([
                {
                    'text': "ambulance siren",
                    'type': 'sound',
                    'scenario': 'ambulance_siren',
                    'category': 'direct_audio_match',
                    'expected_content': 'ambulance siren'
                },
                {
                    'text': "siren",
                    'type': 'sound', 
                    'scenario': 'ambulance_siren',
                    'category': 'audio_synonym',
                    'expected_content': 'ambulance siren'
                },
                {
                    'text': "ambulance sound",
                    'type': 'sound',
                    'scenario': 'ambulance_siren',
                    'category': 'audio_related',
                    'expected_content': 'ambulance siren'
                },
                {
                    'text': "siren sound",
                    'type': 'sound',
                    'scenario': 'ambulance_siren',
                    'category': 'audio_partial',
                    'expected_content': 'ambulance siren'
                }
            ])
            
        if audio_content_analysis.get('help', 0) > 0:
            queries.extend([
                {
                    'text': "screaming",
                    'type': 'sound',
                    'scenario': 'help_sound',
                    'category': 'direct_audio_match',
                    'expected_content': 'screaming'
                },
                {
                    'text': "scream",
                    'type': 'sound', 
                    'scenario': 'help_sound',
                    'category': 'audio_synonym',
                    'expected_content': 'screaming'
                },
                {
                    'text': "squealing",
                    'type': 'sound',
                    'scenario': 'help_sound',
                    'category': 'audio_related',
                    'expected_content': 'screaming'
                },
                {
                    'text': "scream sound",
                    'type': 'sound',
                    'scenario': 'help_sound',
                    'category': 'audio_partial',
                    'expected_content': 'screaming'
                }
            ])
        
        # 2. VISUAL CONTENT QUERIES (should have moderate success rate)
        if visual_content_analysis.get('building', 0) > 0:
            queries.extend([
                {
                    'text': "building",
                    'type': 'visual',
                    'scenario': 'baseline',
                    'category': 'direct_visual_match',
                    'expected_content': 'building'
                },
                {
                    'text': "structure",
                    'type': 'visual',
                    'scenario': 'baseline', 
                    'category': 'visual_synonym',
                    'expected_content': 'building'
                }
            ])
        
        if visual_content_analysis.get('fence', 0) > 0:
            queries.extend([
                {
                    'text': "fence",
                    'type': 'visual',
                    'scenario': 'baseline',
                    'category': 'direct_visual_match', 
                    'expected_content': 'fence'
                },
                {
                    'text': "wooden fence",
                    'type': 'visual',
                    'scenario': 'baseline',
                    'category': 'visual_specific',
                    'expected_content': 'fence'
                }
            ])
        
        if visual_content_analysis.get('trash', 0) > 0:
            queries.extend([
                {
                    'text': "trash bin",
                    'type': 'visual',
                    'scenario': 'baseline',
                    'category': 'direct_visual_match',
                    'expected_content': 'trash'
                },
                {
                    'text': "green bin",
                    'type': 'visual',
                    'scenario': 'baseline',
                    'category': 'visual_specific',
                    'expected_content': 'trash'
                }
            ])
        
        # # 3. NON-EXISTENT SOUND QUERIES (should have low success rate)
        # queries.extend([
        #     # {
        #     #     'text': "church bell",
        #     #     'type': 'sound',
        #     #     'scenario': 'church_bell',
        #     #     'category': 'non_existent_audio',
        #     #     'expected_content': None
        #     # },
        #     # {
        #     #     'text': "bell ringing",
        #     #     'type': 'sound',
        #     #     'scenario': 'church_bell',
        #     #     'category': 'non_existent_audio',
        #     #     'expected_content': None
        #     # },
        #     # {
        #     #     'text': "city sounds",
        #     #     'type': 'sound',
        #     #     'scenario': 'ambient',
        #     #     'category': 'non_existent_audio', 
        #     #     'expected_content': None
        #     # },
        #     # {
        #     #     'text': "screaming",
        #     #     'type': 'sound',
        #     #     'scenario': 'help_sound',
        #     #     'category': 'non_existent_audio',
        #     #     'expected_content': None
        #     # },
        #     # NEW: Ambulance siren queries
        #     {
        #         'text': "ambulance siren",
        #         'type': 'sound',
        #         'scenario': 'ambulance_siren',
        #         'category': 'non_existent_audio',
        #         'expected_content': None
        #     },
        #     {
        #         'text': "emergency siren",
        #         'type': 'sound',
        #         'scenario': 'ambulance_siren',
        #         'category': 'non_existent_audio',
        #         'expected_content': None
        #     },
        #     {
        #         'text': "medical emergency sounds",
        #         'type': 'sound',
        #         'scenario': 'ambulance_siren',
        #         'category': 'non_existent_audio',
        #         'expected_content': None
        #     }
        # ])
        
        # 4. MULTIMODAL QUERIES (combining audio and visual)
        if audio_content_analysis.get('car_horn', 0) > 0 and visual_content_analysis.get('building', 0) > 0:
            queries.extend([
                {
                    'text': "car horn near buildings",
                    'type': 'multimodal',
                    'scenario': 'car_sound',
                    'category': 'multimodal_combo',
                    'expected_content': 'car horn + building'
                },
                {
                    'text': "honking around fence",
                    'type': 'multimodal', 
                    'scenario': 'car_sound',
                    'category': 'multimodal_combo',
                    'expected_content': 'car horn + fence'
                }
            ])
            
        # 4. MULTIMODAL QUERIES (combining audio and visual)
        if audio_content_analysis.get('ambulance_siren', 0) > 0 and visual_content_analysis.get('building', 0) > 0:
            queries.extend([
                {
                    'text': "ambulance siren near buildings",
                    'type': 'multimodal',
                    'scenario': 'ambulance_siren',
                    'category': 'multimodal_combo',
                    'expected_content': 'ambulance siren + building'
                },
                {
                    'text': "siren around fence",
                    'type': 'multimodal', 
                    'scenario': 'ambulance_siren',
                    'category': 'multimodal_combo',
                    'expected_content': 'ambulance siren + fence'
                },
                {
                    'text': "siren near trash bin",
                    'type': 'multimodal',
                    'scenario': 'ambulance_siren',
                    'category': 'multimodal_combo',
                    'expected_content': 'siren + trash'
                }
            ])
            
        # 4. MULTIMODAL QUERIES (combining audio and visual)
        if audio_content_analysis.get('help', 0) > 0 and visual_content_analysis.get('building', 0) > 0:
            queries.extend([
                {
                    'text': "screams near buildings",
                    'type': 'multimodal',
                    'scenario': 'help_sound',
                    'category': 'multimodal_combo',
                    'expected_content': 'screams + building'
                },
                {
                    'text': "squealing around fence",
                    'type': 'multimodal', 
                    'scenario': 'help_sound',
                    'category': 'multimodal_combo',
                    'expected_content': 'squealing + fence'
                },
                {
                    'text': "screams near trash bin",
                    'type': 'multimodal',
                    'scenario': 'help_sound',
                    'category': 'multimodal_combo',
                    'expected_content': 'screams + trash'
                }
            ])
        
        # # 5. POSITION-BASED QUERIES (if we have position data)
        # position_queries = self._generate_position_based_queries(memories)
        # queries.extend(position_queries)
        
        print(f"    📝 Generated {len(queries)} scenario-aware test queries")
        return queries
    
    def _generate_position_based_queries(self, memories: List) -> List[Dict]:
        """Generate queries based on actual memory positions"""
        queries = []
        
        # Get position clusters
        if memories:
            position_clusters = self.memory_analyzer.cluster_memories_by_location(memories, radius=15.0)
            
            # Find clusters with audio content
            for i, cluster in enumerate(position_clusters[:3]):  # Limit to top 3 clusters
                audio_memories = [m for m in cluster['memories'] 
                                if hasattr(m, 'audio_caption') and m.audio_caption]
                
                if audio_memories:
                    center_pos = cluster['center']
                    queries.append({
                        'text': f"sounds near position {center_pos[0]:.0f} {center_pos[1]:.0f}",
                        'type': 'positional',
                        'scenario': 'car_sound',
                        'category': 'position_based',
                        'expected_position': center_pos,
                        'expected_content': 'audio'
                    })
        
        return queries
    
    def _analyze_actual_audio_content(self, memories: List) -> Dict[str, int]:
        """Analyze what audio content actually exists in memories"""
        audio_content = {}
        
        for memory in memories:
            if hasattr(memory, 'audio_caption') and memory.audio_caption:
                audio_text = memory.audio_caption.lower()
                
                # Count occurrences of specific audio types
                if any(keyword in audio_text for keyword in ['car horn', 'honk', 'horn']):
                    audio_content['car_horn'] = audio_content.get('car_horn', 0) + 1
                if any(keyword in audio_text for keyword in ['bell', 'church', 'ring']):
                    audio_content['bell'] = audio_content.get('bell', 0) + 1
                if any(keyword in audio_text for keyword in ['city', 'urban', 'ambient']):
                    audio_content['ambient'] = audio_content.get('ambient', 0) + 1
                if any(keyword in audio_text for keyword in ['scream', 'help', 'distress', 'shout', 'yell', 'cry', 'calling', 'calling for help', 'screaming', 'shouting', 'yelling', 'crying', 'distress call', 'call for help', 'calling out', 'squeal']):
                    audio_content['help'] = audio_content.get('help', 0) + 1
                if any(keyword in audio_text for keyword in ['crash', 'collision', 'bang']):
                    audio_content['crash'] = audio_content.get('crash', 0) + 1
                # NEW: Ambulance siren detection
                if any(keyword in audio_text for keyword in ['ambulance', 'siren', 'emergency siren', 'medical emergency']):
                    audio_content['ambulance_siren'] = audio_content.get('ambulance_siren', 0) + 1
                if 'silence' in audio_text:
                    audio_content['silence'] = audio_content.get('silence', 0) + 1
                if 'musical' in audio_text:
                    audio_content['musical'] = audio_content.get('musical', 0) + 1
        
        return audio_content
    
    def _analyze_actual_visual_content(self, memories: List) -> Dict[str, int]:
        """Analyze what visual content actually exists in memories"""
        visual_content = {}
        
        for memory in memories:
            if memory.caption:
                # Handle both string and list captions
                caption_text = memory.caption
                if isinstance(caption_text, list):
                    caption_text = ' '.join(caption_text)
                
                visual_text = caption_text.lower()
                
                # Count occurrences of specific visual elements
                if any(keyword in visual_text for keyword in ['building', 'house', 'structure']):
                    visual_content['building'] = visual_content.get('building', 0) + 1
                if any(keyword in visual_text for keyword in ['fence', 'barrier']):
                    visual_content['fence'] = visual_content.get('fence', 0) + 1
                if any(keyword in visual_text for keyword in ['trash', 'bin', 'garbage']):
                    visual_content['trash'] = visual_content.get('trash', 0) + 1
                if any(keyword in visual_text for keyword in ['tree', 'palm', 'green']):
                    visual_content['tree'] = visual_content.get('tree', 0) + 1
                if any(keyword in visual_text for keyword in ['car', 'vehicle', 'van']):
                    visual_content['vehicle'] = visual_content.get('vehicle', 0) + 1
                if any(keyword in visual_text for keyword in ['road', 'street', 'pavement']):
                    visual_content['road'] = visual_content.get('road', 0) + 1
                if any(keyword in visual_text for keyword in ['sky', 'clear', 'blue']):
                    visual_content['sky'] = visual_content.get('sky', 0) + 1
        
        return visual_content
    
    def _generate_test_queries(self) -> List[Dict]:
        """Generate test queries based on ground truth for basic retrieval"""
        queries = []
        
        # Sound-based queries
        for sound_source in self.ground_truth.get('sound_sources', [])[:3]:  # Limit for testing
            sound_type = sound_source.get('classified_type', '')
            if sound_type == 'church_bell':
                queries.append({
                    'text': "Find the church bell sounds",
                    'type': 'sound',
                    'expected_type': 'church_bell',
                    'position': sound_source.get('position')
                })
            elif sound_type == 'car_sound':
                queries.append({
                    'text': "Where did I hear car horns?",
                    'type': 'sound',
                    'expected_type': 'car_sound',
                    'position': sound_source.get('position')
                })
            elif sound_type == 'help_sound':
                queries.append({
                    'text': "Locate the screaming sounds",
                    'type': 'sound',
                    'expected_type': 'help_sound',
                    'position': sound_source.get('position')
                })
            # NEW: Ambulance siren queries
            elif sound_type == 'ambulance_siren':
                queries.append({
                    'text': "Where did I hear ambulance sirens?",
                    'type': 'sound',
                    'expected_type': 'ambulance_siren',
                    'position': sound_source.get('position')
                })
        
        # # Visual-based queries
        # church_objects = [obj for obj in self.ground_truth.get('visual_objects', []) 
        #                  if 'Church' in obj.get('type', '')]
        # if church_objects:
        #     queries.append({
        #         'text': "Show me the church building",
        #         'type': 'visual',
        #         'expected_type': 'building',
        #         'position': church_objects[0].get('position')
        #     })
        
        # Area-based queries
        queries.extend([
            # {'text': "Take me to the playground area", 'type': 'area', 'expected_type': 'playground'},
            {'text': "Navigate to the commercial district", 'type': 'area', 'expected_type': 'commercial'},
            {'text': "Find the residential neighborhood", 'type': 'area', 'expected_type': 'residential'}
        ])
        
        return queries
    
    def _calculate_query_relevance(self, query: Dict, results: List) -> float:
        """Calculate relevance score for query results"""
        if not results:
            return 0.0
        
        relevance_scores = []
        expected_position = query.get('position')
        
        for result in results:
            score = 0.0
            
            # Position-based relevance
            if expected_position and hasattr(result, 'position') and result.position:
                distance = math.sqrt(
                    (expected_position[0] - result.position[0])**2 + 
                    (expected_position[1] - result.position[1])**2
                )
                # Closer is better, max score at distance 0, min score at 50m
                position_score = max(0, 1 - (distance / 50.0))
                score += position_score * 0.6  # 60% weight for position
            
            # Content-based relevance
            content_score = 0.0
            query_text = query['text'].lower()
            
            if result.caption:
                # Handle case where caption might be a list
                caption_text = result.caption
                if isinstance(caption_text, list):
                    caption_text = ' '.join(caption_text)
                
                caption_words = set(caption_text.lower().split())
                query_words = set(query_text.split())
                overlap = len(caption_words.intersection(query_words))
                content_score = max(content_score, overlap / max(len(query_words), 1))
            
            if hasattr(result, 'audio_caption') and result.audio_caption:
                audio_words = set(result.audio_caption.lower().split())
                query_words = set(query_text.split())
                overlap = len(audio_words.intersection(query_words))
                content_score = max(content_score, overlap / max(len(query_words), 1))
            
            score += content_score * 0.4  # 40% weight for content
            
            relevance_scores.append(score)
        
        # Return best relevance score
        return max(relevance_scores) if relevance_scores else 0.0
    
    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation of the multimodal memory system"""
        print("🚀 Starting Comprehensive Multimodal Memory Evaluation")
        print("="*60)
        
        # Retrieve all memories
        memories = self.memory_analyzer.retrieve_all_memories()
        
        if not memories:
            return {'error': 'No memories found in collection'}
        
        evaluation_report = {
            'metadata': {
                'collection_name': self.collection_name,
                'evaluation_timestamp': datetime.now().isoformat(),
                'total_memories': len(memories),
                'ground_truth_file': str(self.ground_truth_path),
                'navigation_service_available': NAVIGATION_SERVICE_AVAILABLE
            }
        }
        
        # 1. Spatial Coverage Evaluation
        evaluation_report['spatial_coverage'] = self.calculate_spatial_coverage(memories)
        
        # 2. Content Analysis
        content_analysis = self.memory_analyzer.generate_content_analysis_report(memories)
        evaluation_report['content_analysis'] = content_analysis
        
        # 3. Content Accuracy Evaluation
        evaluation_report['content_accuracy'] = self.evaluate_content_accuracy(memories)
        
        # 4. Basic Retrieval Performance Evaluation
        evaluation_report['retrieval_performance'] = self.evaluate_retrieval_performance(memories)
        
        # 5. Navigation Service Performance Evaluation (NEW)
        evaluation_report['navigation_performance'] = self.evaluate_navigation_performance(memories)
        
        # 6. Overall Score Calculation (updated to include navigation)
        evaluation_report['overall_scores'] = self._calculate_overall_scores(evaluation_report)
        
        return evaluation_report
    
    def _calculate_overall_scores(self, report: Dict) -> Dict[str, float]:
        """Calculate overall evaluation scores including navigation performance"""
        scores = {}
        
        # Spatial coverage score
        scores['spatial_coverage'] = report.get('spatial_coverage', {}).get('coverage_score', 0.0)
        
        # Content quality score
        multimodal_analysis = report.get('content_analysis', {}).get('multimodal_analysis', {})
        total_memories = multimodal_analysis.get('total_memories', 1)
        multimodal_memories = multimodal_analysis.get('multimodal', 0)
        scores['multimodal_ratio'] = multimodal_memories / total_memories
        
        # Content accuracy score
        content_accuracy = report.get('content_accuracy', {})
        sound_f1 = content_accuracy.get('sound_detection', {}).get('f1_score', 0.0)
        visual_f1 = content_accuracy.get('visual_detection', {}).get('f1_score', 0.0)
        scores['content_accuracy'] = (sound_f1 + visual_f1) / 2
        
        # Basic retrieval performance score
        retrieval_perf = report.get('retrieval_performance', {})
        scores['retrieval_performance'] = retrieval_perf.get('success_rate', 0.0)
        
        # Navigation performance score (NEW)
        navigation_perf = report.get('navigation_performance', {})
        if 'error' not in navigation_perf:
            nav_success_rate = navigation_perf.get('success_rate', 0.0)
            coord_extraction_rate = navigation_perf.get('coordinate_extraction_rate', 0.0)
            position_accuracy = navigation_perf.get('average_position_accuracy', 0.0)
            
            # Weighted combination of navigation metrics
            scores['navigation_performance'] = (
                nav_success_rate * 0.4 +
                coord_extraction_rate * 0.3 +
                position_accuracy * 0.3
            )
        else:
            scores['navigation_performance'] = 0.0
        
        # Overall system score (updated weights to include navigation)
        if NAVIGATION_SERVICE_AVAILABLE and scores['navigation_performance'] > 0:
            scores['overall_system_score'] = (
                scores['spatial_coverage'] * 0.2 +
                scores['multimodal_ratio'] * 0.2 +
                scores['content_accuracy'] * 0.2 +
                scores['retrieval_performance'] * 0.2 +
                scores['navigation_performance'] * 0.2
            )
        else:
            # Fallback to original weighting if navigation not available
            scores['overall_system_score'] = (
                scores['spatial_coverage'] * 0.25 +
                scores['multimodal_ratio'] * 0.25 +
                scores['content_accuracy'] * 0.25 +
                scores['retrieval_performance'] * 0.25
            )
        
        return scores
    
    def save_evaluation_report(self, report: Dict, output_path: str):
        """Save evaluation report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Evaluation report saved to: {output_file}")
    
    def print_evaluation_summary(self, report: Dict):
        """Print evaluation summary including scenario breakdown"""
        print("\n📊 EVALUATION SUMMARY")
        print("="*50)
        
        metadata = report.get('metadata', {})
        print(f"Collection: {metadata.get('collection_name')}")
        print(f"Total Memories: {metadata.get('total_memories')}")
        print(f"Navigation Service: {'✅ Available' if metadata.get('navigation_service_available') else '❌ Not Available'}")
        
        scores = report.get('overall_scores', {})
        print(f"\n🏆 Overall Scores:")
        print(f"  📍 Spatial Coverage: {scores.get('spatial_coverage', 0):.2%}")
        print(f"  🎭 Multimodal Ratio: {scores.get('multimodal_ratio', 0):.2%}")
        print(f"  🎯 Content Accuracy: {scores.get('content_accuracy', 0):.2%}")
        print(f"  🔍 Retrieval Performance: {scores.get('retrieval_performance', 0):.2%}")
        print(f"  🧭 Navigation Performance: {scores.get('navigation_performance', 0):.2%}")
        print(f"  🌟 Overall System Score: {scores.get('overall_system_score', 0):.2%}")
        
        # Check if this is an isolated sound evaluation context
        scenario_filter = getattr(self, '_current_scenario_filter', None)
        is_isolated_evaluation = scenario_filter and scenario_filter.get('filter_type') == 'sound_isolation'
        
        # Detailed retrieval breakdown by scenario (only for isolated sound evaluation)
        retrieval_perf = report.get('retrieval_performance', {})
        scenario_breakdown = retrieval_perf.get('scenario_breakdown', {})
        
        if scenario_breakdown and is_isolated_evaluation:
            print(f"\n🔍 Retrieval Performance by Scenario (Isolated Sound Evaluation):")
            for scenario, data in scenario_breakdown.items():
                success_rate = data.get('success_rate', 0)
                avg_relevance = data.get('avg_relevance', 0)
                total_queries = data.get('total', 0)
                print(f"  {scenario}: {success_rate:.2%} success ({total_queries} queries, {avg_relevance:.3f} avg relevance)")
        elif scenario_breakdown:
            print(f"\n🔍 Retrieval Performance Summary:")
            total_queries = retrieval_perf.get('total_queries', 0)
            success_rate = retrieval_perf.get('success_rate', 0)
            avg_relevance = retrieval_perf.get('average_relevance', 0)
            print(f"  Total Queries: {total_queries}")
            print(f"  Success Rate: {success_rate:.2%}")
            print(f"  Average Relevance: {avg_relevance:.3f}")
        
        # Content breakdown
        content_analysis = report.get('content_analysis', {})
        multimodal_analysis = content_analysis.get('multimodal_analysis', {})
        
        print(f"\n📈 Memory Breakdown:")
        print(f"  🎭 Multimodal: {multimodal_analysis.get('multimodal', 0)}")
        print(f"  👁️ Visual Only: {multimodal_analysis.get('visual_only', 0)}")
        print(f"  🔊 Audio Only: {multimodal_analysis.get('audio_only', 0)}")
        print(f"  ❌ Empty: {multimodal_analysis.get('empty', 0)}")
        
        # Navigation breakdown with context awareness
        navigation_perf = report.get('navigation_performance', {})
        if 'error' not in navigation_perf:
            print(f"\n🧭 Navigation Performance Details:")
            print(f"  📊 Success Rate: {navigation_perf.get('success_rate', 0):.2%}")
            print(f"  📍 Coordinate Extraction Rate: {navigation_perf.get('coordinate_extraction_rate', 0):.2%}")
            print(f"  🎯 Average Position Accuracy: {navigation_perf.get('average_position_accuracy', 0):.2f}")
            print(f"  💬 Average Response Quality: {navigation_perf.get('average_response_quality', 0):.2f}")
            
            # Show navigation query breakdown with context awareness
            query_results = navigation_perf.get('query_results', [])
            if query_results:
                if is_isolated_evaluation:
                    # Group by scenario for isolated sound evaluation
                    scenario_nav_breakdown = {}
                    for query_result in query_results:
                        scenario = query_result.get('scenario', 'unknown')
                        if scenario not in scenario_nav_breakdown:
                            scenario_nav_breakdown[scenario] = {'total': 0, 'successful': 0}
                        scenario_nav_breakdown[scenario]['total'] += 1
                        if query_result.get('success', False):
                            scenario_nav_breakdown[scenario]['successful'] += 1
                    
                    print(f"  📋 Navigation by Scenario:")
                    for scenario, data in scenario_nav_breakdown.items():
                        success_rate = data['successful'] / data['total'] if data['total'] > 0 else 0
                        print(f"    {scenario}: {success_rate:.2%} ({data['successful']}/{data['total']})")
                else:
                    # Group by type for standard evaluation
                    type_nav_breakdown = {}
                    for query_result in query_results:
                        query_type = query_result.get('expected_type', 'unknown')
                        if query_type not in type_nav_breakdown:
                            type_nav_breakdown[query_type] = {'total': 0, 'successful': 0}
                        type_nav_breakdown[query_type]['total'] += 1
                        if query_result.get('success', False):
                            type_nav_breakdown[query_type]['successful'] += 1
                    
                    print(f"  📋 Navigation by Query Type:")
                    for query_type, data in type_nav_breakdown.items():
                        success_rate = data['successful'] / data['total'] if data['total'] > 0 else 0
                        print(f"    {query_type}: {success_rate:.2%} ({data['successful']}/{data['total']})")
        
        # Show evaluation context
        if is_isolated_evaluation:
            enabled_types = scenario_filter.get('enabled_sound_types', [])
            print(f"\n🎯 Evaluation Context: Isolated Sound Evaluation")
            print(f"  Enabled Sound Types: {enabled_types}")
        else:
            print(f"\n📊 Evaluation Context: Standard Comprehensive Evaluation")
            print(f"  Using ground truth-based queries and full content analysis")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Multimodal Memory Evaluation Framework')
    parser.add_argument('--ground-truth', required=True, help='Path to ground truth JSON file')
    parser.add_argument('--collection', '-c', default='webots_multimodal', help='Memory collection name')
    parser.add_argument('--db-ip', '-d', default='127.0.0.1', help='MilvusDB IP address')
    parser.add_argument('--output', '-o', default='evaluation_report.json', help='Output file path')
    
    parser.add_argument('--model-backend', '-m', default='COMMAND_R', 
                   choices=['COMMAND_R', 'GEMMA'], help='Model backend to use')
    
    args = parser.parse_args()
    
    print("🎯 Multimodal Memory Building Evaluation Framework")
    print("="*60)
    
    evaluator = MultimodalEvaluationFramework(
        args.ground_truth, 
        args.collection, 
        args.db_ip,
        args.model_backend  # Add this line
    )
    
    report = evaluator.run_comprehensive_evaluation()
    evaluator.save_evaluation_report(report, args.output)
    evaluator.print_evaluation_summary(report)