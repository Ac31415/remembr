#!/Users/wen-chungcheng/anaconda3/envs/Webots-Sim/bin/python

"""
Spatially-Aware Sound Controller
Dynamically adjusts sound volume and stereo positioning based on robot location.
Uses ground truth data for sound source positions and real-time robot positioning.
"""

import json
import time
import math
import random
import sys
import os
from pathlib import Path
# Remove this line:
# from controller import Robot, Speaker, Supervisor, Keyboard
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Add these imports for standalone audio playback
import subprocess
import threading

class SpatialSoundSource:
    """Sound source with spatial audio capabilities"""
    
    def __init__(self, speaker_name: str, sound_file: str, position: List[float], 
                 sound_type: str = "ambient", enabled: bool = False, **kwargs):
        self.speaker_name = speaker_name
        self.sound_file = sound_file
        self.position = np.array(position[:3])  # x, y, z coordinates
        self.sound_type = sound_type
        self.enabled = enabled
        self.speaker = None
        
        # Audio parameters
        self.base_volume = kwargs.get('volume', 0.5)
        self.max_audible_distance = kwargs.get('max_distance', 100.0)  # Maximum hearing distance
        self.min_volume = kwargs.get('min_volume', 0.01)  # Minimum volume before silence
        self.distance_falloff = kwargs.get('distance_falloff', 2.0)  # Distance attenuation factor
        
        # Timing parameters based on sound type
        self._set_timing_parameters(**kwargs)
        
        # State tracking
        self.is_playing = False
        self.sound_start_time = 0
        self.next_sound_time = time.time() + random.uniform(1.0, 10.0)
        self.play_count = 0
        self.last_volume = 0.0
        self.last_balance = 0.0
        
        # Sound type emoji for display
        self.emoji = {
            "church_bell": "🔔", "ambient": "🏙️", "car_sound": "🚗",
            "help_sound": "🆘", "crash": "💥", "ambulance_siren": "🚑",
            "nature": "🌿", "human": "👥"
        }.get(sound_type, "🔊")
    
    def _set_timing_parameters(self, **kwargs):
        """Set timing parameters based on sound type"""
        timing_configs = {
            "church_bell": {"min_interval": 30.0, "max_interval": 120.0, "duration": 10.0},
            "ambient": {"min_interval": 0.5, "max_interval": 2.0, "duration": 30.0},
            "car_sound": {"min_interval": 5.0, "max_interval": 15.0, "duration": 3.0},
            "help_sound": {"min_interval": 20.0, "max_interval": 60.0, "duration": 5.0},
            "ambulance_siren": {"min_interval": 10.0, "max_interval": 30.0, "duration": 15.0},
            "crash": {"min_interval": 15.0, "max_interval": 45.0, "duration": 2.0},
            "nature": {"min_interval": 2.0, "max_interval": 8.0, "duration": 20.0},
            "human": {"min_interval": 10.0, "max_interval": 30.0, "duration": 8.0}
        }
        
        config = timing_configs.get(self.sound_type, {"min_interval": 1.0, "max_interval": 5.0, "duration": 5.0})
        self.min_interval = kwargs.get('min_interval', config['min_interval'])
        self.max_interval = kwargs.get('max_interval', config['max_interval'])
        self.estimated_duration = kwargs.get('estimated_duration', config['duration'])
    
    def calculate_spatial_audio(self, robot_position: np.ndarray, robot_heading: float) -> Tuple[float, float]:
        """
        Calculate volume and stereo balance based on robot position and orientation
        
        Args:
            robot_position: Robot's [x, y, z] position
            robot_heading: Robot's heading in radians
            
        Returns:
            Tuple of (volume, balance) where:
            - volume: 0.0 to base_volume based on distance
            - balance: -1.0 (left) to 1.0 (right) based on relative direction
        """
        # Calculate distance vector
        distance_vector = self.position - robot_position
        distance_2d = np.linalg.norm(distance_vector[:2])  # Only x, y for 2D distance
        distance_3d = np.linalg.norm(distance_vector)      # Full 3D distance
        
        # Calculate volume based on distance with falloff
        if distance_2d > self.max_audible_distance:
            volume = 0.0
        else:
            # Use inverse square law with configurable falloff
            distance_factor = 1.0 / (1.0 + (distance_2d / 10.0) ** self.distance_falloff)
            volume = self.base_volume * distance_factor
            
            # Apply minimum volume threshold
            if volume < self.min_volume:
                volume = 0.0
        
        # Calculate stereo balance based on relative angle
        balance = 0.0
        if distance_2d > 0.1:  # Avoid division by zero for very close sounds
            # Calculate angle from robot to sound source
            sound_angle = math.atan2(distance_vector[1], distance_vector[0])
            
            # Calculate relative angle considering robot's heading
            relative_angle = sound_angle - robot_heading
            
            # Normalize angle to [-π, π]
            while relative_angle > math.pi:
                relative_angle -= 2 * math.pi
            while relative_angle < -math.pi:
                relative_angle += 2 * math.pi
            
            # Convert to stereo balance (-1.0 to 1.0)
            # Sounds directly in front/behind have balance = 0
            # Sounds to the right have positive balance, left have negative
            balance = math.sin(relative_angle)
            
            # Limit balance to reasonable range
            balance = max(-1.0, min(1.0, balance))
        
        return volume, balance
    
    def initialize_speaker(self, robot=None) -> bool:
        """Initialize the speaker device - standalone version"""
        # Check if sound file exists
        if Path(self.sound_file).exists():
            print(f"✓ Sound file found: {self.speaker_name} at {self.position}")
            return True
        else:
            print(f"⚠️ Sound file not found: {self.sound_file}")
            return False
    
    def should_play(self, current_time: float) -> bool:
        """Check if it's time to play this sound"""
        return self.enabled and current_time >= self.next_sound_time
    
    def play_spatial_sound(self, volume: float, balance: float) -> bool:
        """Play sound with spatial audio parameters using system audio"""
        if not self.enabled or not Path(self.sound_file).exists():
            return False
        
        if volume <= 0.0:
            return False  # Don't play if volume is zero
        
        try:
            # Store last used parameters for debugging
            self.last_volume = volume
            self.last_balance = balance
            
            print(f"🎵 {self.emoji} {self.sound_type}: vol={volume:.3f}, bal={balance:.3f}, pos={self.position[:2]}")
            
            # Use system audio to play the sound
            # On macOS, use afplay with volume control
            cmd = ['afplay', self.sound_file, '-v', str(volume)]
            
            # Play in background thread so it doesn't block
            def play_audio():
                try:
                    subprocess.run(cmd, capture_output=True)
                except Exception as e:
                    print(f"Error playing audio: {e}")
            
            threading.Thread(target=play_audio, daemon=True).start()
            
            self.is_playing = True
            self.sound_start_time = time.time()
            self.play_count += 1
            return True
            
        except Exception as e:
            print(f"❌ Error playing spatial sound {self.sound_file}: {e}")
            return False
    
    def schedule_next(self, current_time: float):
        """Schedule the next sound playback"""
        if self.sound_type == "ambient":
            interval = random.uniform(self.min_interval, self.max_interval)
            self.next_sound_time = current_time + self.estimated_duration + interval
        else:
            interval = random.uniform(self.min_interval, self.max_interval)
            self.next_sound_time = current_time + interval
    
    def update_playing_state(self, current_time: float):
        """Update the playing state based on estimated duration"""
        if self.is_playing and (current_time - self.sound_start_time) > self.estimated_duration:
            self.is_playing = False
    
    def get_status_info(self, robot_position: np.ndarray) -> Dict[str, Any]:
        """Get detailed status information for debugging"""
        distance = np.linalg.norm(self.position[:2] - robot_position[:2])
        return {
            'speaker_name': self.speaker_name,
            'sound_type': self.sound_type,
            'position': self.position.tolist(),
            'distance': distance,
            'enabled': self.enabled,
            'is_playing': self.is_playing,
            'play_count': self.play_count,
            'last_volume': self.last_volume,
            'last_balance': self.last_balance
        }


