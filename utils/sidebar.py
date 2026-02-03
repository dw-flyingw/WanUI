"""
Sidebar utilities for consistent branding across pages.
"""

from pathlib import Path
import streamlit as st


def render_sidebar_header():
    """
    Render the WanUI Studio header at the TOP of the sidebar (above navigation).
    Uses st.logo() to place large logo above the navigation menu.
    Call this at the start of each page for consistent branding.
    """
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"

    # Use st.logo() to place large logo at the very top of sidebar (above navigation)
    if logo_path.exists():
        st.logo(str(logo_path), size="large")  # Large size, full width

    # Add title and tagline in sidebar (will appear above page-specific content, below logo)
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 0 0 0.75rem 0; margin-top: -0.5rem;">
                <h3 style="margin: 0.5rem 0;">WanUI Studio</h3>
                <p style="font-size: 0.9rem; color: #888; margin: 0.25rem 0; line-height: 1.4;">
                    Professional Video Generation<br/>with Wan2.2 Models
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
