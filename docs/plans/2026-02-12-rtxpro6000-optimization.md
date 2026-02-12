# RTX PRO 6000 Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Optimize WanUI + Wan2.2 for 4x RTX PRO 6000 Blackwell GPUs (96GB VRAM) with a tiered performance system, extended video duration, and concurrent job support.

**Architecture:** Three performance tiers (Quality/Balanced/Speed) implemented via new CLI flags in the patched generate.py. The WanUI frontend adds tier selection UI and passes flags to the subprocess. GPU allocation is enhanced to support concurrent isolated jobs. All optimizations are injected via the existing patch system.

**Tech Stack:** Python, Streamlit, PyTorch 2.9.1+cu128, CUDA 12.8, Wan2.2 (upstream)

---

### Task 1: Add GPU Hardware Detection

**Files:**
- Modify: `utils/gpu.py`

**Step 1: Add `detect_gpu_profile()` function to `utils/gpu.py`**

After the existing `get_gpu_info()` function (line 67), add:

```python
def detect_gpu_profile() -> dict:
    """
    Detect GPU hardware capabilities for optimization decisions.

    Returns:
        dict with keys:
            - vram_gb: float (per GPU)
            - compute_capability: str (e.g., "12.0")
            - gpu_name: str
            - gpu_count: int
            - high_vram: bool (True if >= 80GB)
            - is_blackwell: bool (True if SM >= 12.0)
    """
    gpus = get_gpu_info()
    if not gpus:
        return {
            "vram_gb": 0,
            "compute_capability": "unknown",
            "gpu_name": "unknown",
            "gpu_count": 0,
            "high_vram": False,
            "is_blackwell": False,
        }

    # Get compute capability via nvidia-smi
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=compute_cap",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        compute_caps = [line.strip() for line in result.stdout.strip().split("\n")]
        compute_cap = compute_caps[0] if compute_caps else "unknown"
    except Exception:
        compute_cap = "unknown"

    vram_gb = gpus[0]["memory_total_mb"] / 1024
    gpu_name = gpus[0]["name"]

    # Parse major version for architecture detection
    try:
        major = int(compute_cap.split(".")[0])
    except (ValueError, IndexError):
        major = 0

    return {
        "vram_gb": vram_gb,
        "compute_capability": compute_cap,
        "gpu_name": gpu_name,
        "gpu_count": len(gpus),
        "high_vram": vram_gb >= 80,
        "is_blackwell": major >= 12,
    }
```

**Step 2: Verify it works**

Run: `cd /data2/opt/WanUI && python -c "from utils.gpu import detect_gpu_profile; print(detect_gpu_profile())"`
Expected: Dict with `vram_gb` ~96, `compute_capability` "12.0", `is_blackwell` True

**Step 3: Commit**

```bash
git add utils/gpu.py
git commit -m "feat: add GPU hardware detection for optimization decisions"
```

---

### Task 2: Add Performance Tier Configuration

**Files:**
- Modify: `utils/config.py`

**Step 1: Add performance tier constants and config to `utils/config.py`**

After the `MODELS_PATH` line (line 18), add:

```python
# Performance tier definitions
PERF_TIERS = {
    "quality": {
        "label": "Quality",
        "description": "Best quality, ~40% faster (TF32, no offloading)",
        "tf32": True,
        "cudnn_benchmark": True,
        "torch_compile": False,
        "teacache": False,
        "magcache": False,
    },
    "balanced": {
        "label": "Balanced",
        "description": "Same quality, ~2x faster (+ torch.compile, first-run warmup)",
        "tf32": True,
        "cudnn_benchmark": True,
        "torch_compile": True,
        "teacache": False,
        "magcache": True,  # Only used for I2V
    },
    "speed": {
        "label": "Speed",
        "description": "Slight quality trade-off, ~3x faster (+ TeaCache step skipping)",
        "tf32": True,
        "cudnn_benchmark": True,
        "torch_compile": True,
        "teacache": True,
        "magcache": True,  # Only used for I2V
    },
}

DEFAULT_PERF_TIER = "quality"
DEFAULT_TEACACHE_THRESHOLD = 0.25

# GPU allocation strategy definitions
GPU_STRATEGIES = {
    "auto": {
        "label": "Auto",
        "description": "Smart allocation: spread across GPUs when idle, use free GPUs when busy",
    },
    "max_speed": {
        "label": "Max Speed",
        "description": "Use all selected GPUs for one job, queue blocks others",
    },
    "concurrent": {
        "label": "Concurrent",
        "description": "Isolate GPUs for parallel jobs (up to 4 simultaneous)",
    },
}

DEFAULT_GPU_STRATEGY = "auto"
```