class SpatiallyAwareSoundController:
    """Main controller for spatially-aware sound management"""
    
    def __init__(self, ground_truth_file: str = None, config_file: str = None):
        # Remove all Webots robot initialization
        # Add robot status file path
        self.robot_status_file = Path("/tmp/webots_memory/robot_status.json")
        
        # Initialize position tracking
        self.last_position = np.array([0.0, 0.0, 0.0])
        self.last_heading = 0.0
        self.position_update_time = 0.0
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Load ground truth data for sound source positions
        self.ground_truth_data = self.load_ground_truth(ground_truth_file)
        
        # Create spatial sound sources
        self.spatial_sources = self.create_spatial_sources()
        
        # Initialize all spatial sources (no robot parameter needed)
        self.active_sources = []
        for source in self.spatial_sources:
            if source.initialize_speaker():  # Remove robot parameter
                self.active_sources.append(source)
        
        # Control state
        self.spatial_audio_enabled = True
        self.debug_mode = False
        
        # Status reporting
        self.status_update_interval = 2.0
        self.last_status_time = 0
        
        print(f"\n🎯 Spatially-Aware Sound Controller initialized (standalone mode)")
        print(f"🔊 Managing {len(self.active_sources)} spatial sound sources")
        self.print_controls()
        self.print_source_summary()
    
    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration settings"""
        default_config = {
            'max_audible_distance': 100.0,
            'distance_falloff': 2.0,
            'min_volume': 0.01,
            'volume_multiplier': 1.0,
            'enable_3d_audio': True,
            'debug_output': False
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                config = {**default_config, **user_config}
                print(f"📋 Loaded spatial audio config from: {config_file}")
                return config
            except Exception as e:
                print(f"⚠️ Error loading config, using defaults: {e}")
        
        return default_config
    
    def load_ground_truth(self, ground_truth_file: str = None) -> Dict[str, Any]:
        """Load ground truth data containing sound source positions"""
        if not ground_truth_file:
            # Try to find ground truth file in common locations
            possible_paths = [
                "/tmp/webots_memory/ground_truth.json",
                "./ground_truth.json",
                "../ground_truth.json"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    ground_truth_file = path
                    break
        
        if ground_truth_file and Path(ground_truth_file).exists():
            try:
                with open(ground_truth_file, 'r') as f:
                    data = json.load(f)
                print(f"📍 Loaded ground truth data from: {ground_truth_file}")
                return data
            except Exception as e:
                print(f"⚠️ Error loading ground truth data: {e}")
        
        print("⚠️ No ground truth data available - using default positions")
        return {'sound_sources': []}
    
    def create_spatial_sources(self) -> List[SpatialSoundSource]:
        """Create spatial sound sources from ground truth data and fallback defaults"""
        spatial_sources = []
        
        # Try to load from ground truth first
        if self.ground_truth_data and 'sound_sources' in self.ground_truth_data:
            print("🗺️ Creating spatial sources from ground truth data...")
            
            for source_data in self.ground_truth_data['sound_sources']:
                try:
                    spatial_source = SpatialSoundSource(
                        speaker_name=source_data['speaker_name'],
                        sound_file=source_data['sound_file'],
                        position=source_data['position'],
                        sound_type=source_data.get('classified_type', source_data.get('sound_type', 'ambient')),
                        enabled=False,  # Start disabled
                        max_distance=self.config['max_audible_distance'],
                        distance_falloff=self.config['distance_falloff'],
                        min_volume=self.config['min_volume']
                    )
                    spatial_sources.append(spatial_source)
                    print(f"  ✓ {spatial_source.emoji} {source_data['speaker_name']} at {source_data['position'][:2]}")
                    
                except Exception as e:
                    print(f"  ❌ Error creating spatial source {source_data.get('speaker_name', 'unknown')}: {e}")
        
        # Fallback to default sources if no ground truth available
        if not spatial_sources:
            print("🔄 Creating default spatial sources...")
            spatial_sources = self.create_default_spatial_sources()
        
        return spatial_sources
    
    def create_default_spatial_sources(self) -> List[SpatialSoundSource]:
        """Create default spatial sound sources with estimated positions"""
        default_sources = [
            # Church Bell (estimated position)
            SpatialSoundSource(
                "church_bell_speaker",
                "/Users/wen-chungcheng/Downloads/ambient sounds/church-bell-273815.wav",
                [-183.9, 86.2, 5.0],  # Estimated church position
                "church_bell",
                max_distance=150.0  # Church bells carry far
            ),
            
            # City Ambient Sounds (distributed positions)
            SpatialSoundSource(
                "city_amb_speaker_1",
                "/Users/wen-chungcheng/Downloads/ambient sounds/city-ambience-9272.wav",
                [-100.0, 50.0, 1.0],
                "ambient"
            ),
            SpatialSoundSource(
                "city_amb_speaker_2",
                "/Users/wen-chungcheng/Downloads/ambient sounds/city-ambience-9265.wav",
                [100.0, 150.0, 1.0],
                "ambient"
            ),
            
            # Car Sounds (road positions)
            SpatialSoundSource(
                "car_honk_speaker_1",
                "/Users/wen-chungcheng/Downloads/car sounds/car-horn-6408.wav",
                [50.0, 0.0, 1.0],
                "car_sound"
            ),
            SpatialSoundSource(
                "car_honk_speaker_2",
                "/Users/wen-chungcheng/Downloads/car sounds/double-car-horn-352443.wav",
                [-50.0, 100.0, 1.0],
                "car_sound"
            ),
            
            # Help Sounds (various positions)
            SpatialSoundSource(
                "help_sound_speaker_1",
                "/Users/wen-chungcheng/Downloads/help sounds/759456__akridiy__a-single-scream-of-a-young-male.wav",
                [25.0, 75.0, 1.0],
                "help_sound"
            ),
            SpatialSoundSource(
                "help_sound_speaker_2",
                "/Users/wen-chungcheng/Downloads/help sounds/402861__jacksonacademyashmore__gurgled-scream.wav",
                [-75.0, 25.0, 1.0],
                "help_sound"
            ),
            
            # Ambulance Sirens (emergency routes)
            SpatialSoundSource(
                "ambulance_speaker_1",
                "/Users/wen-chungcheng/Downloads/ambulance siren sounds/siren-passing-275127.wav",
                [200.0, 50.0, 1.0],
                "ambulance_siren"
            ),
            SpatialSoundSource(
                "ambulance_speaker_2",
                "/Users/wen-chungcheng/Downloads/ambulance siren sounds/ambulance-6399.wav",
                [-200.0, 150.0, 1.0],
                "ambulance_siren"
            ),
        ]
        
        print(f"📍 Created {len(default_sources)} default spatial sources")
        return default_sources
    
    def get_robot_position(self) -> np.ndarray:
        """Get current robot position from status file"""
        try:
            if self.robot_status_file.exists():
                with open(self.robot_status_file, 'r') as f:
                    status = json.load(f)
                
                position = status.get('position', [0.0, 0.0, 0.0])
                self.last_position = np.array([float(position[0]), float(position[1]), float(position[2])])
                self.position_update_time = status.get('timestamp', time.time())
                
                return self.last_position
            else:
                print("⚠️ Robot status file not found - using last known position")
                return self.last_position
                
        except Exception as e:
            print(f"Error reading robot position: {e}")
            return self.last_position
    
    def get_robot_heading(self) -> float:
        """Get current robot heading from status file"""
        try:
            if self.robot_status_file.exists():
                with open(self.robot_status_file, 'r') as f:
                    status = json.load(f)
                
                self.last_heading = float(status.get('orientation', 0.0))
                return self.last_heading
            else:
                return self.last_heading
                
        except Exception as e:
            print(f"Error reading robot heading: {e}")
            return self.last_heading
    
    def print_controls(self):
        """Print keyboard controls"""
        print("\n🎮 Spatial Audio Controls (Standalone Mode):")
        print("="*50)
        print("  Type commands and press Enter:")
        print("  'space' - Toggle spatial audio on/off")
        print("  '1'-'9' - Toggle individual sound sources")
        print("  'e'     - Enable all sources")
        print("  'x'     - Disable all sources")
        print("  'd'     - Toggle debug mode")
        print("  's'     - Show detailed status")
        print("  'r'     - Reset all sources")
        print("  'q'     - Quit")
        print("="*50)
    
    def print_source_summary(self):
        """Print summary of spatial sound sources"""
        print(f"\n🔊 Spatial Sound Sources ({len(self.active_sources)} active):")
        print("="*60)
        for i, source in enumerate(self.active_sources, 1):
            status = "🟢" if source.enabled else "🔴"
            pos_str = f"({source.position[0]:.1f}, {source.position[1]:.1f})"
            print(f"  {i}. {status} {source.emoji} {source.sound_type} at {pos_str}")
    
    def process_keyboard_input(self) -> bool:
        """Process console input for spatial audio control"""
        try:
            # Use non-blocking input check
            import select
            import sys
            
            # Check if input is available (Unix/Mac only)
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                key_input = sys.stdin.readline().strip().lower()
                
                if key_input == 'q':
                    print("👋 Quitting spatial sound controller...")
                    return False
                elif key_input in ['space', ' ']:
                    self.spatial_audio_enabled = not self.spatial_audio_enabled
                    status = "enabled" if self.spatial_audio_enabled else "disabled"
                    print(f"🔄 Spatial audio {status}")
                elif key_input == 'd':
                    self.debug_mode = not self.debug_mode
                    status = "enabled" if self.debug_mode else "disabled"
                    print(f"🐛 Debug mode {status}")
                elif key_input == 's':
                    self.print_detailed_status()
                elif key_input == 'e':
                    for source in self.active_sources:
                        source.enabled = True
                    print("🟢 All spatial sources enabled")
                elif key_input == 'x':
                    for source in self.active_sources:
                        source.enabled = False
                    print("🔴 All spatial sources disabled")
                elif key_input == 'r':
                    self.reset_all_sources()
                elif key_input.isdigit() and 1 <= int(key_input) <= 9:
                    source_index = int(key_input) - 1
                    if source_index < len(self.active_sources):
                        source = self.active_sources[source_index]
                        source.enabled = not source.enabled
                        status = "enabled" if source.enabled else "disabled"
                        print(f"🔄 {source.emoji} {source.sound_type}: {status}")
        except:
            pass  # Ignore input errors in standalone mode
        
        return True
    
    def reset_all_sources(self):
        """Reset timing for all sound sources"""
        current_time = time.time()
        for source in self.active_sources:
            source.next_sound_time = current_time + random.uniform(1.0, 10.0)
            source.is_playing = False
        print("🔄 All spatial sources reset")
    
    def print_detailed_status(self):
        """Print detailed status of all sources"""
        robot_pos = self.get_robot_position()
        
        print(f"\n📊 Detailed Spatial Audio Status:")
        print(f"🤖 Robot position: ({robot_pos[0]:.2f}, {robot_pos[1]:.2f}, {robot_pos[2]:.2f})")
        print(f"🧭 Robot heading: {math.degrees(self.get_robot_heading()):.1f}°")
        print(f"🔊 Spatial audio: {'enabled' if self.spatial_audio_enabled else 'disabled'}")
        print("="*80)
        
        for i, source in enumerate(self.active_sources, 1):
            status_info = source.get_status_info(robot_pos)
            volume, balance = source.calculate_spatial_audio(robot_pos, self.get_robot_heading())
            
            print(f"{i:2d}. {source.emoji} {source.sound_type}")
            print(f"    Position: ({status_info['position'][0]:.1f}, {status_info['position'][1]:.1f})")
            print(f"    Distance: {status_info['distance']:.1f}m")
            print(f"    Volume: {volume:.3f} | Balance: {balance:.3f}")
            print(f"    Status: {'🟢 ON' if status_info['enabled'] else '🔴 OFF'} | "
                  f"Playing: {'🎵 YES' if status_info['is_playing'] else '⏸️ NO'} | "
                  f"Played: {status_info['play_count']}x")
    
    def update_spatial_audio(self):
        """Update spatial audio for all active sources"""
        if not self.spatial_audio_enabled:
            return
        
        # Get current robot state from status file
        robot_position = self.get_robot_position()
        robot_heading = self.get_robot_heading()
        
        # Check if position data is recent (within last 5 seconds)
        current_time = time.time()
        if current_time - self.position_update_time > 5.0:
            if self.debug_mode:
                print(f"⚠️ Robot position data is stale ({current_time - self.position_update_time:.1f}s old)")
        
        # Update last known position and heading
        self.last_position = robot_position
        self.last_heading = robot_heading
        
        current_time = time.time()
        
        # Process each active source
        for source in self.active_sources:
            # Update playing state
            source.update_playing_state(current_time)
            
            # Check if it's time to play
            if source.should_play(current_time):
                # Calculate spatial audio parameters
                volume, balance = source.calculate_spatial_audio(robot_position, robot_heading)
                
                # Apply global volume multiplier
                volume *= self.config['volume_multiplier']
                
                # Play sound with spatial parameters
                if source.play_spatial_sound(volume, balance):
                    source.schedule_next(current_time)
        
        # Periodic status updates in debug mode
        if self.debug_mode and (current_time - self.last_status_time) > self.status_update_interval:
            self.print_debug_info(robot_position, robot_heading)
            self.last_status_time = current_time
    
    def print_debug_info(self, robot_position: np.ndarray, robot_heading: float):
        """Print debug information"""
        playing_sources = [s for s in self.active_sources if s.is_playing]
        
        if playing_sources:
            print(f"\n🐛 Debug: Robot at ({robot_position[0]:.1f}, {robot_position[1]:.1f}), "
                  f"heading {math.degrees(robot_heading):.1f}°")
            
            for source in playing_sources:
                volume, balance = source.calculate_spatial_audio(robot_position, robot_heading)
                distance = np.linalg.norm(source.position[:2] - robot_position[:2])
                print(f"  🎵 {source.emoji} {source.sound_type}: "
                      f"dist={distance:.1f}m, vol={volume:.3f}, bal={balance:.3f}")
    
    def run(self):
        """Main control loop - standalone version"""
        if not self.active_sources:
            print("❌ No active spatial sound sources available")
            return
        
        print("🎯 Spatially-Aware Sound Controller running (standalone mode)...")
        print("🔊 Sounds will adjust based on robot position from status file")
        print("💡 Type commands and press Enter:")
        print("   q=quit, space=toggle audio, d=debug, s=status, e=enable all, x=disable all, r=reset, 1-9=toggle source")
        
        try:
            while True:
                # Process console input
                if not self.process_keyboard_input():
                    break
                
                # Update spatial audio
                self.update_spatial_audio()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⏹️ Spatial sound controller stopped by user")
        except Exception as e:
            print(f"❌ Error in spatial sound controller: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔇 Spatial sound controller stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Spatially-Aware Sound Controller')
    parser.add_argument('--ground-truth', '-g', 
                       help='Path to ground truth JSON file with sound source positions')
    parser.add_argument('--config', '-c',
                       help='Path to spatial audio configuration file')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("🎯 Spatially-Aware Sound Controller")
    print("="*50)
    
    controller = SpatiallyAwareSoundController(
        ground_truth_file=args.ground_truth,
        config_file=args.config
    )
    
    if args.debug:
        controller.debug_mode = True
        print("🐛 Debug mode enabled")
    
    controller.run()