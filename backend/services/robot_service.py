"""
Robot Service
=============
Production-level service for robot control operations.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from models.schemas import RobotStatus

# Import robot controller
try:
    from robot_playback_controller import RobotPlaybackController
except ImportError:
    RobotPlaybackController = None

logger = logging.getLogger(__name__)


class RobotService:
    """Service for managing robot operations."""
    
    def __init__(self):
        """Initialize robot service."""
        self.controller: Optional[RobotPlaybackController] = None
        self._lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        """Connect to robot."""
        async with self._lock:
            try:
                if RobotPlaybackController is None:
                    logger.error("Robot controller not available")
                    return False
                
                if self.controller is None:
                    self.controller = RobotPlaybackController()
                
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(None, self.controller.connect)
                
                if success:
                    logger.info("Robot connected successfully")
                else:
                    logger.error("Failed to connect to robot")
                
                return success
                
            except Exception as e:
                logger.error(f"Robot connection error: {e}")
                return False
    
    async def disconnect(self):
        """Disconnect from robot."""
        async with self._lock:
            try:
                if self.controller:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.controller.disconnect)
                    self.controller = None
                    logger.info("Robot disconnected")
                    
            except Exception as e:
                logger.error(f"Robot disconnection error: {e}")
    
    async def is_connected(self) -> bool:
        """Check if robot is connected."""
        return (self.controller is not None and 
                hasattr(self.controller, 'is_connected') and 
                self.controller.is_connected)
    
    async def home(self) -> bool:
        """Move robot to home position."""
        if not await self.is_connected():
            logger.error("Robot not connected")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self.controller.home_robot)
            
            if success:
                logger.info("Robot homed successfully")
            else:
                logger.error("Failed to home robot")
            
            return success
            
        except Exception as e:
            logger.error(f"Robot homing error: {e}")
            return False
    
    async def load_commands(self, commands_file: str) -> bool:
        """Load robot commands from file."""
        if not await self.is_connected():
            logger.error("Robot not connected")
            return False
        
        try:
            commands_path = Path(f"processed/{commands_file}")
            if not commands_path.exists():
                logger.error(f"Commands file not found: {commands_path}")
                return False
            
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, self.controller.load_commands, str(commands_path)
            )
            
            if success:
                logger.info(f"Commands loaded from {commands_file}")
            else:
                logger.error(f"Failed to load commands from {commands_file}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading commands: {e}")
            return False
    
    async def play(self, speed: float = 1.0, loop: bool = False) -> bool:
        """Start playback of loaded commands."""
        if not await self.is_connected():
            logger.error("Robot not connected")
            return False
        
        try:
            loop_obj = asyncio.get_event_loop()
            success = await loop_obj.run_in_executor(
                None, self.controller.play, speed, loop
            )
            
            if success:
                logger.info(f"Playback started at {speed}x speed, loop={loop}")
            else:
                logger.error("Failed to start playback")
            
            return success
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False
    
    async def stop(self):
        """Stop robot operation."""
        if self.controller:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.controller.stop)
                logger.info("Robot operation stopped")
                
            except Exception as e:
                logger.error(f"Error stopping robot: {e}")
    
    async def pause(self):
        """Pause robot operation."""
        if self.controller:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.controller.pause)
                logger.info("Robot operation paused")
                
            except Exception as e:
                logger.error(f"Error pausing robot: {e}")
    
    async def emergency_stop(self):
        """Emergency stop for robot."""
        if self.controller:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.controller.stop)
                logger.warning("Emergency stop executed")
                
            except Exception as e:
                logger.error(f"Emergency stop error: {e}")
    
    async def get_status(self) -> RobotStatus:
        """Get robot status."""
        try:
            if not self.controller:
                return RobotStatus(
                    connected=False,
                    homed=False,
                    playing=False,
                    commands_loaded=0
                )
            
            loop = asyncio.get_event_loop()
            status_data = await loop.run_in_executor(None, self.controller.get_status)
            
            return RobotStatus(
                connected=status_data.get('connected', False),
                homed=True,  # Assume homed if connected
                playing=status_data.get('playing', False),
                commands_loaded=status_data.get('commands_loaded', 0),
                current_position=None,  # TODO: Implement position reading
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error getting robot status: {e}")
            return RobotStatus(
                connected=False,
                homed=False,
                playing=False,
                commands_loaded=0,
                error=str(e)
            )
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed robot status."""
        try:
            status = await self.get_status()
            
            detailed_status = {
                "basic_status": status.dict(),
                "capabilities": await self.get_capabilities(),
                "last_command_time": None,  # TODO: Implement
                "error_history": [],  # TODO: Implement
                "performance_metrics": {}  # TODO: Implement
            }
            
            return detailed_status
            
        except Exception as e:
            logger.error(f"Error getting detailed status: {e}")
            return {"error": str(e)}
    
    async def get_position(self) -> Optional[Dict[str, float]]:
        """Get current robot position."""
        if not await self.is_connected():
            return None
        
        try:
            # TODO: Implement position reading from robot
            # This would depend on the specific robot controller capabilities
            return {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "r": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting robot position: {e}")
            return None
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get robot capabilities."""
        return {
            "max_speed": 3.0,
            "min_speed": 0.1,
            "workspace": {
                "x_range": [200, 300],
                "y_range": [-100, 100],
                "z_range": [50, 250]
            },
            "features": [
                "position_control",
                "gripper_control",
                "smooth_movement",
                "command_playback"
            ],
            "supported_file_formats": ["json"],
            "safety_features": [
                "movement_limits",
                "emergency_stop",
                "collision_detection"
            ]
        }


# Dependency injection
_robot_service: Optional[RobotService] = None


@lru_cache()
def get_robot_service() -> RobotService:
    """Get robot service instance (singleton)."""
    global _robot_service
    if _robot_service is None:
        _robot_service = RobotService()
    return _robot_service