**Step 2: Update duration ranges for high-VRAM GPUs**

After the `MODEL_CONFIGS` dict (after line 146), add:

```python
# Extended duration ranges for high-VRAM GPUs (96GB+)
EXTENDED_DURATION_RANGES = {
    "t2v-A14B": {
        "1280*720": {"min": 5, "max": 21, "step": 1, "default": 5},
        "720*1280": {"min": 5, "max": 21, "step": 1, "default": 5},
        "832*480": {"min": 5, "max": 33, "step": 1, "default": 5},
        "480*832": {"min": 5, "max": 33, "step": 1, "default": 5},
    },
    "i2v-A14B": {
        "1280*720": {"min": 5, "max": 21, "step": 1, "default": 5},
        "720*1280": {"min": 5, "max": 21, "step": 1, "default": 5},
        "832*480": {"min": 5, "max": 33, "step": 1, "default": 5},
        "480*832": {"min": 5, "max": 33, "step": 1, "default": 5},
    },
}


def get_duration_range(task: str, resolution: str, high_vram: bool = False) -> dict:
    """
    Get duration range for a task, optionally extended for high-VRAM GPUs.

    Args:
        task: Task name (e.g., "t2v-A14B")
        resolution: Resolution string (e.g., "1280*720")
        high_vram: Whether the GPU has >= 80GB VRAM

    Returns:
        Duration range dict with min, max, step, default
    """
    if high_vram and task in EXTENDED_DURATION_RANGES:
        extended = EXTENDED_DURATION_RANGES[task]
        if resolution in extended:
            return extended[resolution]

    config = MODEL_CONFIGS.get(task, {})
    return config.get("duration_range", {"min": 2, "max": 10, "step": 1, "default": 5})
```

**Step 3: Add `render_perf_tier_selector()` function**

After the `render_duration_slider()` function, add:

```python
def render_perf_tier_selector(task: str) -> tuple[str, float | None]:
    """
    Render performance tier dropdown and optional TeaCache threshold slider.

    Args:
        task: Task name (e.g., "t2v-A14B")

    Returns:
        Tuple of (perf_tier, teacache_threshold)
        teacache_threshold is None unless speed mode is selected
    """
    st.subheader("Performance")

    tier_options = list(PERF_TIERS.keys())
    tier_labels = [f"{PERF_TIERS[t]['label']} — {PERF_TIERS[t]['description']}" for t in tier_options]

    selected_idx = st.selectbox(
        "Performance Mode",
        range(len(tier_options)),
        index=tier_options.index(DEFAULT_PERF_TIER),
        format_func=lambda i: tier_labels[i],
        help="Controls speed/quality trade-off. Quality is safest. Balanced adds torch.compile (first run slower). Speed adds step skipping.",
    )
    perf_tier = tier_options[selected_idx]

    teacache_threshold = None
    if perf_tier == "speed":
        teacache_threshold = st.slider(
            "Speed/Quality Balance",
            min_value=0.1,
            max_value=0.5,
            value=DEFAULT_TEACACHE_THRESHOLD,
            step=0.05,
            help="Lower = more quality, higher = more speed. 0.25 is a good default.",
        )

    return perf_tier, teacache_threshold


def render_gpu_strategy_selector() -> str:
    """
    Render GPU allocation strategy dropdown.

    Returns:
        Strategy key: "auto", "max_speed", or "concurrent"
    """
    strategy_options = list(GPU_STRATEGIES.keys())
    strategy_labels = [
        f"{GPU_STRATEGIES[s]['label']} — {GPU_STRATEGIES[s]['description']}"
        for s in strategy_options
    ]

    selected_idx = st.selectbox(
        "GPU Strategy",
        range(len(strategy_options)),
        index=strategy_options.index(DEFAULT_GPU_STRATEGY),
        format_func=lambda i: strategy_labels[i],
        help="Auto adapts to current GPU usage. Max Speed uses all GPUs for one job. Concurrent isolates GPUs for parallel jobs.",
    )

    return strategy_options[selected_idx]
```

