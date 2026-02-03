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
from utils.sidebar import render_sidebar_header

# Render sidebar header
render_sidebar_header()

st.title("🎬 Gallery")
st.markdown("Browse and filter your video generations")

# Initialize history
history = OutputHistory()

# Scan all projects
with st.spinner("Scanning projects..."):
    all_projects = history.scan_projects()

st.success(f"Found {len(all_projects)} project(s)")

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    # Model type filter
    model_options = ["All"] + list(MODEL_CONFIGS.keys())
    selected_model = st.selectbox(
        "Model Type",
        options=model_options,
        index=0,
    )

    # Date range filter
    st.subheader("Date Range")
    date_filter_enabled = st.checkbox("Filter by date", value=False)

    if date_filter_enabled:
        date_from = st.date_input(
            "From",
            value=datetime.now() - timedelta(days=30),
        )
        date_to = st.date_input(
            "To",
            value=datetime.now(),
        )
    else:
        date_from = None
        date_to = None

    # Resolution filter
    all_resolutions = set()
    for _, metadata in all_projects:
        if metadata.resolution:
            all_resolutions.add(metadata.resolution)

    resolution_options = ["All"] + sorted(list(all_resolutions))
    selected_resolution = st.selectbox(
        "Resolution",
        options=resolution_options,
        index=0,
    )

    # Search filter
    st.subheader("Search")
    search_text = st.text_input(
        "Search in prompts",
        placeholder="Enter keywords...",
        help="Search for text in user prompts and extended prompts"
    )

    # Apply filters button
    st.divider()
    if st.button("Apply Filters", use_container_width=True, type="primary"):
        st.rerun()

# Apply filters
filtered_projects = history.filter_projects(
    all_projects,
    task=selected_model if selected_model != "All" else None,
    date_from=datetime.combine(date_from, datetime.min.time()) if date_from and date_filter_enabled else None,
    date_to=datetime.combine(date_to, datetime.max.time()) if date_to and date_filter_enabled else None,
    resolution=selected_resolution if selected_resolution != "All" else None,
    search_text=search_text.strip() if search_text.strip() else None,
)

# Display filter summary
if len(filtered_projects) < len(all_projects):
    st.info(
        f"Showing {len(filtered_projects)} of {len(all_projects)} projects "
        f"(filtered by: "
        f"{f'model={selected_model}, ' if selected_model != 'All' else ''}"
        f"{f'resolution={selected_resolution}, ' if selected_resolution != 'All' else ''}"
        f"{f'date range, ' if date_filter_enabled else ''}"
        f"{f'search=\"{search_text}\"' if search_text.strip() else ''}".rstrip(", ")
        + ")"
    )

st.divider()

# Sort options
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    sort_by = st.selectbox(
        "Sort by",
        ["Newest First", "Oldest First", "Resolution", "Duration"],
        index=0,
    )

with col2:
    columns = st.selectbox("Columns", [2, 3, 4], index=1)

with col3:
    st.metric("Results", len(filtered_projects))

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
    if search_text or selected_model != "All" or selected_resolution != "All" or date_filter_enabled:
        st.warning("No projects match the selected filters. Try adjusting your filter criteria.")
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
    - Use filters to narrow down results by model, date, or resolution
    - Search for specific prompts or keywords
    - Click on project cards to expand details
    - All metadata is saved in each project's `metadata.json` file
    """
)
