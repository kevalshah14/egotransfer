"""
Pydantic Models and Schemas
==========================
Production-level data models for the Video-to-Robot API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TargetHand(str, Enum):
    """Target hand enumeration."""
    RIGHT = "right"
    LEFT = "left"


class RobotAction(str, Enum):
    """Robot action enumeration."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HOME = "home"
    PLAY = "play"
    STOP = "stop"
    PAUSE = "pause"
    STATUS = "status"


class ProcessingRequest(BaseModel):
    """Request model for video processing."""
    target_hand: TargetHand = Field(TargetHand.RIGHT, description="Target hand for robot control")
    include_ai: bool = Field(True, description="Include AI analysis")
    speed: float = Field(1.0, ge=0.1, le=3.0, description="Processing speed multiplier")

    class Config:
        use_enum_values = True


class ProcessingJob(BaseModel):
    """Model for processing job data."""
    job_id: str = Field(..., description="Unique job identifier")
    user_id: Optional[str] = Field(None, description="User ID who created the job")
    status: JobStatus = Field(JobStatus.PENDING, description="Current job status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: str = Field("", description="Status message")
    current_step: str = Field("", description="Current processing step")
    video_name: str = Field("", description="Original video filename")
    processed_files: Dict[str, str] = Field(default_factory=dict, description="Generated files")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ProcessingResponse(BaseModel):
    """Response model for processing requests."""
    job_id: str = Field(..., description="Job identifier")
    message: str = Field(..., description="Response message")
    status: JobStatus = Field(..., description="Initial status")

    class Config:
        use_enum_values = True


class RobotCommand(BaseModel):
    """Model for robot commands."""
    action: RobotAction = Field(..., description="Robot action to perform")
    speed: float = Field(1.0, ge=0.1, le=3.0, description="Movement speed")
    loop: bool = Field(False, description="Loop playback")
    commands_file: Optional[str] = Field(None, description="Commands file to load")

    @validator('speed')
    def validate_speed(cls, v):
        if not 0.1 <= v <= 3.0:
            raise ValueError('Speed must be between 0.1 and 3.0')
        return v

    class Config:
        use_enum_values = True


class RobotStatus(BaseModel):
    """Model for robot status."""
    connected: bool = Field(..., description="Connection status")
    homed: bool = Field(False, description="Home position status")
    playing: bool = Field(False, description="Playback status")
    commands_loaded: int = Field(0, description="Number of loaded commands")
    current_position: Optional[Dict[str, float]] = Field(None, description="Current robot position")
    error: Optional[str] = Field(None, description="Error message")


class RobotResponse(BaseModel):
    """Response model for robot commands."""
    success: bool = Field(..., description="Command success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field("healthy", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_modules_available: bool = Field(..., description="Processing modules availability")
    active_jobs: int = Field(..., description="Number of active jobs")
    robot_connected: bool = Field(..., description="Robot connection status")
    version: str = Field("1.0.0", description="API version")


class APIError(BaseModel):
    """Error response model."""
    error: bool = Field(True)
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class FileUploadResponse(BaseModel):
    """File upload response model."""
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., description="File size in bytes")
    job_id: str = Field(..., description="Processing job ID")
    message: str = Field(..., description="Upload status message")


class HandTrackingData(BaseModel):
    """Model for hand tracking data."""
    frame_number: int = Field(..., description="Frame number")
    timestamp: float = Field(..., description="Timestamp in video")
    left_hand: Optional[List[Dict[str, Any]]] = Field(None, description="Left hand landmarks")
    right_hand: Optional[List[Dict[str, Any]]] = Field(None, description="Right hand landmarks")


class AIAnalysisResult(BaseModel):
    """Model for AI analysis results."""
    task_description: str = Field(..., description="Main task description")
    timeline: List[Dict[str, Any]] = Field(..., description="Action timeline")
    robot_notes: str = Field(..., description="Robot control insights")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")


class ProcessingStats(BaseModel):
    """Model for processing statistics."""
    total_frames: int = Field(..., description="Total video frames")
    processed_frames: int = Field(..., description="Successfully processed frames")
    hands_detected: int = Field(..., description="Frames with hand detection")
    processing_time: float = Field(..., description="Total processing time in seconds")
    file_sizes: Dict[str, int] = Field(..., description="Generated file sizes")
