"""
Thread-safe generation queue with per-GPU allocation for concurrent jobs.

All Streamlit sessions run in the same Python process, so a module-level singleton
with threading locks coordinates access. Supports running multiple jobs concurrently
when each job is assigned to distinct GPUs.
"""

import threading
import time
from collections import OrderedDict

import streamlit as st


class GpuAwareQueue:
    """Thread-safe queue that allocates GPUs to concurrent generation jobs.

    Supports both legacy single-job mode (backward compatible) and multi-GPU
    concurrent mode where multiple jobs run simultaneously on different GPUs.

    Internal state:
        _queue: OrderedDict of waiting jobs (job_id -> metadata).
        _gpu_assignments: Mapping of gpu_id -> job metadata for occupied GPUs.
        _active_jobs: Mapping of job_id -> job info (gpu_ids, task, etc.)
                      for currently running jobs.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._queue: OrderedDict[str, dict] = OrderedDict()
        self._gpu_assignments: dict[int, dict] = {}  # gpu_id -> {job_id, task, started_at}
        self._active_jobs: dict[str, dict] = {}  # job_id -> {gpu_ids, task, prompt_preview, started_at}

    def submit(self, job_id: str, task: str, prompt_preview: str, requested_gpus: int = 1) -> None:
        """Add a job to the queue.

        Args:
            job_id: Unique identifier for the job.
            task: Task type (e.g., 't2v-A14B').
            prompt_preview: Short preview of the prompt text.
            requested_gpus: Number of GPUs requested (default 1, backward compat).
        """
        with self._lock:
            self._queue[job_id] = {
                "task": task,
                "prompt_preview": prompt_preview,
                "requested_gpus": requested_gpus,
            }

    def get_position(self, job_id: str) -> int:
        """Get 0-based position in queue. Returns -1 if not found."""
        with self._lock:
            for i, qid in enumerate(self._queue):
                if qid == job_id:
                    return i
            return -1

    def get_queue_length(self) -> int:
        """Get number of waiting jobs."""
        with self._lock:
            return len(self._queue)

    def get_active_info(self) -> dict | None:
        """Get info about the first active job, or None if idle.

        Backward compatible: returns a dict with 'task' and 'prompt_preview'
        matching the old GenerationQueue interface.
        """
        with self._lock:
            if self._active_jobs:
                # Return info about the first active job for legacy compat
                first_job_id = next(iter(self._active_jobs))
                info = self._active_jobs[first_job_id]
                return {
                    "task": info["task"],
                    "prompt_preview": info["prompt_preview"],
                    "gpu_ids": info["gpu_ids"],
                    "job_id": first_job_id,
                }
            return None

    def get_active_jobs(self) -> dict[str, dict]:
        """Get all currently active (running) jobs.

        Returns:
            Dict of job_id -> {gpu_ids, task, prompt_preview, started_at}
        """
        with self._lock:
            return dict(self._active_jobs)

    def get_free_gpus(self, total_gpus: int) -> list[int]:
        """Get list of GPU indices that are not currently assigned to any job.

        Args:
            total_gpus: Total number of GPUs available on the system.

        Returns:
            Sorted list of free GPU indices.
        """
        with self._lock:
            all_gpus = set(range(total_gpus))
            occupied = set(self._gpu_assignments.keys())
            return sorted(all_gpus - occupied)

    def try_acquire(self, job_id: str, gpu_ids: list[int] | None = None) -> list[int] | None:
        """Try to acquire GPU(s) for a job.

        Args:
            job_id: The job requesting GPUs.
            gpu_ids: Specific GPU indices to acquire. If None, behaves in legacy
                     single-job mode: acquires only if no other jobs are active,
                     and returns [0] as a default GPU list.

        Returns:
            List of acquired GPU IDs on success, None on failure.
        """
        with self._lock:
            if gpu_ids is None:
                # Legacy single-job mode: only one job at a time
                if self._active_jobs:
                    return None
                # Only the first job in queue can acquire
                if self._queue:
                    first_id = next(iter(self._queue))
                    if first_id != job_id:
                        return None
                # Acquire with default GPU [0]
                info = self._queue.pop(job_id, {"task": "unknown", "prompt_preview": ""})
                acquired = [0]
                self._active_jobs[job_id] = {
                    "gpu_ids": acquired,
                    "task": info["task"],
                    "prompt_preview": info.get("prompt_preview", ""),
                    "started_at": time.time(),
                }
                for gid in acquired:
                    self._gpu_assignments[gid] = {
                        "job_id": job_id,
                        "task": info["task"],
                        "started_at": time.time(),
                    }
                return acquired
            else:
                # Multi-GPU mode: check requested GPUs are all free
                for gid in gpu_ids:
                    if gid in self._gpu_assignments:
                        return None
                # All requested GPUs are free -- acquire them
                info = self._queue.pop(job_id, {"task": "unknown", "prompt_preview": ""})
                self._active_jobs[job_id] = {
                    "gpu_ids": list(gpu_ids),
                    "task": info["task"],
                    "prompt_preview": info.get("prompt_preview", ""),
                    "started_at": time.time(),
                }
                now = time.time()
                for gid in gpu_ids:
                    self._gpu_assignments[gid] = {
                        "job_id": job_id,
                        "task": info["task"],
                        "started_at": now,
                    }
                return list(gpu_ids)

    def release(self, job_id: str) -> None:
        """Release all GPUs held by a job after completion."""
        with self._lock:
            job_info = self._active_jobs.pop(job_id, None)
            if job_info is not None:
                for gid in job_info.get("gpu_ids", []):
                    self._gpu_assignments.pop(gid, None)

    def cancel(self, job_id: str) -> None:
        """Remove a job from the queue (before it starts running)."""
        with self._lock:
            self._queue.pop(job_id, None)


# Module-level singleton -- backward compatible with existing imports
generation_queue = GpuAwareQueue()


def wait_for_queue_turn(
    job_id: str, cancellation_check=None, gpu_ids: list[int] | None = None
) -> list[int] | None:
    """Wait until this job can run. Shows queue position in st.status if waiting.

    Args:
        job_id: Unique job identifier (must have been submitted first).
        cancellation_check: Optional callable returning True if the job should
                            be cancelled. Passed positionally by existing callers.
        gpu_ids: Optional list of specific GPU indices to acquire. When None,
                 falls back to legacy single-job behavior.

    Returns:
        List of acquired GPU IDs on success (truthy), or None if cancelled (falsy).
        Existing callers using ``if not wait_for_queue_turn(...)`` continue to
        work because a non-empty list is truthy and None is falsy.
    """
    # Fast path: try to acquire immediately
    acquired = generation_queue.try_acquire(job_id, gpu_ids)
    if acquired is not None:
        return acquired

    # Need to wait -- show queue UI
    with st.status("Waiting in queue...", expanded=True) as status:
        while True:
            # Check cancellation
            if cancellation_check and cancellation_check():
                generation_queue.cancel(job_id)
                status.update(label="Cancelled while waiting in queue", state="error")
                return None

            # Try to acquire
            acquired = generation_queue.try_acquire(job_id, gpu_ids)
            if acquired is not None:
                status.update(label="Queue position acquired", state="complete")
                return acquired

            # Show position
            pos = generation_queue.get_position(job_id)
            active_jobs = generation_queue.get_active_jobs()
            if pos >= 0:
                msg = f"Position in queue: {pos + 1}"
                if active_jobs:
                    running_count = len(active_jobs)
                    gpu_count = sum(
                        len(j["gpu_ids"]) for j in active_jobs.values()
                    )
                    tasks = ", ".join(j["task"] for j in active_jobs.values())
                    msg += (
                        f" ({running_count} job{'s' if running_count != 1 else ''}"
                        f" running on {gpu_count} GPU{'s' if gpu_count != 1 else ''}"
                        f": {tasks})"
                    )
                st.write(msg)
                status.update(label=f"Waiting in queue (position {pos + 1})...")

            time.sleep(1)


def get_queue_status_message() -> str | None:
    """Get a human-readable queue status string, or None if idle.

    Returns messages like:
    - "1 job running on GPUs [0, 1] (t2v-A14B)"
    - "2 jobs running on 4 GPUs, 1 in queue"
    """
    active_jobs = generation_queue.get_active_jobs()
    queue_len = generation_queue.get_queue_length()

    if not active_jobs and queue_len == 0:
        return None

    parts = []
    if active_jobs:
        count = len(active_jobs)
        all_gpus = []
        tasks = []
        for info in active_jobs.values():
            all_gpus.extend(info["gpu_ids"])
            tasks.append(info["task"])
        task_str = ", ".join(tasks)
        if count == 1:
            parts.append(f"1 job running on GPU{'s' if len(all_gpus) > 1 else ''} {all_gpus} ({task_str})")
        else:
            parts.append(
                f"{count} jobs running on {len(all_gpus)} GPUs ({task_str})"
            )
    if queue_len > 0:
        parts.append(f"{queue_len} in queue")

    return ", ".join(parts)
