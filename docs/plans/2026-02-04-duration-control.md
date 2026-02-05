# Duration Control Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add user-configurable video duration controls to WanUI with model-specific ranges

**Architecture:** Duration-to-frames calculation approach where users select duration in seconds via slider, system calculates frame_num at generation time. Configuration lives in MODEL_CONFIGS, UI component is reusable, metadata tracks both duration and frame count.

**Tech Stack:** Python, Streamlit, Wan2.2 integration

---

## Task 1: Add Duration Configuration to MODEL_CONFIGS

**Files:**
- Modify: `utils/config.py:41-137` (MODEL_CONFIGS dict)

**Step 1: Add duration_range to t2v-A14B config**

In `utils/config.py`, add to the `"t2v-A14B"` dict after line 58:

```python
"duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
"supports_duration_control": True,
```

**Step 2: Add duration_range to i2v-A14B config**

In `utils/config.py`, add to the `"i2v-A14B"` dict after line 76:

```python
"duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
"supports_duration_control": True,
```

**Step 3: Add duration_range to ti2v-5B config**

In `utils/config.py`, add to the `"ti2v-5B"` dict after line 95:

```python
"duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2},
"supports_duration_control": True,
```

**Step 4: Add duration_range to animate-14B config**

In `utils/config.py`, add to the `"animate-14B"` dict after line 135:

```python
"duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2.5},
"supports_duration_control": True,
```

**Step 5: Add supports_duration_control flag to s2v-14B config**

In `utils/config.py`, add to the `"s2v-14B"` dict after line 116:

```python
"supports_duration_control": False,  # Audio-driven, duration determined by audio
```

**Step 6: Verify configuration**

Run: `python -c "from utils.config import MODEL_CONFIGS; import json; print(json.dumps({k: v.get('duration_range', 'N/A') for k, v in MODEL_CONFIGS.items()}, indent=2))"`

Expected output showing duration_range for all models except s2v-14B

**Step 7: Commit configuration changes**

```bash
git add utils/config.py
git commit -m "feat: add duration configuration to MODEL_CONFIGS

Add duration_range and supports_duration_control fields to model configs:
- T2V/I2V: 5-10s in 1s steps
- TI2V/Animate: 2-5s in 0.5s steps
- S2V: no control (audio-driven)"
```

---

## Task 2: Add Duration Calculation Helper

**Files:**
- Modify: `utils/config.py` (add after line 267, before `init_session_state`)

**Step 1: Add calculate_frame_num function**

Add this function to `utils/config.py` after `render_example_prompts`:

```python
def calculate_frame_num(duration_seconds: float, fps: int) -> int:
    """
    Calculate frame count from duration and fps, with rounding.

    Args:
        duration_seconds: Desired duration in seconds
        fps: Frames per second

    Returns:
        Rounded frame count

    Example:
        >>> calculate_frame_num(5.0, 16)
        80
        >>> calculate_frame_num(6.0, 16)
        96
    """
    return round(duration_seconds * fps)
```

**Step 2: Test the helper function**

Run: `python -c "from utils.config import calculate_frame_num; assert calculate_frame_num(5.0, 16) == 80; assert calculate_frame_num(6.0, 16) == 96; assert calculate_frame_num(2.0, 24) == 48; print('Tests passed')"`

Expected: `Tests passed`

**Step 3: Commit helper function**

```bash
git add utils/config.py
git commit -m "feat: add calculate_frame_num helper

Add function to convert duration in seconds to frame count.
Used by duration slider to calculate frame_num parameter."
```

---

## Task 3: Add Duration Slider UI Component

**Files:**
- Modify: `utils/config.py` (add after `calculate_frame_num`)

**Step 1: Add render_duration_slider function**

Add this function to `utils/config.py` after `calculate_frame_num`:

```python
def render_duration_slider(task: str) -> float | None:
    """
    Render duration slider for tasks that support it.

    Args:
        task: Task name (e.g., "t2v-A14B")

    Returns:
        Selected duration in seconds, or None if not supported

    Example:
        >>> duration = render_duration_slider("t2v-A14B")
        # Renders slider, returns selected value (5.0-10.0)
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
        min_value=float(duration_range["min"]),
        max_value=float(duration_range["max"]),
        value=float(duration_range["default"]),
        step=float(duration_range["step"]),
        key=f"{task.replace('-', '_')}_duration",
        label_visibility="collapsed"
    )

    # Show calculated frame count
    fps = config["sample_fps"]
    frame_count = calculate_frame_num(duration, fps)
    st.caption(f"→ {frame_count} frames @ {fps} fps")

    return duration
```

