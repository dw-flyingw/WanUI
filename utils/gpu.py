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


def render_gpu_selector(default_value: int = 1, allow_gpu_selection: bool = True, num_heads: int | None = None) -> tuple[int, list[int] | None]:
    """
    Render GPU selection widget with visual memory usage indicators.

    Args:
        default_value: Default number of GPUs to select
        allow_gpu_selection: If True, allows selecting specific GPU IDs via checkbox
        num_heads: Number of attention heads in the model (for Ulysses parallelism validation).
                   If provided, only allows GPU counts that divide num_heads evenly.

    Returns:
        tuple: (num_gpus, gpu_ids)
            - num_gpus: Number of GPUs to use
            - gpu_ids: List of specific GPU IDs to use, or None for default (0 to num_gpus-1)
    """
    available_gpus = get_available_gpus()
    gpu_info = get_gpu_info()

    st.subheader("GPU Configuration")

    # Determine which GPUs to auto-select: pick the N freest GPUs
    freest_gpu_indices = set()
    if gpu_info and allow_gpu_selection:
        sorted_by_free = sorted(gpu_info, key=lambda g: g["memory_free_mb"], reverse=True)
        for gpu in sorted_by_free[:default_value]:
            freest_gpu_indices.add(gpu["index"])

    # Display GPU usage visualization
    selected_gpu_ids = []
    if gpu_info:
        for gpu in gpu_info:
            # Create columns for checkbox and GPU info
            if allow_gpu_selection:
                col_check, col_info = st.columns([0.5, 9.5])
            else:
                col_info = st.container()
                col_check = None

            with col_info:
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

            # Add checkbox for GPU selection if enabled
            if allow_gpu_selection and col_check:
                with col_check:
                    # Auto-check the N freest GPUs (where N = default_value)
                    default_checked = gpu["index"] in freest_gpu_indices
                    if st.checkbox("", value=default_checked, key=f"gpu_{gpu['index']}_select", label_visibility="collapsed"):
                        selected_gpu_ids.append(gpu["index"])

            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    else:
        st.info(f"{available_gpus} GPU(s) detected (detailed info unavailable)")

    # Calculate valid GPU counts if num_heads constraint exists
    valid_gpu_counts = list(range(1, available_gpus + 1))
    if num_heads is not None:
        valid_gpu_counts = [n for n in range(1, available_gpus + 1) if num_heads % n == 0]
        if not valid_gpu_counts:
            valid_gpu_counts = [1]  # Always allow single GPU

    # Determine which GPUs to use
    gpu_ids_to_use = None
    if allow_gpu_selection and selected_gpu_ids:
        # User manually selected specific GPUs
        gpu_ids_to_use = sorted(selected_gpu_ids)
        num_gpus = len(gpu_ids_to_use)

        # Validate against num_heads constraint
        if num_heads is not None and num_gpus not in valid_gpu_counts:
            # Fall back to largest valid count
            num_gpus = max([v for v in valid_gpu_counts if v <= len(selected_gpu_ids)] or [1])
            gpu_ids_to_use = sorted(selected_gpu_ids)[:num_gpus]
    else:
        # Use slider for GPU count
        if num_heads is not None and len(valid_gpu_counts) < available_gpus:
            # Show dropdown for valid counts when constrained
            help_text = f"Model has {num_heads} attention heads. Only GPU counts that divide {num_heads} evenly are valid."
            num_gpus = st.selectbox(
                "Number of GPUs to use",
                options=valid_gpu_counts,
                index=min(len(valid_gpu_counts) - 1, valid_gpu_counts.index(default_value) if default_value in valid_gpu_counts else 0),
                help=help_text,
            )
        else:
            # Use slider when no constraints or all counts valid
            num_gpus = st.slider(
                "Number of GPUs to use",
                min_value=1,
                max_value=available_gpus,
                value=min(default_value, available_gpus),
                help=f"Select how many GPUs to use for generation (will use GPUs 0-{available_gpus-1})",
            )

    return num_gpus, gpu_ids_to_use
