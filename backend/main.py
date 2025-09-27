"""
Main FastAPI Application
========================
Production-level FastAPI application for Video-to-Robot processing.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

# Import routes
from backend.routes.robot_control import router as robot_router
from backend.routes.ai_processing import router as ai_router
from backend.routes.hand_processing import router as hand_router

# Import models and services
from backend.models.schemas import HealthCheck, APIError
from backend.services.job_manager import get_job_manager
from backend.services.robot_service import get_robot_service
from backend.services.ai_service import get_ai_service
from backend.services.hand_service import get_hand_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
REQUIRED_DIRS = ['uploads', 'processed', 'feedback', 'static', 'logs']
for dir_name in REQUIRED_DIRS:
    Path(dir_name).mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("🚀 Video-to-Robot API starting up...")
    
    # Initialize services
    job_manager = get_job_manager()
    robot_service = get_robot_service()
    ai_service = get_ai_service()
    hand_service = get_hand_service()
    
    logger.info("✅ Services initialized")
    
    # Cleanup old jobs on startup
    cleaned = job_manager.cleanup_old_jobs(max_age_hours=24)
    if cleaned > 0:
        logger.info(f"🧹 Cleaned up {cleaned} old jobs")
    
    yield
    
    # Shutdown
    logger.info("🛑 Video-to-Robot API shutting down...")
    
    # Disconnect robot if connected
    try:
        await robot_service.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting robot: {e}")
    
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Video-to-Robot Processing API",
    description="""
    Production-level API for processing videos with hand tracking and controlling robots.
    
    ## Features
    
    * **Hand Processing**: Extract MANO-style hand landmarks with color coding
    * **AI Analysis**: Gemini-powered video understanding and task analysis  
    * **Robot Control**: Direct robot control and command playback
    * **Job Management**: Async processing with status tracking
    * **File Management**: Upload, process, and download files
    
    ## Architecture
    
    The API is organized into three main route groups:
    - `/hand` - Hand tracking and processing operations
    - `/ai` - AI-powered video analysis 
    - `/robot` - Robot control and command execution
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files from newfrontend
newfrontend_path = Path(__file__).parent.parent / "newfrontend" / "dist" / "public"
if newfrontend_path.exists():
    # Mount assets directory for CSS/JS files
    app.mount("/assets", StaticFiles(directory=str(newfrontend_path / "assets")), name="assets")
    # Mount static directory for any other static files
    app.mount("/static", StaticFiles(directory=str(newfrontend_path)), name="static")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIError(
            error=True,
            message=exc.detail,
            code=f"HTTP_{exc.status_code}",
            details={"path": str(request.url.path)}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIError(
            error=True,
            message="Internal server error",
            code="INTERNAL_ERROR",
            details={"path": str(request.url.path)}
        ).dict()
    )


# Include routers
app.include_router(robot_router)
app.include_router(ai_router)
app.include_router(hand_router)


# Main routes
@app.get("/", response_class=HTMLResponse)
async def get_main_page():
    """Serve the newfrontend web interface."""
    try:
        newfrontend_html = Path(__file__).parent.parent / "newfrontend" / "dist" / "public" / "index.html"
        if newfrontend_html.exists():
            with open(newfrontend_html, 'r') as f:
                return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Failed to serve newfrontend: {e}")
    
    # Fallback to embedded HTML
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video-to-Robot API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
            .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎥 Video-to-Robot Processing API</h1>
            <p>Production-level FastAPI server for hand tracking and robot control</p>
        </div>
        
        <div class="section">
            <h2>📚 API Documentation</h2>
            <div class="links">
                <a href="/docs">Interactive Docs</a>
                <a href="/redoc">ReDoc</a>
                <a href="/health">Health Check</a>
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 API Endpoints</h2>
            <ul>
                <li><strong>Hand Processing:</strong> /hand/* - Hand tracking and MANO landmarks</li>
                <li><strong>AI Analysis:</strong> /ai/* - Video analysis with Gemini AI</li>
                <li><strong>Robot Control:</strong> /robot/* - Robot control and command execution</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>🚀 Quick Start</h2>
            <ol>
                <li>Use <code>POST /hand/process</code> to upload and process videos</li>
                <li>Check job status with <code>GET /jobs/{job_id}</code></li>
                <li>Download results with <code>GET /hand/video/{job_id}</code></li>
                <li>Control robot with <code>POST /robot/command</code></li>
            </ol>
        </div>
    </body>
    </html>
    """)




@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Application health check."""
    try:
        job_manager = get_job_manager()
        robot_service = get_robot_service()
        ai_service = get_ai_service()
        hand_service = get_hand_service()
        
        # Check if services are available
        processing_available = (
            hand_service.processor is not None and 
            hand_service.converter is not None
        )
        
        ai_available = ai_service.genai_available
        robot_connected = await robot_service.is_connected()
        
        active_jobs = job_manager.get_active_jobs_count()
        
        return HealthCheck(
            status="healthy",
            timestamp=datetime.now(),
            processing_modules_available=processing_available,
            active_jobs=active_jobs,
            robot_connected=robot_connected,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/jobs")
async def list_all_jobs():
    """List all processing jobs across services."""
    try:
        job_manager = get_job_manager()
        jobs = job_manager.list_jobs()
        
        return {
            "success": True,
            "total_jobs": len(jobs),
            "jobs": [job.dict() for job in jobs],
            "stats": job_manager.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    try:
        job_manager = get_job_manager()
        success = job_manager.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True, "message": f"Job {job_id} and all associated files deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/jobs")
async def delete_all_jobs():
    """Delete all jobs and their associated files."""
    try:
        job_manager = get_job_manager()
        deleted_count = job_manager.delete_all_jobs()
        
        return {
            "success": True, 
            "message": f"Successfully deleted {deleted_count} jobs and all associated files",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to delete all jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Download processed files directly."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    try:
        # Security check - only allow certain file types
        allowed_types = ['video', 'data', 'json', 'mp4']
        if file_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Check in processed directory
        file_path = Path("processed") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Determine media type
        if filename.endswith('.mp4'):
            media_type = 'video/mp4'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_system_stats():
    """Get system-wide statistics."""
    try:
        job_manager = get_job_manager()
        ai_service = get_ai_service()
        robot_service = get_robot_service()
        
        # Get service stats
        job_stats = job_manager.get_stats()
        ai_stats = await ai_service.get_usage_stats()
        robot_status = await robot_service.get_status()
        
        # System stats
        system_stats = {
            "uptime": "unknown",  # TODO: Implement
            "total_disk_usage": 0,  # TODO: Implement
            "memory_usage": "unknown"  # TODO: Implement
        }
        
        return {
            "success": True,
            "timestamp": datetime.now(),
            "jobs": job_stats,
            "ai_service": ai_stats,
            "robot_service": robot_status.dict(),
            "system": system_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: Static files already mounted above for newfrontend


def create_app():
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    # This should not be used in production
    # Use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
