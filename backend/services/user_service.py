"""
User Service
===========
Service for managing users and sessions in the database.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import logging

from models.database import User, Session

logger = logging.getLogger(__name__)


class UserService:
    """Service for user and session management."""
    
    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None
    ) -> User:
        """Get existing user or create a new one."""
        # Try to get existing user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Update last login and increment login count
            user.last_login = datetime.utcnow()
            user.login_count += 1
            # Update name and picture if provided
            if name:
                user.name = name
            if picture:
                user.picture = picture
        else:
            # Create new user
            user = User(
                id=user_id,
                email=email,
                name=name,
                picture=picture,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                login_count=1
            )
            db.add(user)
            logger.info(f"Created new user: {email}")
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        session_id: str,
        user_id: str,
        expires_in_hours: int = 24
    ) -> Session:
        """Create a new session."""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_activity=datetime.utcnow()
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        result = await db.execute(select(Session).where(Session.session_id == session_id))
        session = result.scalar_one_or_none()
        
        if session:
            # Check if session is expired
            if session.expires_at and session.expires_at < datetime.utcnow():
                await UserService.delete_session(db, session_id)
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            await db.commit()
        
        return session
    
    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> bool:
        """Delete a session."""
        result = await db.execute(delete(Session).where(Session.session_id == session_id))
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete_user_sessions(db: AsyncSession, user_id: str) -> int:
        """Delete all sessions for a user."""
        result = await db.execute(delete(Session).where(Session.user_id == user_id))
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions."""
        result = await db.execute(
            delete(Session).where(Session.expires_at < datetime.utcnow())
        )
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def list_all_users(db: AsyncSession, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users with pagination."""
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def count_users(db: AsyncSession) -> int:
        """Get total number of users."""
        result = await db.execute(select(User))
        return len(result.scalars().all())
    
    @staticmethod
    async def get_user_sessions(db: AsyncSession, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
        )
        return list(result.scalars().all())

