"""
Example media library system for browsing and loading example inputs.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

import streamlit as st


@dataclass
class ExampleMedia:
    """Represents a single example media item."""

    id: str
    path: Path
    thumbnail: Path
    category: str
    tags: List[str]
    description: str
    compatible_tasks: List[str]
    media_type: str  # 'image', 'video', or 'audio'
    metadata: Optional[Dict[str, Any]] = None


class ExampleLibrary:
    """Manages the example media library."""

    def __init__(self, examples_root: Path):
        """
        Initialize the example library.

        Args:
            examples_root: Root directory containing examples/ folder
        """
        self.root = examples_root
        self.metadata_path = self.root / "metadata.json"
        self.examples: List[ExampleMedia] = []
        self.load_metadata()

    def load_metadata(self):
        """Load example metadata from metadata.json."""
        if not self.metadata_path.exists():
            st.warning(f"Example metadata file not found: {self.metadata_path}")
            self.examples = []
            return

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.examples = []
            for item in data.get("examples", []):
                # Resolve paths relative to examples root
                media_path = self.root / item["path"]
                thumb_path = self.root / item["thumbnail"]

                example = ExampleMedia(
                    id=item["id"],
                    path=media_path,
                    thumbnail=thumb_path,
                    category=item["category"],
                    tags=item.get("tags", []),
                    description=item.get("description", ""),
                    compatible_tasks=item.get("compatible_tasks", []),
                    media_type=item.get("media_type", "image"),
                    metadata=item.get("metadata")
                )
                self.examples.append(example)

        except Exception as e:
            st.error(f"Error loading example metadata: {e}")
            self.examples = []

    def get_examples(
        self,
        task: Optional[str] = None,
        category: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> List[ExampleMedia]:
        """
        Filter examples by task and/or category.

        Args:
            task: Task name to filter by (e.g., "t2v-A14B")
            category: Category to filter by (e.g., "portraits")
            media_type: Media type to filter by ('image', 'video', 'audio')

        Returns:
            List of matching examples
        """
        filtered = self.examples

        if task:
            filtered = [e for e in filtered if task in e.compatible_tasks]

        if category:
            filtered = [e for e in filtered if e.category == category]

        if media_type:
            filtered = [e for e in filtered if e.media_type == media_type]

        return filtered

    def get_example_by_id(self, example_id: str) -> Optional[ExampleMedia]:
        """
        Get a specific example by ID.

        Args:
            example_id: Example ID

        Returns:
            ExampleMedia or None if not found
        """
        for example in self.examples:
            if example.id == example_id:
                return example
        return None

    def display_example_browser(
        self,
        task: str,
        on_select_callback: Optional[Callable[[ExampleMedia], None]] = None,
        columns: int = 3
    ) -> Optional[ExampleMedia]:
        """
        Display a Streamlit component for browsing examples.

        Args:
            task: Task to filter examples for
            on_select_callback: Function to call when an example is selected
            columns: Number of columns in the grid

        Returns:
            Selected example or None
        """
        # Get filtered examples for this task
        examples = self.get_examples(task=task)

        if not examples:
            st.info(
                "No example media available yet. "
                "See EXAMPLE_MEDIA_REQUIREMENTS.md for information on adding examples."
            )
            return None

        # Category filter
        categories = list(set(e.category for e in examples))
        categories.sort()
        selected_category = st.selectbox(
            "Filter by category",
            options=["All"] + categories,
            key=f"{task}_example_category_filter"
        )

        if selected_category != "All":
            examples = [e for e in examples if e.category == selected_category]

        if not examples:
            st.info(f"No examples found in category '{selected_category}'")
            return None

        # Display examples in a grid
        st.write(f"Found {len(examples)} example(s)")

        cols = st.columns(columns)
        selected_example = None

        for idx, example in enumerate(examples):
            col = cols[idx % columns]

            with col:
                # Display thumbnail
                if example.thumbnail.exists():
                    st.image(str(example.thumbnail), use_container_width=True)
                else:
                    st.info("No thumbnail")

                # Display info
                st.caption(f"**{example.category}**")
                st.caption(example.description[:100] + "..." if len(example.description) > 100 else example.description)

                # Display tags
                if example.tags:
                    st.caption(" ".join([f"`{tag}`" for tag in example.tags[:3]]))

                # Use button
                if st.button(
                    "Use this example",
                    key=f"use_example_{example.id}",
                    use_container_width=True
                ):
                    selected_example = example
                    if on_select_callback:
                        on_select_callback(example)
                    st.success(f"Loaded: {example.id}")

        return selected_example

    def display_radio_grid(
        self,
        task: str,
        media_type: Optional[str] = None,
        columns: int = 3,
        show_none_option: bool = False,
        key_suffix: str = ""
    ) -> Optional[str]:
        """
        Display a radio button grid for selecting examples.

        Args:
            task: Task to filter examples for (e.g., "i2v-A14B")
            media_type: Media type to filter by ('image', 'video', 'audio')
            columns: Number of columns in the grid
            show_none_option: If True, adds "None (Upload My Own)" as first option
            key_suffix: Suffix for widget keys to avoid conflicts

        Returns:
            Selected example ID (str) or None
        """
        # Validate columns parameter
        if columns < 1:
            st.warning(f"Invalid columns value: {columns}. Using default of 3.")
            columns = 3

        # Get filtered examples
        examples = self.get_examples(task=task, media_type=media_type)

        if not examples and not show_none_option:
            media_label = media_type if media_type else "media"
            st.info(f"No example {media_label} available")
            return None

        # Build option IDs for selection
        option_ids = []

        if show_none_option:
            option_ids.append(None)

        for example in examples:
            option_ids.append(example.id)

        if not option_ids:
            return None

        # Use radio for selection (hidden labels, we'll show visual grid)
        st.write("**Select an example:**")

        # Create visual grid
        cols = st.columns(columns)

        # Initialize selection in session state if not exists
        selection_key = f"example_selection_{task}_{key_suffix}"
        if selection_key not in st.session_state:
            st.session_state[selection_key] = option_ids[0]

        # Render grid
        for idx, example in enumerate(examples):
            col = cols[idx % columns]

            with col:
                # Show thumbnail
                if example.thumbnail.exists():
                    st.image(str(example.thumbnail), use_container_width=True)
                else:
                    st.warning("No thumbnail")

                # Category badge
                st.caption(f"**{example.category}**")

                # Radio button for this example
                is_selected = st.session_state[selection_key] == example.id
                if st.button(
                    "Select" if not is_selected else "✓ Selected",
                    key=f"select_{example.id}_{key_suffix}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state[selection_key] = example.id
                    st.rerun()

        # If show_none_option, add it as a button below the grid
        if show_none_option:
            st.divider()
            is_none_selected = st.session_state[selection_key] is None
            if st.button(
                "None (Upload My Own)" if not is_none_selected else "✓ None (Upload My Own)",
                key=f"select_none_{key_suffix}",
                use_container_width=True,
                type="primary" if is_none_selected else "secondary"
            ):
                st.session_state[selection_key] = None
                st.rerun()

        return st.session_state[selection_key]
