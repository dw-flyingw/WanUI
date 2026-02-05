"""
Theme utilities for WanUI Studio - Obsidian Precision design system.
"""

from pathlib import Path

import streamlit as st


def load_custom_theme():
    """
    Load the Obsidian Precision custom CSS theme.
    Call this at the start of each page for consistent styling.
    """
    css_file = Path(__file__).parent.parent / ".streamlit" / "custom.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_page_header(title: str, description: str, icon: str = ""):
    """
    Render a consistent page header with the Obsidian Precision style.

    Args:
        title: Main page title
        description: Brief description of the page
        icon: Optional emoji icon
    """
    icon_html = f'<span style="margin-right: 0.75rem;">{icon}</span>' if icon else ""

    st.markdown(
        f"""
        <div style="margin-bottom: 2rem;">
            <h1 style="
                font-family: 'Outfit', sans-serif;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
            ">
                {icon_html}{title}
            </h1>
            <p style="
                font-size: 1.05rem;
                color: #a0a0a0;
                margin: 0;
                line-height: 1.6;
            ">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str = ""):
    """
    Render a section header with consistent styling.

    Args:
        title: Section title
        description: Optional description
    """
    desc_html = (
        f'<p style="color: #a0a0a0; margin-bottom: 1.5rem; font-size: 0.95rem;">{description}</p>'
        if description
        else ""
    )

    st.markdown(
        f"""
        <h3 style="
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
        ">{title}</h3>
        {desc_html}
        """,
        unsafe_allow_html=True,
    )
