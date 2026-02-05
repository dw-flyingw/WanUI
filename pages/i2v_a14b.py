"""
I2V-A14B page for Image-to-Video generation.
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
    save_uploaded_file,
)
from utils.examples import ExampleLibrary
from utils.gpu import render_gpu_selector
from utils.config import (
    DEFAULT_PROMPTS,
    MODEL_CONFIGS,
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

TASK = "i2v-A14B"
TASK_KEY = get_task_session_key(TASK)
CONFIG = MODEL_CONFIGS[TASK]
# Render sidebar header
render_sidebar_header()
load_custom_theme()

# Initialize example library
EXAMPLES_ROOT = Path(__file__).parent.parent / "assets" / "examples"
example_library = ExampleLibrary(EXAMPLES_ROOT)

st.title("🖼️ Image to Video")
st.markdown("Generate video from an image with text guidance using the I2V-A14B model")

# Initialize session state for this page
if f"{TASK_KEY}_extended_prompt" not in st.session_state:
    st.session_state[f"{TASK_KEY}_extended_prompt"] = None
if f"{TASK_KEY}_generating" not in st.session_state:
    st.session_state[f"{TASK_KEY}_generating"] = False
if f"{TASK_KEY}_cancel_requested" not in st.session_state:
    st.session_state[f"{TASK_KEY}_cancel_requested"] = False
# Initialize example selector session state
if f"{TASK_KEY}_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_example_loaded"] = False
if f"{TASK_KEY}_loaded_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
if f"{TASK_KEY}_loaded_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_id"] = None

# Auto-select optimal defaults
resolution = CONFIG["default_size"]
frame_num = CONFIG["frame_num"]

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

# Initialize image source variables
uploaded_image = None

# Input image
st.subheader("Input Image")

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
        "Upload source image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Image to animate. Output aspect ratio will match this image.",
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
        show_none_option=example_loaded,  # Show "None" option if coming from loaded state
        key_suffix="i2v"
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

# Project name
st.subheader("Project")
default_project_name = datetime.now().strftime("i2v_%Y%m%d_%H%M%S")
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
    "Your Prompt (optional)",
    height=120,
    help="Describe how you want the image to animate. Leave empty to let the model decide.",
    key=f"{TASK_KEY}_prompt_input",
)

# Example prompts
render_example_prompts(TASK)

st.divider()

# Prompt extension button
extend_clicked = st.button("Extend Prompt", disabled=not PROMPT_EXTEND_MODEL, use_container_width=True)

if extend_clicked:
    with st.spinner("Extending prompt..."):
        # For I2V, we can pass the image for vision-language extension
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
        # Determine image source
        example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
        loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")

        # Validate input
        if not example_loaded and not uploaded_image:
            st.error("Please upload a source image or select an example")
        elif example_loaded and not loaded_example_path:
            st.error("Example path not found. Please select an example again.")
        else:
            # Set generating flag
            st.session_state[f"{TASK_KEY}_generating"] = True
            st.session_state[f"{TASK_KEY}_cancel_requested"] = False

            generation_start = datetime.now()

        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        input_dir = project_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        # Determine and save image source
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
        else:
            # Save uploaded image
            try:
                image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")
            except Exception as e:
                st.error(f"Failed to save uploaded image: {e}")
                st.stop()

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output = project_dir / f"output_{timestamp}.mp4"

        # Use extended prompt if available
        generation_prompt = st.session_state.get(f"{TASK_KEY}_extended_prompt") or prompt

        # Cancellation check function
        def check_cancellation():
            return st.session_state.get(f"{TASK_KEY}_cancel_requested", False)

        with st.status("Generating video...", expanded=True) as status:
            st.write(f"Running on {num_gpus} GPU(s)...")
            st.write(f"Resolution: {resolution}, Frames: {frame_num}")
            if generation_prompt:
                st.write(f"Prompt: {generation_prompt[:100]}...")
            else:
                st.write("Prompt: (auto-generated from image)")

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
                gpu_ids=gpu_ids,
                seed=seed,
                image_path=image_path,
                frame_num=frame_num,
                use_prompt_extend=False,  # Already extended in UI
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
            source_image_path="input/image.jpg",
            extra_settings={
                "frame_num": frame_num,
                "source_type": "example" if example_loaded else "upload",
                "example_id": st.session_state.get(f"{TASK_KEY}_loaded_example_id") if example_loaded else None,
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

                st.write(f"**GPUs Used:** {num_gpus}")
                st.write(f"**Resolution:** {resolution}")
                st.write(f"**Frames:** {frame_num}")

            # Show project contents
            with st.expander("Project files"):
                for subdir in [input_dir, project_dir]:
                    if subdir == project_dir:
                        files = [f for f in subdir.glob("*") if f.is_file()]
                    else:
                        files = list(subdir.glob("*"))
                    if files:
                        label = f"**{subdir.relative_to(project_dir)}/**" if subdir != project_dir else "**Root:**"
                        st.write(label)
                        for f in files:
                            st.write(f"  - {f.name}")
        else:
            st.warning("Output file not found at expected location. Check logs for details.")
            st.code(output)

# Footer
st.divider()
st.markdown(
    """
**Tips:**
- Upload an image and describe how you want it to animate
- **Or select an example image below the uploader to try pre-configured samples**
- Leave the prompt empty to let the model automatically determine motion
- Output video aspect ratio will match your input image
- Click "Extend Prompt" to enhance your description with cinematic elements
- Use 2+ GPUs for faster generation with FSDP parallelism
- **Click "Change image" to switch between uploaded and example images**
"""
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
