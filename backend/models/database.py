"""
Database Models and Connection
==============================
SQLAlchemy models and database connection setup for user and session management.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, Float, ForeignKey, Boolean

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert postgres:// to postgresql+asyncpg:// for async support
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine (only if DATABASE_URL is provided)
engine = None
if DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Create async session factory (only if engine exists)
AsyncSessionLocal = None
if engine:
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model for OAuth-authenticated users."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Google user ID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name}, is_admin={self.is_admin})>"


class Session(Base):
    """Session model for tracking user sessions."""
    __tablename__ = "sessions"
    
    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id})>"


class Video(Base):
    """Video model for storing uploaded video metadata."""
    __tablename__ = "videos"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # job_id or unique video ID
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # Path to uploaded file
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Duration in seconds
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Video width in pixels
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Video height in pixels
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Frames per second
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Video format (mp4, avi, etc.)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)  # uploaded, processing, completed, failed
    job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # Associated processing job
    processed_video_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Path to processed video
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Video(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


class AuditLog(Base):
    """Audit log model for tracking admin actions."""
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "list_users", "view_user", "list_videos"
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "user", "video"
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID of the resource accessed
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string with additional details
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, admin={self.admin_email}, action={self.action}, created_at={self.created_at})>"


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    if not AsyncSessionLocal:
        raise RuntimeError("Database not configured. Please set DATABASE_URL environment variable.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    if not engine:
        logging.warning("DATABASE_URL not set. Database features will be disabled.")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()