**Step 4: Verify imports work**

Run: `cd /data2/opt/WanUI && python -c "from utils.config import PERF_TIERS, GPU_STRATEGIES, get_duration_range; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add utils/config.py
git commit -m "feat: add performance tier and GPU strategy configuration"
```

---

### Task 3: Update Generation Runner with Performance Flags

**Files:**
- Modify: `utils/generation.py`

**Step 1: Add performance-related parameters to `run_generation()`**

Add these parameters to the function signature (after the `gpu_ids` parameter at line 161):

```python
    # Performance optimization
    perf_mode: str = "quality",
    teacache_threshold: float | None = None,
```

**Step 2: Add environment variable configuration**

After the existing env setup block (after line 226, `env["CUDA_VISIBLE_DEVICES"]`), add:

```python
    # Performance optimization environment variables
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,garbage_collection_threshold:0.8"
    env["TORCH_CUDA_ARCH_LIST"] = "12.0"

    # NCCL tuning for multi-GPU NVLink
    if num_gpus > 1:
        env["NCCL_NVLS_ENABLE"] = "1"
        env["NCCL_P2P_LEVEL"] = "NVL"
```

**Step 3: Add performance flags to command construction**

After the multi-GPU options block (after line 278, the `--ulysses_size` line), add:

```python
    # Performance mode flags
    cmd.extend(["--perf_mode", perf_mode])

    if perf_mode == "speed" and teacache_threshold is not None:
        cmd.extend(["--teacache_threshold", str(teacache_threshold)])
```

**Step 4: Enhance OOM error message with optimization suggestions**

In the OOM error hint block (around line 361), extend the message:

Replace:
```python
                error_msg += f"\n- Try reducing num_gpus or using gpu_ids to skip busy GPUs"
                error_msg += f"\n- Run 'nvidia-smi' to check GPU memory availability"
```

With:
```python
                error_msg += f"\n- Try reducing video duration or switching to a lower resolution"
                error_msg += f"\n- Try reducing num_gpus or using gpu_ids to skip busy GPUs"
                error_msg += f"\n- Run 'nvidia-smi' to check GPU memory availability"
```

**Step 5: Verify syntax**

Run: `cd /data2/opt/WanUI && python -c "from utils.generation import run_generation; print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add utils/generation.py
git commit -m "feat: add performance mode flags and env vars to generation runner"
```

---

### Task 4: Patch generate.py with Performance Mode Support

**Files:**
- Modify: `patches/generate.py`

**Step 1: Add performance-related CLI arguments**

After the `--convert_model_dtype` argument (line 223), add:

```python
    # Performance optimization
    parser.add_argument(
        "--perf_mode",
        type=str,
        default="quality",
        choices=["quality", "balanced", "speed"],
        help="Performance optimization tier: quality (TF32 only), balanced (+torch.compile), speed (+TeaCache).")
    parser.add_argument(
        "--teacache_threshold",
        type=float,
        default=0.25,
        help="TeaCache threshold for speed mode (0.1-0.5). Lower = more quality.")
```

**Step 2: Add TF32 and cuDNN settings in `generate()` function**

After `device = local_rank` (line 319), add:

```python
    # Performance optimizations based on perf_mode
    if args.perf_mode in ("quality", "balanced", "speed"):
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision('high')
        logging.info("Enabled TF32 matmul, cuDNN benchmark, and high float32 precision")
```

**Step 3: Auto-detect high-VRAM and disable offloading**

Replace the existing offload_model auto-detection block (lines 322-325):

```python
    if args.offload_model is None:
        args.offload_model = False if world_size > 1 else True
        logging.info(
            f"offload_model is not specified, set to {args.offload_model}.")
```

With:

```python
    if args.offload_model is None:
        # Auto-detect GPU VRAM - disable offloading for high-VRAM GPUs
        try:
            vram_gb = torch.cuda.get_device_properties(local_rank).total_mem / (1024**3)
        except Exception:
            vram_gb = 0
        if vram_gb >= 80:
            args.offload_model = False
            logging.info(f"High-VRAM GPU detected ({vram_gb:.0f}GB), offloading disabled")
        else:
            args.offload_model = False if world_size > 1 else True
            logging.info(f"offload_model set to {args.offload_model} (VRAM: {vram_gb:.0f}GB)")
```

