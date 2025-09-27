"""
Job Manager Service
==================
Manages processing jobs with thread-safe operations and persistence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock
import logging

from functools import lru_cache
from backend.models.schemas import ProcessingJob, JobStatus

logger = logging.getLogger(__name__)


class JobManager:
    """Thread-safe job manager for processing tasks."""
    
    def __init__(self, jobs_file: Path = None):
        """Initialize job manager with optional persistence."""
        self._jobs: Dict[str, ProcessingJob] = {}
        self._lock = Lock()
        self.jobs_file = jobs_file or Path("jobs.json")
        self._load_jobs()
    
    def create_job(self, video_name: str, **kwargs) -> str:
        """Create a new processing job."""
        job_id = str(uuid.uuid4())[:8]
        
        job = ProcessingJob(
            job_id=job_id,
            video_name=video_name,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **kwargs
        )
        
        with self._lock:
            self._jobs[job_id] = job
            
        self._save_jobs()
        logger.info(f"Created job {job_id} for video {video_name}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, **updates) -> bool:
        """Update job with new data."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            # Update job data
            job_data = self._jobs[job_id].dict()
            job_data.update(updates)
            job_data['updated_at'] = datetime.now()
            
            self._jobs[job_id] = ProcessingJob(**job_data)
            
        self._save_jobs()
        logger.debug(f"Updated job {job_id}: {updates}")
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job by ID."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            del self._jobs[job_id]
            
        self._save_jobs()
        logger.info(f"Deleted job {job_id}")
        return True
    
    def list_jobs(self, status: Optional[JobStatus] = None) -> List[ProcessingJob]:
        """List all jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._jobs.values())
            
        if status:
            jobs = [job for job in jobs if job.status == status]
            
        # Sort by creation time, newest first
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)
    
    def get_active_jobs_count(self) -> int:
        """Get count of active (pending/processing) jobs."""
        active_statuses = {JobStatus.PENDING, JobStatus.PROCESSING}
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status in active_statuses)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and clean up its associated files."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            # Clean up associated files
            self._cleanup_job_files(job)
            
            # Remove from jobs
            del self._jobs[job_id]
            
        self._save_jobs()
        logger.info(f"Deleted job {job_id}")
        return True
    
    def delete_all_jobs(self) -> int:
        """Delete all jobs and clean up all associated files."""
        count = 0
        with self._lock:
            for job in self._jobs.values():
                self._cleanup_job_files(job)
                count += 1
            
            self._jobs.clear()
        
        self._save_jobs()
        logger.info(f"Deleted all {count} jobs")
        return count
    
    def _cleanup_job_files(self, job: ProcessingJob):
        """Clean up all files associated with a job."""
        files_to_delete = []
        
        # Original uploaded video
        original_video = Path(f"uploads/{job.job_id}_{job.video_name}")
        if original_video.exists():
            files_to_delete.append(original_video)
        
        # Processed files
        if job.processed_files:
            for file_type, filename in job.processed_files.items():
                file_path = Path(f"processed/{filename}")
                if file_path.exists():
                    files_to_delete.append(file_path)
        
        # Delete all files
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        deleted_count = 0
        
        with self._lock:
            jobs_to_delete = []
            for job_id, job in self._jobs.items():
                if (job.status in {JobStatus.COMPLETED, JobStatus.FAILED} and 
                    job.updated_at.timestamp() < cutoff_time):
                    jobs_to_delete.append(job_id)
            
            for job_id in jobs_to_delete:
                del self._jobs[job_id]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_jobs()
            logger.info(f"Cleaned up {deleted_count} old jobs")
            
        return deleted_count
    
    def _load_jobs(self):
        """Load jobs from persistence file."""
        if not self.jobs_file.exists():
            return
            
        try:
            with open(self.jobs_file, 'r') as f:
                jobs_data = json.load(f)
                
            for job_data in jobs_data:
                job = ProcessingJob(**job_data)
                self._jobs[job.job_id] = job
                
            logger.info(f"Loaded {len(self._jobs)} jobs from {self.jobs_file}")
            
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
    
    def _save_jobs(self):
        """Save jobs to persistence file."""
        try:
            jobs_data = [job.dict() for job in self._jobs.values()]
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def get_stats(self) -> Dict:
        """Get job statistics."""
        with self._lock:
            stats = {
                'total_jobs': len(self._jobs),
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for job in self._jobs.values():
                status_key = job.status.value if hasattr(job.status, 'value') else job.status
                if status_key in stats:
                    stats[status_key] += 1
                
        return stats


# Dependency injection
_job_manager: Optional[JobManager] = None


@lru_cache()
def get_job_manager() -> JobManager:
    """Get job manager instance (singleton)."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