**Step 2: Test slider component manually**

Create test file `test_slider_manual.py`:

```python
import streamlit as st
from utils.config import MODEL_CONFIGS, render_duration_slider

st.set_page_config(page_title="Duration Slider Test")

task = st.selectbox("Select Task", list(MODEL_CONFIGS.keys()))
duration = render_duration_slider(task)

if duration:
    st.write(f"Selected duration: {duration}s")
else:
    st.write("This task does not support duration control")
```

Run: `streamlit run test_slider_manual.py --server.headless true --server.port 8561`

Manually test in browser, then stop server and delete test file.

**Step 3: Commit slider component**

```bash
git add utils/config.py
git commit -m "feat: add render_duration_slider UI component

Add reusable Streamlit slider for duration selection.
Features:
- Model-specific ranges from config
- Info tooltip for VRAM warning
- Frame count caption
- Returns None for unsupported tasks (S2V)"
```

---

## Task 4: Update Session State Initialization

**Files:**
- Modify: `utils/config.py:196-209` (init_session_state function)

**Step 1: Add duration to session state**

In `utils/config.py`, modify `init_session_state` function to add duration state after line 206:

```python
def init_session_state():
    """Initialize session state for all tasks."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True

        # Per-task state
        for task in MODEL_CONFIGS.keys():
            task_key = task.replace("-", "_")
            st.session_state[f"{task_key}_prompt"] = DEFAULT_PROMPTS.get(task, "")
            st.session_state[f"{task_key}_extended_prompt"] = None
            st.session_state[f"{task_key}_generation_running"] = False
            st.session_state[f"{task_key}_last_output"] = None
            st.session_state[f"{task_key}_last_metadata"] = None

            # Add duration state for tasks that support it
            config = MODEL_CONFIGS[task]
            if config.get("supports_duration_control", False):
                duration_range = config["duration_range"]
                st.session_state[f"{task_key}_duration"] = float(duration_range["default"])
```

**Step 2: Test session state initialization**

Run: `python -c "import streamlit as st; from utils.config import init_session_state, MODEL_CONFIGS; init_session_state(); assert 't2v_A14B_duration' in st.session_state; assert st.session_state['t2v_A14B_duration'] == 5.0; print('Session state test passed')"`

Expected: `Session state test passed`

**Step 3: Commit session state changes**

```bash
git add utils/config.py
git commit -m "feat: initialize duration in session state

Add duration session state initialization for tasks that
support duration control. Uses default value from config."
```

---

## Task 5: Update Metadata to Track Duration

**Files:**
- Modify: `utils/metadata.py:12-56` (GenerationMetadata dataclass)
- Modify: `utils/metadata.py:75-98` (create_metadata function)

**Step 1: Add duration fields to GenerationMetadata**

In `utils/metadata.py`, add after line 42 (after `seed` field):

```python
# Duration (for tasks with duration control)
duration_seconds: float | None = None
frame_num: int | None = None
```

**Step 2: Update create_metadata function signature**

In `utils/metadata.py`, add parameters after line 97:

```python
def create_metadata(
    task: str,
    model_checkpoint: str,
    user_prompt: str,
    resolution: str,
    num_gpus: int,
    sample_steps: int,
    sample_shift: float,
    sample_guide_scale: float,
    sample_solver: str,
    seed: int,
    generation_start: datetime,
    generation_end: datetime,
    output_video_path: Path,
    output_video_length_seconds: float,
    output_video_file_size_bytes: int,
    extended_prompt: str | None = None,
    source_video_path: str | None = None,
    source_image_path: str | None = None,
    source_audio_path: str | None = None,
    pose_video_path: str | None = None,
    preprocessing_time_seconds: float | None = None,
    extra_settings: dict | None = None,
    duration_seconds: float | None = None,  # Add this
    frame_num: int | None = None,  # Add this
) -> GenerationMetadata:
```

**Step 3: Update GenerationMetadata instantiation**

In `utils/metadata.py`, add to the return statement after line 130:

