"""
Configuration for Wan2.2 models and default settings.
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
FRONTEND_ROOT = Path(__file__).parent.parent.resolve()
load_dotenv(FRONTEND_ROOT / ".env")

# Environment configuration
WAN2_2_REPO = os.getenv("WAN2_2_REPO", "./Wan2.2")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "./output")
MODELS_PATH = os.getenv("MODELS_PATH", "/opt/huggingface")
PROMPT_EXTEND_METHOD = os.getenv("PROMPT_EXTEND_METHOD", "openai")
PROMPT_EXTEND_LANG = os.getenv("PROMPT_EXTEND_LANG", "en")
PROMPT_EXTEND_MODEL = os.getenv("PROMPT_EXTEND_MODEL", "")

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
        "magcache": True,
    },
    "speed": {
        "label": "Speed",
        "description": "Slight quality trade-off, ~3x faster (+ TeaCache step skipping)",
        "tf32": True,
        "cudnn_benchmark": True,
        "torch_compile": True,
        "teacache": True,
        "magcache": True,
    },
}

DEFAULT_PERF_TIER = "quality"
DEFAULT_TEACACHE_THRESHOLD = 0.25

# GPU allocation strategy definitions
GPU_STRATEGIES = {
    "auto": {
        "label": "Auto",
        "description": "Smart allocation based on current GPU usage",
    },
    "max_speed": {
        "label": "Max Speed",
        "description": "All GPUs for one job, queue blocks others",
    },
    "concurrent": {
        "label": "Concurrent",
        "description": "Isolate GPUs for parallel jobs (up to 4 simultaneous)",
    },
}

DEFAULT_GPU_STRATEGY = "auto"

# Resolve paths
if not Path(WAN2_2_REPO).is_absolute():
    WAN2_2_ROOT = FRONTEND_ROOT / WAN2_2_REPO
else:
    WAN2_2_ROOT = Path(WAN2_2_REPO)

if not Path(OUTPUT_PATH).is_absolute():
    OUTPUT_ROOT = FRONTEND_ROOT / OUTPUT_PATH
else:
    OUTPUT_ROOT = Path(OUTPUT_PATH)

PREPROCESS_SCRIPT = WAN2_2_ROOT / "wan" / "modules" / "animate" / "preprocess" / "preprocess_data.py"
GENERATE_SCRIPT = WAN2_2_ROOT / "generate.py"

# Ensure output directory exists
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# Model configurations
MODEL_CONFIGS = {
    "t2v-A14B": {
        "task": "t2v-A14B",
        "name": "Text to Video",
        "description": "Generate video from text prompts only",
        "checkpoint": f"{MODELS_PATH}/Wan2.2-T2V-A14B",
        "sizes": ["1280*720", "720*1280", "832*480", "480*832"],
        "default_size": "1280*720",
        "default_steps": 40,
        "default_shift": 12.0,
        "default_guide_scale": 3.5,
        "frame_num": 81,
        "sample_fps": 16,
        "num_heads": 40,  # For Ulysses parallelism - GPU count must divide this evenly
        "requires_image": False,
        "requires_video": False,
        "requires_audio": False,
        "requires_preprocessing": False,
        "duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
        "supports_duration_control": True,
    },
    "i2v-A14B": {
        "task": "i2v-A14B",
        "name": "Image to Video",
        "description": "Generate video from an image with text guidance",
        "checkpoint": f"{MODELS_PATH}/Wan2.2-I2V-A14B",
        "sizes": ["1280*720", "720*1280", "832*480", "480*832"],
        "default_size": "1280*720",
        "default_steps": 40,
        "default_shift": 5.0,
        "default_guide_scale": 3.5,
        "frame_num": 81,
        "sample_fps": 16,
        "num_heads": 40,  # For Ulysses parallelism - GPU count must divide this evenly
        "requires_image": True,
        "requires_video": False,
        "requires_audio": False,
        "requires_preprocessing": False,
        "duration_range": {"min": 5, "max": 10, "step": 1, "default": 5},
        "supports_duration_control": True,
    },
    "ti2v-5B": {
        "task": "ti2v-5B",
        "name": "Text/Image to Video (Fast)",
        "description": "Fast 720P generation at 24fps - supports both text-only and image+text input",
        "checkpoint": f"{MODELS_PATH}/Wan2.2-TI2V-5B",
        "sizes": ["1280*720", "720*1280"],
        "default_size": "1280*720",
        "default_steps": 30,
        "default_shift": 8.0,
        "default_guide_scale": 3.0,
        "frame_num": 49,
        "sample_fps": 24,
        "num_heads": 24,  # For Ulysses parallelism - GPU count must divide this evenly
        "requires_image": False,
        "requires_video": False,
        "requires_audio": False,
        "requires_preprocessing": False,
        "supports_both_t2v_i2v": True,
        "duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2},
        "supports_duration_control": True,
    },
    "s2v-14B": {
        "task": "s2v-14B",
        "name": "Speech to Video",
        "description": "Generate talking head video from audio and reference image",
        "checkpoint": f"{MODELS_PATH}/Wan2.2-S2V-14B",
        "sizes": ["1024*704", "704*1024", "1280*720", "720*1280", "832*480", "480*832"],
        "default_size": "1024*704",
        "default_steps": 40,
        "default_shift": 3.0,
        "default_guide_scale": 4.5,
        "frame_num": None,  # Determined by audio length
        "infer_frames": 80,
        "sample_fps": 16,
        "num_heads": 40,  # For Ulysses parallelism - GPU count must divide this evenly
        "requires_image": True,
        "requires_video": False,
        "requires_audio": True,
        "requires_preprocessing": False,
        "supports_tts": True,
        "supports_pose_video": True,
        "supports_duration_control": False,  # Audio-driven, duration determined by audio
    },
    "animate-14B": {
        "task": "animate-14B",
        "name": "Animate",
        "description": "Animate a character from reference image using motion from source video",
        "checkpoint": f"{MODELS_PATH}/Wan2.2-Animate-14B",
        "process_checkpoint": f"{MODELS_PATH}/Wan2.2-Animate-14B/process_checkpoint",
        "sizes": ["1280*720", "720*1280"],
        "default_size": "1280*720",
        "default_steps": 20,
        "default_shift": 5.0,
        "default_guide_scale": 1.0,
        "frame_num": 77,
        "sample_fps": 30,
        "num_heads": 40,  # For Ulysses parallelism - GPU count must divide this evenly
        "requires_image": True,
        "requires_video": True,
        "requires_audio": False,  # Optional
        "requires_preprocessing": True,
        "duration_range": {"min": 2, "max": 5, "step": 0.5, "default": 2.5},
        "supports_duration_control": True,
    },
}

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
    """Get duration range, optionally extended for high-VRAM GPUs."""
    if high_vram and task in EXTENDED_DURATION_RANGES:
        extended = EXTENDED_DURATION_RANGES[task]
        if resolution in extended:
            return extended[resolution]
    config = MODEL_CONFIGS.get(task, {})
    return config.get("duration_range", {"min": 2, "max": 10, "step": 1, "default": 5})

# Default sample prompts for each model
DEFAULT_PROMPTS = {
    "t2v-A14B": (
        "Two anthropomorphic cats in comfy boxing gear and bright gloves fight "
        "intensely on a spotlighted stage. The camera captures dynamic action "
        "with cinematic lighting and dramatic poses."
    ),
    "i2v-A14B": (
        "The subject in the image comes to life with natural, fluid movement. "
        "Camera slowly pushes in as the scene unfolds with subtle environmental "
        "details like wind and light changes."
    ),
    "ti2v-5B": (
        "A serene mountain landscape transforms as the golden hour light shifts "
        "across the peaks. Clouds drift slowly, casting moving shadows. "
        "Camera pans gently to reveal the full majesty of the scene."
    ),
    "s2v-14B": (
        "The person speaks expressively with natural lip movements and subtle "
        "facial expressions that match the audio. Eyes blink naturally and head "
        "moves slightly with speech emphasis."
    ),
    "animate-14B": (
        "The person from the reference image performs the same movements as shown "
        "in the source video, seamlessly matching the original motion and expression."
    ),
}

# Example prompts for quick testing (3 per task)
EXAMPLE_PROMPTS = {
    "t2v-A14B": [
        "A majestic dragon soars through clouds at sunset, scales shimmering with golden light",
        "A bustling Tokyo street at night, neon signs reflecting on wet pavement as people rush by",
        "A serene underwater coral reef with colorful fish swimming among swaying sea plants",
    ],
    "i2v-A14B": [
        "The scene comes alive with natural movement and subtle camera motion",
        "Gentle wind causes elements to sway naturally while the camera slowly zooms in",
        "Dynamic lighting shifts across the scene as clouds pass overhead",
    ],
    "ti2v-5B": [
        "A time-lapse of a blooming flower opening its petals as morning sun illuminates the scene",
        "A lone astronaut explores an alien landscape under a sky with two moons",
        "A cozy coffee shop interior with steam rising from fresh cups as rain patters on windows",
    ],
    "s2v-14B": [
        "The speaker delivers a passionate speech with expressive gestures and animated facial expressions",
        "Natural conversation with authentic lip sync, eye contact, and subtle head movements",
        "Friendly narration with warm smile, occasional blinks, and gentle head nods for emphasis",
    ],
    "animate-14B": [
        "Replicate the dancing movements with fluid motion and energetic expressions",
        "Match the gestures and body language exactly as shown in the reference video",
        "Perform the athletic movements with precision and natural flow",
    ],
}

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


def get_task_session_key(task: str) -> str:
    """Convert task name to session state key format."""
    return task.replace("-", "_")


def render_example_prompts(task: str, prompt_key: str = "prompt"):
    """
    Render example prompt buttons in a 3-column layout.

    Args:
        task: Task name (e.g., "t2v-A14B")
        prompt_key: Session state key for the prompt text area
    """
    examples = EXAMPLE_PROMPTS.get(task, [])
    if not examples:
        return

    # Add custom CSS for the example buttons (matching Medgemma style)
    st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > button {
            white-space: normal;
            height: auto;
            min-height: 60px;
            padding: 0.75rem;
            text-align: left;
            font-size: 0.85rem;
            line-height: 1.3;
            transition: all 0.2s ease;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div > button:hover {
            background-color: rgba(240, 242, 246, 0.1);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("#### Try these examples:")

    # Create three columns for the example buttons
    cols = st.columns(3)

    # Create a button in each column
    for idx, (col, example) in enumerate(zip(cols, examples)):
        with col:
            # Use a shortened version for button label if too long
            if len(example) > 60:
                button_label = example[:57] + "..."
            else:
                button_label = example

            if st.button(button_label, key=f"example_{task}_{idx}", use_container_width=True):
                # Store the example prompt to fill the text area
                st.session_state[f"{task.replace('-', '_')}_example_clicked"] = example
                st.rerun()


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


def render_perf_tier_selector(task: str) -> tuple[str, float | None]:
    """Render performance tier dropdown and optional TeaCache threshold slider."""
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
    """Render GPU allocation strategy dropdown."""
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
