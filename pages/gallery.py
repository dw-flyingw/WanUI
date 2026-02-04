"""
Gallery page - Browse and filter past video generations.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.history import OutputHistory
from utils.config import MODEL_CONFIGS
from utils.sidebar import render_sidebar_header, render_sidebar_footer
from utils.theme import load_custom_theme

# Render sidebar header
render_sidebar_header()
load_custom_theme()

st.title("🎬 Gallery")
st.markdown("Browse and filter your video generations")

# Initialize history
history = OutputHistory()

# Scan all projects
with st.spinner("Scanning projects..."):
    all_projects = history.scan_projects()

# Show all projects without filtering
filtered_projects = all_projects


# Default sort and display settings
sort_by = "Newest First"
columns = 3

# Apply sorting
if sort_by == "Newest First":
    sorted_projects = sorted(filtered_projects, key=lambda x: x[1].timestamp, reverse=True)
elif sort_by == "Oldest First":
    sorted_projects = sorted(filtered_projects, key=lambda x: x[1].timestamp, reverse=False)
elif sort_by == "Resolution":
    sorted_projects = sorted(filtered_projects, key=lambda x: x[1].resolution, reverse=True)
elif sort_by == "Duration":
    sorted_projects = sorted(filtered_projects, key=lambda x: x[1].output_video_length_seconds, reverse=True)
else:
    sorted_projects = filtered_projects

st.divider()

# Display gallery
if sorted_projects:
    history.display_gallery_grid(sorted_projects, columns=columns)
else:
    st.info(
        """
        No projects found yet. Start generating videos to build your gallery!

        **Get Started:**
        1. Navigate to any model page from the sidebar
        2. Generate a video
        3. Come back here to browse your creations
        """
    )

# Footer
st.divider()
st.markdown(
    """
    **Tips:**
    - Click on "View Details" to see full metadata for each project
    - All metadata is saved in each project's `metadata.json` file
    """
)

# Render sidebar footer with HPE badge
render_sidebar_footer()