```python
return GenerationMetadata(
    timestamp=datetime.now().isoformat(),
    generation_start=generation_start.isoformat(),
    generation_end=generation_end.isoformat(),
    task=task,
    model_checkpoint=model_checkpoint,
    source_video_path=source_video_path,
    source_image_path=source_image_path,
    source_audio_path=source_audio_path,
    pose_video_path=pose_video_path,
    user_prompt=user_prompt,
    extended_prompt=extended_prompt,
    resolution=resolution,
    num_gpus=num_gpus,
    sample_steps=sample_steps,
    sample_shift=sample_shift,
    sample_guide_scale=sample_guide_scale,
    sample_solver=sample_solver,
    seed=seed,
    preprocessing_time_seconds=preprocessing_time_seconds,
    generation_time_seconds=generation_time,
    total_time_seconds=total_time,
    output_video_path=output_video_path.name,
    output_video_length_seconds=output_video_length_seconds,
    output_video_file_size_bytes=output_video_file_size_bytes,
    extra_settings=extra_settings or {},
    duration_seconds=duration_seconds,  # Add this
    frame_num=frame_num,  # Add this
)
```

**Step 4: Commit metadata changes**

```bash
git add utils/metadata.py
git commit -m "feat: add duration tracking to metadata

Add duration_seconds and frame_num fields to GenerationMetadata
for tracking user-selected duration and calculated frame count."
```

---

## Task 6: Update T2V Page

**Files:**
- Modify: `pages/t2v_a14b.py:20-34` (imports)
- Modify: `pages/t2v_a14b.py:64-108` (sidebar settings)
- Modify: `pages/t2v_a14b.py:179-250` (generation section)

**Step 1: Add render_duration_slider to imports**

In `pages/t2v_a14b.py`, update imports at line 21-29:

```python
from utils.config import (
    DEFAULT_PROMPTS,
    MODEL_CONFIGS,
    OUTPUT_PATH,
    OUTPUT_ROOT,
    PROMPT_EXTEND_METHOD,
    PROMPT_EXTEND_MODEL,
    calculate_frame_num,  # Add this
    get_task_session_key,
    render_duration_slider,  # Add this
    render_example_prompts,
)
```

**Step 2: Remove hardcoded frame_num assignment**

In `pages/t2v_a14b.py`, delete line 62:

```python
# DELETE THIS LINE:
frame_num = CONFIG["frame_num"]
```

**Step 3: Add duration slider after resolution selection**

In `pages/t2v_a14b.py`, add after sidebar settings section (around line 108), before the divider:

```python
    st.divider()

    # Duration control
    st.subheader("Duration")
    duration = render_duration_slider(TASK)
```

**Step 4: Calculate frame_num before generation**

In `pages/t2v_a14b.py`, in the generate button handler (around line 195), add before `run_generation` call:

```python
# Calculate frame_num from duration
if duration is not None:
    frame_num = calculate_frame_num(duration, CONFIG["sample_fps"])
else:
    frame_num = CONFIG["frame_num"]
```

**Step 5: Pass duration and frame_num to run_generation**

In `pages/t2v_a14b.py`, update `run_generation` call (around line 205) to include frame_num:

```python
success, message, elapsed = run_generation(
    task=TASK,
    output_file=output_file,
    prompt=final_prompt,
    num_gpus=num_gpus,
    resolution=resolution,
    sample_steps=sample_steps,
    sample_solver=sample_solver,
    sample_shift=sample_shift,
    sample_guide_scale=sample_guide_scale,
    seed=seed,
    use_prompt_extend=bool(extended_prompt),
    frame_num=frame_num,  # Add this
    gpu_ids=gpu_ids,
    timeout=7200,
    cancellation_check=lambda: st.session_state.get(f"{TASK_KEY}_cancel_requested", False),
)
```

**Step 6: Pass duration to create_metadata**

In `pages/t2v_a14b.py`, update `create_metadata` call (around line 235) to include duration:

```python
metadata = create_metadata(
    task=TASK,
    model_checkpoint=CONFIG["checkpoint"],
    user_prompt=prompt,
    resolution=resolution,
    num_gpus=num_gpus,
    sample_steps=sample_steps,
    sample_shift=sample_shift,
    sample_guide_scale=sample_guide_scale,
    sample_solver=sample_solver,
    seed=seed,
    generation_start=generation_start,
    generation_end=generation_end,
    output_video_path=output_file,
    output_video_length_seconds=video_info.duration,
    output_video_file_size_bytes=output_file.stat().st_size,
    extended_prompt=extended_prompt,
    duration_seconds=duration,  # Add this
    frame_num=frame_num,  # Add this
)
```

**Step 7: Test T2V page manually**

Run: `streamlit run pages/t2v_a14b.py --server.headless true --server.port 8562`

