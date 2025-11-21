"""
Video Service
=============
Service for managing videos in the database.
"""

from datetime import datetime
from typing import Optional, List
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
import logging

from models.database import Video

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video database operations."""
    
    @staticmethod
    async def create_video(
        db: AsyncSession,
        video_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        duration: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
        format: Optional[str] = None,
        status: str = "uploaded"
    ) -> Video:
        """Create a new video record."""
        video = Video(
            id=video_id,
            user_id=user_id,
            filename=filename,
            original_filename=filename,
            file_path=file_path,
            file_size=file_size,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            format=format,
            status=status,
            job_id=job_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(video)
        await db.commit()
        await db.refresh(video)
        logger.info(f"Created video record: {video_id} ({filename})")
        return video
    
    @staticmethod
    async def get_video_by_id(db: AsyncSession, video_id: str) -> Optional[Video]:
        """Get video by ID."""
        result = await db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_video_by_job_id(db: AsyncSession, job_id: str) -> Optional[Video]:
        """Get video by job ID."""
        result = await db.execute(select(Video).where(Video.job_id == job_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_video(
        db: AsyncSession,
        video_id: str,
        **updates
    ) -> Optional[Video]:
        """Update video with new data."""
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return None
        
        for key, value in updates.items():
            if hasattr(video, key):
                setattr(video, key, value)
        
        video.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(video)
        logger.debug(f"Updated video {video_id}: {updates}")
        return video
    
    @staticmethod
    async def list_videos_by_user(
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Video]:
        """List videos for a specific user."""
        query = select(Video).where(Video.user_id == user_id)
        
        if status:
            query = query.where(Video.status == status)
        
        query = query.order_by(Video.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def list_all_videos(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Video]:
        """List all videos."""
        query = select(Video)
        
        if status:
            query = query.where(Video.status == status)
        
        query = query.order_by(Video.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_videos_by_user(
        db: AsyncSession,
        user_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count videos for a user."""
        query = select(func.count(Video.id)).where(Video.user_id == user_id)
        
        if status:
            query = query.where(Video.status == status)
        
        result = await db.execute(query)
        return result.scalar_one() or 0
    
    @staticmethod
    async def count_all_videos(
        db: AsyncSession,
        status: Optional[str] = None
    ) -> int:
        """Count all videos."""
        query = select(func.count(Video.id))
        
        if status:
            query = query.where(Video.status == status)
        
        result = await db.execute(query)
        return result.scalar_one() or 0
    
    @staticmethod
    async def delete_video(db: AsyncSession, video_id: str) -> bool:
        """Delete a video record."""
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return False
        
        await db.delete(video)
        await db.commit()
        logger.info(f"Deleted video record: {video_id}")
        return True
    
    @staticmethod
    async def update_video_status(
        db: AsyncSession,
        video_id: str,
        status: str,
        processed_video_path: Optional[str] = None
    ) -> Optional[Video]:
        """Update video status."""
        updates = {"status": status, "updated_at": datetime.utcnow()}
        if processed_video_path:
            updates["processed_video_path"] = processed_video_path
        
        return await VideoService.update_video(db, video_id, **updates)

