"""
TI2V-5B page for fast Text/Image-to-Video generation.
"""

import sys
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
from utils.gpu import render_gpu_selector
from utils.config import (
    DEFAULT_PROMPTS,
    FRONTEND_ROOT,
    MODEL_CONFIGS,
    OUTPUT_ROOT,
    PROMPT_EXTEND_METHOD,
    PROMPT_EXTEND_MODEL,
    get_task_session_key,
)
from utils.generation import run_generation
from utils.metadata import create_metadata
from utils.prompt_utils import extend_prompt
from utils.sidebar import render_sidebar_header, render_sidebar_footer
from utils.theme import load_custom_theme

TASK = "ti2v-5B"
TASK_KEY = get_task_session_key(TASK)
CONFIG = MODEL_CONFIGS[TASK]

# Render sidebar header
render_sidebar_header()
load_custom_theme()

st.title("⚡ Fast Text/Image to Video")
st.markdown("Fast 720P video generation at 24fps - supports both text-only and image+text input")

# Initialize session state for this page
if f"{TASK_KEY}_extended_prompt" not in st.session_state:
    st.session_state[f"{TASK_KEY}_extended_prompt"] = None
if f"{TASK_KEY}_mode" not in st.session_state:
    st.session_state[f"{TASK_KEY}_mode"] = "Text Only (T2V)"

# Mode selection at the top
st.subheader("Mode Selection")
mode = st.radio(
    "Choose generation mode",
    ["Text Only (T2V)", "Image + Text (I2V)"],
    horizontal=True,
    key=f"{TASK_KEY}_mode_select",
    help="TI2V-5B supports both text-only generation and image-guided generation"
)
st.session_state[f"{TASK_KEY}_mode"] = mode

# Sidebar configuration
# Auto-select optimal defaults
resolution = CONFIG["default_size"]

with st.sidebar:
    st.header("Settings")

    # GPU selection with usage visualization
    num_gpus = render_gpu_selector(default_value=1)

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

    seed = st.number_input("Seed", min_value=-1, max_value=2147483647, value=-1, help="-1 for random")

    st.divider()

# Prompt extension handled by button in main area
use_prompt_extend = False

# Project name
st.subheader("Project")
default_project_name = datetime.now().strftime("ti2v_%Y%m%d_%H%M%S")
project_name = st.text_input(
    "Project name",
    value=default_project_name,
    help="All files will be saved in ./output/<project_name>/",
)
project_name = sanitize_project_name(project_name) or default_project_name
project_dir = OUTPUT_ROOT / project_name
st.caption(f"Output folder: `output/{project_name}`")

if project_dir.exists():
    existing_files = list(project_dir.glob("*"))
    if existing_files:
        st.warning(f"Project folder already exists with {len(existing_files)} files. Files may be overwritten.")

# Image upload (only for I2V mode)
uploaded_image = None
image_path = None

if mode == "Image + Text (I2V)":
    st.subheader("Reference Image")
    uploaded_image = st.file_uploader(
        "Upload reference image",
        type=["jpg", "jpeg", "png"],
        help="Upload an image to guide the video generation"
    )

    if uploaded_image:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded_image, caption="Reference Image", use_container_width=True)
        with col2:
            st.info(
                f"**File:** {uploaded_image.name}  \n"
                f"**Size:** {uploaded_image.size / 1024:.1f} KB  \n"
                f"**Type:** {uploaded_image.type}"
            )

# Prompt section
st.subheader("Prompt")

prompt = st.text_area(
    "Your Prompt",
    value=DEFAULT_PROMPTS[TASK],
    height=120,
    help="Describe the video you want to generate. In I2V mode, describe the motion/action for the reference image.",
)

# Prompt extension button
col1, col2 = st.columns([1, 4])
with col1:
    extend_clicked = st.button("Extend Prompt", disabled=not use_prompt_extend or not PROMPT_EXTEND_MODEL)

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
        st.text_area(
            "Extended",
            value=st.session_state[f"{TASK_KEY}_extended_prompt"],
            height=150,
            disabled=True,
            label_visibility="collapsed",
        )

# Generate button
st.divider()

if st.button("Generate Video", type="primary", use_container_width=True):
    if not prompt.strip():
        st.error("Please enter a prompt")
    elif mode == "Image + Text (I2V)" and not uploaded_image:
        st.error("Please upload a reference image for I2V mode")
    else:
        generation_start = datetime.now()

        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        input_dir = project_dir / "input"
        input_dir.mkdir(exist_ok=True)

        # Save uploaded image if in I2V mode
        if uploaded_image:
            image_path = input_dir / uploaded_image.name
            with open(image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output = project_dir / f"output_{timestamp}.mp4"

        # Use extended prompt if available
        generation_prompt = st.session_state.get(f"{TASK_KEY}_extended_prompt") or prompt

        with st.status("Generating video...", expanded=True) as status:
            st.write(f"Mode: {mode}")
            st.write(f"Running on {num_gpus} GPU(s)...")
            st.write(f"Resolution: {resolution}, Frames: {CONFIG['frame_num']} @ {CONFIG['sample_fps']} fps")
            st.write(f"Prompt: {generation_prompt[:100]}...")

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
                frame_num=CONFIG["frame_num"],
                use_prompt_extend=False,  # Already extended in UI
                image=str(image_path) if image_path else None,
            )

            if not success:
                status.update(label="Generation failed", state="error")
                st.error(output)
                st.stop()

            status.update(label=f"Generation complete ({format_duration(generation_time)})", state="complete")

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
            source_image_path=str(image_path.relative_to(project_dir)) if image_path else None,
            extra_settings={
                "frame_num": CONFIG["frame_num"],
                "sample_fps": CONFIG["sample_fps"],
                "mode": mode,
            },
        )
        metadata.save(project_dir / "metadata.json")

        # Also save prompt.txt for reference
        (project_dir / "prompt.txt").write_text(prompt)

        # Display result
        if final_output.exists():
            st.success(f"Video generated successfully! Saved to `output/{project_name}`")
            st.video(str(final_output))

            # Show metadata summary
            with st.expander("Generation Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", f"{video_info['duration']:.1f}s")
                with col2:
                    st.metric("File Size", format_file_size(video_info["file_size_bytes"]))
                with col3:
                    st.metric("Generation Time", format_duration(generation_time))

                st.write(f"**Mode:** {mode}")
                st.write(f"**GPUs Used:** {num_gpus}")
                st.write(f"**Resolution:** {resolution}")
                st.write(f"**Frames:** {CONFIG['frame_num']} @ {CONFIG['sample_fps']} fps")

            # Show project contents
            with st.expander("Project files"):
                for f in sorted(project_dir.rglob("*")):
                    if f.is_file():
                        st.write(f"  - {f.relative_to(project_dir)}")
        else:
            st.warning("Output file not found at expected location. Check logs for details.")
            st.code(output)

# Footer
st.divider()
st.markdown(
    f"""
**About TI2V-5B:**
- **Fast model**: Generates 49 frames at 24fps (faster than A14B models at 16fps)
- **Dual mode**: Supports both text-only (T2V) and image-guided (I2V) generation
- **720P output**: Optimized for 1280x720 resolution
- **Quality**: Good balance between speed and quality

**Tips:**
- Use **Text Only** mode for creative scene generation from scratch
- Use **Image + Text** mode to animate a reference image with guided motion
- Click "Extend Prompt" to enhance your description with cinematic elements
- Higher sampling steps (30-40) generally produce better quality
- Use 2+ GPUs for faster generation with FSDP parallelism
"""
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
