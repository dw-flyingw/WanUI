"""
Examples page - Browse and use example media for video generation.
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import FRONTEND_ROOT, MODEL_CONFIGS
from utils.examples import ExampleLibrary
from utils.sidebar import render_sidebar_header

# Render sidebar header
render_sidebar_header()

st.title("📁 Example Media Library")
st.markdown("Browse example images, videos, and audio files to use with models")

# Initialize example library
examples_root = FRONTEND_ROOT / "assets" / "examples"
library = ExampleLibrary(examples_root)

# Display library stats
total_examples = len(library.examples)
if total_examples > 0:
    st.success(f"Found {total_examples} example(s) in the library")
else:
    st.warning("No examples found. See instructions below to add examples.")

st.divider()

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    # Media type filter
    media_types = ["All"] + list(set(e.media_type for e in library.examples))
    selected_media_type = st.selectbox(
        "Media Type",
        options=media_types,
        index=0,
    )

with col2:
    # Category filter
    categories = ["All"] + sorted(list(set(e.category for e in library.examples)))
    selected_category = st.selectbox(
        "Category",
        options=categories,
        index=0,
    )

with col3:
    # Compatible task filter
    task_options = ["All"] + list(MODEL_CONFIGS.keys())
    selected_task = st.selectbox(
        "Compatible With",
        options=task_options,
        index=0,
        help="Filter by which models can use this media"
    )

st.divider()

# Apply filters
filtered_examples = library.get_examples(
    task=selected_task if selected_task != "All" else None,
    category=selected_category if selected_category != "All" else None,
    media_type=selected_media_type if selected_media_type != "All" else None,
)

st.write(f"**Showing {len(filtered_examples)} example(s)**")

# Display examples in grid
if filtered_examples:
    cols = st.columns(3)

    for idx, example in enumerate(filtered_examples):
        col = cols[idx % 3]

        with col:
            with st.container():
                # Display thumbnail or placeholder
                if example.thumbnail.exists():
                    st.image(str(example.thumbnail), use_container_width=True)
                else:
                    st.info("No thumbnail available")

                # Display info
                st.markdown(f"**{example.category}** ({example.media_type})")
                st.caption(example.description)

                # Display tags
                if example.tags:
                    tag_str = " ".join([f"`{tag}`" for tag in example.tags[:4]])
                    st.caption(tag_str)

                # Display compatible models
                with st.expander("Compatible Models"):
                    for task in example.compatible_tasks:
                        model_name = MODEL_CONFIGS.get(task, {}).get("name", task)
                        st.markdown(f"• {model_name}")

                # Action buttons
                button_col1, button_col2 = st.columns(2)

                with button_col1:
                    # View details
                    if st.button("Details", key=f"details_{example.id}", use_container_width=True):
                        st.session_state[f"show_details_{example.id}"] = True

                with button_col2:
                    # Navigate to compatible model
                    if len(example.compatible_tasks) > 0:
                        primary_task = example.compatible_tasks[0]
                        model_name = MODEL_CONFIGS[primary_task]["name"]
                        if st.button(
                            f"Use →",
                            key=f"use_{example.id}",
                            use_container_width=True,
                            type="primary"
                        ):
                            st.info(f"Navigate to **{model_name}** from the sidebar to use this example")

                # Show details if expanded
                if st.session_state.get(f"show_details_{example.id}", False):
                    with st.expander("Full Details", expanded=True):
                        st.write(f"**ID:** {example.id}")
                        st.write(f"**Path:** {example.path.relative_to(examples_root)}")
                        st.write(f"**Media Type:** {example.media_type}")
                        st.write(f"**Category:** {example.category}")
                        st.write(f"**Tags:** {', '.join(example.tags)}")
                        st.write(f"**Description:** {example.description}")

                        if example.metadata:
                            st.write("**Metadata:**")
                            st.json(example.metadata)

                        # Preview actual file (if exists)
                        if example.path.exists():
                            if example.media_type == "image":
                                st.image(str(example.path), caption="Full Image")
                            elif example.media_type == "video":
                                st.video(str(example.path), caption="Video Preview")
                            elif example.media_type == "audio":
                                st.audio(str(example.path), caption="Audio Preview")

                        if st.button("Close", key=f"close_{example.id}"):
                            st.session_state[f"show_details_{example.id}"] = False
                            st.rerun()

else:
    st.info("No examples match the selected filters.")

st.divider()

# Instructions section
st.header("Adding Examples")

with st.expander("📖 How to Add Your Own Examples", expanded=False):
    st.markdown(
        f"""
        The example library is designed to be user-populated. To add your own examples:

        1. **Place media files** in the appropriate category folder:
           - Images: `assets/examples/images/{{category}}/`
           - Videos: `assets/examples/videos/{{category}}/`
           - Audio: `assets/examples/audio/{{category}}/`

        2. **Generate thumbnails** (320x180 recommended):
           ```bash
           # For images
           convert input.jpg -resize 320x180 assets/examples/thumbnails/images/output.jpg

           # For videos (extract first frame)
           ffmpeg -i input.mp4 -vf "select=eq(n\\,0)" -frames:v 1 -s 320x180 assets/examples/thumbnails/videos/output.jpg

           # For audio (generate waveform)
           ffmpeg -i input.mp3 -filter_complex "showwavespic=s=320x180" assets/examples/thumbnails/audio/output.png
           ```

        3. **Add metadata entry** to `assets/examples/metadata.json`:
           ```json
           {{
             "id": "unique_id",
             "path": "images/portraits/my_image.jpg",
             "thumbnail": "thumbnails/images/my_image_thumb.jpg",
             "category": "portraits",
             "tags": ["person", "close-up"],
             "description": "Description of the media",
             "compatible_tasks": ["i2v-A14B", "s2v-14B"],
             "media_type": "image"
           }}
           ```

        4. **Refresh the page** to see your new example

        **For detailed requirements**, see the `EXAMPLE_MEDIA_REQUIREMENTS.md` file in the project root.

        **Current library location:** `{examples_root}`
        """
    )

# Footer
st.divider()
st.markdown(
    """
    **Tips:**
    - Examples make it easy to test models without uploading your own media
    - Each example is tagged with compatible models
    - Use the "Use →" button to navigate to a compatible model page
    - The example library is stored in the `examples/` directory
    """
)
