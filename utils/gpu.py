"""
GPU utilities for detecting and managing NVIDIA GPUs.
"""

import subprocess


def get_available_gpus() -> int:
    """
    Get number of available NVIDIA GPUs.

    Returns:
        int: Number of GPUs detected, defaults to 1 if detection fails
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(result.stdout.strip().split("\n"))
    except Exception:
        return 1


def get_gpu_info() -> list[dict]:
    """
    Get detailed GPU information including memory usage.

    Returns:
        list[dict]: List of GPU information dictionaries with keys:
            - index: GPU index
            - name: GPU model name
            - memory_total_mb: Total memory in MB
            - memory_used_mb: Used memory in MB
            - memory_free_mb: Free memory in MB
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        gpus = []
        for line in result.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpus.append(
                    {
                        "index": int(parts[0]),
                        "name": parts[1],
                        "memory_total_mb": int(parts[2]),
                        "memory_used_mb": int(parts[3]),
                        "memory_free_mb": int(parts[4]),
                    }
                )
        return gpus
    except Exception:
        return []
