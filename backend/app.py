"""
FastAPI Application Factory
==========================
Creates and configures the FastAPI application with all routes and middleware.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from routes import ai_processing, hand_processing, robot_control
from services.job_manager import JobManager, get_job_manager

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(ai_processing.router)
    app.include_router(hand_processing.router)
    app.include_router(robot_control.router)
    
    # Add general jobs endpoints
    @app.get("/jobs")
    async def get_all_jobs(
        job_manager: JobManager = Depends(get_job_manager)
    ):
        """Get all processing jobs."""
        try:
            jobs = job_manager.list_jobs()
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
        job_manager: JobManager = Depends(get_job_manager)
    ):
        """Get the status of a processing job."""
        try:
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
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
        job_manager: JobManager = Depends(get_job_manager)
    ):
        """Delete a specific processing job."""
        try:
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
        job_manager: JobManager = Depends(get_job_manager)
    ):
        """Clear all processing jobs."""
        try:
            deleted_count = job_manager.delete_all_jobs()
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
