"""
TI2V-5B page for fast Text/Image-to-Video generation.
"""

import shutil
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
from utils.examples import ExampleLibrary
from utils.gpu import render_gpu_selector
from utils.config import (
    DEFAULT_PROMPTS,
    FRONTEND_ROOT,
    MODEL_CONFIGS,
    OUTPUT_PATH,
    OUTPUT_ROOT,
    PROMPT_EXTEND_METHOD,
    PROMPT_EXTEND_MODEL,
    get_task_session_key,
    render_example_prompts,
)
from utils.generation import run_generation
from utils.metadata import create_metadata
from utils.prompt_utils import extend_prompt
from utils.sidebar import render_sidebar_header, render_sidebar_footer
from utils.theme import load_custom_theme

TASK = "ti2v-5B"
TASK_KEY = get_task_session_key(TASK)
CONFIG = MODEL_CONFIGS[TASK]

# Initialize example library
EXAMPLES_ROOT = Path(__file__).parent.parent / "assets" / "examples"
example_library = ExampleLibrary(EXAMPLES_ROOT)

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
if f"{TASK_KEY}_generating" not in st.session_state:
    st.session_state[f"{TASK_KEY}_generating"] = False
if f"{TASK_KEY}_cancel_requested" not in st.session_state:
    st.session_state[f"{TASK_KEY}_cancel_requested"] = False
# Initialize example selector session state (for I2V mode)
if f"{TASK_KEY}_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_example_loaded"] = False
if f"{TASK_KEY}_loaded_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
if f"{TASK_KEY}_loaded_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_id"] = None

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
    num_gpus, gpu_ids = render_gpu_selector(
        default_value=1,
        allow_gpu_selection=True,
        num_heads=CONFIG.get("num_heads"),
    )

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

# Prompt extension available via button in main area

# Project name
st.subheader("Project")
default_project_name = datetime.now().strftime("ti2v_%Y%m%d_%H%M%S")
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
        st.warning(f"Project folder already exists with {len(existing_files)} files. Files may be overwritten.")

# Image upload (only for I2V mode)
uploaded_image = None
image_path = None

if mode == "Image + Text (I2V)":
    st.subheader("Reference Image")

    # Check if example is loaded
    example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
    loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")
    loaded_example_id = st.session_state.get(f"{TASK_KEY}_loaded_example_id")

    if example_loaded and loaded_example_path:
        # Show loaded example with change button
        st.image(str(loaded_example_path), use_container_width=True)
        st.caption(f"Using example: **{loaded_example_id}**")

        if st.button("📝 Change image", key="change_image_btn"):
            # Clear example state to re-show selectors
            st.session_state[f"{TASK_KEY}_example_loaded"] = False
            st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
            st.session_state[f"{TASK_KEY}_loaded_example_id"] = None
            st.rerun()
    else:
        # Show file uploader
        uploaded_image = st.file_uploader(
            "Upload reference image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload an image to guide the video generation"
        )
        if uploaded_image:
            st.image(uploaded_image, use_container_width=True)

        # Show example selector
        st.divider()
        st.write("**OR select an example image:**")

        # Display radio grid
        selected_id = example_library.display_radio_grid(
            task=TASK,
            media_type="image",
            columns=3,
            show_none_option=example_loaded,
            key_suffix="ti2v"
        )

        # Load button
        if selected_id is not None:
            if st.button("Load Selected Example", type="primary", use_container_width=True):
                # Get example details
                example = example_library.get_example_by_id(selected_id)
                if example and example.path.exists():
                    # Set session state
                    st.session_state[f"{TASK_KEY}_example_loaded"] = True
                    st.session_state[f"{TASK_KEY}_loaded_example_path"] = example.path
                    st.session_state[f"{TASK_KEY}_loaded_example_id"] = example.id
                    st.rerun()
                else:
                    st.error(f"Example file not found: {selected_id}")

# Prompt section
st.subheader("Prompt")

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
    help="Describe the video you want to generate. In I2V mode, describe the motion/action for the reference image.",
    key=f"{TASK_KEY}_prompt_input",
)

# Example prompts
render_example_prompts(TASK)

st.divider()

# Prompt extension button
extend_clicked = st.button("Extend Prompt", disabled=not PROMPT_EXTEND_MODEL, use_container_width=True)

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
            # I2V-specific validation
            if mode == "Image + Text (I2V)":
                example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
                loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")

                if not example_loaded and not uploaded_image:
                    st.error("Please upload a reference image or select an example for I2V mode")
                    st.stop()
                elif example_loaded and not loaded_example_path:
                    st.error("Example path not found. Please select an example again.")
                    st.stop()

            # Generation logic for both modes
            # Set generating flag
            st.session_state[f"{TASK_KEY}_generating"] = True
            st.session_state[f"{TASK_KEY}_cancel_requested"] = False

            generation_start = datetime.now()

            # Create project directory
            project_dir.mkdir(parents=True, exist_ok=True)
            input_dir = project_dir / "input"
            input_dir.mkdir(exist_ok=True)

            # Determine and save image source (only for I2V mode)
            if mode == "Image + Text (I2V)":
                example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
                loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")

                if example_loaded:
                    # Copy example to input directory
                    try:
                        if not loaded_example_path.exists():
                            st.error(f"Example image file not found: {loaded_example_path}")
                            st.session_state[f"{TASK_KEY}_example_loaded"] = False
                            st.stop()

                        image_path = input_dir / "image.jpg"
                        with st.spinner("Preparing example image..."):
                            shutil.copy2(loaded_example_path, image_path)

                        # Verify copy succeeded
                        if not image_path.exists() or image_path.stat().st_size == 0:
                            st.error("Failed to prepare input image. Please try again.")
                            st.stop()

                    except (IOError, PermissionError) as e:
                        st.error(f"Failed to copy example image: {e}")
                        st.stop()
                elif uploaded_image:
                    # Save uploaded image
                    image_path = input_dir / uploaded_image.name
                    with open(image_path, "wb") as f:
                        f.write(uploaded_image.getbuffer())

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_output = project_dir / f"output_{timestamp}.mp4"

            # Use extended prompt if available
            generation_prompt = st.session_state.get(f"{TASK_KEY}_extended_prompt") or prompt

            # Cancellation check function
            def check_cancellation():
                return st.session_state.get(f"{TASK_KEY}_cancel_requested", False)

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
                    gpu_ids=gpu_ids,
                    use_prompt_extend=False,  # Already extended in UI
                    image_path=image_path,
                    cancellation_check=check_cancellation,
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
                    "source_type": "example" if (mode == "Image + Text (I2V)" and st.session_state.get(f"{TASK_KEY}_example_loaded", False)) else "upload" if mode == "Image + Text (I2V)" else "text_only",
                    "example_id": st.session_state.get(f"{TASK_KEY}_loaded_example_id") if (mode == "Image + Text (I2V)" and st.session_state.get(f"{TASK_KEY}_example_loaded", False)) else None,
                },
            )
            metadata.save(project_dir / "metadata.json")

            # Also save prompt.txt for reference
            (project_dir / "prompt.txt").write_text(prompt)

            # Display result
            if final_output.exists():
                st.success(f"Video generated successfully! Saved to `{OUTPUT_PATH}/{project_name}`")
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
- **In I2V mode: Upload your own image or select an example below the uploader**
- Click "Extend Prompt" to enhance your description with cinematic elements
- Higher sampling steps (30-40) generally produce better quality
- Use 2+ GPUs for faster generation with FSDP parallelism
- **Click "Change image" to switch between uploaded and example images**
"""
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
