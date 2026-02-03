"""
GPU utilities for detecting and managing NVIDIA GPUs.
"""

import subprocess

import streamlit as st


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


def render_gpu_selector(default_value: int = 1) -> int:
    """
    Render GPU selection widget with visual memory usage indicators.

    Args:
        default_value: Default number of GPUs to select

    Returns:
        int: Selected number of GPUs
    """
    available_gpus = get_available_gpus()
    gpu_info = get_gpu_info()

    st.subheader("GPU Configuration")

    # Display GPU usage visualization
    if gpu_info:
        for gpu in gpu_info:
            # GPU header
            st.markdown(
                f"<div style='margin-bottom: 0.5rem;'>"
                f"<strong style='color: var(--text-primary);'>GPU {gpu['index']}</strong> "
                f"<span style='color: var(--text-secondary); font-size: 0.85rem;'>{gpu['name']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Memory usage bar and stats
            col1, col2 = st.columns([3, 1])
            with col1:
                usage_pct = gpu["memory_used_mb"] / gpu["memory_total_mb"]
                # Color based on usage level
                if usage_pct > 0.9:
                    bar_color = "🔴"
                elif usage_pct > 0.7:
                    bar_color = "🟡"
                else:
                    bar_color = "🟢"
                st.progress(
                    usage_pct,
                    text=f"{bar_color} {usage_pct*100:.1f}% used",
                )
            with col2:
                free_gb = gpu["memory_free_mb"] / 1024
                st.caption(f"**{free_gb:.1f} GB** free")

            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    else:
        st.info(f"{available_gpus} GPU(s) detected (detailed info unavailable)")

    # GPU selection slider
    num_gpus = st.slider(
        "Number of GPUs to use",
        min_value=1,
        max_value=available_gpus,
        value=min(default_value, available_gpus),
        help=f"Select how many GPUs to use for generation",
    )

    return num_gpus
