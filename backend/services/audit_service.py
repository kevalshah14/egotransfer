"""
Audit Service
=============
Service for logging admin actions for security and compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import json
import logging

from models.database import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        admin_user_id: str,
        admin_email: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an admin action."""
        audit_log = AuditLog(
            admin_user_id=admin_user_id,
            admin_email=admin_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        logger.info(f"Audit log: {admin_email} performed {action} on {resource_type or 'system'}")
        return audit_log
    
    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """Get audit logs with optional filtering."""
        query = select(AuditLog)
        
        if admin_user_id:
            query = query.where(AuditLog.admin_user_id == admin_user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        query = query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_audit_logs(
        db: AsyncSession,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> int:
        """Count audit logs with optional filtering."""
        from sqlalchemy import func
        
        query = select(func.count(AuditLog.id))
        
        if admin_user_id:
            query = query.where(AuditLog.admin_user_id == admin_user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        result = await db.execute(query)
        return result.scalar_one() or 0

