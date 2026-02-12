"""
T2V-A14B page for Text-to-Video generation.
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import (
    format_duration,
    format_file_size,
    get_video_info,
    sanitize_project_name,
)
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
    render_gpu_strategy_selector,
    render_perf_tier_selector,
)
from utils.generation import run_generation
from utils.gpu import detect_gpu_profile, render_gpu_selector
from utils.metadata import create_metadata
from utils.prompt_utils import extend_prompt
from utils.queue import generation_queue, get_queue_status_message, wait_for_queue_turn
from utils.sidebar import render_sidebar_footer, render_sidebar_header
from utils.theme import load_custom_theme, render_page_header

TASK = "t2v-A14B"
TASK_KEY = get_task_session_key(TASK)
CONFIG = MODEL_CONFIGS[TASK]
GPU_PROFILE = detect_gpu_profile()

# Load theme and render sidebar
load_custom_theme()
render_sidebar_header()

# Page header
render_page_header(
    title="Text to Video",
    description="Generate high-quality videos from text prompts using the T2V-A14B model (MoE 14B)",
    icon="📄",
)

# Initialize session state for this page
if f"{TASK_KEY}_extended_prompt" not in st.session_state:
    st.session_state[f"{TASK_KEY}_extended_prompt"] = None
if f"{TASK_KEY}_generating" not in st.session_state:
    st.session_state[f"{TASK_KEY}_generating"] = False
if f"{TASK_KEY}_cancel_requested" not in st.session_state:
    st.session_state[f"{TASK_KEY}_cancel_requested"] = False

# Auto-select optimal defaults
resolution = CONFIG["default_size"]

# Sidebar configuration
with st.sidebar:
    st.header("Settings")

    # GPU selection with usage visualization
    num_gpus, gpu_ids = render_gpu_selector(
        default_value=1,
        allow_gpu_selection=True,
        num_heads=CONFIG.get("num_heads"),
    )

    st.divider()

    # Performance optimization
    perf_tier, teacache_threshold = render_perf_tier_selector(TASK)

    # GPU Strategy
    if GPU_PROFILE["gpu_count"] > 1:
        gpu_strategy = render_gpu_strategy_selector()
    else:
        gpu_strategy = "max_speed"

    st.divider()

    # Sampling settings
    st.subheader("Quality Settings")

    sample_steps = st.slider(
        "Sampling steps",
        min_value=10,
        max_value=50,
        value=CONFIG["default_steps"],
        help="More steps = better quality but slower",
    )

    sample_shift = st.slider(
        "Sample shift",
        min_value=1.0,
        max_value=20.0,
        value=CONFIG["default_shift"],
        step=0.5,
    )

    sample_guide_scale = st.slider(
        "Guidance scale",
        min_value=1.0,
        max_value=10.0,
        value=CONFIG["default_guide_scale"],
        step=0.5,
        help="Higher = more prompt adherence",
    )

    sample_solver = st.selectbox("Solver", ["unipc", "dpm++"], index=0)

    seed = st.number_input(
        "Seed", min_value=-1, max_value=2147483647, value=-1, help="-1 for random"
    )

    st.divider()

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
        st.caption("Extended range available (high-VRAM GPU)")

    st.divider()

# Prompt extension available via button in main area

# Project name
st.subheader("Project")
default_project_name = datetime.now().strftime("t2v_%Y%m%d_%H%M%S")
project_name = st.text_input(
    "Project name",
    value=default_project_name,
    help=f"All files will be saved in {OUTPUT_PATH}/<project_name>/",
)
project_name = sanitize_project_name(project_name) or default_project_name
project_dir = OUTPUT_ROOT / project_name
st.caption(f"Output folder: `{OUTPUT_PATH}/{project_name}`")

if project_dir.exists():
    existing_files = list(project_dir.glob("*"))
    if existing_files:
        st.warning(
            f"Project folder already exists with {len(existing_files)} files. Files may be overwritten."
        )

# Prompt section
st.subheader("Prompts")

# Check if an example was clicked
if f"{TASK_KEY}_example_clicked" in st.session_state:
    example_text = st.session_state[f"{TASK_KEY}_example_clicked"]
    del st.session_state[f"{TASK_KEY}_example_clicked"]
    # Update the text area's session state value directly
    st.session_state[f"{TASK_KEY}_prompt_input"] = example_text

# Get the default prompt if the key doesn't exist yet
if f"{TASK_KEY}_prompt_input" not in st.session_state:
    st.session_state[f"{TASK_KEY}_prompt_input"] = DEFAULT_PROMPTS[TASK]

prompt = st.text_area(
    "Your Prompt",
    height=120,
    help="Describe the video you want to generate",
    key=f"{TASK_KEY}_prompt_input",
)

# Example prompts
render_example_prompts(TASK)

st.divider()

# Prompt extension button
extend_clicked = st.button(
    "Extend Prompt", disabled=not PROMPT_EXTEND_MODEL, use_container_width=True
)

if extend_clicked:
    with st.spinner("Extending prompt..."):
        result = extend_prompt(prompt, TASK)
        if result.success:
            st.session_state[f"{TASK_KEY}_extended_prompt"] = result.extended_prompt
            st.success("Prompt extended successfully!")
        else:
            st.warning(f"Extension failed: {result.message}")

# Show extended prompt if available
if st.session_state.get(f"{TASK_KEY}_extended_prompt"):
    with st.expander("Extended Prompt (from LLM)", expanded=True):
        st.session_state[f"{TASK_KEY}_extended_prompt"] = st.text_area(
            "Extended",
            value=st.session_state[f"{TASK_KEY}_extended_prompt"],
            height=150,
            key=f"{TASK_KEY}_extended_prompt_input",
            label_visibility="collapsed",
        )

# Generate button
st.divider()

# Show queue status if busy
queue_status = get_queue_status_message()
if queue_status:
    st.info(f"Queue: {queue_status}")

if st.session_state.get(f"{TASK_KEY}_generating", False):
    # Show cancel button while generating
    if st.button("⏹️ Cancel Generation", type="secondary", use_container_width=True):
        st.session_state[f"{TASK_KEY}_cancel_requested"] = True
        st.rerun()
else:
    # Show generate button
    if st.button("Generate Video", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Please enter a prompt")
        else:
            # Set generating flag
            st.session_state[f"{TASK_KEY}_generating"] = True
            st.session_state[f"{TASK_KEY}_cancel_requested"] = False

            generation_start = datetime.now()

            # Create project directory
            project_dir.mkdir(parents=True, exist_ok=True)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_output = project_dir / f"output_{timestamp}.mp4"

            # Use extended prompt if available
            generation_prompt = (
                st.session_state.get(f"{TASK_KEY}_extended_prompt") or prompt
            )

            # Calculate frame_num from duration
            if duration is not None:
                frame_num = calculate_frame_num(duration, CONFIG["sample_fps"])
            else:
                frame_num = CONFIG["frame_num"]

            # Cancellation check function
            def check_cancellation():
                return st.session_state.get(f"{TASK_KEY}_cancel_requested", False)

            # Queue management
            job_id = uuid.uuid4().hex[:8]
            generation_queue.submit(job_id, TASK, generation_prompt[:50])

            if not wait_for_queue_turn(job_id, check_cancellation):
                st.session_state[f"{TASK_KEY}_generating"] = False
                st.warning("Generation was cancelled while waiting in queue.")
                st.stop()

            try:
                with st.status("Generating video...", expanded=True) as status:
                    st.write(f"Running on {num_gpus} GPU(s)...")
                    st.write(f"Resolution: {resolution}, Frames: {frame_num}")
                    st.write(f"Prompt: {generation_prompt[:100]}...")
                    st.write(f"Performance: {perf_tier.title()} mode")

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
                        use_prompt_extend=False,  # Already extended in UI
                        cancellation_check=check_cancellation,
                        perf_mode=perf_tier,
                        teacache_threshold=teacache_threshold,
                    )

                    # Reset generating flag
                    st.session_state[f"{TASK_KEY}_generating"] = False

                    if not success:
                        if "cancelled by user" in output.lower():
                            status.update(label="Generation cancelled", state="error")
                            st.warning("Generation was cancelled.")
                        else:
                            status.update(label="Generation failed", state="error")
                            st.error(output)
                        st.stop()

                    status.update(
                        label=f"Generation complete ({format_duration(generation_time)})",
                        state="complete",
                    )
            finally:
                generation_queue.release(job_id)

            generation_end = datetime.now()

        # Get output video info
        video_info = get_video_info(final_output)

        # Save metadata
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
            output_video_path=final_output,
            output_video_length_seconds=video_info["duration"],
            output_video_file_size_bytes=video_info["file_size_bytes"],
            extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt"),
            duration_seconds=duration,
            frame_num=frame_num,
            extra_settings={
                "frame_num": frame_num,
            },
        )
        metadata.save(project_dir / "metadata.json")

        # Also save prompt.txt for reference
        (project_dir / "prompt.txt").write_text(prompt)

        # Display result
        if final_output.exists():
            st.success(
                f"Video generated successfully! Saved to `{OUTPUT_PATH}/{project_name}`"
            )
            st.video(str(final_output))

            # Show metadata summary
            with st.expander("Generation Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", f"{video_info['duration']:.1f}s")
                with col2:
                    st.metric(
                        "File Size", format_file_size(video_info["file_size_bytes"])
                    )
                with col3:
                    st.metric("Generation Time", format_duration(generation_time))

                st.write(f"**GPUs Used:** {num_gpus}")
                st.write(f"**Resolution:** {resolution}")
                st.write(f"**Frames:** {frame_num}")

            # Show project contents
            with st.expander("Project files"):
                for f in project_dir.glob("*"):
                    if f.is_file():
                        st.write(f"  - {f.name}")
        else:
            st.warning(
                "Output file not found at expected location. Check logs for details."
            )
            st.code(output)

# Footer
st.divider()
st.markdown(
    """
**Tips:**
- Use descriptive prompts with details about subjects, actions, lighting, and camera angles
- Click "Extend Prompt" to enhance your description with cinematic elements
- Higher sampling steps generally produce better quality but take longer
- Use 2+ GPUs for faster generation with FSDP parallelism
"""
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
