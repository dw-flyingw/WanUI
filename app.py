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

import streamlit as st

from utils.config import init_session_state

# Page configuration
st.set_page_config(
    page_title="WanUI Studio",
    page_icon="🎬",
    layout="wide",
)

# Initialize session state
init_session_state()

# Define pages
home_page = st.Page("pages/home.py", title="Home", icon="🏠", default=True)

# Model pages
t2v_page = st.Page("pages/t2v_a14b.py", title="Text to Video", icon="📝")
i2v_page = st.Page("pages/i2v_a14b.py", title="Image to Video", icon="🖼️")
ti2v_page = st.Page("pages/ti2v_5b.py", title="Fast T2V/I2V", icon="⚡")
s2v_page = st.Page("pages/s2v_14b.py", title="Speech to Video", icon="🎤")
animate_page = st.Page("pages/animate_14b.py", title="Animate", icon="🎭")

# Utility pages
gallery_page = st.Page("pages/gallery.py", title="Gallery", icon="🎬")
examples_page = st.Page("pages/examples.py", title="Examples", icon="📁")

# Navigation with sections
pg = st.navigation(
    {
        "Overview": [home_page],
        "Models": [t2v_page, i2v_page, ti2v_page, s2v_page, animate_page],
        "Library": [gallery_page, examples_page],
    },
    position="sidebar",
)

# Run the selected page
pg.run()