Check:
- Duration slider appears in sidebar
- Default is 5 seconds
- Range is 5-10 seconds
- Frame count caption updates
- Info tooltip shows

Stop server after testing.

**Step 8: Commit T2V page changes**

```bash
git add pages/t2v_a14b.py
git commit -m "feat: add duration control to T2V page

- Add duration slider to sidebar
- Calculate frame_num from selected duration
- Pass duration and frame_num to generation and metadata
- Remove hardcoded frame_num assignment"
```

---

## Task 7: Update I2V Page

**Files:**
- Modify: `pages/i2v_a14b.py` (same pattern as T2V)

**Step 1: Add imports**

Update imports section to include `calculate_frame_num` and `render_duration_slider`.

**Step 2: Remove hardcoded frame_num**

Delete the `frame_num = CONFIG["frame_num"]` line.

**Step 3: Add duration slider to sidebar**

Add after resolution/quality settings:

```python
    st.divider()

    # Duration control
    st.subheader("Duration")
    duration = render_duration_slider(TASK)
```

**Step 4: Calculate frame_num before generation**

Add before `run_generation` call:

```python
# Calculate frame_num from duration
if duration is not None:
    frame_num = calculate_frame_num(duration, CONFIG["sample_fps"])
else:
    frame_num = CONFIG["frame_num"]
```

**Step 5: Pass frame_num to run_generation**

Add `frame_num=frame_num` to the call.

**Step 6: Pass duration and frame_num to create_metadata**

Add `duration_seconds=duration` and `frame_num=frame_num` to the call.

**Step 7: Test I2V page**

Run: `streamlit run pages/i2v_a14b.py --server.headless true --server.port 8563`

Verify slider appears and works correctly. Stop server.

**Step 8: Commit I2V page changes**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: add duration control to I2V page

Same implementation as T2V:
- Duration slider in sidebar (5-10s range)
- Frame count calculation
- Metadata tracking"
```

---

## Task 8: Update TI2V Page

**Files:**
- Modify: `pages/ti2v_5b.py` (same pattern, different range)

**Step 1: Add imports**

Update imports to include `calculate_frame_num` and `render_duration_slider`.

**Step 2: Remove hardcoded frame_num**

Delete the `frame_num = CONFIG["frame_num"]` line.

**Step 3: Add duration slider to sidebar**

Add duration slider (will use 2-5s range from config).

**Step 4: Calculate frame_num before generation**

Add calculation before `run_generation`.

**Step 5: Pass frame_num to run_generation**

Add parameter to call.

**Step 6: Pass duration and frame_num to metadata**

Add parameters to `create_metadata` call.

**Step 7: Test TI2V page**

Verify slider shows 2-5 second range with 0.5s steps.

**Step 8: Commit TI2V page changes**

```bash
git add pages/ti2v_5b.py
git commit -m "feat: add duration control to TI2V page

Duration range: 2-5 seconds in 0.5s steps
Matches faster model characteristics (24fps)"
```

---

## Task 9: Update Animate Page

**Files:**
- Modify: `pages/animate_14b.py` (same pattern, 2-5s range)

**Step 1: Add imports**

Update imports to include helpers.

**Step 2: Remove hardcoded frame_num**

Delete hardcoded assignment.

**Step 3: Add duration slider to sidebar**

Add slider with 2-5s range.

**Step 4: Calculate frame_num before generation**

Add calculation (note: 30fps for Animate).

**Step 5: Pass frame_num to run_generation**

Add parameter.

**Step 6: Pass duration and frame_num to metadata**

Add to metadata.

**Step 7: Test Animate page**

Verify 2-5s range, 30fps calculations.

**Step 8: Commit Animate page changes**

```bash
git add pages/animate_14b.py
git commit -m "feat: add duration control to Animate page

Duration range: 2-5 seconds in 0.5s steps
30fps frame rate for motion replication"
```

---

## Task 10: Update Gallery to Display Duration

**Files:**
- Modify: `pages/gallery.py` (add duration display in project cards)

**Step 1: Find metadata display section**

Locate where metadata is displayed in project cards.

**Step 2: Add duration display**

Add after resolution/settings display:

```python
# Show duration if available
if metadata.get("duration_seconds"):
    st.caption(f"Duration: {metadata['duration_seconds']}s ({metadata.get('frame_num', 'N/A')} frames)")
