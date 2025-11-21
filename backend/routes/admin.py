"""
Admin Routes
============
Admin endpoints for viewing users and managing the system.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from models.database import get_db
from services.user_service import UserService
from routes.auth import get_current_user_required

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_required)
):
    """
    List all users (requires authentication).
    
    - **limit**: Maximum number of users to return (1-1000)
    - **offset**: Number of users to skip for pagination
    """
    try:
        users = await UserService.list_all_users(db, limit=limit, offset=offset)
        total_count = await UserService.count_users(db)
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture,
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
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_required)
):
    """Get user details by ID."""
    try:
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's active sessions
        sessions = await UserService.get_user_sessions(db, user_id)
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
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
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_required)
):
    """Get admin statistics."""
    try:
        total_users = await UserService.count_users(db)
        
        # Get recent users (last 24 hours)
        recent_users = await UserService.list_all_users(db, limit=1000, offset=0)
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_count = sum(1 for u in recent_users if u.created_at and u.created_at >= cutoff)
        
        return {
            "total_users": total_users,
            "users_last_24h": recent_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

