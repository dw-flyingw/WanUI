"""
Output history system for browsing past generations.
"""

import io
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

from utils.common import extract_thumbnail
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
        # Handle both absolute paths (old metadata) and relative paths (new metadata)
        video_path = Path(metadata.output_video_path)
        if video_path.is_absolute():
            # Old absolute path - try to find file by name in project_dir
            output_path = project_dir / video_path.name
        else:
            # New relative path
            output_path = project_dir / video_path

        if not output_path.exists():
            st.warning("Output video not found")
            return

        # Check for cached thumbnail or generate it
        thumbnail_path = project_dir / "thumbnail.jpg"
        use_thumbnail = False

        if thumbnail_path.exists():
            # Use cached thumbnail
            use_thumbnail = True
        else:
            # Generate thumbnail on-demand
            if extract_thumbnail(output_path, thumbnail_path):
                use_thumbnail = True

        # Display thumbnail or fall back to video
        if use_thumbnail:
            st.image(str(thumbnail_path), use_container_width=True)

            # Add Play Video button
            video_key = f"video_expanded_{project_dir.name}"
            if video_key not in st.session_state:
                st.session_state[video_key] = False

            button_label = "⏸ Hide Video" if st.session_state[video_key] else "▶ Play Video"
            if st.button(button_label, key=f"play_{project_dir.name}", use_container_width=True):
                st.session_state[video_key] = not st.session_state[video_key]

            # Show video player if expanded
            if st.session_state[video_key]:
                st.video(str(output_path))
        else:
            # Fallback to video if thumbnail generation fails
            st.video(str(output_path))

        # Display project info
        st.caption(f"**Model:** {metadata.task}")
        st.caption(f"**Project:** {project_dir.name}")

        # Show duration if available
        if metadata.duration_seconds:
            st.caption(f"**Duration:** {metadata.duration_seconds}s ({metadata.frame_num} frames)")

        # Expandable details
        self._render_details_expander(project_dir, metadata)

    def _render_details_expander(self, project_dir: Path, metadata: GenerationMetadata):
        """
        Render the expandable details section for a project card.

        Args:
            project_dir: Path to the project directory
            metadata: Project metadata
        """
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

            # Action buttons
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                # Create zip file in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add all files from project directory
                    for file_path in project_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(project_dir)
                            zip_file.write(file_path, arcname)

                zip_buffer.seek(0)

                st.download_button(
                    label="📥 Download Project",
                    data=zip_buffer,
                    file_name=f"{project_dir.name}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

            with col2:
                if st.button("🗑️ Remove Project", type="secondary", use_container_width=True, key=f"remove_{project_dir.name}"):
                    try:
                        shutil.rmtree(project_dir)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to remove project: {e}")
