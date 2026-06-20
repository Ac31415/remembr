"""
Automatic Ground Truth Labeling System
Extracts and labels sound sources and visual objects from Webots world file
"""

import re
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
import xml.etree.ElementTree as ET

class GroundTruthLabeler:
    """Extract ground truth labels from Webots world file and simulation data"""
    
    def __init__(self, world_file_path: str, sound_controller_path: str = None):
        self.world_file_path = Path(world_file_path)
        self.sound_controller_path = Path(sound_controller_path) if sound_controller_path else None
        
        # Sound type mappings
        self.sound_type_keywords = {
            'church_bell': ['church', 'bell', 'Church'],
            'ambient': ['city', 'ambience', 'ambient', 'playground'],
            'car_sound': ['car', 'horn', 'honk', 'vehicle'],
            'crash': ['crash', 'collision'],
            'help_sound': ['scream', 'help', 'gurgled'],
            'nature': ['wind', 'water', 'bird', 'forest'],
            'human': ['voice', 'talk', 'speak', 'conversation'],
            # NEW: Ambulance siren classification
            'ambulance_siren': ['ambulance', 'siren', 'emergency', 'medical']
        }
        
        # Visual object type mappings
        self.visual_object_keywords = {
            'building': ['Building', 'House', 'Church', 'Warehouse', 'Tower', 'Restaurant'],
            'vehicle': ['Simple', 'Car', 'Bus', 'Truck', 'Lincoln', 'Toyota', 'Tesla'],
            'furniture': ['Bench', 'Chair', 'Table', 'Bin', 'Trash', 'Mailbox'],
            'nature': ['Tree', 'Cypress', 'Palm', 'Sassafras', 'Pine'],
            'infrastructure': ['Road', 'TrafficLight', 'StreetLight', 'BusStop', 'Fence'],
            'playground': ['Swing', 'Slide', 'Fountain'],
            'robot': ['Pioneer3at', 'Pioneer']
        }
        
        self.ground_truth_data = {
            'sound_sources': [],
            'visual_objects': [],
            'areas': []
        }
        
        # Map speaker names to their Pose DEF names for easier lookup
        self.speaker_pose_mapping = {}
        self._build_speaker_mapping()
        
    def _build_speaker_mapping(self):
        """Build mapping from speaker names to their parent Pose DEF names"""
        if not self.world_file_path.exists():
            print(f"⚠️ World file not found: {self.world_file_path}")
            return
            
        try:
            with open(self.world_file_path, 'r') as f:
                content = f.read()
            
            print(f"[Debug] World file size: {len(content)} characters")
            
            # More robust pattern to find Pose blocks with DEF names
            # This pattern handles the nested structure better
            pose_pattern = r'DEF\s+(\w+)\s+Pose\s*\{([^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*)\}'
            pose_matches = re.findall(pose_pattern, content, re.DOTALL)
            
            print(f"[Debug] Found {len(pose_matches)} Pose blocks with DEF names")
            
            for pose_def_name, pose_content in pose_matches:
                print(f"[Debug] Checking Pose block: {pose_def_name}")
                print(f"[Debug] Content preview: {pose_content[:200]}...")
                
                # Look for Speaker with name inside this Pose block
                # More flexible pattern for Speaker name
                speaker_patterns = [
                    r'Speaker\s*\{\s*name\s+"([^"]+)"',  # Original pattern
                    r'Speaker\s*\{\s*[^}]*name\s+"([^"]+)"',  # Speaker with other fields before name
                    r'name\s+"([^"]+)"\s*[^}]*Speaker',  # name before Speaker (unlikely but possible)
                ]
                
                speaker_name = None
                for pattern in speaker_patterns:
                    speaker_match = re.search(pattern, pose_content, re.DOTALL)
                    if speaker_match:
                        speaker_name = speaker_match.group(1)
                        print(f"[Debug] Found speaker name: {speaker_name} using pattern: {pattern}")
                        break
                
                if speaker_name:
                    self.speaker_pose_mapping[speaker_name] = pose_def_name
                    print(f"📍 Mapped speaker '{speaker_name}' to Pose '{pose_def_name}'")
                else:
                    # Check if this Pose contains "Speaker" at all
                    if 'Speaker' in pose_content:
                        print(f"[Debug] Pose '{pose_def_name}' contains 'Speaker' but no name found")
                        # Show more of the content for debugging
                        print(f"[Debug] Full Speaker context: {pose_content}")
            
            print(f"🗺️ Built speaker mapping with {len(self.speaker_pose_mapping)} speakers")
            
            # If no speakers found, let's debug further
            if len(self.speaker_pose_mapping) == 0:
                print("[Debug] No speakers found. Let's check for any Speaker mentions...")
                speaker_mentions = re.findall(r'Speaker[^}]*\}', content, re.DOTALL)
                print(f"[Debug] Found {len(speaker_mentions)} Speaker mentions in file")
                for i, mention in enumerate(speaker_mentions[:3]):  # Show first 3
                    print(f"[Debug] Speaker mention {i+1}: {mention}")
                
                # Check for DEF Pose blocks specifically
                def_poses = re.findall(r'DEF\s+\w+\s+Pose', content)
                print(f"[Debug] Found {len(def_poses)} DEF Pose blocks: {def_poses[:10]}")
                
        except Exception as e:
            print(f"Error building speaker mapping: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_sound_sources_from_controller(self) -> List[Dict]:
        """Extract sound source information from controller file"""
        if not self.sound_controller_path or not self.sound_controller_path.exists():
            print("⚠️ Sound controller file not found, using default sound mappings")
            return []
            
        sound_sources = []
        
        try:
            with open(self.sound_controller_path, 'r') as f:
                content = f.read()
            
            # Extract SoundSource definitions from the controller
            # Look for SoundSource instantiations in the controller
            pattern = r'SoundSource\s*\(\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"[^)]*\)'
            matches = re.findall(pattern, content)
            
            print(f"[Debug] Found {len(matches)} SoundSource definitions in controller")
            
            for speaker_name, sound_file, sound_type in matches:
                print(f"[Debug] Processing SoundSource: {speaker_name}")
                
                # Extract coordinates from world file for this speaker
                coords = self.find_speaker_coordinates(speaker_name)
                
                # Classify sound type
                classified_type = self.classify_sound_type(sound_file, sound_type)
                
                sound_source = {
                    'speaker_name': speaker_name,
                    'sound_file': sound_file,
                    'sound_type': sound_type,
                    'classified_type': classified_type,
                    'position': coords,
                    'description': self.generate_sound_description(classified_type, sound_file)
                }
                
                sound_sources.append(sound_source)
                
        except Exception as e:
            print(f"Error extracting sound sources: {e}")
            import traceback
            traceback.print_exc()
            
        return sound_sources
    
    def find_speaker_coordinates(self, speaker_name: str) -> List[float]:
        """Find speaker coordinates in world file using the speaker mapping"""
        try:
            # First, check if we have a mapping for this speaker
            if speaker_name not in self.speaker_pose_mapping:
                print(f"⚠️ No mapping found for speaker: {speaker_name}")
                print(f"[Debug] Available mappings: {list(self.speaker_pose_mapping.keys())}")
                return [0.0, 0.0, 0.0]
            
            pose_def_name = self.speaker_pose_mapping[speaker_name]
            
            with open(self.world_file_path, 'r') as f:
                content = f.read()
            
            # Look for the Pose definition and extract translation
            # More flexible pattern to handle variations in spacing/formatting
            pattern = rf'DEF\s+{re.escape(pose_def_name)}\s+Pose\s*\{{\s*translation\s+([-\d.e\s]+)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                coords_str = match.group(1).strip()
                coords = [float(x) for x in coords_str.split()]
                print(f"✅ Found coordinates for '{speaker_name}' at Pose '{pose_def_name}': {coords[:3]}")
                return coords[:3]  # x, y, z
            else:
                print(f"⚠️ Could not find translation for Pose: {pose_def_name}")
                # Let's try a more flexible search
                flex_pattern = rf'DEF\s+{re.escape(pose_def_name)}.*?translation\s+([-\d.e\s]+)'
                flex_match = re.search(flex_pattern, content, re.DOTALL)
                if flex_match:
                    coords_str = flex_match.group(1).strip()
                    coords = [float(x) for x in coords_str.split()]
                    print(f"✅ Found coordinates (flexible search) for '{speaker_name}': {coords[:3]}")
                    return coords[:3]
                else:
                    return [0.0, 0.0, 0.0]
                
        except Exception as e:
            print(f"Error finding speaker coordinates for '{speaker_name}': {e}")
            import traceback
            traceback.print_exc()
            return [0.0, 0.0, 0.0]
    
    def classify_sound_type(self, sound_file: str, declared_type: str) -> str:
        """Classify sound type based on filename and declared type"""
        sound_file_lower = sound_file.lower()
        declared_type_lower = declared_type.lower()
        
        # First check declared type
        for sound_type, keywords in self.sound_type_keywords.items():
            if any(keyword.lower() in declared_type_lower for keyword in keywords):
                return sound_type
        
        # Then check filename
        for sound_type, keywords in self.sound_type_keywords.items():
            if any(keyword.lower() in sound_file_lower for keyword in keywords):
                return sound_type
        
        return declared_type
    
    def generate_sound_description(self, sound_type: str, sound_file: str) -> str:
        """Generate human-readable description for sound"""
        filename = Path(sound_file).name
        
        descriptions = {
            'church_bell': f"Church bell ringing sound from {filename}",
            'ambient': f"City ambient background sounds from {filename}",
            'car_sound': f"Car horn or vehicle sound from {filename}",
            'crash': f"Crash or collision sound from {filename}",
            'help_sound': f"Human distress or help sound from {filename}",
            'nature': f"Natural environment sound from {filename}",
            'human': f"Human voice or conversation from {filename}",
            # NEW: Ambulance siren description
            'ambulance_siren': f"Ambulance siren or emergency vehicle sound from {filename}"
        }
        
        return descriptions.get(sound_type, f"Audio sound of type {sound_type} from {filename}")
    
    def extract_visual_objects_from_world(self) -> List[Dict]:
        """Extract visual object information from world file"""
        visual_objects = []
        
        try:
            with open(self.world_file_path, 'r') as f:
                content = f.read()
            
            # Extract object definitions with positions
            patterns = [
                # Pattern for objects with translation
                r'(\w+)\s*\{\s*translation\s+([-\d.e\s]+)[^}]*?\}',
                # Pattern for DEF objects
                r'DEF\s+(\w+)\s+(\w+)\s*\{\s*translation\s+([-\d.e\s]+)[^}]*?\}'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                
                for match in matches:
                    if len(match) == 2:  # First pattern
                        object_type, coords_str = match
                        object_name = object_type
                    else:  # Second pattern
                        object_name, object_type, coords_str = match
                    
                    # Skip speaker Poses as they're handled separately
                    if object_name in self.speaker_pose_mapping.values():
                        continue
                    
                    # Parse coordinates
                    try:
                        coords = [float(x) for x in coords_str.strip().split()]
                        position = coords[:3] if len(coords) >= 3 else [0.0, 0.0, 0.0]
                    except:
                        continue
                    
                    # Classify object type
                    classified_type = self.classify_visual_object(object_type)
                    
                    if classified_type != 'unknown':
                        visual_object = {
                            'name': object_name,
                            'type': object_type,
                            'classified_type': classified_type,
                            'position': position,
                            'description': self.generate_visual_description(classified_type, object_type, object_name)
                        }
                        
                        visual_objects.append(visual_object)
                        
        except Exception as e:
            print(f"Error extracting visual objects: {e}")
            
        return visual_objects
    
    def classify_visual_object(self, object_type: str) -> str:
        """Classify visual object type"""
        for category, keywords in self.visual_object_keywords.items():
            if any(keyword in object_type for keyword in keywords):
                return category
        return 'unknown'
    
    def generate_visual_description(self, classified_type: str, object_type: str, object_name: str) -> str:
        """Generate human-readable description for visual object"""
        descriptions = {
            'building': f"Building structure: {object_type}",
            'vehicle': f"Vehicle: {object_type}",
            'furniture': f"Street furniture: {object_type}",
            'nature': f"Natural element: {object_type}",
            'infrastructure': f"Infrastructure: {object_type}",
            'playground': f"Playground equipment: {object_type}",
            'robot': f"Robot: {object_type}"
        }
        
        base_desc = descriptions.get(classified_type, f"Object: {object_type}")
        if object_name != object_type:
            base_desc += f" named {object_name}"
        
        return base_desc
    
    def create_spatial_areas(self) -> List[Dict]:
        """Create spatial area definitions based on object clustering"""
        areas = []
        
        # Define known areas based on typical urban layout
        area_definitions = [
            {
                'name': 'Church Area',
                'center': [-183.9, 86.2, 0],
                'radius': 50,
                'description': 'Area around the church with religious buildings'
            },
            {
                'name': 'Residential District',
                'center': [-250, 150, 0],
                'radius': 100,
                'description': 'Residential area with houses and suburban buildings'
            },
            {
                'name': 'Commercial District',
                'center': [300, 250, 0],
                'radius': 80,
                'description': 'Commercial area with businesses and warehouses'
            },
            {
                'name': 'Industrial Zone',
                'center': [-250, -200, 0],
                'radius': 70,
                'description': 'Industrial area with warehouses and windmills'
            },
            {
                'name': 'Playground Area',
                'center': [50, 120, 0],
                'radius': 40,
                'description': 'Recreation area with playground equipment and parks'
            }
        ]
        
        return area_definitions
    
    def generate_ground_truth(self) -> Dict:
        """Generate complete ground truth data"""
        print("🏷️ Generating ground truth labels...")
        
        # Extract sound sources
        print("  📢 Extracting sound sources...")
        sound_sources = self.extract_sound_sources_from_controller()
        
        # Extract visual objects
        print("  👁️ Extracting visual objects...")
        visual_objects = self.extract_visual_objects_from_world()
        
        # Create spatial areas
        print("  🗺️ Creating spatial areas...")
        areas = self.create_spatial_areas()
        
        self.ground_truth_data = {
            'sound_sources': sound_sources,
            'visual_objects': visual_objects,
            'areas': areas,
            'speaker_mapping': self.speaker_pose_mapping,  # Include mapping for reference
            'metadata': {
                'world_file': str(self.world_file_path),
                'sound_controller': str(self.sound_controller_path) if self.sound_controller_path else None,
                'num_sound_sources': len(sound_sources),
                'num_visual_objects': len(visual_objects),
                'num_areas': len(areas),
                'num_speakers_mapped': len(self.speaker_pose_mapping)
            }
        }
        
        print(f"✅ Ground truth generated:")
        print(f"   📢 {len(sound_sources)} sound sources")
        print(f"   👁️ {len(visual_objects)} visual objects") 
        print(f"   🗺️ {len(areas)} spatial areas")
        print(f"   🔊 {len(self.speaker_pose_mapping)} speakers mapped")
        
        return self.ground_truth_data
    
    def save_ground_truth(self, output_path: str):
        """Save ground truth data to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.ground_truth_data, f, indent=2)
        
        print(f"💾 Ground truth saved to: {output_file}")
    
    def load_ground_truth(self, input_path: str) -> Dict:
        """Load ground truth data from JSON file"""
        with open(input_path, 'r') as f:
            self.ground_truth_data = json.load(f)
        
        print(f"📖 Ground truth loaded from: {input_path}")
        return self.ground_truth_data

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate ground truth labels')
    parser.add_argument('--world-file', required=True, help='Path to Webots world file')
    parser.add_argument('--sound-controller', help='Path to sound controller file')
    parser.add_argument('--output', '-o', default='ground_truth.json', help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    print("🏷️ Automatic Ground Truth Labeling System")
    print("="*50)
    
    labeler = GroundTruthLabeler(args.world_file, args.sound_controller)
    ground_truth = labeler.generate_ground_truth()
    labeler.save_ground_truth(args.output)
    
    print(f"\n📋 Summary:")
    print(f"   World file: {args.world_file}")
    print(f"   Sound controller: {args.sound_controller}")
    print(f"   Output: {args.output}")
    
    # Display the speaker mappings for verification
    if labeler.speaker_pose_mapping:
        print(f"\n🔊 Speaker Mappings:")
        for speaker_name, pose_def in labeler.speaker_pose_mapping.items():
            coords = labeler.find_speaker_coordinates(speaker_name)
            print(f"   {speaker_name} → {pose_def} @ {coords}")
    else:
        print(f"\n⚠️ No speaker mappings found!")
        print(f"   This indicates the regex patterns need further adjustment")
        print(f"   Check the debug output above for more details")