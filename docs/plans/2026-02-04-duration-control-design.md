# Duration Control Design

**Date:** 2026-02-04
**Status:** Approved
**Author:** User + Claude

## Overview

Add user-configurable video duration support to WanUI, allowing users to select video length via a slider. Different models will support different duration ranges based on their characteristics and typical use cases.

## Requirements

- Users can select video duration in seconds using a slider
- Duration ranges are model-specific:
  - **T2V-A14B:** 5-10 seconds (1s steps)
  - **I2V-A14B:** 5-10 seconds (1s steps)
  - **TI2V-5B:** 2-5 seconds (0.5s steps)
  - **Animate-14B:** 2-5 seconds (0.5s steps)
  - **S2V-14B:** No control (audio-driven)
- Info icon with tooltip warns about memory/performance
- Duration stored in metadata for gallery display
- Maintains backward compatibility with existing generations

## Approach

**Duration-to-Frames Calculation:** Users select duration in seconds (natural UX), system calculates `frame_num = round(duration * fps)` at generation time.

**Why this approach?**
- Users think in seconds, not frame counts
- Simple to implement and understand
- Flexible for any duration
- Minor rounding differences (~0.06s) are imperceptible

## Architecture

### 1. Configuration Changes (`utils/config.py`)

Extend `MODEL_CONFIGS` to include duration configuration:

```python
"t2v-A14B": {
    # ... existing config ...
    "duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
    "supports_duration_control": True,
},
"i2v-A14B": {
    # ... existing config ...
    "duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
    "supports_duration_control": True,
},
"ti2v-5B": {
    # ... existing config ...
    "duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2},
    "supports_duration_control": True,
},
"animate-14B": {
    # ... existing config ...
    "duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2.5},
    "supports_duration_control": True,
},
"s2v-14B": {
    # ... existing config ...
    "supports_duration_control": False,  # Audio-driven
},
```

Add helper function:

```python
def calculate_frame_num(duration_seconds: float, fps: int) -> int:
    """Calculate frame count from duration and fps, with rounding."""
    return round(duration_seconds * fps)
```

### 2. UI Component (`utils/config.py`)

Create reusable slider component:

```python
def render_duration_slider(task: str) -> float:
    """
    Render duration slider for tasks that support it.

    Returns:
        Selected duration in seconds, or None if not supported
    """
    config = MODEL_CONFIGS[task]

    if not config.get("supports_duration_control", False):
        return None

    duration_range = config["duration_range"]

    # Create columns for label and info icon
    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        st.markdown("**Duration**")
    with col2:
        st.markdown(
            "ℹ️",
            help="Longer videos require more GPU memory and generation time. "
                 "10 seconds may require 80GB+ VRAM."
        )

    # Render slider
    duration = st.slider(
        "Duration (seconds)",
        min_value=duration_range["min"],
        max_value=duration_range["max"],
        value=duration_range["default"],
        step=duration_range["step"],
        key=f"{task.replace('-', '_')}_duration",
        label_visibility="collapsed"
    )

    # Show calculated frame count
    fps = config["sample_fps"]
    frame_count = calculate_frame_num(duration, fps)
    st.caption(f"→ {frame_count} frames @ {fps} fps")

    return duration
```

**UI Features:**
- Label with info icon tooltip
- Slider with model-specific range
- Caption shows calculated frame count
- Collapsed label (we show it manually above)

### 3. Page Integration

Update each model page (e.g., `pages/t2v_a14b.py`):

```python
# In parameters section
size = st.selectbox("Resolution", config["sizes"], index=...)
duration = render_duration_slider(task)  # Add slider

steps = st.slider("Steps", ...)
# ... other parameters ...

# In generation button handler
if st.button("Generate Video"):
    # Calculate frame_num from duration
    if duration is not None:
        frame_num = calculate_frame_num(duration, config["sample_fps"])
    else:
        frame_num = config["frame_num"]  # Use default for S2V

    # Pass to generation
    success, output_path, metadata = run_generation(
        task=task,
        prompt=prompt,
        size=size,
        steps=steps,
        frame_num=frame_num,  # Override default
        duration=duration,  # For metadata
        # ... other params ...
    )
```

### 4. Generation Flow (`utils/generation.py`)

Update `run_generation()` to accept and pass `frame_num`:

```python
def run_generation(
    task: str,
    prompt: str,
    size: str,
    steps: int,
    frame_num: int = None,
    duration: float = None,
    # ... other params ...
):
    config = MODEL_CONFIGS[task]

    # Validate frame_num
    if frame_num is not None:
        if frame_num < 1:
            raise ValueError(f"frame_num must be >= 1, got {frame_num}")
        if frame_num > 500:  # Reasonable upper limit
            st.warning(f"⚠️ {frame_num} frames may require significant VRAM")

    # Use default if not provided
    if frame_num is None:
        frame_num = config["frame_num"]

    # Build command
    cmd = [
        "python" if gpu_count == 1 else "torchrun",
        # ... existing args ...
        "--frame_num", str(frame_num),
    ]

    # ... execute generation ...

    # Save metadata with duration
    metadata = {
        "duration_seconds": duration,
        "frame_num": frame_num,
        # ... other fields ...
    }
```

