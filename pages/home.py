"""
Home page - Landing page for WanUI Studio.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render_sidebar_header, render_sidebar_footer
from utils.theme import load_custom_theme

# Page configuration
st.set_page_config(
    page_title="WanUI Studio",
    page_icon="🎬",
    layout="wide",
)

# Load theme and render sidebar
load_custom_theme()
render_sidebar_header()

# Welcome section with refined styling
st.markdown(
    """
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(135deg, #f0f0f0 0%, #00d4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            WanUI Studio
        </h1>
        <p style="font-size: 1.1rem; color: #a0a0a0; margin: 0;">
            Professional video generation powered by Wan2.2 AI models
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick Start Guide
st.markdown("### Quick Start Guide")
st.markdown(
    '<p style="color: #a0a0a0; margin-bottom: 1.5rem;">Learn how to use each model effectively</p>',
    unsafe_allow_html=True,
)

# Custom collapsible sections with Phosphor Icons
st.markdown(
    """
    <style>
    .guide-section {
        margin-bottom: 0.5rem;
    }
    .guide-header {
        background: var(--obsidian-elevated);
        border: 1px solid var(--obsidian-border);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        cursor: pointer;
        transition: all var(--transition-fast);
    }
    .guide-header:hover {
        background: var(--obsidian-surface);
        border-color: var(--accent-cyan);
    }
    .guide-icon {
        font-family: 'Phosphor-Light';
        font-size: 18px;
        margin-right: 8px;
        color: var(--text-secondary);
    }
    .guide-title {
        color: var(--text-primary);
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.expander("📄  Text to Video (T2V-A14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Generates videos from text prompts alone

        **How to use:**
        1. Navigate to **Text to Video** page
        2. Enter a descriptive prompt (e.g., "A serene mountain landscape at sunset")
        3. (Optional) Click "Extend Prompt" to enhance with cinematic details
        4. Adjust sampling settings if needed
        5. Click "Generate Video"

        **Tips:**
        - Be specific about subjects, actions, lighting, and camera movements
        - Higher sampling steps (40-50) = better quality but slower
        - Use multiple GPUs for faster generation
        """
    )

with st.expander("🖼️  Image to Video (I2V-A14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Animates static images with natural motion

        **How to use:**
        1. Navigate to **Image to Video** page
        2. Upload a reference image
        3. Enter a prompt describing the desired motion
        4. Generate

        **Tips:**
        - Works best with clear, well-composed images
        - Describe motion and camera movement in your prompt
        - Images with depth work well for parallax effects
        """
    )

with st.expander("⚡  Fast T2V/I2V (TI2V-5B)", expanded=False):
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

with st.expander("〰️  Speech to Video (S2V-14B)", expanded=False):
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

with st.expander("✨  Character Animation (Animate-14B)", expanded=False):
    st.markdown(
        """
        **What it does:** Animates or replaces characters using motion from source videos

        **How to use:**
        1. Navigate to **Animate** page
        2. Choose mode: "Animation" or "Replacement"
        3. Upload source video (with motion) and reference image
        4. Generate

        **Tips:**
        - Use 5-10 second source videos with clear motion
        - Animation mode: mimics motion from video
        - Replacement mode: replaces person in video with reference character
        """
    )


# Render sidebar footer with HPE badge
render_sidebar_footer()
