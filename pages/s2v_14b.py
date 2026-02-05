"""
S2V-14B page for Speech-to-Video generation.
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

TASK = "s2v-14B"
TASK_KEY = get_task_session_key(TASK)
CONFIG = MODEL_CONFIGS[TASK]
# Render sidebar header
render_sidebar_header()
load_custom_theme()

# Initialize example library
EXAMPLES_ROOT = Path(__file__).parent.parent / "assets" / "examples"
example_library = ExampleLibrary(EXAMPLES_ROOT)


st.title("〰️ Speech to Video")
st.markdown("Generate talking head video from audio and reference image using the S2V-14B model")

# Initialize session state for this page
if f"{TASK_KEY}_extended_prompt" not in st.session_state:
    st.session_state[f"{TASK_KEY}_extended_prompt"] = None
if f"{TASK_KEY}_generating" not in st.session_state:
    st.session_state[f"{TASK_KEY}_generating"] = False
if f"{TASK_KEY}_cancel_requested" not in st.session_state:
    st.session_state[f"{TASK_KEY}_cancel_requested"] = False

# Initialize example selector session state
if f"{TASK_KEY}_image_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_image_example_loaded"] = False
if f"{TASK_KEY}_loaded_image_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_image_example_path"] = None
if f"{TASK_KEY}_loaded_image_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_image_example_id"] = None

if f"{TASK_KEY}_audio_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_audio_example_loaded"] = False
if f"{TASK_KEY}_loaded_audio_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_audio_example_path"] = None
if f"{TASK_KEY}_loaded_audio_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_audio_example_id"] = None

if f"{TASK_KEY}_pose_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_pose_example_loaded"] = False
if f"{TASK_KEY}_loaded_pose_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_pose_example_path"] = None
if f"{TASK_KEY}_loaded_pose_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_pose_example_id"] = None

# Auto-select optimal defaults
resolution = CONFIG["default_size"]
infer_frames = CONFIG["infer_frames"]
num_clip = 1
start_from_ref = False

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
        max_value=10.0,
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

# Main content - Input section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Reference Image")

    image_example_loaded = st.session_state.get(f"{TASK_KEY}_image_example_loaded", False)

    if image_example_loaded:
        # Show loaded example
        example_path = st.session_state[f"{TASK_KEY}_loaded_image_example_path"]
        example_id = st.session_state[f"{TASK_KEY}_loaded_image_example_id"]

        st.success(f"Using example: `{example_id}`")
        if example_path and Path(example_path).exists():
            st.image(str(example_path), use_container_width=True)

        # Clear button
        if st.button("Clear Example (Upload My Own)", key="clear_image_example", use_container_width=True):
            st.session_state[f"{TASK_KEY}_image_example_loaded"] = False
            st.session_state[f"{TASK_KEY}_loaded_image_example_path"] = None
            st.session_state[f"{TASK_KEY}_loaded_image_example_id"] = None
            st.rerun()
    else:
        # Show file uploader
        uploaded_image = st.file_uploader(
            "Upload reference image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Image of the person who will be speaking",
        )
        if uploaded_image:
            st.image(uploaded_image, use_container_width=True)

        # Show example selector
        st.divider()
        st.write("**OR select an example image:**")

        # Display radio grid
        selected_image_id = example_library.display_radio_grid(
            task=TASK,
            media_type="image",
            columns=2,
            show_none_option=image_example_loaded,
            key_suffix="s2v_image"
        )

        # Load button
        if selected_image_id is not None:
            if st.button("Load Selected Example", key="load_image_example", type="primary", use_container_width=True):
                # Get example details
                example = example_library.get_example_by_id(selected_image_id)
                if example and example.path.exists():
                    st.session_state[f"{TASK_KEY}_image_example_loaded"] = True
                    st.session_state[f"{TASK_KEY}_loaded_image_example_path"] = example.path
                    st.session_state[f"{TASK_KEY}_loaded_image_example_id"] = example.id
                    st.rerun()
                else:
                    st.error(f"Example file not found: {selected_image_id}")

with col2:
    st.subheader("Audio Source")
    audio_mode = st.radio(
        "Audio source",
        ["Upload audio file", "Text-to-Speech (TTS)"],
        help="Choose how to provide audio",
    )

    audio_example_loaded = st.session_state.get(f"{TASK_KEY}_audio_example_loaded", False)

    if audio_mode == "Upload audio file":
        if audio_example_loaded:
            # Show loaded example
            example_path = st.session_state[f"{TASK_KEY}_loaded_audio_example_path"]
            example_id = st.session_state[f"{TASK_KEY}_loaded_audio_example_id"]

            st.success(f"Using example: `{example_id}`")
            if example_path and Path(example_path).exists():
                st.audio(str(example_path))

            # Clear button
            if st.button("Clear Example (Upload My Own)", key="clear_audio_example", use_container_width=True):
                st.session_state[f"{TASK_KEY}_audio_example_loaded"] = False
                st.session_state[f"{TASK_KEY}_loaded_audio_example_path"] = None
                st.session_state[f"{TASK_KEY}_loaded_audio_example_id"] = None
                st.rerun()
        else:
            # Show file uploader
            uploaded_audio = st.file_uploader(
                "Upload audio file",
                type=["mp3", "wav", "m4a", "aac"],
                help="Audio file for lip sync",
            )
            if uploaded_audio:
                st.audio(uploaded_audio)

            # Show example selector
            st.divider()
            st.write("**OR select an example audio:**")

            # Display radio grid
            selected_audio_id = example_library.display_radio_grid(
                task=TASK,
                media_type="audio",
                columns=2,
                show_none_option=audio_example_loaded,
                key_suffix="s2v_audio"
            )

            # Load button
            if selected_audio_id is not None:
                if st.button("Load Selected Example", key="load_audio_example", type="primary", use_container_width=True):
                    # Get example details
                    example = example_library.get_example_by_id(selected_audio_id)
                    if example and example.path.exists():
                        st.session_state[f"{TASK_KEY}_audio_example_loaded"] = True
                        st.session_state[f"{TASK_KEY}_loaded_audio_example_path"] = example.path
                        st.session_state[f"{TASK_KEY}_loaded_audio_example_id"] = example.id
                        st.rerun()
                    else:
                        st.error(f"Example file not found: {selected_audio_id}")
        enable_tts = False
    else:
        enable_tts = True
        st.info("TTS requires a reference audio sample (5-15s, 16kHz+)")

        if audio_example_loaded:
            # Show loaded example as TTS reference
            example_path = st.session_state[f"{TASK_KEY}_loaded_audio_example_path"]
            example_id = st.session_state[f"{TASK_KEY}_loaded_audio_example_id"]

            st.success(f"Using example as TTS reference: `{example_id}`")
            if example_path and Path(example_path).exists():
                st.audio(str(example_path))

            # Clear button
            if st.button("Clear Example (Upload My Own)", key="clear_tts_audio_example", use_container_width=True):
                st.session_state[f"{TASK_KEY}_audio_example_loaded"] = False
                st.session_state[f"{TASK_KEY}_loaded_audio_example_path"] = None
                st.session_state[f"{TASK_KEY}_loaded_audio_example_id"] = None
                st.rerun()
        else:
            # Show file uploader
            tts_prompt_audio = st.file_uploader(
                "TTS reference audio",
                type=["wav", "mp3"],
                help="5-15 second audio sample for voice cloning",
            )
            if tts_prompt_audio:
                st.audio(tts_prompt_audio)

            # Show example selector
            st.divider()
            st.write("**OR select an example audio:**")

            # Display radio grid
            selected_tts_audio_id = example_library.display_radio_grid(
                task=TASK,
                media_type="audio",
                columns=2,
                show_none_option=audio_example_loaded,
                key_suffix="s2v_tts_audio"
            )

            # Load button
            if selected_tts_audio_id is not None:
                if st.button("Load Selected Example", key="load_tts_audio_example", type="primary", use_container_width=True):
                    # Get example details
                    example = example_library.get_example_by_id(selected_tts_audio_id)
                    if example and example.path.exists():
                        st.session_state[f"{TASK_KEY}_audio_example_loaded"] = True
                        st.session_state[f"{TASK_KEY}_loaded_audio_example_path"] = example.path
                        st.session_state[f"{TASK_KEY}_loaded_audio_example_id"] = example.id
                        st.rerun()
                    else:
                        st.error(f"Example file not found: {selected_tts_audio_id}")

        tts_prompt_text = st.text_input(
            "Reference audio text",
            help="Text that exactly matches the reference audio content",
        )

        tts_text = st.text_area(
            "Text to synthesize",
            height=100,
            help="The text you want the character to speak",
        )
        uploaded_audio = None

# Optional pose video
with st.expander("Advanced: Pose-driven generation"):
    st.markdown("Optionally provide a pose video to control head movement and gestures")

    pose_example_loaded = st.session_state.get(f"{TASK_KEY}_pose_example_loaded", False)

    if pose_example_loaded:
        # Show loaded example
        example_path = st.session_state[f"{TASK_KEY}_loaded_pose_example_path"]
        example_id = st.session_state[f"{TASK_KEY}_loaded_pose_example_id"]

        st.success(f"Using example: `{example_id}`")
        if example_path and Path(example_path).exists():
            st.video(str(example_path))

        # Clear button
        if st.button("Clear Example (Upload My Own)", key="clear_pose_example", use_container_width=True):
            st.session_state[f"{TASK_KEY}_pose_example_loaded"] = False
            st.session_state[f"{TASK_KEY}_loaded_pose_example_path"] = None
            st.session_state[f"{TASK_KEY}_loaded_pose_example_id"] = None
            st.rerun()
    else:
        # Show file uploader
        pose_video = st.file_uploader(
            "Upload pose video (optional)",
            type=["mp4", "avi", "mov"],
            help="DW-Pose sequence for pose-driven generation",
        )
        if pose_video:
            st.video(pose_video)

        # Show example selector
        st.divider()
        st.write("**OR select an example pose video:**")

        # Display radio grid
        selected_pose_id = example_library.display_radio_grid(
            task=TASK,
            media_type="video",
            columns=1,
            show_none_option=pose_example_loaded,
            key_suffix="s2v_pose"
        )

        # Load button
        if selected_pose_id is not None:
            if st.button("Load Selected Example", key="load_pose_example", type="primary", use_container_width=True):
                # Get example details
                example = example_library.get_example_by_id(selected_pose_id)
                if example and example.path.exists():
                    st.session_state[f"{TASK_KEY}_pose_example_loaded"] = True
                    st.session_state[f"{TASK_KEY}_loaded_pose_example_path"] = example.path
                    st.session_state[f"{TASK_KEY}_loaded_pose_example_id"] = example.id
                    st.rerun()
                else:
                    st.error(f"Example file not found: {selected_pose_id}")

# Project name
st.subheader("Project")
default_project_name = datetime.now().strftime("s2v_%Y%m%d_%H%M%S")
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
    "Your Prompt",
    height=100,
    help="Describe the speaking style and expressions",
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

# Validation
can_generate = True
error_messages = []

# Check for reference image (uploaded or example)
image_example_loaded = st.session_state.get(f"{TASK_KEY}_image_example_loaded", False)
if not uploaded_image and not image_example_loaded:
    can_generate = False
    error_messages.append("Please upload a reference image or select an example")

# Check for audio (uploaded or example)
audio_example_loaded = st.session_state.get(f"{TASK_KEY}_audio_example_loaded", False)
if audio_mode == "Upload audio file":
    if not uploaded_audio and not audio_example_loaded:
        can_generate = False
        error_messages.append("Please upload an audio file or select an example")
elif audio_mode == "Text-to-Speech (TTS)":
    if not tts_prompt_audio and not audio_example_loaded:
        can_generate = False
        error_messages.append("Please upload TTS reference audio or select an example")
    if not tts_text:
        can_generate = False
        error_messages.append("Please enter text to synthesize")

if st.session_state.get(f"{TASK_KEY}_generating", False):
    # Show cancel button while generating
    if st.button("⏹️ Cancel Generation", type="secondary", use_container_width=True):
        st.session_state[f"{TASK_KEY}_cancel_requested"] = True
        st.rerun()
else:
    # Show generate button
    if st.button("Generate Video", type="primary", use_container_width=True):
        if not can_generate:
            for msg in error_messages:
                st.error(msg)
        else:
            # Set generating flag
            st.session_state[f"{TASK_KEY}_generating"] = True
            st.session_state[f"{TASK_KEY}_cancel_requested"] = False

            generation_start = datetime.now()

            # Create project directory
            project_dir.mkdir(parents=True, exist_ok=True)
            input_dir = project_dir / "input"
            input_dir.mkdir(parents=True, exist_ok=True)

            # Save or copy image (uploaded vs example)
            if uploaded_image:
                image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")
            else:
                # Copy from example
                example_image_path = Path(st.session_state[f"{TASK_KEY}_loaded_image_example_path"])
                image_path = input_dir / "image.jpg"
                shutil.copy(example_image_path, image_path)

            audio_path = None
            tts_audio_path = None
            if uploaded_audio:
                audio_ext = Path(uploaded_audio.name).suffix
                audio_path = save_uploaded_file(uploaded_audio, input_dir / f"audio{audio_ext}")
            elif audio_example_loaded and not enable_tts:
                # Copy from example for direct audio mode
                example_audio_path = Path(st.session_state[f"{TASK_KEY}_loaded_audio_example_path"])
                audio_ext = example_audio_path.suffix
                audio_path = input_dir / f"audio{audio_ext}"
                shutil.copy(example_audio_path, audio_path)

            if enable_tts:
                if tts_prompt_audio:
                    tts_ext = Path(tts_prompt_audio.name).suffix
                    tts_audio_path = save_uploaded_file(tts_prompt_audio, input_dir / f"tts_reference{tts_ext}")
                elif audio_example_loaded:
                    # Copy from example for TTS reference
                    example_audio_path = Path(st.session_state[f"{TASK_KEY}_loaded_audio_example_path"])
                    tts_ext = example_audio_path.suffix
                    tts_audio_path = input_dir / f"tts_reference{tts_ext}"
                    shutil.copy(example_audio_path, tts_audio_path)

            pose_video_path = None
            pose_example_loaded = st.session_state.get(f"{TASK_KEY}_pose_example_loaded", False)
            if pose_video:
                pose_ext = Path(pose_video.name).suffix
                pose_video_path = save_uploaded_file(pose_video, input_dir / f"pose{pose_ext}")
            elif pose_example_loaded:
                # Copy from example
                example_pose_path = Path(st.session_state[f"{TASK_KEY}_loaded_pose_example_path"])
                pose_ext = example_pose_path.suffix
                pose_video_path = input_dir / f"pose{pose_ext}"
                shutil.copy(example_pose_path, pose_video_path)

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
                st.write(f"Resolution: {resolution}, Frames per clip: {infer_frames}")
                if enable_tts:
                    st.write("Using TTS for audio generation...")
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
                image_path=image_path,
                audio_path=audio_path,
                gpu_ids=gpu_ids,
                use_prompt_extend=False,  # Already extended in UI
                enable_tts=enable_tts,
                tts_prompt_audio=tts_audio_path,
                tts_prompt_text=tts_prompt_text if enable_tts else None,
                tts_text=tts_text if enable_tts else None,
                pose_video=pose_video_path,
                infer_frames=infer_frames,
                start_from_ref=start_from_ref,
                num_clip=num_clip if num_clip > 1 else None,
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
            source_audio_path=str(audio_path.relative_to(project_dir)) if audio_path else None,
            pose_video_path=str(pose_video_path.relative_to(project_dir)) if pose_video_path else None,
            extra_settings={
                "audio_mode": audio_mode,
                "enable_tts": enable_tts,
                "infer_frames": infer_frames,
                "num_clip": num_clip,
                "start_from_ref": start_from_ref,
                "tts_text": tts_text if enable_tts else None,
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
                st.write(f"**Audio Mode:** {audio_mode}")

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
- Upload a clear frontal image of the person for best lip-sync results
- Audio length determines video length (max limited by clip settings)
- **TTS Mode**: Provide a 5-15 second reference audio sample with matching text for voice cloning
- **Pose Video**: Optionally provide DW-Pose sequence to control head/body movement
- "Start from reference" uses your image as the first frame
- Use 2+ GPUs for faster generation with FSDP parallelism
"""
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
