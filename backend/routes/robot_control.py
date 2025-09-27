"""
Robot Control Routes
===================
Production-level FastAPI routes for robot control operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from backend.models.schemas import RobotCommand, RobotStatus, RobotResponse, RobotAction
from backend.services.robot_service import RobotService, get_robot_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/robot", tags=["Robot Control"])


@router.post("/command", response_model=RobotResponse)
async def execute_robot_command(
    command: RobotCommand,
    robot_service: RobotService = Depends(get_robot_service)
):
    """
    Execute robot command.
    
    Available actions:
    - connect: Connect to robot
    - disconnect: Disconnect from robot
    - home: Move robot to home position
    - play: Start playback of loaded commands
    - stop: Stop current operation
    - pause: Pause current operation
    - status: Get detailed status
    """
    try:
        logger.info(f"Executing robot command: {command.action}")
        
        if command.action == RobotAction.CONNECT:
            success = await robot_service.connect()
            message = "Robot connected successfully" if success else "Failed to connect to robot"
            
        elif command.action == RobotAction.DISCONNECT:
            await robot_service.disconnect()
            success = True
            message = "Robot disconnected successfully"
            
        elif command.action == RobotAction.HOME:
            success = await robot_service.home()
            message = "Robot moved to home position" if success else "Failed to home robot"
            
        elif command.action == RobotAction.PLAY:
            if command.commands_file:
                load_success = await robot_service.load_commands(command.commands_file)
                if not load_success:
                    raise HTTPException(status_code=400, detail="Failed to load commands file")
            
            success = await robot_service.play(speed=command.speed, loop=command.loop)
            message = "Playback started successfully" if success else "Failed to start playback"
            
        elif command.action == RobotAction.STOP:
            await robot_service.stop()
            success = True
            message = "Robot operation stopped"
            
        elif command.action == RobotAction.PAUSE:
            await robot_service.pause()
            success = True
            message = "Robot operation paused"
            
        elif command.action == RobotAction.STATUS:
            status_data = await robot_service.get_detailed_status()
            return RobotResponse(
                success=True,
                message="Robot status retrieved",
                data=status_data
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {command.action}")
        
        return RobotResponse(success=success, message=message)
        
    except Exception as e:
        logger.error(f"Robot command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=RobotStatus)
async def get_robot_status(robot_service: RobotService = Depends(get_robot_service)):
    """Get current robot status."""
    try:
        status = await robot_service.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get robot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect", response_model=RobotResponse)
async def connect_robot(robot_service: RobotService = Depends(get_robot_service)):
    """Connect to robot (convenience endpoint)."""
    try:
        success = await robot_service.connect()
        message = "Robot connected successfully" if success else "Failed to connect to robot"
        return RobotResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"Robot connection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect", response_model=RobotResponse)
async def disconnect_robot(robot_service: RobotService = Depends(get_robot_service)):
    """Disconnect from robot (convenience endpoint)."""
    try:
        await robot_service.disconnect()
        return RobotResponse(success=True, message="Robot disconnected successfully")
    except Exception as e:
        logger.error(f"Robot disconnection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/home", response_model=RobotResponse)
async def home_robot(robot_service: RobotService = Depends(get_robot_service)):
    """Move robot to home position (convenience endpoint)."""
    try:
        if not await robot_service.is_connected():
            raise HTTPException(status_code=400, detail="Robot not connected")
            
        success = await robot_service.home()
        message = "Robot moved to home position" if success else "Failed to home robot"
        return RobotResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"Robot homing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency_stop", response_model=RobotResponse)
async def emergency_stop(robot_service: RobotService = Depends(get_robot_service)):
    """Emergency stop for robot operations."""
    try:
        await robot_service.emergency_stop()
        logger.warning("Emergency stop executed")
        return RobotResponse(success=True, message="Emergency stop executed")
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_robot_capabilities(robot_service: RobotService = Depends(get_robot_service)):
    """Get robot capabilities and configuration."""
    try:
        capabilities = await robot_service.get_capabilities()
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get robot capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position")
async def get_robot_position(robot_service: RobotService = Depends(get_robot_service)):
    """Get current robot position."""
    try:
        if not await robot_service.is_connected():
            raise HTTPException(status_code=400, detail="Robot not connected")
            
        position = await robot_service.get_position()
        return {
            "success": True,
            "position": position
        }
    except Exception as e:
        logger.error(f"Failed to get robot position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
