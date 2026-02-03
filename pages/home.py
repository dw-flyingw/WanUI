"""
Home page - Landing page for WanUI Studio.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import get_available_gpus
from utils.history import OutputHistory
from utils.model_cards import MODEL_CAPABILITIES
from utils.sidebar import render_sidebar_header

# Page configuration
st.set_page_config(
    page_title="WanUI Studio",
    page_icon="🎬",
    layout="wide",
)

# Render sidebar header
render_sidebar_header()

# Welcome section
st.markdown("## Welcome to WanUI Studio")
st.markdown("Generate professional videos with 5 different Wan2.2 models. Choose a model below or from the sidebar to get started.")

# GPU Status Widget
available_gpus = get_available_gpus()
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.metric("Available GPUs", available_gpus, help="Number of CUDA devices detected")

with col2:
    st.metric("Models", "5", help="5 different video generation models")

with col3:
    st.metric("Max Resolution", "1280x720", help="Up to 720P resolution")

st.divider()

# Model Cards Grid
st.header("Available Models")
st.markdown("Choose from 5 specialized models for different video generation tasks")

# Get all model capabilities in desired order
model_order = ["t2v-A14B", "i2v-A14B", "ti2v-5B", "s2v-14B", "animate-14B"]
capabilities = [MODEL_CAPABILITIES[task] for task in model_order]

# Display cards in a 3-column grid
cols = st.columns(3)

for idx, capability in enumerate(capabilities):
    col = cols[idx % 3]

    with col:
        with st.container():
            # Card styling
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #444;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, rgba(76, 175, 80, 0.05), rgba(33, 150, 243, 0.05));
                ">
                    <h3 style="margin-top: 0;">{capability.icon} {capability.name}</h3>
                    <p style="color: #ccc;">{capability.description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Specs in columns
            spec_col1, spec_col2, spec_col3 = st.columns(3)
            with spec_col1:
                st.caption("**Resolution**")
                st.caption(capability.resolution)
            with spec_col2:
                st.caption("**FPS**")
                st.caption(f"{capability.fps}")
            with spec_col3:
                st.caption("**Quality**")
                st.caption(capability.quality_rating)

            # Key features
            with st.expander("✨ Key Features"):
                for feature in capability.key_features:
                    st.markdown(f"• {feature}")

            # Try now button - uses Streamlit page navigation
            page_path = f"pages/{capability.page_file}"
            if st.button(
                "Try Now →",
                key=f"try_{capability.task}",
                use_container_width=True,
                type="primary"
            ):
                # Note: Streamlit doesn't support direct page navigation from buttons
                # This will be handled by sidebar navigation instead
                st.info(f"Navigate to **{capability.name}** from the sidebar →")

st.divider()

# Recent Outputs Section
st.header("Recent Outputs")
st.markdown("Latest video generations from all models")

history = OutputHistory()
recent_projects = history.get_recent(limit=6)

if recent_projects:
    history.display_gallery_grid(recent_projects, columns=3)
else:
    st.info(
        """
        No recent outputs yet. Generate your first video using one of the models above!

        **Quick Start:**
        1. Choose a model from the cards above
        2. Navigate to the model page using the sidebar
        3. Upload your inputs (if required)
        4. Enter a prompt
        5. Click "Generate" and watch the magic happen!
        """
    )

st.divider()

# Quick Start Guide
st.header("Quick Start Guide")

with st.expander("📝 Text to Video (T2V-A14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Generates videos from text prompts alone

        **How to use:**
        1. Navigate to **Text to Video** page
        2. Enter a descriptive prompt (e.g., "A serene mountain landscape at sunset")
        3. (Optional) Click "Extend Prompt" to enhance with cinematic details
        4. Adjust resolution and sampling settings
        5. Click "Generate Video"

        **Tips:**
        - Be specific about subjects, actions, lighting, and camera movements
        - Higher sampling steps (40-50) = better quality but slower
        - Use 2+ GPUs for faster generation
        """
    )

with st.expander("🖼️ Image to Video (I2V-A14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Animates static images with natural motion

        **How to use:**
        1. Navigate to **Image to Video** page
        2. Upload a reference image
        3. Enter a prompt describing the desired motion
        4. Adjust settings and generate

        **Tips:**
        - Works best with clear, well-composed images
        - Describe motion and camera movement in your prompt
        - Images with depth work well for parallax effects
        """
    )

with st.expander("⚡ Fast T2V/I2V (TI2V-5B)", expanded=False):
    st.markdown(
        """
        **What it does:** Fast video generation - supports both text-only and image-guided

        **How to use:**
        1. Navigate to **Fast T2V/I2V** page
        2. Choose mode: "Text Only" or "Image + Text"
        3. Upload image (if I2V mode) and enter prompt
        4. Generate at 24fps

        **Tips:**
        - Use for quick iterations and previews
        - Faster than A14B models but good quality
        - Great for prototyping ideas
        """
    )

with st.expander("🎤 Speech to Video (S2V-14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Creates talking head videos with lip-sync

        **How to use:**
        1. Navigate to **Speech to Video** page
        2. Upload a reference image (portrait recommended)
        3. Choose audio source:
           - Upload audio file, OR
           - Use TTS with voice cloning (upload reference audio + transcript)
        4. Enter prompt for speaking style
        5. Generate

        **Tips:**
        - Portrait-oriented images work best
        - For TTS: use clean 5-15 second reference audio at 16kHz+
        - Can optionally provide pose video for head movement control
        """
    )

with st.expander("🎭 Character Animation (Animate-14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Animates or replaces characters using motion from source videos

        **How to use:**
        1. Navigate to **Animate** page
        2. Choose mode: "Animation" or "Replacement"
        3. Upload source video (with motion) and reference image
        4. Choose preprocessing options:
           - Animation mode: Use pose retargeting for different body types
           - Replacement mode: Adjust mask parameters for clean compositing
        5. Generate

        **Tips:**
        - Use 5-10 second source videos with clear motion
        - Animation mode: mimics motion from video
        - Replacement mode: replaces person in video with reference character
        - Enable pose retargeting when poses differ significantly
        """
    )

st.divider()

# Footer
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0; color: #666;">
        <p>Powered by Wan2.2 Models | Built with Streamlit</p>
        <p>For best results, use portrait images for S2V, clear motion for Animate, and descriptive prompts for T2V/I2V</p>
    </div>
    """,
    unsafe_allow_html=True,
)