### 5. Metadata & Gallery (`utils/metadata.py`, `pages/gallery.py`)

**Metadata tracking:**

```python
def save_generation_metadata(output_dir: Path, config: dict, **kwargs):
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "task": config["task"],
        "prompt": kwargs.get("prompt"),
        "size": kwargs.get("size"),
        "duration_seconds": kwargs.get("duration"),  # Add
        "frame_num": kwargs.get("frame_num"),  # Add
        "sample_fps": config["sample_fps"],
        # ... other fields ...
    }
```

**Gallery display:**

```python
# In project card display
if "duration_seconds" in metadata:
    st.caption(f"Duration: {metadata['duration_seconds']}s")
```

### 6. Session State

Update `init_session_state()` in `utils/config.py`:

```python
def init_session_state():
    """Initialize session state for all tasks."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True

        for task, config in MODEL_CONFIGS.items():
            task_key = task.replace("-", "_")
            # ... existing state ...

            # Add duration state
            if config.get("supports_duration_control"):
                duration_range = config["duration_range"]
                st.session_state[f"{task_key}_duration"] = duration_range["default"]
```

## Data Flow

1. User moves slider → Streamlit updates session state
2. UI shows calculated frame count (duration × fps)
3. User clicks "Generate Video"
4. Page calculates `frame_num = round(duration * fps)`
5. Passes to `run_generation(frame_num=...)`
6. Generation script passes `--frame_num` to Wan2.2's `generate.py`
7. Metadata saved with duration and frame_num
8. Gallery displays duration if available

## Testing Checklist

### Per-Model Validation
- [ ] T2V: 5s→81f, 6s→96f, 10s→160f @ 16fps
- [ ] I2V: 5s→81f, 6s→96f, 10s→160f @ 16fps
- [ ] TI2V: 2s→48f, 3s→72f, 5s→120f @ 24fps
- [ ] Animate: 2s→60f, 3s→90f, 5s→150f @ 30fps
- [ ] S2V: No slider shown, uses audio length

### UI/UX
- [ ] Slider appears for T2V/I2V/TI2V/Animate pages
- [ ] No slider shown for S2V page
- [ ] Info icon tooltip displays on hover
- [ ] Frame count caption updates with slider movement
- [ ] Default values match current behavior (5s for T2V/I2V, ~2s for others)

### Generation
- [ ] Videos generate at selected length
- [ ] Metadata captures duration_seconds and frame_num
- [ ] Gallery displays duration correctly
- [ ] No regression for S2V audio-driven flow
- [ ] Single-GPU generation works
- [ ] Multi-GPU generation works

### Edge Cases
- [ ] Very long durations (10s) show warning about VRAM
- [ ] Rounding produces valid integer frame counts
- [ ] Frame count validation rejects invalid values
- [ ] Works with prompt extension enabled/disabled

## Implementation Notes

**Files to modify:**
1. `utils/config.py` - Add duration config, helper function, slider component
2. `pages/t2v_a14b.py` - Add slider, pass frame_num
3. `pages/i2v_a14b.py` - Add slider, pass frame_num
4. `pages/ti2v_5b.py` - Add slider, pass frame_num
5. `pages/animate_14b.py` - Add slider, pass frame_num
6. `utils/generation.py` - Accept frame_num parameter, pass to generate.py
7. `utils/metadata.py` - Add duration fields
8. `pages/gallery.py` - Display duration in cards

**Order of implementation:**
1. Add config and helper functions
2. Add slider component
3. Update one page (T2V) as proof-of-concept
4. Test T2V thoroughly
5. Roll out to other pages
6. Update metadata and gallery

## Trade-offs

**Chosen approach (duration → frames):**
- ✅ User-friendly (seconds, not frames)
- ✅ Simple implementation
- ✅ Flexible
- ❌ Minor rounding differences (~0.06s max)

**Alternative (direct frame control):**
- ✅ No rounding issues
- ❌ Unintuitive UX
- ❌ Users don't think in frames

**Alternative (predefined presets):**
- ✅ Exact durations
- ❌ Less flexible
- ❌ More configuration overhead

The minor rounding trade-off is acceptable for significantly better UX.

## Future Enhancements

- Support for custom duration input (text field)
- Per-resolution duration limits (smaller resolutions can go longer)
- Estimated generation time display
- VRAM usage calculator
- Frame interpolation for smooth playback at different fps
