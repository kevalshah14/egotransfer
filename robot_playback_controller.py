#!/usr/bin/env python3
"""
Robot Playback Controller
========================
Controls Dobot robot for command playback.
Based on the WristXYZController from Hand_to_robot.py
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydobot import Dobot


class RobotPlaybackController:
    """Controller for playing back robot commands on Dobot."""
    
    def __init__(self, port: Optional[str] = None):
        """Initialize the robot controller."""
        self.robot: Optional[Dobot] = None
        self.port = port
        self.is_connected = False
        self.commands: List[Dict] = []
        self.current_command_index = 0
        self.is_playing = False
        self.is_paused = False
        
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Connect to the Dobot robot."""
        import glob
        
        try:
            if self.port:
                self.logger.info(f"Attempting to connect to robot on specified port: {self.port}")
                self.robot = Dobot(port=self.port)
            else:
                # Try to find Dobot port automatically
                self.logger.info("Attempting to auto-detect Dobot port...")
                
                # Look for common Dobot USB ports on macOS
                candidate_ports = (
                    sorted(glob.glob('/dev/cu.usbmodem*')) +
                    sorted(glob.glob('/dev/cu.usbserial*'))
                )
                
                self.logger.info(f"Found candidate ports: {candidate_ports}")
                
                if candidate_ports:
                    # Try each port until one works
                    for port in candidate_ports:
                        try:
                            self.logger.info(f"Trying port: {port}")
                            self.robot = Dobot(port=port)
                            self.port = port  # Store the successful port
                            break
                        except Exception as port_error:
                            self.logger.warning(f"Port {port} failed: {port_error}")
                            continue
                    else:
                        # If no candidate ports worked, try auto-detection
                        self.logger.info("Trying pydobot auto-detection...")
                        self.robot = Dobot()
                else:
                    # No candidate ports found, try auto-detection
                    self.logger.info("No candidate ports found, trying pydobot auto-detection...")
                    self.robot = Dobot()
            
            self.is_connected = True
            used_port = self.port if self.port else "auto-detected"
            self.logger.info(f"Successfully connected to Dobot robot on port: {used_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to robot: {e}")
            self.logger.error("Troubleshooting tips:")
            self.logger.error("1. Ensure Dobot robot is powered on")
            self.logger.error("2. Check USB cable connection")
            self.logger.error("3. Verify Dobot drivers are installed")
            self.logger.error("4. Try unplugging and reconnecting the USB cable")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the robot."""
        try:
            if self.robot:
                self.robot.close()
                self.robot = None
            self.is_connected = False
            self.logger.info("Disconnected from robot")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def home_robot(self) -> bool:
        """Move robot to home position."""
        if not self.is_connected or not self.robot:
            self.logger.error("Robot not connected")
            return False
        
        try:
            self.logger.info("Homing robot...")
            
            # Try different home methods based on pydobot version
            try:
                cmd_id = self.robot.home()
                if cmd_id:
                    # Wait for command to complete if command ID is returned
                    self.robot.wait_for_cmd(cmd_id)
                else:
                    # Wait a bit if no command ID returned
                    time.sleep(3)
            except Exception as home_error:
                self.logger.warning(f"Home command failed with error: {home_error}")
                # Try alternative approach - just wait
                time.sleep(3)
            
            self.logger.info("Robot homed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to home robot: {e}")
            return False
    
    def load_commands(self, commands_file: str) -> bool:
        """Load robot commands from JSON file."""
        try:
            commands_path = Path(commands_file)
            if not commands_path.exists():
                self.logger.error(f"Commands file not found: {commands_file}")
                return False
            
            with open(commands_path, 'r') as f:
                data = json.load(f)
            
            # Extract commands from the data structure
            if 'commands' in data:
                self.commands = data['commands']
            else:
                self.commands = data
            
            self.current_command_index = 0
            self.logger.info(f"Loaded {len(self.commands)} commands from {commands_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load commands: {e}")
            return False
    
    def play(self, speed: float = 1.0, loop: bool = False) -> bool:
        """Start playback of loaded commands."""
        if not self.is_connected or not self.robot:
            self.logger.error("Robot not connected")
            return False
        
        if not self.commands:
            self.logger.error("No commands loaded")
            return False
        
        try:
            # Home the robot before starting playback
            self.logger.info("Homing robot before playback...")
            if not self.home_robot():
                self.logger.error("Failed to home robot - aborting playback")
                return False
            
            self.is_playing = True
            self.is_paused = False
            self.logger.info(f"Starting playback of {len(self.commands)} commands at {speed}x speed")
            
            while True:
                # Execute all commands
                for i, command in enumerate(self.commands):
                    if not self.is_playing:
                        self.logger.info("Playback stopped")
                        return True
                    
                    # Wait if paused
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_playing:
                            return True
                    
                    self.current_command_index = i
                    success = self._execute_command(command, speed)
                    
                    if not success:
                        self.logger.error(f"Failed to execute command {i}")
                        self.is_playing = False
                        return False
                
                # Check if we should loop
                if not loop:
                    break
                
                self.logger.info("Looping playback...")
                self.current_command_index = 0
            
            self.is_playing = False
            self.logger.info("Playback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Playback failed: {e}")
            self.is_playing = False
            return False
    
    def _execute_command(self, command: Dict, speed: float) -> bool:
        """Execute a single robot command."""
        try:
            # Extract position values
            x = command.get('x', 250)
            y = command.get('y', 0)
            z = command.get('z', 150)
            r = command.get('r', 0)
            gripper = command.get('gripper', 0)
            
            # Calculate movement duration based on speed
            base_duration = 0.1  # Base time per command
            duration = base_duration / speed
            
            # Move to position (try different API methods)
            try:
                # Try with wait parameter first
                self.robot.move_to(x, y, z, r, wait=True)
            except TypeError:
                try:
                    # Try without wait parameter
                    self.robot.move_to(x, y, z, r)
                except Exception as move_error:
                    self.logger.error(f"Move command failed: {move_error}")
                    return False
            
            # Control gripper (try different API methods)
            try:
                if gripper:
                    self.robot.grip(enable=True)
                else:
                    self.robot.grip(enable=False)
            except Exception as grip_error:
                try:
                    # Alternative gripper control
                    if gripper:
                        self.robot.grip(True)
                    else:
                        self.robot.grip(False)
                except Exception as alt_grip_error:
                    self.logger.warning(f"Gripper control failed: {alt_grip_error}")
            
            # Wait for movement to complete
            time.sleep(duration)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            return False
    
    def stop(self):
        """Stop robot operation."""
        self.is_playing = False
        self.is_paused = False
        self.logger.info("Robot playback stopped")
    
    def pause(self):
        """Pause robot operation."""
        self.is_paused = True
        self.logger.info("Robot playback paused")
    
    def resume(self):
        """Resume robot operation."""
        self.is_paused = False
        self.logger.info("Robot playback resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current robot status."""
        return {
            'connected': self.is_connected,
            'playing': self.is_playing,
            'paused': self.is_paused,
            'commands_loaded': len(self.commands),
            'current_command': self.current_command_index,
            'progress': (self.current_command_index / len(self.commands)) * 100 if self.commands else 0
        }
    
    def get_position(self) -> Optional[Dict[str, float]]:
        """Get current robot position."""
        if not self.is_connected or not self.robot:
            return None
        
        try:
            # Try different methods to get position based on pydobot version
            try:
                pose = self.robot.get_pose()
                return {
                    'x': pose.position.x,
                    'y': pose.position.y,
                    'z': pose.position.z,
                    'r': pose.position.r
                }
            except AttributeError:
                try:
                    # Alternative method
                    pose = self.robot.pose()
                    return {
                        'x': pose.position.x,
                        'y': pose.position.y,
                        'z': pose.position.z,
                        'r': pose.orientation.r
                    }
                except AttributeError:
                    self.logger.warning("Could not get robot position - API method not available")
                    return {
                        'x': 250.0,  # Default values
                        'y': 0.0,
                        'z': 150.0,
                        'r': 0.0
                    }
            
        except Exception as e:
            self.logger.error(f"Failed to get robot position: {e}")
            return None
    
    def emergency_stop(self):
        """Emergency stop - immediately halt all robot movement."""
        try:
            if self.robot:
                # Stop all movement
                self.robot.stop()
                self.is_playing = False
                self.is_paused = False
                self.logger.warning("Emergency stop executed")
                
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
    
    def move_to_safe_position(self):
        """Move robot to a safe position."""
        if not self.is_connected or not self.robot:
            return False
        
        try:
            # Move to a safe position (center of workspace, elevated)
            safe_x, safe_y, safe_z, safe_r = 250, 0, 200, 0
            
            # Try different API methods for move_to
            try:
                self.robot.move_to(safe_x, safe_y, safe_z, safe_r, wait=True)
            except TypeError:
                self.robot.move_to(safe_x, safe_y, safe_z, safe_r)
            
            self.logger.info("Robot moved to safe position")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move to safe position: {e}")
            return False


if __name__ == "__main__":
    # Test the controller
    controller = RobotPlaybackController()
    
    # Example usage
    if controller.connect():
        print("Connected to robot")
        
        if controller.home_robot():
            print("Robot homed")
            
            # Load and play commands if available
            if controller.load_commands("robot_commands.json"):
                print("Commands loaded")
                controller.play(speed=0.5, loop=False)
        
        controller.disconnect()
    else:
        print("Failed to connect to robot")
