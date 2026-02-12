# RTX PRO 6000 Optimization Design

## Overview

Optimize WanUI and Wan2.2 to take full advantage of 4x NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs (96GB VRAM each, SM 12.0, NVLink P2P, ~252 TFLOPS BF16).

## Goals

1. Faster generation turnaround (target: 2-3x over current baseline)
2. Longer video output (beyond current 5-10s cap)
3. Concurrent job support (multiple simultaneous generations)
4. User-selectable speed/quality trade-off

## Hardware Profile

- 4x RTX PRO 6000 Blackwell Server Edition
- 96 GB GDDR7 ECC per GPU
- SM 12.0 (Blackwell architecture)
- 5th Gen Tensor Cores (FP4/FP6/FP8/BF16/FP16/TF32)
- NVLink P2P (Server Edition)
- PyTorch 2.9.1+cu128, CUDA 12.8
- Flash Attention 2.8.3 installed

## Design

### 1. Performance Tier System

Three selectable tiers via UI dropdown on each generation page.

#### Quality Mode (~40% faster, lossless)

- `torch.backends.cuda.matmul.allow_tf32 = True`
- `torch.backends.cudnn.benchmark = True`
- `torch.set_float32_matmul_precision('high')`
- Disable `--offload_model` (auto-detected for 96GB+ GPUs)
- Disable `--t5_cpu` (keep T5 on GPU)
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,garbage_collection_threshold:0.8`
- NCCL tuning: `NCCL_NVLS_ENABLE=1`, `NCCL_P2P_LEVEL=NVL`

#### Balanced Mode (~2x faster, lossless)

- Everything from Quality, plus:
- `torch.compile(model, mode="max-autotune-no-cudagraphs", fullgraph=False)` on DiT
- MagCache for I2V: `--use_magcache --magcache_K 2 --magcache_thresh 0.12 --retention_ratio 0.2`
- First generation has ~2 min compile warmup (cached for session)

#### Speed Mode (~3x faster, minor quality trade-off)

- Everything from Balanced, plus:
- TeaCache with configurable threshold (default 0.25, range 0.1-0.5)
- TeaCache warmup: skip caching for first 10% of steps
- UI shows additional slider for speed/quality balance

### 2. Extended Video Duration

With 96GB VRAM and offloading disabled:

| Model | Resolution | Current Max | New Max | Max Frames |
|-------|-----------|-------------|---------|------------|
| T2V-A14B | 1280x720 | 10s | 21s | 337 |
| T2V-A14B | 832x480 | 10s | 33s | 529 |
| I2V-A14B | 1280x720 | 10s | 21s | 337 |
| I2V-A14B | 832x480 | 10s | 33s | 529 |

Frame count must be `4n+1`. Duration slider max adjusts based on resolution. Pre-generation VRAM estimate warns if usage exceeds 85% of available VRAM.

### 3. GPU Allocation Strategy

New GPU Strategy selector in UI:

- **Auto**: Smart allocation. If no jobs running, use all GPUs for speed. If GPUs are busy, assign job to free GPUs.
- **Max Speed**: All selected GPUs for one job. Queue blocks additional jobs.
- **Concurrent**: Each job gets a single GPU. Up to 4 simultaneous jobs. Queue tracks per-GPU state.

Per-GPU state tracking in `utils/queue.py`:

```
GPU N: idle | busy(job_id, task_type, started_at)
```

Allocator enforces Ulysses num_heads divisibility, sets `CUDA_VISIBLE_DEVICES` per subprocess, releases GPUs on completion or failure.

### 4. Environment Configuration

Subprocess environment variables (set per generation, not system-wide):

```bash
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,garbage_collection_threshold:0.8
TORCH_CUDA_ARCH_LIST=12.0
NCCL_NVLS_ENABLE=1        # Multi-GPU only
NCCL_P2P_LEVEL=NVL        # Multi-GPU only
```

### 5. Hardware Detection

New `detect_gpu_profile()` in `utils/gpu.py`:

- Returns: vram_gb, compute_capability, gpu_name per GPU
- Auto-disables offloading when VRAM >= 80GB
- Enables Blackwell-specific optimizations when SM >= 12.0
- Sets default performance mode based on hardware
- Informs max duration estimates

### 6. Patches to Wan2.2

#### Extended: `patches/generate.py`

- Add `--perf_mode` flag (quality/balanced/speed)
- Add `--teacache_threshold` flag
- Add `--use_magcache` and related flags
- Add torch.compile wrapping of DiT model in balanced/speed modes
- Add TeaCache integration in speed mode
- Auto-detect VRAM and skip offloading for high-VRAM GPUs

#### New: `patches/wan/modules/attention.py`

- Enable TF32 at module load
- SageAttention integration (optional, when installed)
- Maintain existing FA3 -> FA2 -> SDPA fallback chain

#### Extended: `patches/wan/configs/shared_config.py`

- TF32 and cuDNN benchmark settings
- Performance-mode-aware defaults

### 7. Error Handling

- **Pre-generation VRAM estimate**: Warn if estimated usage > 85% of available VRAM
- **OOM recovery**: Enhanced error messages with specific reduction suggestions
- **Fallback chain**: Speed -> Balanced -> Quality -> baseline
- **torch.compile warmup UX**: Status message during first compilation
- **Concurrent safety**: Process isolation via CUDA_VISIBLE_DEVICES, GPU cleanup on crash
- **Validation**: GPU count vs num_heads, GPU availability, TeaCache range, frame count (4n+1)

### 8. UI Changes

Each generation page gets:

```
Performance Mode: [Quality | Balanced | Speed]
GPU Strategy: [Auto | Max Speed | Concurrent]
```

Speed mode adds: `Speed/Quality Balance: [slider 0.1-0.5]`

Extended duration slider with resolution-aware max.

GPU status dashboard showing busy/free state per GPU.

## Files Modified

| File | Changes |
|------|---------|
| `utils/generation.py` | Perf mode args, env vars, extended frame limits, hardware detection |
| `utils/config.py` | Perf mode configs, extended duration ranges, GPU profile defaults |
| `utils/gpu.py` | `detect_gpu_profile()`, per-GPU state tracking |
| `utils/queue.py` | Multi-job queue with per-GPU allocation |
| `pages/t2v_a14b.py` | Perf mode dropdown, GPU strategy, extended duration |
| `pages/i2v_a14b.py` | Same + MagCache indicator |
| `pages/s2v_14b.py` | Perf mode dropdown, GPU strategy |
| `pages/animate_14b.py` | Perf mode dropdown, GPU strategy |
| `patch.py` | Register new patch files |
| `patches/generate.py` | Perf mode, TeaCache, MagCache, torch.compile |
| `patches/wan/modules/attention.py` | TF32, SageAttention |
| `patches/wan/configs/shared_config.py` | TF32, cuDNN benchmark |

## What NOT to Do

- Do NOT use `--offload_model` on 96GB GPUs
- Do NOT use `fullgraph=True` with torch.compile (Wan2.2 distributed ops break it)
- Do NOT use `max-autotune` mode (use `max-autotune-no-cudagraphs` -- CUDA graphs incompatible with FSDP/Ulysses)
- Do NOT combine FP8 with SageAttention (produces black output)
- Do NOT set `CUDA_LAUNCH_BLOCKING=1` in production
- Do NOT over-tune NCCL (auto-tuning is sophisticated)

## Future Optimizations

- Flash Attention 4 (when released for Blackwell)
- FP8 inference via NVIDIA Transformer Engine
- SageAttention 2.2.0 (when stable for Blackwell + PyTorch 2.9.1)
- Batched forward passes (~15% speedup)
- Optimized time embeddings (~13% component reduction)
