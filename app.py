#!/usr/bin/env python3
"""
WanUI Studio - Professional video generation showcase for Wan2.2 models.

Supports:
- T2V-A14B: Text to Video (MoE 14B)
- I2V-A14B: Image to Video (MoE 14B)
- TI2V-5B: Fast Text/Image to Video (5B)
- S2V-14B: Speech to Video (Audio-driven)
- Animate-14B: Character Animation & Replacement

Usage:
    streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from utils.config import init_session_state

# Page configuration
st.set_page_config(
    page_title="WanUI Studio",
    page_icon="🎬",
    layout="wide",
)

# Load custom CSS
def load_custom_css():
    """Load custom CSS for Obsidian Precision theme."""
    css_file = Path(__file__).parent / ".streamlit" / "custom.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_custom_css()

# Initialize session state
init_session_state()

# Define pages
home_page = st.Page("pages/home.py", title="Home", default=True)

# Model pages
t2v_page = st.Page("pages/t2v_a14b.py", title="Text to Video")
i2v_page = st.Page("pages/i2v_a14b.py", title="Image to Video")
ti2v_page = st.Page("pages/ti2v_5b.py", title="Fast T2V/I2V")
s2v_page = st.Page("pages/s2v_14b.py", title="Speech to Video")
animate_page = st.Page("pages/animate_14b.py", title="Animate")

# Utility pages
gallery_page = st.Page("pages/gallery.py", title="Gallery")
examples_page = st.Page("pages/examples.py", title="Examples")

# Navigation with sections
pg = st.navigation(
    {
        "Overview": [home_page, gallery_page],
        "Models": [t2v_page, i2v_page, ti2v_page, s2v_page, animate_page],
        "Library": [examples_page],
    },
    position="sidebar",
)

# Run the selected page
pg.run()
