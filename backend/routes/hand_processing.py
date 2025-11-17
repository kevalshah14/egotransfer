"""
Hand Processing Routes
=====================
Production-level FastAPI routes for hand tracking and processing operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Query, Depends, Request
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

from models.schemas import (
    ProcessingJob, ProcessingResponse, HandTrackingData, 
    TargetHand, ProcessingStats
)
from services.hand_service import HandService, get_hand_service
from services.job_manager import JobManager, get_job_manager
from routes.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hand", tags=["Hand Processing"])


@router.post("/process", response_model=ProcessingResponse)
async def process_video_hand_tracking(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    target_hand: TargetHand = Form(TargetHand.RIGHT),
    confidence_threshold: float = Form(0.7, ge=0.1, le=1.0),
    tracking_confidence: float = Form(0.5, ge=0.1, le=1.0),
    max_hands: int = Form(2, ge=1, le=2),
    generate_video: bool = Form(True),
    generate_robot_commands: bool = Form(True),
    include_ai_analysis: bool = Form(True),
    include_task_analysis: bool = Form(True),
    include_movement_analysis: bool = Form(True),
    analysis_detail_level: str = Form("standard"),
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Process video for hand tracking with MANO-style landmarks and optional AI analysis.
    
    - **file**: Video file to process (MP4, AVI, MOV, MKV)
    - **target_hand**: Target hand for robot control (right/left)
    - **confidence_threshold**: Hand detection confidence (0.1-1.0)
    - **tracking_confidence**: Hand tracking confidence (0.1-1.0)
    - **max_hands**: Maximum number of hands to track (1-2)
    - **generate_video**: Generate processed video with hand overlay
    - **generate_robot_commands**: Generate robot control commands
    - **include_ai_analysis**: Include AI analysis in parallel
    - **include_task_analysis**: Include task description and timeline
    - **include_movement_analysis**: Include movement pattern analysis
    - **analysis_detail_level**: Level of analysis detail (basic/standard/detailed)
    """
    try:
        # Get current user
        current_user = await get_current_user_optional(request)
        user_id = current_user["id"] if current_user else None
        
        # Validate file type
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create processing job with user_id
        job_id = job_manager.create_job(
            video_name=file.filename,
            user_id=user_id,
            message="Hand processing queued",
            current_step="Initializing"
        )
        
        # Immediately update progress to 0 to avoid race condition
        job_manager.update_job(
            job_id,
            progress=0,
            message="Starting video processing...",
            current_step="Initializing"
        )
        
        # Save uploaded file
        upload_path = Path(f"uploads/{job_id}_{file.filename}")
        upload_path.parent.mkdir(exist_ok=True)
        
        content = await file.read()
        file_size = len(content)
        
        # Check file size (100MB limit)
        max_size = 100 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
            )
        
        with open(upload_path, 'wb') as f:
            f.write(content)
        
        # Start background hand processing with AI analysis
        background_tasks.add_task(
            hand_service.process_video_background,
            job_id=job_id,
            video_path=upload_path,
            target_hand=target_hand,
            confidence_threshold=confidence_threshold,
            tracking_confidence=tracking_confidence,
            max_hands=max_hands,
            generate_video=generate_video,
            generate_robot_commands=generate_robot_commands,
            include_ai_analysis=include_ai_analysis,
            include_task_analysis=include_task_analysis,
            include_movement_analysis=include_movement_analysis,
            analysis_detail_level=analysis_detail_level,
            job_manager=job_manager
        )
        
        logger.info(f"Started hand processing for job {job_id}")
        
        return ProcessingResponse(
            job_id=job_id,
            message="Hand processing started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Hand processing failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracking/{job_id}", response_model=List[HandTrackingData])
async def get_hand_tracking_data(
    job_id: str,
    frame_start: Optional[int] = Query(None, ge=0),
    frame_end: Optional[int] = Query(None, ge=0),
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get hand tracking data for a specific job."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Processing not completed. Current status: {job.status}"
            )
        
        # Get tracking data
        tracking_data = await hand_service.get_tracking_data(
            job_id, frame_start, frame_end
        )
        
        return tracking_data
        
    except Exception as e:
        logger.error(f"Failed to get tracking data for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/landmarks/{job_id}")