```

**Step 3: Test gallery display**

Create a test generation with new metadata, verify gallery shows duration.

**Step 4: Commit gallery changes**

```bash
git add pages/gallery.py
git commit -m "feat: display duration in gallery

Show user-selected duration and frame count in project cards
when metadata contains duration_seconds field"
```

---

## Task 11: Verify S2V Page Unaffected

**Files:**
- Test: `pages/s2v_14b.py`

**Step 1: Run S2V page**

Run: `streamlit run pages/s2v_14b.py --server.headless true --server.port 8564`

**Step 2: Verify no duration slider appears**

Confirm S2V page does not show duration slider (audio-driven behavior unchanged).

**Step 3: Document verification**

```bash
git add --all
git commit --allow-empty -m "test: verify S2V page unaffected by duration control

S2V remains audio-driven with no duration slider.
Duration determined by audio length as before."
```

---

## Task 12: Integration Testing

**Files:**
- Test all pages

**Step 1: Test T2V with 5s duration**

Generate video with 5s setting, verify output is ~5s.

**Step 2: Test T2V with 10s duration**

Generate video with 10s setting, verify output is ~10s (160 frames @ 16fps).

**Step 3: Test TI2V with 2s duration**

Generate with 2s setting, verify ~2s output (48 frames @ 24fps).

**Step 4: Test Animate with 5s duration**

Generate with 5s setting, verify ~5s output (150 frames @ 30fps).

**Step 5: Test metadata persistence**

Verify gallery correctly displays duration for all generated videos.

**Step 6: Test backward compatibility**

Verify old videos without duration_seconds in metadata still display correctly.

**Step 7: Document testing**

```bash
git commit --allow-empty -m "test: integration testing complete

All models tested with duration control:
- T2V: 5s, 10s (16fps)
- I2V: 5s, 10s (16fps)
- TI2V: 2s, 5s (24fps)
- Animate: 2s, 5s (30fps)
- S2V: audio-driven (unchanged)

Gallery displays duration correctly.
Backward compatibility verified."
```

---

## Final Task: Merge to Main

**Step 1: Review all changes**

Run: `git log --oneline feature/duration-control`

Verify all commits are present and logical.

**Step 2: Ensure working directory is clean**

Run: `git status`

Expected: nothing to commit, working tree clean

**Step 3: Switch to main branch**

Run: `git checkout main`

**Step 4: Merge feature branch**

Run: `git merge --no-ff feature/duration-control -m "feat: add user-configurable duration control

Add duration slider UI for T2V, I2V, TI2V, and Animate models
with model-specific ranges:
- T2V/I2V: 5-10 seconds
- TI2V/Animate: 2-5 seconds
- S2V: unchanged (audio-driven)

Duration stored in metadata and displayed in gallery."`

**Step 5: Verify main branch**

Run: `streamlit run app.py --server.headless true`

Quick smoke test all pages.

**Step 6: Clean up feature branch**

Use @superpowers:finishing-a-development-branch for cleanup guidance.

---

## Implementation Notes

**Key Design Decisions:**
- Duration stored in seconds (user-friendly)
- Frame count calculated at generation time
- Metadata tracks both duration and frame_num
- S2V excluded (audio-driven)
- Backward compatible (old metadata without duration still works)

**Testing Strategy:**
- Manual UI testing per page
- Integration testing with actual generation
- Backward compatibility testing
- Metadata persistence verification

**Risks & Mitigations:**
- **Risk:** Long durations cause OOM
  - **Mitigation:** Info tooltip warns users about VRAM requirements
- **Risk:** Rounding errors in frame calculations
  - **Mitigation:** Acceptable (<0.1s difference), show exact frame count in UI
- **Risk:** Breaking existing generations
  - **Mitigation:** duration_seconds is optional field, old metadata still loads

**Files Modified (11 total):**
1. `utils/config.py` - Config, helpers, UI component, session state
2. `utils/metadata.py` - Metadata tracking
3. `pages/t2v_a14b.py` - T2V integration
4. `pages/i2v_a14b.py` - I2V integration
5. `pages/ti2v_5b.py` - TI2V integration
6. `pages/animate_14b.py` - Animate integration
7. `pages/gallery.py` - Display duration
8. (S2V unchanged - verified only)

**Estimated Implementation Time:**
- Config & helpers: 15 minutes
- UI component: 20 minutes
- Metadata: 10 minutes
- Per-page integration (4 pages): 60 minutes
- Gallery update: 10 minutes
- Testing: 30 minutes
- **Total: ~2.5 hours**
