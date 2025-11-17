"""
AI Processing Routes
===================
Production-level FastAPI routes for AI video analysis operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends, Request
from typing import List, Optional
import logging
from pathlib import Path

from models.schemas import ProcessingJob, AIAnalysisResult, ProcessingResponse
from services.ai_service import AIService, get_ai_service
from services.job_manager import JobManager, get_job_manager
from routes.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Processing"])


@router.post("/analyze_existing/{job_id}", response_model=ProcessingResponse)
async def analyze_existing_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    include_task_analysis: bool = Form(True),
    include_movement_analysis: bool = Form(True),
    analysis_detail_level: str = Form("standard"),
    ai_service: AIService = Depends(get_ai_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Analyze an existing processed video with AI."""
    try:
        # Get current user
        current_user = await get_current_user_optional(request)
        user_id = current_user["id"] if current_user else None
        
        # Get the existing job
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user has access to this job
        if job.user_id and job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this job")
        
        # Find the original video file
        original_video_path = Path(f"uploads/{job_id}_{job.video_name}")
        if not original_video_path.exists():
            raise HTTPException(status_code=404, detail="Original video file not found")
        
        # Create new AI analysis job with same user_id
        ai_job_id = job_manager.create_job(
            video_name=f"ai_analysis_{job.video_name}",
            user_id=user_id,
            message="AI analysis queued for existing video",
            current_step="Initializing"
        )
        
        # Start background AI analysis
        background_tasks.add_task(
            ai_service.analyze_video_background,
            job_id=ai_job_id,
            video_path=original_video_path,
            include_task_analysis=include_task_analysis,
            include_movement_analysis=include_movement_analysis,
            detail_level=analysis_detail_level,
            job_manager=job_manager
        )
        
        logger.info(f"Started AI analysis for existing job {job_id} -> new job {ai_job_id}")
        
        return ProcessingResponse(
            job_id=ai_job_id,
            message="AI analysis started for existing video",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"AI analysis failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ProcessingResponse)
async def analyze_video_with_ai(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    include_task_analysis: bool = Form(True),
    include_movement_analysis: bool = Form(True),
    analysis_detail_level: str = Form("standard"),  # basic, standard, detailed
    ai_service: AIService = Depends(get_ai_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Analyze video with AI for task understanding and movement insights.
    
    - **file**: Video file to analyze (MP4, AVI, MOV, MKV)
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
            message="AI analysis queued",
            current_step="Initializing"
        )
        
        # Save uploaded file
        upload_path = Path(f"uploads/{job_id}_{file.filename}")
        upload_path.parent.mkdir(exist_ok=True)
        
        content = await file.read()
        with open(upload_path, 'wb') as f:
            f.write(content)
        
        # Start background AI analysis
        background_tasks.add_task(
            ai_service.analyze_video_background,
            job_id=job_id,
            video_path=upload_path,
            include_task_analysis=include_task_analysis,
            include_movement_analysis=include_movement_analysis,
            detail_level=analysis_detail_level,
            job_manager=job_manager
        )
        
        logger.info(f"Started AI analysis for job {job_id}")
        
        return ProcessingResponse(
            job_id=job_id,
            message="AI analysis started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"AI analysis failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{job_id}", response_model=AIAnalysisResult)
async def get_analysis_result(
    job_id: str,
    request: Request,
    ai_service: AIService = Depends(get_ai_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get AI analysis results for a specific job."""
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
        
        if job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed. Current status: {job.status}"
            )
        
        # Get analysis results
        analysis = await ai_service.get_analysis_result(job_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="AI analysis results not available. Hand tracking completed successfully, but AI analysis may have failed.")
        
        return analysis
        
    except HTTPException:
        # Re-raise HTTP exceptions (404, 403, 400) without wrapping them
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting analysis result for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/models")
async def get_available_ai_models(ai_service: AIService = Depends(get_ai_service)):
    """Get list of available AI models and their capabilities."""
    try:
        models = await ai_service.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to get AI models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reanalyze/{job_id}", response_model=ProcessingResponse)
async def reanalyze_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    analysis_detail_level: str = Form("standard"),
    ai_service: AIService = Depends(get_ai_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Re-analyze an existing video with different parameters."""
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
        
        # Create new job for re-analysis with same user_id
        new_job_id = job_manager.create_job(
            video_name=f"reanalysis_{job.video_name}",
            user_id=user_id,
            message="Re-analysis queued",
            current_step="Initializing"
        )
        
        # Get original video path
        original_video_path = Path(f"uploads/{job_id}_{job.video_name}")
        if not original_video_path.exists():
            raise HTTPException(status_code=404, detail="Original video file not found")
        
        # Start background re-analysis
        background_tasks.add_task(
            ai_service.analyze_video_background,
            job_id=new_job_id,
            video_path=original_video_path,
            include_task_analysis=True,
            include_movement_analysis=True,
            detail_level=analysis_detail_level,
            job_manager=job_manager
        )
        
        logger.info(f"Started re-analysis for job {new_job_id} (original: {job_id})")
        
        return ProcessingResponse(
            job_id=new_job_id,
            message="Re-analysis started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Re-analysis failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{job_id}")
async def get_movement_insights(
    job_id: str,
    ai_service: AIService = Depends(get_ai_service),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get detailed movement insights for robot programming."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        insights = await ai_service.get_movement_insights(job_id)
        return {
            "success": True,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get movement insights for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{job_id}")
async def submit_analysis_feedback(
    job_id: str,
    feedback: dict,
    ai_service: AIService = Depends(get_ai_service)
):
    """Submit feedback on AI analysis quality for model improvement."""
    try:
        success = await ai_service.submit_feedback(job_id, feedback)
        
        if success:
            logger.info(f"Received feedback for job {job_id}")
            return {"success": True, "message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to submit feedback")
            
    except Exception as e:
        logger.error(f"Failed to submit feedback for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_ai_usage_stats(ai_service: AIService = Depends(get_ai_service)):
    """Get AI service usage statistics."""
    try:
        stats = await ai_service.get_usage_stats()
        return {
            "success": True,
            "usage_stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get AI usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
