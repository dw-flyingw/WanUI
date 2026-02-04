"""
Sidebar utilities for consistent branding across pages.
"""

import sys
from pathlib import Path

import streamlit as st

# Add assets directory to path for badge imports
assets_path = Path(__file__).parent.parent / "assets"
if assets_path.exists() and str(assets_path) not in sys.path:
    sys.path.insert(0, str(assets_path))

from assets import render_hpe_badge, render_wan22_badge


def render_sidebar_header():
    """
    Render the WanUI Studio header at the TOP of the sidebar (above navigation).
    Call this at the start of each page for consistent branding.
    """
    pass


def render_sidebar_footer():
    """
    Render the sidebar footer with Wan2.2 and HPE PCAI badges at the bottom.
    Call this at the end of sidebar content on each page.
    """
    with st.sidebar:
        # Add spacing before footer
        st.markdown("<br>", unsafe_allow_html=True)

        # Render Wan2.2 badge
        render_wan22_badge()

        # Small spacing between badges
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)

        # Render HPE badge
        render_hpe_badge()
