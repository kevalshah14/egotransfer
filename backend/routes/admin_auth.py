"""
Admin Authentication
====================
Dependencies and utilities for admin access control.
"""

from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from models.database import get_db
from services.user_service import UserService
from routes.auth import get_current_user_required

logger = logging.getLogger(__name__)


async def require_admin(
    request: Request,
    current_user: dict = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Dependency to require admin access.
    Checks if user is admin via database field or email list.
    """
    # Get full user record from database
    user = await UserService.get_user_by_id(db, current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    # Check admin status
    if not user.is_admin:
        # Also check email list as fallback (for environment variable)
        import os
        admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
        admin_emails = [e.strip().lower() for e in admin_emails if e.strip()]
        
        if current_user["email"].lower() not in admin_emails:
            logger.warning(f"Unauthorized admin access attempt by {current_user['email']}")
            raise HTTPException(
                status_code=403,
                detail="Admin access required. You do not have permission to access this resource."
            )
        else:
            # Grant admin if in email list but not in DB
            user.is_admin = True
            await db.commit()
            logger.info(f"Granted admin access to {current_user['email']} via email list")
    
    # Return user dict with admin flag
    return {
        **current_user,
        "is_admin": True
    }


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    # Check for forwarded IP (common in proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")

