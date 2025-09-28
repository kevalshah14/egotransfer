"""
Hand Service
============
Production-level service for hand tracking and processing operations.
"""

import asyncio
import json
import csv
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache
from datetime import datetime

from models.schemas import HandTrackingData, ProcessingStats, JobStatus, TargetHand
from .job_manager import JobManager
from .ai_service import AIService, get_ai_service

# Import hand processors
try:
    from video_hand_processor import VideoHandProcessor
    from robot_position_converter import RobotPositionConverter
except ImportError:
    VideoHandProcessor = None
    RobotPositionConverter = None

logger = logging.getLogger(__name__)


class HandService:
    """Service for managing hand tracking and processing operations."""
    
    def __init__(self):
        """Initialize hand service."""
        self.tracking_cache: Dict[str, List[HandTrackingData]] = {}
        self._processor = None
        self._converter = None
    
    def _get_processor(self):
        """Get video processor instance, creating if needed."""
        if self._processor is None:
            try:
                from video_hand_processor import VideoHandProcessor
                self._processor = VideoHandProcessor()
                logger.info("VideoHandProcessor initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import VideoHandProcessor: {e}")
                return None
        return self._processor
    
    def _get_converter(self):
        """Get robot position converter instance, creating if needed."""
        if self._converter is None:
            try:
                from video_hand_processor import RobotPositionConverter
                self._converter = RobotPositionConverter()
                logger.info("RobotPositionConverter initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import RobotPositionConverter: {e}")
                return None
        return self._converter
    
    async def process_video_background(
        self,
        job_id: str,
        video_path: Path,
        target_hand: TargetHand,
        confidence_threshold: float = 0.7,
        tracking_confidence: float = 0.5,
        max_hands: int = 2,
        generate_video: bool = True,
        generate_robot_commands: bool = True,
        include_ai_analysis: bool = True,
        include_task_analysis: bool = True,
        include_movement_analysis: bool = True,
        analysis_detail_level: str = "standard",
        job_manager: JobManager = None
    ):
        """Background task for hand tracking processing."""
        start_time = datetime.now()
        
        try:
            processor = self._get_processor()
            if not processor:
                raise Exception("Hand processor not available")
            
            # Update job status
            if job_manager:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.PROCESSING,
                    progress=10,
                    current_step="Hand Tracking",
                    message="Starting hand tracking analysis..."
                )
            
            # Configure processor
            processor.hands = processor.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=confidence_threshold,
                min_tracking_confidence=tracking_confidence,
                model_complexity=1
            )
            
            # Process video for hand tracking
            video_name = video_path.stem
            output_video_path = Path(f"processed/{video_name}_processed.mp4") if generate_video else None
            tracking_data_path = Path(f"processed/{video_name}_tracking.json")
            
            # Ensure processed directory exists
            Path("processed").mkdir(exist_ok=True)
            
            # Update progress
            if job_manager:
                job_manager.update_job(
                    job_id,
                    progress=0,
                    message="Starting video processing..."
                )
            
            # Define progress callback
            def progress_callback(progress: float, eta: float):
                if job_manager:
                    # Scale video processing progress to 0-70%
                    scaled_progress = int(progress * 0.7)
                    logger.info(f"Progress callback for job {job_id}: {progress:.1f}% -> {scaled_progress}% (ETA: {eta:.1f}s)")
                    job_manager.update_job(
                        job_id,
                        progress=scaled_progress,
                        message=f"Processing video frames... Progress: {progress:.1f}% - ETA: {eta:.1f}s"
                    )
            
            # Run processing in executor
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, 
                processor.process_video,
                str(video_path),
                str(output_video_path) if output_video_path else None,
                str(tracking_data_path),
                progress_callback
            )
            
            if not success:
                raise Exception("Hand tracking processing failed")
            
            # Update progress
            if job_manager:
                job_manager.update_job(
                    job_id,
                    progress=70,
                    current_step="Converting to Robot Commands",
                    message="Converting hand positions to robot commands..."
                )
            
            # Generate robot commands if requested
            robot_commands_file = None
            if generate_robot_commands:
                robot_commands_file = await self._generate_robot_commands(
                    job_id, tracking_data_path, target_hand
                )
            
            # Update hand processing completion
            if job_manager:
                processed_files = {}
                
                if output_video_path and output_video_path.exists():
                    processed_files['processed_video'] = output_video_path.name
                
                if tracking_data_path.exists():
                    processed_files['tracking_data'] = tracking_data_path.name
                
                if robot_commands_file and robot_commands_file.exists():
                    processed_files['robot_commands'] = robot_commands_file.name
                
                # Update progress to 70% (hand processing complete)
                job_manager.update_job(
                    job_id,
                    progress=70,
                    current_step="Hand Processing Complete",
                    message=f"Hand processing completed successfully. Generated {len(processed_files)} files.",
                    processed_files=processed_files
                )
                
                # Start AI analysis in parallel if requested
                if include_ai_analysis:
                    try:
                        ai_service = AIService()
                        await ai_service.analyze_video_background(
                            job_id=job_id,
                            video_path=video_path,
                            include_task_analysis=include_task_analysis,
                            include_movement_analysis=include_movement_analysis,
                            detail_level=analysis_detail_level,
                            job_manager=job_manager
                        )
                    except Exception as ai_error:
                        logger.error(f"Failed to start AI analysis for job {job_id}: {ai_error}")
                        # Continue without AI analysis
                        job_manager.update_job(
                            job_id,
                            status=JobStatus.COMPLETED,
                            progress=100,
                            current_step="Complete",
                            message=f"Hand processing completed successfully. AI analysis failed: {str(ai_error)}",
                            processed_files=processed_files
                        )
                else:
                    # Complete job without AI analysis
                    job_manager.update_job(
                        job_id,
                        status=JobStatus.COMPLETED,
                        progress=100,
                        current_step="Complete",
                        message=f"Hand processing completed successfully. Generated {len(processed_files)} files.",
                        processed_files=processed_files
                    )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Hand processing completed for job {job_id} in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Hand processing failed: {str(e)}"
            logger.error(f"Job {job_id}: {error_msg}")
            
            if job_manager:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    progress=0,
                    current_step="Error",
                    message=error_msg,
                    error=str(e)
                )
    
    async def _generate_robot_commands(
        self, 
        job_id: str, 
        tracking_data_path: Path, 
        target_hand: TargetHand
    ) -> Optional[Path]:
        """Generate robot commands from tracking data."""
        try:
            converter = self._get_converter()
            if not converter:
                logger.error("Robot position converter not available")
                return None
            
            # Load tracking data
            loop = asyncio.get_event_loop()
            tracking_data = await loop.run_in_executor(
                None, converter.load_tracking_data, str(tracking_data_path)
            )
            
            if not tracking_data:
                logger.error("No tracking data found")
                return None
            
            # Convert to robot commands
            commands = await loop.run_in_executor(
                None, 
                converter.convert_to_robot_commands, 
                tracking_data, 
                target_hand.value
            )
            
            if not commands:
                logger.error("No robot commands generated")
                return None
            
            # Apply smoothing and filtering
            smoothed_commands = await loop.run_in_executor(
                None, converter.smooth_commands, commands
            )
            
            filtered_commands = await loop.run_in_executor(
                None, converter.filter_minimal_movement, smoothed_commands
            )
            
            # Save commands
            commands_file = Path(f"processed/{job_id}_robot_commands.json")
            await loop.run_in_executor(
                None, converter.save_commands, filtered_commands, str(commands_file)
            )
            
            logger.info(f"Generated {len(filtered_commands)} robot commands for job {job_id}")
            return commands_file
            
        except Exception as e:
            logger.error(f"Failed to generate robot commands for job {job_id}: {e}")
            return None
    
    async def get_tracking_data(
        self, 
        job_id: str, 
        frame_start: Optional[int] = None, 
        frame_end: Optional[int] = None
    ) -> List[HandTrackingData]:
        """Get hand tracking data for a job."""
        # Check cache first
        if job_id in self.tracking_cache:
            data = self.tracking_cache[job_id]
        else:
            # Load from file
            tracking_file = Path(f"processed/{job_id}_tracking.json")
            if not tracking_file.exists():
                return []
            
            try:
                with open(tracking_file, 'r') as f:
                    file_data = json.load(f)
                
                frames_data = file_data.get('frames', [])
                data = [HandTrackingData(**frame) for frame in frames_data]
                
                # Cache the data
                self.tracking_cache[job_id] = data
                
            except Exception as e:
                logger.error(f"Failed to load tracking data for job {job_id}: {e}")
                return []
        
        # Apply frame filtering if specified
        if frame_start is not None or frame_end is not None:
            filtered_data = []
            for frame_data in data:
                frame_num = frame_data.frame_number
                if frame_start is not None and frame_num < frame_start:
                    continue
                if frame_end is not None and frame_num > frame_end:
                    continue
                filtered_data.append(frame_data)
            return filtered_data
        
        return data
    
    async def get_frame_landmarks(
        self, 
        job_id: str, 
        frame_number: int, 
        hand_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed landmarks for a specific frame."""
        tracking_data = await self.get_tracking_data(job_id)
        
        # Find the specific frame
        target_frame = None
        for frame_data in tracking_data:
            if frame_data.frame_number == frame_number:
                target_frame = frame_data
                break
        
        if not target_frame:
            return {"error": f"Frame {frame_number} not found"}
        
        landmarks = {}
        
        if hand_type is None or hand_type == "left":
            if target_frame.left_hand:
                landmarks["left_hand"] = target_frame.left_hand
        
        if hand_type is None or hand_type == "right":
            if target_frame.right_hand:
                landmarks["right_hand"] = target_frame.right_hand
        
        return landmarks
    
    async def get_processing_stats(self, job_id: str) -> ProcessingStats:
        """Get processing statistics for a job."""
        try:
            tracking_data = await self.get_tracking_data(job_id)
            
            total_frames = len(tracking_data)
            hands_detected = sum(1 for frame in tracking_data 
                               if frame.left_hand or frame.right_hand)
            
            # Get file sizes
            file_sizes = {}
            processed_files = [
                f"processed/{job_id}_processed.mp4",
                f"processed/{job_id}_tracking.json",
                f"processed/{job_id}_robot_commands.json"
            ]
            
            for file_path in processed_files:
                path = Path(file_path)
                if path.exists():
                    file_sizes[path.name] = path.stat().st_size
            
            # Calculate processing time (estimate based on frame count)
            estimated_processing_time = total_frames * 0.1  # Rough estimate
            
            return ProcessingStats(
                total_frames=total_frames,
                processed_frames=total_frames,
                hands_detected=hands_detected,
                processing_time=estimated_processing_time,
                file_sizes=file_sizes
            )
            
        except Exception as e:
            logger.error(f"Failed to get stats for job {job_id}: {e}")
            # Return empty stats on error
            return ProcessingStats(
                total_frames=0,
                processed_frames=0,
                hands_detected=0,
                processing_time=0.0,
                file_sizes={}
            )
    
    async def export_robot_commands(self, job_id: str, format: str = "json") -> Path:
        """Export robot commands in specified format."""
        commands_file = Path(f"processed/{job_id}_robot_commands.json")
        
        if format == "json":
            return commands_file
        
        elif format == "csv":
            csv_file = Path(f"processed/{job_id}_robot_commands.csv")
            
            try:
                # Load JSON commands
                with open(commands_file, 'r') as f:
                    data = json.load(f)
                
                commands = data.get('commands', [])
                
                # Write CSV
                with open(csv_file, 'w', newline='') as f:
                    if commands:
                        writer = csv.DictWriter(f, fieldnames=commands[0].keys())
                        writer.writeheader()
                        writer.writerows(commands)
                
                return csv_file
                
            except Exception as e:
                logger.error(f"Failed to export CSV for job {job_id}: {e}")
                return commands_file
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def compare_tracking_results(self, job_id1: str, job_id2: str) -> Dict[str, Any]:
        """Compare hand tracking results between two jobs."""
        try:
            data1 = await self.get_tracking_data(job_id1)
            data2 = await self.get_tracking_data(job_id2)
            
            comparison = {
                "job1": {
                    "id": job_id1,
                    "total_frames": len(data1),
                    "hands_detected": sum(1 for frame in data1 if frame.left_hand or frame.right_hand)
                },
                "job2": {
                    "id": job_id2,
                    "total_frames": len(data2),
                    "hands_detected": sum(1 for frame in data2 if frame.left_hand or frame.right_hand)
                },
                "differences": {
                    "frame_count_diff": len(data1) - len(data2),
                    "detection_rate_diff": 0.0
                }
            }
            
            # Calculate detection rates
            if len(data1) > 0:
                rate1 = comparison["job1"]["hands_detected"] / len(data1)
            else:
                rate1 = 0.0
            
            if len(data2) > 0:
                rate2 = comparison["job2"]["hands_detected"] / len(data2)
            else:
                rate2 = 0.0
            
            comparison["differences"]["detection_rate_diff"] = rate1 - rate2
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare jobs {job_id1} and {job_id2}: {e}")
            return {"error": str(e)}


# Dependency injection
_hand_service: Optional[HandService] = None


@lru_cache()
def get_hand_service() -> HandService:
    """Get hand service instance (singleton)."""
    global _hand_service
    if _hand_service is None:
        _hand_service = HandService()
    return _hand_service


# Job manager dependency
@lru_cache()
def get_job_manager() -> JobManager:
    """Get job manager instance (singleton)."""
    return JobManager()