**Step 4: Add torch.compile wrapper for balanced/speed modes**

This is the most complex change. After the model pipeline creation blocks (after each `wan.WanT2V(...)`, `wan.WanI2V(...)`, etc. call), we need to wrap the model with torch.compile.

After the T2V pipeline creation block (after line 420), add:

```python
        # Apply torch.compile in balanced/speed mode
        if args.perf_mode in ("balanced", "speed"):
            logging.info("Applying torch.compile to DiT model (first run will be slower)...")
            try:
                wan_t2v.model = torch.compile(
                    wan_t2v.model,
                    mode="max-autotune-no-cudagraphs",
                    fullgraph=False,
                )
                logging.info("torch.compile applied successfully")
            except Exception as e:
                logging.warning(f"torch.compile failed, continuing without compilation: {e}")
```

Repeat the same pattern after each pipeline creation:
- After `wan.WanI2V(...)` creation (I2V block)
- After `wan.WanTI2V(...)` creation (TI2V block)
- After `wan.WanAnimate(...)` creation (Animate block)
- After `wan.WanS2V(...)` creation (S2V block)

Use the appropriate variable name for each (`wan_i2v.model`, `wan_ti2v.model`, etc.).

Note: The Wan2.2 pipeline classes (WanT2V, WanI2V, etc.) may use `.low_noise_model` and `.high_noise_model` instead of a single `.model`. Check via a quick exploration. If so, compile both:

```python
        if args.perf_mode in ("balanced", "speed"):
            logging.info("Applying torch.compile to DiT models...")
            try:
                if hasattr(wan_t2v, 'model'):
                    wan_t2v.model = torch.compile(
                        wan_t2v.model, mode="max-autotune-no-cudagraphs", fullgraph=False)
                if hasattr(wan_t2v, 'low_noise_model'):
                    wan_t2v.low_noise_model = torch.compile(
                        wan_t2v.low_noise_model, mode="max-autotune-no-cudagraphs", fullgraph=False)
                if hasattr(wan_t2v, 'high_noise_model'):
                    wan_t2v.high_noise_model = torch.compile(
                        wan_t2v.high_noise_model, mode="max-autotune-no-cudagraphs", fullgraph=False)
                logging.info("torch.compile applied successfully")
            except Exception as e:
                logging.warning(f"torch.compile failed, falling back to eager mode: {e}")
```

**Step 5: Add TeaCache support for speed mode**

TeaCache modifies the denoising loop to skip redundant steps. This requires patching the pipeline's `generate()` method, which is in the upstream files `wan/text2video.py` and `wan/image2video.py`.

For the initial implementation, add TeaCache as a separate patch file (Task 5). In this task, just pass the flag through. After the torch.compile block, add:

```python
        # Configure TeaCache for speed mode
        if args.perf_mode == "speed":
            logging.info(f"TeaCache enabled with threshold={args.teacache_threshold}")
            # TeaCache is applied inside the generate() call via the teacache_threshold parameter
```

**Step 6: Pass `teacache_threshold` to the generate calls**

For T2V (line ~423-432), add `teacache_threshold` parameter:

```python
        video = wan_t2v.generate(
            args.prompt,
            size=SIZE_CONFIGS[args.size],
            frame_num=args.frame_num,
            shift=args.sample_shift,
            sample_solver=args.sample_solver,
            sampling_steps=args.sample_steps,
            guide_scale=args.sample_guide_scale,
            seed=args.base_seed,
            offload_model=args.offload_model,
            teacache_threshold=args.teacache_threshold if args.perf_mode == "speed" else None,
        )
```

Apply same pattern to all generate() calls. The `teacache_threshold` parameter will be handled in the patched pipeline (Task 5).

**Step 7: Verify syntax**

