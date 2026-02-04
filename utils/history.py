"""
Output history system for browsing past generations.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

from utils.config import OUTPUT_ROOT
from utils.metadata import GenerationMetadata


class OutputHistory:
    """Manages the output history and provides gallery views."""

    def __init__(self, output_root: Path = OUTPUT_ROOT):
        """
        Initialize output history.

        Args:
            output_root: Root directory containing output projects
        """
        self.output_root = output_root

    def scan_projects(self) -> List[Tuple[Path, GenerationMetadata]]:
        """
        Scan output directories for metadata.json files.

        Returns:
            List of tuples (project_dir, metadata) sorted by timestamp (newest first)
        """
        projects = []

        if not self.output_root.exists():
            return projects

        # Scan all subdirectories for metadata.json
        for project_dir in self.output_root.iterdir():
            if not project_dir.is_dir():
                continue

            metadata_path = project_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                metadata = GenerationMetadata.load(metadata_path)
                projects.append((project_dir, metadata))
            except Exception as e:
                st.warning(f"Failed to load metadata from {project_dir.name}: {e}")
                continue

        # Sort by timestamp (newest first)
        projects.sort(
            key=lambda x: x[1].timestamp,
            reverse=True
        )

        return projects

    def filter_projects(
        self,
        projects: List[Tuple[Path, GenerationMetadata]],
        task: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        resolution: Optional[str] = None,
        search_text: Optional[str] = None,
    ) -> List[Tuple[Path, GenerationMetadata]]:
        """
        Filter projects by various criteria.

        Args:
            projects: List of (project_dir, metadata) tuples
            task: Filter by task type (e.g., "t2v-A14B")
            date_from: Filter projects after this date
            date_to: Filter projects before this date
            resolution: Filter by resolution (e.g., "1280*720")
            search_text: Search in prompts

        Returns:
            Filtered list of projects
        """
        filtered = projects

        if task:
            filtered = [p for p in filtered if p[1].task == task]

        if date_from:
            filtered = [
                p for p in filtered
                if datetime.fromisoformat(p[1].timestamp) >= date_from
            ]

        if date_to:
            filtered = [
                p for p in filtered
                if datetime.fromisoformat(p[1].timestamp) <= date_to
            ]

        if resolution:
            filtered = [p for p in filtered if p[1].resolution == resolution]

        if search_text:
            search_lower = search_text.lower()
            filtered = [
                p for p in filtered
                if search_lower in p[1].user_prompt.lower()
                or (p[1].extended_prompt and search_lower in p[1].extended_prompt.lower())
            ]

        return filtered

    def get_recent(self, limit: int = 10) -> List[Tuple[Path, GenerationMetadata]]:
        """
        Get N most recent generations.

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of recent projects
        """
        projects = self.scan_projects()
        return projects[:limit]

    def display_gallery_grid(
        self,
        projects: List[Tuple[Path, GenerationMetadata]],
        columns: int = 3
    ):
        """
        Display projects in a grid view.

        Args:
            projects: List of (project_dir, metadata) tuples
            columns: Number of columns in the grid
        """
        if not projects:
            st.info("No projects found.")
            return

        cols = st.columns(columns)

        for idx, (project_dir, metadata) in enumerate(projects):
            col = cols[idx % columns]

            with col:
                self._render_project_card(project_dir, metadata)

    def _render_project_card(self, project_dir: Path, metadata: GenerationMetadata):
        """
        Render an individual project card.

        Args:
            project_dir: Path to the project directory
            metadata: Project metadata
        """
        # Display video or thumbnail
        output_path = project_dir / metadata.output_video_path
        if output_path.exists():
            st.video(str(output_path))
        else:
            st.warning("Output video not found")

        # Display project info
        st.caption(f"**Model:** {metadata.task}")
        st.caption(f"**Project:** {project_dir.name}")

        # Expandable details
        with st.expander("View Details"):
            st.write("**Full Prompt:**")
            st.write(metadata.user_prompt)

            if metadata.extended_prompt:
                st.write("**Extended Prompt:**")
                st.write(metadata.extended_prompt)

            st.write("**Settings:**")
            st.json({
                "Model": metadata.model_checkpoint.split("/")[-1],
                "Steps": metadata.sample_steps,
                "Shift": metadata.sample_shift,
                "Guide Scale": metadata.sample_guide_scale,
                "Solver": metadata.sample_solver,
                "Seed": metadata.seed,
                "GPUs": metadata.num_gpus,
            })

            st.write("**Timing:**")
            st.json({
                "Generation Time": f"{metadata.generation_time_seconds:.1f}s",
                "Total Time": f"{metadata.total_time_seconds:.1f}s",
            })

            st.write("**Output:**")
            st.json({
                "File Size": f"{metadata.output_video_file_size_bytes / 1024 / 1024:.2f} MB",
                "Duration": f"{metadata.output_video_length_seconds:.1f}s",
                "Project": project_dir.name,
            })

            # Source files
            if metadata.source_image_path:
                st.write(f"**Source Image:** {metadata.source_image_path}")
            if metadata.source_video_path:
                st.write(f"**Source Video:** {metadata.source_video_path}")
            if metadata.source_audio_path:
                st.write(f"**Source Audio:** {metadata.source_audio_path}")
            if metadata.pose_video_path:
                st.write(f"**Pose Video:** {metadata.pose_video_path}")

            # Extra settings
            if metadata.extra_settings:
                st.write("**Extra Settings:**")
                st.json(metadata.extra_settings)
