"""
FastAPI Application Factory
==========================
Creates and configures the FastAPI application with all routes and middleware.
"""

import os

# Configure OpenCV to run in headless mode (must be before cv2 import)
os.environ.setdefault('OPENCV_VIDEOIO_PRIORITY_MSMF', '0')
os.environ.setdefault('OPENCV_VIDEOIO_DEBUG', '0')

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from routes import ai_processing, hand_processing, robot_control, auth, admin
from routes.auth import get_current_user_optional, get_current_user_required
from services.job_manager import JobManager, get_job_manager
from models.database import init_db, close_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Video-to-Robot Processing System",
        description="Production-level FastAPI application for processing videos with hand tracking and controlling robots",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    # In production, set ALLOWED_ORIGINS environment variable
    # Example: ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if allowed_origins == ["*"] and os.getenv("ENVIRONMENT") == "production":
        logger.warning("⚠️  CORS is set to allow all origins in production! This is insecure.")
        logger.warning("⚠️  Set ALLOWED_ORIGINS environment variable to restrict access.")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(ai_processing.router)
    app.include_router(hand_processing.router)
    app.include_router(robot_control.router)
    
    # Initialize database on startup
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on application startup."""
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't fail startup if DATABASE_URL is not set (for development)
            if os.getenv("DATABASE_URL"):
                raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Close database connections on shutdown."""
        await close_db()
        logger.info("Database connections closed")
    
    # Add general jobs endpoints
    @app.get("/videos")
    async def get_user_videos(
        request: Request,
        current_user: dict = Depends(get_current_user_optional)
    ):
        """Get all videos for the current user."""
        try:
            from services.video_service import VideoService
            from models.database import AsyncSessionLocal
            
            # Filter videos by user_id if authenticated
            user_id = current_user["id"] if current_user else None
            if not user_id:
                return {"videos": [], "total": 0}
            
            if not AsyncSessionLocal:
                return {"videos": [], "total": 0}
            
            async with AsyncSessionLocal() as db:
                videos = await VideoService.list_videos_by_user(db, user_id, limit=100, offset=0)
                total_count = await VideoService.count_videos_by_user(db, user_id)
            
            return {
                "videos": [
                    {
                        "id": video.id,
                        "filename": video.filename,
                        "original_filename": video.original_filename,
                        "file_size": video.file_size,
                        "duration": video.duration,
                        "status": video.status,
                        "job_id": video.job_id,
                        "created_at": video.created_at.isoformat() if video.created_at else None,
                    }
                    for video in videos
                ],
                "total": total_count
            }
        except Exception as e:
            logger.error(f"Failed to get user videos: {e}")
            # If database not available, return empty list
            return {"videos": [], "total": 0}
    
    @app.get("/jobs")
    async def get_all_jobs(
        request: Request,
        job_manager: JobManager = Depends(get_job_manager),
        current_user: dict = Depends(get_current_user_optional)
    ):
        """Get all processing jobs for the current user."""
        try:
            # Filter jobs by user_id if authenticated
            user_id = current_user["id"] if current_user else None
            jobs = job_manager.list_jobs(user_id=user_id)
            
            return {
                "jobs": [
                    {
                        "job_id": job.job_id,
                        "status": job.status if isinstance(job.status, str) else job.status.value,
                        "progress": job.progress,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                        "error": job.error_message if hasattr(job, 'error_message') else None
                    }
                    for job in jobs
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get all jobs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/jobs/{job_id}")
    async def get_job_status(
        job_id: str,
        request: Request,
        job_manager: JobManager = Depends(get_job_manager),
        current_user: dict = Depends(get_current_user_optional)
    ):
        """Get the status of a processing job."""
        try:
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Check if user has access to this job
            user_id = current_user["id"] if current_user else None
            if job.user_id and job.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied to this job")
            
            return {
                "job_id": job_id,
                "status": job.status if isinstance(job.status, str) else job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "error": job.error_message if hasattr(job, 'error_message') else None
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/stats")
    async def get_stats(
        job_manager: JobManager = Depends(get_job_manager)
    ):
        """Get processing statistics."""
        try:
            return job_manager.get_stats()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/jobs/{job_id}")
    async def delete_job(
        job_id: str,
        request: Request,
        job_manager: JobManager = Depends(get_job_manager),
        current_user: dict = Depends(get_current_user_optional)
    ):
        """Delete a specific processing job."""
        try:
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Check if user has access to delete this job
            user_id = current_user["id"] if current_user else None
            if job.user_id and job.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied to delete this job")
            
            success = job_manager.delete_job(job_id)
            if not success:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return {"message": f"Job {job_id} deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/jobs")
    async def clear_all_jobs(
        request: Request,
        job_manager: JobManager = Depends(get_job_manager),
        current_user: dict = Depends(get_current_user_optional)
    ):
        """Clear all processing jobs for the current user."""
        try:
            # Get user's jobs
            user_id = current_user["id"] if current_user else None
            jobs = job_manager.list_jobs(user_id=user_id)
            
            # Delete each job
            deleted_count = 0
            for job in jobs:
                if job_manager.delete_job(job.job_id):
                    deleted_count += 1
            
            return {
                "message": f"Cleared {deleted_count} jobs successfully",
                "deleted_count": deleted_count
            }
        except Exception as e:
            logger.error(f"Failed to clear all jobs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "video-to-robot-processing"}
    
    logger.info("FastAPI application created successfully")
    return app