Run: `cd /data2/opt/WanUI && python -c "exec(open('patches/generate.py').read().split('if __name__')[0])"; echo $?`
Expected: Exit code 0 (may show import warnings, that's fine)

**Step 8: Commit**

```bash
git add patches/generate.py
git commit -m "feat: add perf_mode, TF32, torch.compile, and TeaCache flags to patched generate.py"
```

---

### Task 5: Patch Wan2.2 Pipeline with TeaCache Support

**Files:**
- Create: `patches/wan/text2video.py`
- Create: `patches/wan/image2video.py`

This is the most impactful optimization. TeaCache skips redundant denoising steps by comparing timestep embeddings.

**Step 1: Copy upstream text2video.py as base for patch**

```bash
cp /home/users/wrightda/src/Wan2.2.mod/wan/text2video.py /data2/opt/WanUI/patches/wan/text2video.py
```

**Step 2: Modify `patches/wan/text2video.py` to add TeaCache**

Read the copied file to find the exact `generate()` method. The key modification is in the main denoising loop.

In the `generate()` method, add `teacache_threshold=None` parameter to the signature.

Then, before the denoising loop, add:

```python
        # TeaCache setup
        use_teacache = teacache_threshold is not None and teacache_threshold > 0
        prev_timestep_embedding = None
        teacache_warmup_steps = max(1, int(len(timesteps) * 0.1))  # Skip first 10%
```

Inside the denoising loop, wrap the model forward passes with TeaCache logic:

```python
        for step_idx, t in enumerate(tqdm(timesteps)):
            # TeaCache: check if we can skip this step
            skip_step = False
            if use_teacache and step_idx >= teacache_warmup_steps and prev_timestep_embedding is not None:
                # Compute current timestep embedding
                current_te = model.time_embedding(
                    sinusoidal_embedding_1d(model.freq_dim, t.unsqueeze(0).to(device))
                )
                # Compare with previous timestep embedding
                te_diff = (current_te - prev_timestep_embedding).abs().mean().item()
                if te_diff < teacache_threshold:
                    skip_step = True

            if not skip_step:
                # Normal forward passes (existing code)
                noise_pred_cond = model(...)
                noise_pred_uncond = model(...)
                noise_pred = noise_pred_uncond + guide_scale * (noise_pred_cond - noise_pred_uncond)

                # Store timestep embedding for TeaCache
                if use_teacache:
                    prev_timestep_embedding = model.time_embedding(
                        sinusoidal_embedding_1d(model.freq_dim, t.unsqueeze(0).to(device))
                    )
            # else: reuse previous noise_pred

            # Scheduler step (always runs)
            ...
```

**Important**: The exact integration depends on how the model's time embedding is accessed. The implementer should read the WanModel.forward() method in `/home/users/wrightda/src/Wan2.2.mod/wan/modules/model.py` lines 410-497 to find the correct time embedding access pattern.

**Step 3: Copy and patch image2video.py similarly**

```bash
cp /home/users/wrightda/src/Wan2.2.mod/wan/image2video.py /data2/opt/WanUI/patches/wan/image2video.py
```

Apply the same TeaCache modifications to `patches/wan/image2video.py`.

**Step 4: Register new patches in `patch.py`**

Add to the `PATCH_FILES` list:

```python
PATCH_FILES = [
    "generate.py",
    "wan/text2video.py",
    "wan/image2video.py",
    "wan/utils/prompt_extend.py",
    "wan/utils/system_prompt.py",
    "wan/configs/shared_config.py",
    "wan/configs/wan_animate_14B.py",
]
```

**Step 5: Verify patches can be applied**

```bash
cd /data2/opt/WanUI && python patch.py status
```

**Step 6: Commit**

```bash
git add patches/wan/text2video.py patches/wan/image2video.py patch.py
git commit -m "feat: add TeaCache support to patched T2V and I2V pipelines"
```

---

### Task 6: Upgrade Generation Queue for Concurrent Jobs

**Files:**
- Modify: `utils/queue.py`

**Step 1: Replace `GenerationQueue` with `GpuAwareQueue`**

Replace the entire `GenerationQueue` class and module-level code with:

```python
"""
Thread-safe generation queue with per-GPU allocation for concurrent job support.

All Streamlit sessions run in the same Python process, so a module-level singleton
with threading locks coordinates access to prevent torchrun port conflicts.
"""

import threading
import time
from collections import OrderedDict

import streamlit as st


class GpuAwareQueue:
    """Thread-safe queue that tracks per-GPU allocation for concurrent jobs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._queue: OrderedDict[str, dict] = OrderedDict()
        self._gpu_assignments: dict[int, dict] = {}  # gpu_id -> {job_id, task, started_at}
        self._active_jobs: dict[str, dict] = {}  # job_id -> {gpu_ids, task, started_at}

    def submit(self, job_id: str, task: str, prompt_preview: str, requested_gpus: int = 1) -> None:
        """Add a job to the queue."""
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

    def get_active_jobs(self) -> dict[str, dict]:
        """Get all currently running jobs."""
        with self._lock:
            return dict(self._active_jobs)

    def get_active_info(self) -> dict | None:
        """Get info about any currently running job, or None if idle. Legacy compat."""
        with self._lock:
            if self._active_jobs:
                first_job = next(iter(self._active_jobs.values()))
                return first_job
            return None

    def get_free_gpus(self, total_gpus: int) -> list[int]:
        """Get list of GPU IDs not currently assigned to any job."""
        with self._lock:
            all_gpus = set(range(total_gpus))
            busy_gpus = set(self._gpu_assignments.keys())
            return sorted(all_gpus - busy_gpus)

    def try_acquire(self, job_id: str, gpu_ids: list[int] | None = None) -> list[int] | None:
        """
        Try to acquire GPUs for a job.

        Args:
            job_id: The job identifier
            gpu_ids: Specific GPU IDs to acquire. If None, uses first available.

        Returns:
            List of acquired GPU IDs, or None if acquisition failed.
        """
        with self._lock:
            # Must be first in queue
            if self._queue:
                first_id = next(iter(self._queue))
                if first_id != job_id:
                    return None

            job_info = self._queue.get(job_id, {"task": "unknown", "prompt_preview": "", "requested_gpus": 1})

            if gpu_ids is None:
                # Auto-select: find free GPUs
                requested = job_info.get("requested_gpus", 1)
                busy = set(self._gpu_assignments.keys())
                # Try to get requested number of free GPUs
                free = [i for i in range(128) if i not in busy]
                if len(free) < requested:
                    return None
                gpu_ids = free[:requested]

            # Check all requested GPUs are free
            for gid in gpu_ids:
                if gid in self._gpu_assignments:
                    return None

            # Acquire
            self._queue.pop(job_id, None)
            import time as _time
            now = _time.time()
            for gid in gpu_ids:
                self._gpu_assignments[gid] = {
                    "job_id": job_id,
                    "task": job_info["task"],
                    "started_at": now,
                }
            self._active_jobs[job_id] = {
                "gpu_ids": gpu_ids,
                "task": job_info["task"],
                "prompt_preview": job_info.get("prompt_preview", ""),
                "started_at": now,
            }
            return gpu_ids

    def release(self, job_id: str) -> None:
        """Release GPUs after job completion."""
        with self._lock:
            job = self._active_jobs.pop(job_id, None)
            if job:
                for gid in job.get("gpu_ids", []):
                    self._gpu_assignments.pop(gid, None)

    def cancel(self, job_id: str) -> None:
        """Remove a job from the queue (before it starts running)."""
        with self._lock:
            self._queue.pop(job_id, None)


# Module-level singleton
generation_queue = GpuAwareQueue()


def wait_for_queue_turn(job_id: str, gpu_ids: list[int] | None = None, cancellation_check=None) -> list[int] | None:
    """
    Wait until this job can run. Shows queue position in st.status if waiting.

    Returns list of acquired GPU IDs when acquired, None if cancelled.
    """
    # Fast path: try to acquire immediately
    acquired = generation_queue.try_acquire(job_id, gpu_ids)
    if acquired is not None:
        return acquired

    # Need to wait — show queue UI
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
                    running = ", ".join(j["task"] for j in active_jobs.values())
                    msg += f" (running: {running})"
                st.write(msg)
                status.update(label=f"Waiting in queue (position {pos + 1})...")

            time.sleep(1)


def get_queue_status_message() -> str | None:
    """
    Get a human-readable queue status string, or None if idle.
    """
    active_jobs = generation_queue.get_active_jobs()
    queue_len = generation_queue.get_queue_length()

    if not active_jobs and queue_len == 0:
        return None

    parts = []
    if active_jobs:
        count = len(active_jobs)
        tasks = ", ".join(j["task"] for j in active_jobs.values())
        parts.append(f"{count} generation{'s' if count > 1 else ''} running ({tasks})")
    if queue_len > 0:
        parts.append(f"{queue_len} in queue")

    return ", ".join(parts)
```

**Step 2: Verify the module imports correctly**

Run: `cd /data2/opt/WanUI && python -c "from utils.queue import generation_queue, wait_for_queue_turn, get_queue_status_message; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add utils/queue.py
git commit -m "feat: upgrade generation queue with per-GPU allocation for concurrent jobs"
```

---

### Task 7: Update T2V Page with Performance UI

**Files:**
- Modify: `pages/t2v_a14b.py`

**Step 1: Add imports for new config functions**

Update the imports from `utils.config` to include:

```python
from utils.config import (
    DEFAULT_PROMPTS,
    MODEL_CONFIGS,
    OUTPUT_PATH,
    OUTPUT_ROOT,
    PROMPT_EXTEND_METHOD,
    PROMPT_EXTEND_MODEL,
    calculate_frame_num,
    get_duration_range,
    get_task_session_key,
    render_duration_slider,
    render_example_prompts,
    render_perf_tier_selector,
    render_gpu_strategy_selector,
)
```

Add import for GPU detection:

```python
from utils.gpu import detect_gpu_profile, render_gpu_selector
```

**Step 2: Add GPU profile detection after CONFIG**

After line 43 (`CONFIG = MODEL_CONFIGS[TASK]`), add:

```python
GPU_PROFILE = detect_gpu_profile()
```

**Step 3: Add performance tier selector to sidebar**

After the GPU selector block (after line 76, `st.divider()`), add:

```python
    # Performance optimization
    perf_tier, teacache_threshold = render_perf_tier_selector(TASK)

    # GPU Strategy (only show if more than 1 GPU)
    if GPU_PROFILE["gpu_count"] > 1:
        gpu_strategy = render_gpu_strategy_selector()
    else:
        gpu_strategy = "max_speed"

    st.divider()
```

**Step 4: Update duration slider to use extended ranges**

Replace the duration slider section in the sidebar:

```python
    # Duration control - extended for high-VRAM GPUs
    st.subheader("Duration")
    duration_range = get_duration_range(TASK, resolution, GPU_PROFILE["high_vram"])
    duration = st.slider(
        "Duration (seconds)",
        min_value=float(duration_range["min"]),
        max_value=float(duration_range["max"]),
        value=float(duration_range["default"]),
        step=float(duration_range["step"]),
        key=f"{TASK_KEY}_duration",
        label_visibility="collapsed",
    )
    fps = CONFIG["sample_fps"]
    frame_count = calculate_frame_num(duration, fps)
    st.caption(f"→ {frame_count} frames @ {fps} fps")
    if GPU_PROFILE["high_vram"]:
        st.caption(f"Extended range available (96GB VRAM detected)")
```

**Step 5: Pass perf_mode to run_generation()**

In the `run_generation()` call (around line 256), add the new parameters:

```python
                    success, output, generation_time = run_generation(
                        task=TASK,
                        output_file=final_output,
                        prompt=generation_prompt,
                        num_gpus=num_gpus,
                        resolution=resolution,
                        sample_steps=sample_steps,
                        sample_solver=sample_solver,
                        sample_shift=sample_shift,
                        sample_guide_scale=sample_guide_scale,
                        seed=seed,
                        frame_num=frame_num,
                        gpu_ids=gpu_ids,
                        use_prompt_extend=False,
                        cancellation_check=check_cancellation,
                        perf_mode=perf_tier,
                        teacache_threshold=teacache_threshold,
                    )
```

**Step 6: Update status display to show perf mode**

In the `st.status` block, add a line showing the performance mode:

```python
                    st.write(f"Performance: {perf_tier.title()} mode")
```

**Step 7: Update the queue call to pass GPU IDs for concurrent support**

Replace `wait_for_queue_turn(job_id, check_cancellation)` with:

```python
            acquired_gpus = wait_for_queue_turn(job_id, gpu_ids, check_cancellation)
            if acquired_gpus is None:
```

And update the `gpu_ids` used in `run_generation()` to use `acquired_gpus` if concurrent mode is active.

**Step 8: Verify page loads**

Run: `cd /data2/opt/WanUI && python -c "import streamlit; print('imports OK')"`
Expected: `imports OK`

**Step 9: Commit**

```bash
git add pages/t2v_a14b.py
git commit -m "feat: add performance tier and GPU strategy UI to T2V page"
```

---

### Task 8: Update I2V Page with Performance UI

**Files:**
- Modify: `pages/i2v_a14b.py`

Apply the same changes as Task 7 but for the I2V page:

**Step 1:** Update imports (same as Task 7)
**Step 2:** Add GPU profile detection
**Step 3:** Add perf tier and GPU strategy selectors to sidebar
**Step 4:** Update duration slider with extended ranges
**Step 5:** Pass `perf_mode` and `teacache_threshold` to `run_generation()`
**Step 6:** Update status display
**Step 7:** Update queue call for concurrent support

Additionally for I2V, show a MagCache indicator when balanced/speed mode is selected:

```python
    if perf_tier in ("balanced", "speed"):
        st.info("MagCache enabled for I2V (reduces redundant computation)")
```

**Step 8: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: add performance tier and GPU strategy UI to I2V page"
```

---

### Task 9: Update S2V and Animate Pages

**Files:**
- Modify: `pages/s2v_14b.py`
- Modify: `pages/animate_14b.py`

Apply the same pattern as Tasks 7-8:
- Add perf tier selector
- Add GPU strategy selector
- Pass perf_mode to run_generation()
- No MagCache for these tasks (not supported)
- No extended duration for S2V (audio-driven)
- Extended duration for Animate if applicable

**Step 1:** Read and update `pages/s2v_14b.py`
**Step 2:** Read and update `pages/animate_14b.py`
**Step 3:** Commit

```bash
git add pages/s2v_14b.py pages/animate_14b.py
git commit -m "feat: add performance tier and GPU strategy UI to S2V and Animate pages"
```

---

### Task 10: Update Patch System

**Files:**
- Modify: `patch.py`

**Step 1: Add new patch files to PATCH_FILES list**

Update `PATCH_FILES` (line 34) to include the new patches:

```python
PATCH_FILES = [
    "generate.py",
    "wan/text2video.py",
    "wan/image2video.py",
    "wan/utils/prompt_extend.py",
    "wan/utils/system_prompt.py",
    "wan/configs/shared_config.py",
    "wan/configs/wan_animate_14B.py",
]
```

**Step 2: Update docstring**

Add the new patches to the docstring at the top of the file.

**Step 3: Test patch status**

```bash
cd /data2/opt/WanUI && python patch.py status
```

**Step 4: Apply patches**

```bash
cd /data2/opt/WanUI && python patch.py patch
```

**Step 5: Commit**

```bash
git add patch.py
git commit -m "feat: register new performance optimization patches"
```

---

### Task 11: Integration Testing

**Step 1: Verify all imports work**

```bash
cd /data2/opt/WanUI && python -c "
from utils.config import PERF_TIERS, GPU_STRATEGIES, get_duration_range, render_perf_tier_selector
from utils.gpu import detect_gpu_profile, render_gpu_selector
from utils.generation import run_generation
from utils.queue import generation_queue, wait_for_queue_turn
print('All imports OK')
print('GPU Profile:', detect_gpu_profile())
"
```

**Step 2: Verify patch system works**

```bash
cd /data2/opt/WanUI && python patch.py status
cd /data2/opt/WanUI && python patch.py patch
cd /data2/opt/WanUI && python patch.py status
```

**Step 3: Start Streamlit and verify UI loads**

```bash
cd /data2/opt/WanUI && streamlit run app.py --server.port 8560
```

Navigate to the T2V page and verify:
- Performance Mode dropdown appears in sidebar
- GPU Strategy dropdown appears in sidebar
- Duration slider shows extended range
- All three tiers are selectable

**Step 4: Test a generation in Quality mode**

Run a short T2V generation (5s, 480p) in Quality mode to verify the basic pipeline works with the new flags.

**Step 5: Test a generation in Balanced mode**

Run the same generation in Balanced mode. Verify:
- First run shows "Compiling model" in logs
- torch.compile warning/success appears in output

**Step 6: Commit any fixes**

```bash
git add -A
git commit -m "fix: integration testing fixes for RTX PRO 6000 optimization"
```

---

### Task 12: Final Verification and Cleanup

**Step 1: Run the code formatter**

```bash
cd /data2/opt/WanUI && black . && isort .
```

**Step 2: Verify no regressions**

- Start Streamlit app
- Verify all 4 task pages load without errors
- Verify GPU selector still works
- Verify queue status still displays correctly

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: format code after RTX PRO 6000 optimization changes"
```
