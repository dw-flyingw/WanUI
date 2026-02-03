"""
Model capability cards for displaying model information.
"""

from dataclasses import dataclass
from typing import List, Optional

import streamlit as st


@dataclass
class ModelCapability:
    """Represents a model's capabilities and specifications."""

    task: str
    name: str
    icon: str
    description: str
    resolution: str
    fps: int
    quality_rating: str  # "Fast", "Balanced", "High Quality"
    key_features: List[str]
    best_for: List[str]
    page_file: str


# Model capability definitions
MODEL_CAPABILITIES = {
    "t2v-A14B": ModelCapability(
        task="t2v-A14B",
        name="Text to Video",
        icon="📝",
        description="Generate creative video scenes from text descriptions using MoE 14B architecture",
        resolution="1280x720 (16fps)",
        fps=16,
        quality_rating="High Quality",
        key_features=[
            "Pure text-to-video generation",
            "MoE 14B model for high quality",
            "Multiple aspect ratios supported",
            "Cinematic prompt extension",
        ],
        best_for=[
            "Creative scene generation",
            "Storytelling and narratives",
            "Cinematic sequences",
            "Conceptual visualizations",
        ],
        page_file="t2v_a14b.py"
    ),
    "i2v-A14B": ModelCapability(
        task="i2v-A14B",
        name="Image to Video",
        icon="🖼️",
        description="Bring images to life with natural motion and camera movement using MoE 14B architecture",
        resolution="1280x720 (16fps)",
        fps=16,
        quality_rating="High Quality",
        key_features=[
            "Image-guided video generation",
            "Natural motion synthesis",
            "Camera movement control",
            "Multiple aspect ratios",
        ],
        best_for=[
            "Animating static images",
            "Adding life to photos",
            "Creating parallax effects",
            "Environmental scene animation",
        ],
        page_file="i2v_a14b.py"
    ),
    "ti2v-5B": ModelCapability(
        task="ti2v-5B",
        name="Fast Text/Image to Video",
        icon="⚡",
        description="Fastest generation option - supports both text-only and image-guided video at 24fps",
        resolution="1280x720 (24fps)",
        fps=24,
        quality_rating="Fast",
        key_features=[
            "Dual mode: T2V or I2V",
            "24fps output (faster)",
            "5B model for speed",
            "Good quality/speed balance",
        ],
        best_for=[
            "Quick iterations",
            "Previews and concepts",
            "High-volume generation",
            "Prototyping ideas",
        ],
        page_file="ti2v_5b.py"
    ),
    "s2v-14B": ModelCapability(
        task="s2v-14B",
        name="Speech to Video",
        icon="🎤",
        description="Create talking head videos with lip-sync, expressions, and optional TTS voice cloning",
        resolution="1024x704 (16fps)",
        fps=16,
        quality_rating="High Quality",
        key_features=[
            "Audio-driven lip sync",
            "TTS with voice cloning",
            "Pose-driven control",
            "Natural facial expressions",
        ],
        best_for=[
            "Talking head videos",
            "Virtual avatars",
            "Character dialogue",
            "Presentation videos",
        ],
        page_file="s2v_14b.py"
    ),
    "animate-14B": ModelCapability(
        task="animate-14B",
        name="Character Animation",
        icon="🎭",
        description="Animate or replace characters using motion from source videos with advanced preprocessing",
        resolution="1280x720 (30fps)",
        fps=30,
        quality_rating="High Quality",
        key_features=[
            "Animation mode",
            "Replacement mode",
            "Pose retargeting",
            "Relighting LoRA support",
        ],
        best_for=[
            "Character animation",
            "Face swapping",
            "Motion transfer",
            "Video composition",
        ],
        page_file="animate_14b.py"
    ),
}


def render_model_card(
    capability: ModelCapability,
    show_try_button: bool = True,
    on_click_callback: Optional[callable] = None,
) -> None:
    """
    Render a model capability card in Streamlit.

    Args:
        capability: ModelCapability to render
        show_try_button: Whether to show the "Try Now" button
        on_click_callback: Optional callback when button is clicked
    """
    with st.container():
        # Card header
        st.markdown(f"### {capability.icon} {capability.name}")

        # Description
        st.markdown(capability.description)

        # Specs
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("**Resolution**")
            st.caption(capability.resolution)
        with col2:
            st.caption("**FPS**")
            st.caption(f"{capability.fps}")
        with col3:
            st.caption("**Speed/Quality**")
            st.caption(capability.quality_rating)

        # Key features
        with st.expander("Key Features"):
            for feature in capability.key_features:
                st.markdown(f"- {feature}")

        # Best for
        with st.expander("Best For"):
            for use_case in capability.best_for:
                st.markdown(f"- {use_case}")

        # Try now button
        if show_try_button:
            if st.button(
                "Try Now →",
                key=f"try_{capability.task}",
                use_container_width=True,
                type="primary"
            ):
                if on_click_callback:
                    on_click_callback(capability)


def render_model_grid(
    capabilities: List[ModelCapability],
    columns: int = 3,
    show_try_button: bool = True,
) -> None:
    """
    Render multiple model cards in a grid layout.

    Args:
        capabilities: List of ModelCapability objects
        columns: Number of columns in the grid
        show_try_button: Whether to show try buttons
    """
    cols = st.columns(columns)

    for idx, capability in enumerate(capabilities):
        col = cols[idx % columns]

        with col:
            render_model_card(capability, show_try_button=show_try_button)
