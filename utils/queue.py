"""
Thread-safe generation queue for coordinating GPU access across Streamlit sessions.

All Streamlit sessions run in the same Python process, so a module-level singleton
with threading locks coordinates access to prevent torchrun port conflicts.
"""

import threading
import time
from collections import OrderedDict

import streamlit as st


class GenerationQueue:
    """Thread-safe queue that ensures only one generation runs at a time."""

    def __init__(self):
        self._lock = threading.Lock()
        self._queue: OrderedDict[str, dict] = OrderedDict()
        self._active_job_id: str | None = None
        self._active_info: dict | None = None

    def submit(self, job_id: str, task: str, prompt_preview: str) -> None:
        """Add a job to the queue."""
        with self._lock:
            self._queue[job_id] = {
                "task": task,
                "prompt_preview": prompt_preview,
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
        """Get info about the currently running job, or None if idle."""
        with self._lock:
            if self._active_job_id is not None:
                return self._active_info
            return None

    def try_acquire(self, job_id: str) -> bool:
        """Try to acquire the generation slot. Returns True if acquired."""
        with self._lock:
            if self._active_job_id is not None:
                return False
            # Only the first job in queue can acquire
            if self._queue:
                first_id = next(iter(self._queue))
                if first_id != job_id:
                    return False
            # Acquire
            info = self._queue.pop(job_id, {"task": "unknown", "prompt_preview": ""})
            self._active_job_id = job_id
            self._active_info = info
            return True

    def release(self, job_id: str) -> None:
        """Release the generation slot after completion."""
        with self._lock:
            if self._active_job_id == job_id:
                self._active_job_id = None
                self._active_info = None

    def cancel(self, job_id: str) -> None:
        """Remove a job from the queue (before it starts running)."""
        with self._lock:
            self._queue.pop(job_id, None)


# Module-level singleton
generation_queue = GenerationQueue()


def wait_for_queue_turn(job_id: str, cancellation_check=None) -> bool:
    """
    Wait until this job can run. Shows queue position in st.status if waiting.

    Returns True when acquired, False if cancelled.
    """
    # Fast path: try to acquire immediately
    if generation_queue.try_acquire(job_id):
        return True

    # Need to wait — show queue UI
    with st.status("Waiting in queue...", expanded=True) as status:
        while True:
            # Check cancellation
            if cancellation_check and cancellation_check():
                generation_queue.cancel(job_id)
                status.update(label="Cancelled while waiting in queue", state="error")
                return False

            # Try to acquire
            if generation_queue.try_acquire(job_id):
                status.update(label="Queue position acquired", state="complete")
                return True

            # Show position
            pos = generation_queue.get_position(job_id)
            active = generation_queue.get_active_info()
            if pos >= 0:
                msg = f"Position in queue: {pos + 1}"
                if active:
                    msg += f" (running: {active['task']})"
                st.write(msg)
                status.update(label=f"Waiting in queue (position {pos + 1})...")

            time.sleep(1)


def get_queue_status_message() -> str | None:
    """
    Get a human-readable queue status string, or None if idle.

    Returns messages like:
    - "1 generation running"
    - "1 generation running, 2 in queue"
    """
    active = generation_queue.get_active_info()
    queue_len = generation_queue.get_queue_length()

    if active is None and queue_len == 0:
        return None

    parts = []
    if active is not None:
        parts.append(f"1 generation running ({active['task']})")
    if queue_len > 0:
        parts.append(f"{queue_len} in queue")

    return ", ".join(parts)
