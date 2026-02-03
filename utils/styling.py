"""
Custom styling and theme for WanUI Studio.
"""

import streamlit as st


def apply_custom_theme():
    """
    Apply custom CSS theme for professional look across all pages.
    Call this at the start of pages that need custom styling.
    """
    st.markdown(
        """
        <style>
        /* Model card styling */
        .model-card {
            border: 2px solid #444;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.08), rgba(33, 150, 243, 0.08));
            transition: all 0.3s ease;
        }

        .model-card:hover {
            border-color: #4CAF50;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
            transform: translateY(-2px);
        }

        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .status-ready {
            background-color: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
            border: 1px solid #4CAF50;
        }

        .status-running {
            background-color: rgba(255, 193, 7, 0.2);
            color: #FFC107;
            border: 1px solid #FFC107;
        }

        .status-error {
            background-color: rgba(244, 67, 54, 0.2);
            color: #f44336;
            border: 1px solid #f44336;
        }

        .status-complete {
            background-color: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
            border: 1px solid #4CAF50;
        }

        /* Enhanced progress bars */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #4CAF50, #2196F3);
        }

        /* Gallery grid hover effects */
        .gallery-item {
            transition: all 0.3s ease;
            border-radius: 8px;
            overflow: hidden;
        }

        .gallery-item:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        /* Custom button styles */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4CAF50, #45a049);
        }

        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #45a049, #4CAF50);
        }

        /* File uploader styling */
        .stFileUploader > div {
            border: 2px dashed #4CAF50;
            border-radius: 8px;
            padding: 20px;
            background-color: rgba(76, 175, 80, 0.05);
            transition: all 0.3s ease;
        }

        .stFileUploader > div:hover {
            border-color: #45a049;
            background-color: rgba(76, 175, 80, 0.1);
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.05);
        }

        .streamlit-expanderHeader:hover {
            background-color: rgba(255, 255, 255, 0.08);
        }

        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
        }

        /* Container borders */
        .element-container {
            border-radius: 8px;
        }

        /* Text area styling */
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 1px solid #444;
        }

        .stTextArea > div > div > textarea:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 1px #4CAF50;
        }

        /* Select box styling */
        .stSelectbox > div > div {
            border-radius: 8px;
        }

        /* Video player styling */
        video {
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        /* Image styling */
        .stImage > img {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        /* Header styling */
        h1 {
            color: #4CAF50;
            font-weight: 700;
        }

        h2 {
            color: #4CAF50;
            font-weight: 600;
        }

        h3 {
            color: #66BB6A;
            font-weight: 600;
        }

        /* Link styling */
        a {
            color: #4CAF50;
            text-decoration: none;
            transition: color 0.2s ease;
        }

        a:hover {
            color: #66BB6A;
            text-decoration: underline;
        }

        /* Code block styling */
        code {
            background-color: rgba(76, 175, 80, 0.1);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            color: #4CAF50;
        }

        /* Info/success/warning boxes */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(76, 175, 80, 0.05), rgba(33, 150, 243, 0.05));
        }

        /* Divider styling */
        hr {
            margin: 2rem 0;
            border-color: #444;
        }

        /* Spinner styling */
        .stSpinner > div {
            border-top-color: #4CAF50 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> str:
    """
    Generate HTML for a status badge.

    Args:
        status: Status string (ready, running, error, complete)

    Returns:
        HTML string for the badge
    """
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{status.upper()}</span>'


def apply_page_header_style():
    """Apply styling specifically for page headers."""
    st.markdown(
        """
        <style>
        .page-header {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }

        .page-header h1 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }

        .page-header p {
            font-size: 1.25rem;
            color: #888;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