async def get_hand_landmarks(
    job_id: str,
    frame_number: int = Query(..., ge=0),
    hand_type: Optional[str] = Query(None),  # 'left', 'right', or None for both
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get detailed hand landmarks for a specific frame."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        landmarks = await hand_service.get_frame_landmarks(
            job_id, frame_number, hand_type
        )
        
        return {
            "success": True,
            "frame_number": frame_number,
            "landmarks": landmarks
        }
        
    except Exception as e:
        logger.error(f"Failed to get landmarks for job {job_id}, frame {frame_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{job_id}", response_model=ProcessingStats)
async def get_processing_stats(
    job_id: str,
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get processing statistics for a job."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        stats = await hand_service.get_processing_stats(job_id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{job_id}")
async def download_processed_video(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Download processed video with hand tracking overlay."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if processed video exists
        if 'processed_video' not in job.processed_files:
            raise HTTPException(status_code=404, detail="Processed video not found")
        
        video_filename = job.processed_files['processed_video']
        video_path = Path(f"processed/{video_filename}")
        
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found on disk")
        
        return FileResponse(
            path=video_path,
            filename=video_filename,
            media_type='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"Failed to download video for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands/{job_id}")
async def download_robot_commands(
    job_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    job_manager: JobManager = Depends(get_job_manager),
    hand_service: HandService = Depends(get_hand_service)
):
    """Download robot commands in specified format."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate commands file in requested format
        commands_file = await hand_service.export_robot_commands(job_id, format)
        
        if not commands_file.exists():
            raise HTTPException(status_code=404, detail="Commands file not found")
        
        media_type = "application/json" if format == "json" else "text/csv"
        
        return FileResponse(
            path=commands_file,
            filename=f"robot_commands_{job_id}.{format}",
            media_type=media_type
        )
        
    except Exception as e:
        logger.error(f"Failed to download commands for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess/{job_id}", response_model=ProcessingResponse)
async def reprocess_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    target_hand: Optional[TargetHand] = Form(None),
    confidence_threshold: Optional[float] = Form(None, ge=0.1, le=1.0),
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Reprocess an existing video with different parameters."""
    try:
        # Get current user
        current_user = await get_current_user_optional(request)
        user_id = current_user["id"] if current_user else None
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user has access to this job
        if job.user_id and job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this job")
        
        # Create new job for reprocessing with same user_id
        new_job_id = job_manager.create_job(
            video_name=f"reprocess_{job.video_name}",
            user_id=user_id,
            message="Reprocessing queued",
            current_step="Initializing"
        )
        
        # Get original video path
        original_video_path = Path(f"uploads/{job_id}_{job.video_name}")
        if not original_video_path.exists():
            raise HTTPException(status_code=404, detail="Original video file not found")
        
        # Use new parameters or defaults from original job
        new_target_hand = target_hand or TargetHand.RIGHT
        new_confidence = confidence_threshold or 0.7
        
        # Start background reprocessing
        background_tasks.add_task(
            hand_service.process_video_background,
            job_id=new_job_id,
            video_path=original_video_path,
            target_hand=new_target_hand,
            confidence_threshold=new_confidence,
            tracking_confidence=0.5,
            max_hands=2,
            generate_video=True,
            generate_robot_commands=True,
            job_manager=job_manager
        )
        
        logger.info(f"Started reprocessing for job {new_job_id} (original: {job_id})")
        
        return ProcessingResponse(
            job_id=new_job_id,
            message="Reprocessing started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Reprocessing failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get the status of a processing job."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status_value = job.status if isinstance(job.status, str) else job.status.value
        return {
            "job_id": job_id,
            "status": status_value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "processed_files": job.processed_files,
            "error": job.error if hasattr(job, "error") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{job_id1}/{job_id2}")
async def compare_hand_tracking_results(
    job_id1: str,
    job_id2: str,
    hand_service: HandService = Depends(get_hand_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Compare hand tracking results between two jobs."""
    try:
        job1 = job_manager.get_job(job_id1)
        job2 = job_manager.get_job(job_id2)
        
        if not job1 or not job2:
            raise HTTPException(status_code=404, detail="One or both jobs not found")
        
        comparison = await hand_service.compare_tracking_results(job_id1, job_id2)
        
        return {
            "success": True,
            "comparison": comparison
        }
        
    except Exception as e:
        logger.error(f"Failed to compare jobs {job_id1} and {job_id2}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
