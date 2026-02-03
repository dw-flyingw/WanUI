"""
Enhanced file upload components with preview and styling.
"""

from pathlib import Path
from typing import Optional, List

import streamlit as st


def enhanced_file_uploader(
    label: str,
    accepted_types: List[str],
    help_text: Optional[str] = None,
    key: Optional[str] = None,
) -> Optional[st.runtime.uploaded_file_manager.UploadedFile]:
    """
    Enhanced file uploader with custom styling and preview.

    Args:
        label: Label for the uploader
        accepted_types: List of accepted file extensions (e.g., ["jpg", "png"])
        help_text: Optional help text
        key: Optional key for the uploader

    Returns:
        Uploaded file or None
    """
    # Custom CSS for styled upload zone
    st.markdown("""
        <style>
        .uploadedFile {
            border: 2px dashed #4CAF50;
            border-radius: 8px;
            padding: 10px;
            background-color: rgba(76, 175, 80, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label,
        type=accepted_types,
        help=help_text,
        key=key,
    )

    if uploaded_file is not None:
        display_file_preview(uploaded_file)

    return uploaded_file


def display_file_preview(uploaded_file) -> None:
    """
    Display preview and info for an uploaded file.

    Args:
        uploaded_file: Streamlit UploadedFile object
    """
    file_type = uploaded_file.type.split('/')[0]

    with st.expander("📄 File Preview", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            # Display preview based on file type
            if file_type == 'image':
                st.image(uploaded_file, use_container_width=True)
            elif file_type == 'video':
                st.video(uploaded_file)
            elif file_type == 'audio':
                st.audio(uploaded_file)
            else:
                st.info("Preview not available for this file type")

        with col2:
            # Display file info
            st.write("**File Info:**")
            st.write(f"Name: `{uploaded_file.name}`")
            st.write(f"Size: {uploaded_file.size / 1024:.1f} KB")
            st.write(f"Type: {uploaded_file.type}")


def apply_upload_styling():
    """
    Apply custom CSS for upload components.
    Call this at the start of pages that use enhanced uploads.
    """
    st.markdown("""
        <style>
        /* Styled upload zone */
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

        /* File preview styling */
        .stExpander {
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
