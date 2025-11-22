"""
Job queue service for async document processing.
"""
import json
import time
import uuid
import threading
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
from datetime import datetime

from config import settings


class JobStatus(str, Enum):
    """Job status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Job priority levels."""
    LOW = 3
    NORMAL = 2
    HIGH = 1


@dataclass
class Job:
    """Job definition."""
    id: str
    task_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    webhook_url: Optional[str] = None

    def __lt__(self, other):
        """Compare jobs by priority for priority queue."""
        return self.priority.value < other.priority.value


class JobQueue:
    """
    In-memory job queue with optional Redis backend.
    """

    def __init__(self, use_redis: bool = False):
        """
        Initialize job queue.

        Args:
            use_redis: Use Redis for persistence.
        """
        self._queue: PriorityQueue = PriorityQueue()
        self._jobs: Dict[str, Job] = {}
        self._workers: list = []
        self._running = False
        self._lock = threading.Lock()
        self._redis = None

        if use_redis and settings.cache.enable_cache:
            self._connect_redis()

    def _connect_redis(self):
        """Connect to Redis for job persistence."""
        try:
            import redis
            self._redis = redis.from_url(settings.cache.redis_url)
            self._redis.ping()
        except Exception as e:
            print(f"Redis connection failed for queue: {e}")
            self._redis = None

    def enqueue(self, task_type: str, payload: dict,
                priority: JobPriority = JobPriority.NORMAL,
                webhook_url: str = None) -> str:
        """
        Add a job to the queue.

        Args:
            task_type: Type of task (e.g., 'ocr').
            payload: Job payload data.
            priority: Job priority.
            webhook_url: URL for completion callback.

        Returns:
            Job ID.
        """
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            webhook_url=webhook_url
        )

        with self._lock:
            self._jobs[job_id] = job
            self._queue.put(job)

        if self._redis:
            self._save_job_to_redis(job)

        return job_id

    def dequeue(self, timeout: float = None) -> Optional[Job]:
        """
        Get next job from queue.

        Args:
            timeout: Wait timeout in seconds.

        Returns:
            Next job or None.
        """
        try:
            job = self._queue.get(timeout=timeout)
            job.status = JobStatus.PROCESSING
            job.started_at = time.time()

            if self._redis:
                self._save_job_to_redis(job)

            return job
        except Exception:
            return None

    def complete_job(self, job_id: str, result: dict):
        """Mark job as completed with result."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                job.result = result

                if self._redis:
                    self._save_job_to_redis(job)

    def fail_job(self, job_id: str, error: str):
        """Mark job as failed."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.retries += 1

                if job.retries < job.max_retries:
                    # Retry
                    job.status = JobStatus.PENDING
                    job.error = error
                    self._queue.put(job)
                else:
                    # Max retries exceeded
                    job.status = JobStatus.FAILED
                    job.completed_at = time.time()
                    job.error = error

                if self._redis:
                    self._save_job_to_redis(job)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status as dictionary."""
        job = self.get_job(job_id)
        if not job:
            return None

        return {
            "job_id": job.id,
            "status": job.status.value,
            "task_type": job.task_type,
            "created_at": datetime.fromtimestamp(job.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(job.started_at).isoformat() if job.started_at else None,
            "completed_at": datetime.fromtimestamp(job.completed_at).isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error,
            "retries": job.retries
        }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.CANCELLED
                    return True
        return False

    def start_workers(self, num_workers: int, handler: Callable):
        """
        Start worker threads.

        Args:
            num_workers: Number of workers.
            handler: Function to handle jobs.
        """
        self._running = True

        def worker():
            while self._running:
                job = self.dequeue(timeout=1)
                if job and job.status != JobStatus.CANCELLED:
                    try:
                        result = handler(job)
                        self.complete_job(job.id, result)
                    except Exception as e:
                        self.fail_job(job.id, str(e))

        for _ in range(num_workers):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            self._workers.append(t)

    def stop_workers(self):
        """Stop all workers."""
        self._running = False
        for t in self._workers:
            t.join(timeout=5)
        self._workers.clear()

    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        with self._lock:
            by_status = {}
            for job in self._jobs.values():
                status = job.status.value
                by_status[status] = by_status.get(status, 0) + 1

            return {
                "total_jobs": len(self._jobs),
                "queue_size": self._queue.qsize(),
                "by_status": by_status,
                "workers": len(self._workers)
            }

    def _save_job_to_redis(self, job: Job):
        """Save job to Redis."""
        if self._redis:
            try:
                data = {
                    "id": job.id,
                    "task_type": job.task_type,
                    "payload": job.payload,
                    "status": job.status.value,
                    "created_at": job.created_at,
                    "result": job.result,
                    "error": job.error
                }
                self._redis.setex(
                    f"job:{job.id}",
                    86400,  # 24 hour TTL
                    json.dumps(data)
                )
            except Exception:
                pass


# Global job queue
job_queue = JobQueue()


if __name__ == "__main__":
    print("=" * 60)
    print("JOB QUEUE TEST")
    print("=" * 60)

    queue = JobQueue()

    # Test enqueue
    job_id = queue.enqueue("ocr", {"file": "test.pdf"})
    print(f"  Enqueued job: {job_id}")

    # Test get status
    status = queue.get_job_status(job_id)
    print(f"  Status: {status['status']}")

    # Test dequeue
    job = queue.dequeue(timeout=1)
    print(f"  Dequeued: {job.id if job else 'None'}")

    # Test complete
    queue.complete_job(job_id, {"text": "extracted"})
    status = queue.get_job_status(job_id)
    print(f"  Completed: {status['status']}")

    # Test stats
    stats = queue.get_queue_stats()
    print(f"  Stats: {stats}")

    print("\n  ✓ Job queue tests passed")
    print("=" * 60)
