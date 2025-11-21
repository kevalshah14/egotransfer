"""
Admin Routes
============
Admin endpoints for viewing users and managing the system.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging
import json

from models.database import get_db
from services.user_service import UserService
from services.video_service import VideoService
from services.audit_service import AuditService
from routes.admin_auth import require_admin, get_client_ip, get_user_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    List all users (requires admin access).
    
    - **limit**: Maximum number of users to return (1-1000)
    - **offset**: Number of users to skip for pagination
    """
    try:
        users = await UserService.list_all_users(db, limit=limit, offset=offset)
        total_count = await UserService.count_users(db)
        
        # Log admin action
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="list_users",
            resource_type="user",
            details={"limit": limit, "offset": offset, "total_count": total_count},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "login_count": user.login_count,
                }
                for user in users
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get user details by ID (requires admin access)."""
    try:
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's active sessions
        sessions = await UserService.get_user_sessions(db, user_id)
        
        # Log admin action
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="view_user",
            resource_type="user",
            resource_id=user_id,
            details={"viewed_user_email": user.email},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "login_count": user.login_count,
            "active_sessions": len(sessions),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                }
                for session in sessions
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.get("/stats")
async def get_admin_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get admin statistics (requires admin access)."""
    try:
        total_users = await UserService.count_users(db)
        
        # Get recent users (last 24 hours)
        recent_users = await UserService.list_all_users(db, limit=1000, offset=0)
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_count = sum(1 for u in recent_users if u.created_at and u.created_at >= cutoff)
        
        # Get video statistics
        total_videos = await VideoService.count_all_videos(db)
        recent_videos = await VideoService.list_all_videos(db, limit=1000, offset=0)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        videos_last_24h_count = sum(1 for v in recent_videos if v.created_at and v.created_at >= cutoff)
        
        stats = {
            "total_users": total_users,
            "users_last_24h": recent_count,
            "total_videos": total_videos,
            "videos_last_24h": videos_last_24h_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log admin action
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="view_stats",
            resource_type="system",
            details=stats,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/videos")
async def list_videos(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    List all videos (requires admin access).
    
    - **limit**: Maximum number of videos to return (1-1000)
    - **offset**: Number of videos to skip for pagination
    - **status**: Filter by status (uploaded, processing, completed, failed)
    """
    try:
        videos = await VideoService.list_all_videos(db, limit=limit, offset=offset, status=status)
        total_count = await VideoService.count_all_videos(db, status=status)
        
        # Log admin action
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="list_videos",
            resource_type="video",
            details={"limit": limit, "offset": offset, "status": status, "total_count": total_count},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {
            "videos": [
                {
                    "id": video.id,
                    "user_id": video.user_id,
                    "filename": video.filename,
                    "original_filename": video.original_filename,
                    "file_size": video.file_size,
                    "duration": video.duration,
                    "width": video.width,
                    "height": video.height,
                    "fps": video.fps,
                    "format": video.format,
                    "status": video.status,
                    "job_id": video.job_id,
                    "created_at": video.created_at.isoformat() if video.created_at else None,
                    "updated_at": video.updated_at.isoformat() if video.updated_at else None,
                }
                for video in videos
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


@router.get("/videos/user/{user_id}")
async def list_user_videos(
    user_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    List videos for a specific user (requires admin access).
    
    - **user_id**: User ID to get videos for
    - **limit**: Maximum number of videos to return (1-1000)
    - **offset**: Number of videos to skip for pagination
    - **status**: Filter by status (uploaded, processing, completed, failed)
    """
    try:
        videos = await VideoService.list_videos_by_user(db, user_id, limit=limit, offset=offset, status=status)
        total_count = await VideoService.count_videos_by_user(db, user_id, status=status)
        
        # Log admin action
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="list_user_videos",
            resource_type="video",
            resource_id=user_id,
            details={"limit": limit, "offset": offset, "status": status, "total_count": total_count},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {
            "videos": [
                {
                    "id": video.id,
                    "user_id": video.user_id,
                    "filename": video.filename,
                    "original_filename": video.original_filename,
                    "file_size": video.file_size,
                    "duration": video.duration,
                    "width": video.width,
                    "height": video.height,
                    "fps": video.fps,
                    "format": video.format,
                    "status": video.status,
                    "job_id": video.job_id,
                    "created_at": video.created_at.isoformat() if video.created_at else None,
                    "updated_at": video.updated_at.isoformat() if video.updated_at else None,
                }
                for video in videos
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to list user videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list user videos: {str(e)}")


@router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin_user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Get audit logs (requires admin access).
    
    - **limit**: Maximum number of logs to return (1-1000)
    - **offset**: Number of logs to skip for pagination
    - **admin_user_id**: Filter by admin user ID
    - **action**: Filter by action type
    - **resource_type**: Filter by resource type
    """
    try:
        logs = await AuditService.get_audit_logs(
            db=db,
            admin_user_id=admin_user_id,
            action=action,
            resource_type=resource_type,
            limit=limit,
            offset=offset
        )
        total_count = await AuditService.count_audit_logs(
            db=db,
            admin_user_id=admin_user_id,
            action=action,
            resource_type=resource_type
        )
        
        # Log admin action (viewing audit logs)
        await AuditService.log_action(
            db=db,
            admin_user_id=admin_user["id"],
            admin_email=admin_user["email"],
            action="view_audit_logs",
            resource_type="audit_log",
            details={"limit": limit, "offset": offset, "filters": {"admin_user_id": admin_user_id, "action": action, "resource_type": resource_type}},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "admin_user_id": log.admin_user_id,
                    "admin_email": log.admin_email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": json.loads(log.details) if log.details else None,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

