"""Tests for output history system."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import streamlit as st

from utils.history import OutputHistory
from utils.metadata import GenerationMetadata


@pytest.fixture
def mock_metadata():
    """Create mock metadata for testing."""
    return GenerationMetadata(
        timestamp="2026-02-04T10:00:00",
        generation_start="2026-02-04T10:00:00",
        generation_end="2026-02-04T10:00:12",
        task="t2v-A14B",
        model_checkpoint="/models/wan2.2",
        user_prompt="test prompt",
        extended_prompt=None,
        sample_steps=30,
        sample_shift=7.0,
        sample_guide_scale=5.0,
        sample_solver="midpoint",
        seed=42,
        num_gpus=1,
        resolution="1280*720",
        frame_num=81,
        duration_seconds=3.0,
        output_video_path="output.mp4",
        output_video_file_size_bytes=1000000,
        output_video_length_seconds=3.0,
        generation_time_seconds=10.0,
        total_time_seconds=12.0,
    )


@patch('utils.history.OutputHistory._render_details_expander')
@patch('streamlit.image')
@patch('streamlit.button')
@patch('streamlit.video')
@patch('utils.history.extract_thumbnail')
def test_render_project_card_with_cached_thumbnail(
    mock_extract, mock_video, mock_button, mock_image, mock_render_details, tmp_path, mock_metadata
):
    """Test card rendering uses cached thumbnail when available."""
    # Setup
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    video_path = project_dir / "output.mp4"
    video_path.write_text("video")
    thumbnail_path = project_dir / "thumbnail.jpg"
    thumbnail_path.write_text("thumbnail")

    mock_button.return_value = False  # Video not expanded

    history = OutputHistory(tmp_path)

    # Execute
    history._render_project_card(project_dir, mock_metadata)

    # Verify
    mock_extract.assert_not_called()  # Should use cached thumbnail
    mock_image.assert_called_once_with(str(thumbnail_path), use_container_width=True)
    mock_button.assert_called_once()
    mock_video.assert_not_called()  # Video not expanded


@patch('utils.history.OutputHistory._render_details_expander')
@patch('streamlit.image')
@patch('streamlit.button')
@patch('streamlit.video')
@patch('utils.history.extract_thumbnail')
def test_render_project_card_generates_thumbnail(
    mock_extract, mock_video, mock_button, mock_image, mock_render_details, tmp_path, mock_metadata
):
    """Test card rendering generates thumbnail when missing."""
    # Setup
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    video_path = project_dir / "output.mp4"
    video_path.write_text("video")

    mock_extract.return_value = True
    mock_button.return_value = False

    history = OutputHistory(tmp_path)

    # Execute
    history._render_project_card(project_dir, mock_metadata)

    # Verify
    thumbnail_path = project_dir / "thumbnail.jpg"
    mock_extract.assert_called_once_with(video_path, thumbnail_path)
    mock_image.assert_called_once()


@patch('utils.history.OutputHistory._render_details_expander')
@patch('streamlit.image')
@patch('streamlit.button')
@patch('streamlit.video')
@patch('streamlit.warning')
@patch('utils.history.extract_thumbnail')
def test_render_project_card_thumbnail_generation_fails(
    mock_extract, mock_warning, mock_video, mock_button, mock_image, mock_render_details, tmp_path, mock_metadata
):
    """Test card rendering falls back gracefully when thumbnail fails."""
    # Setup
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    video_path = project_dir / "output.mp4"
    video_path.write_text("video")

    mock_extract.return_value = False  # Thumbnail generation fails
    mock_button.return_value = False

    history = OutputHistory(tmp_path)

    # Execute
    history._render_project_card(project_dir, mock_metadata)

    # Verify fallback to video
    mock_video.assert_called_once_with(str(video_path))
    mock_image.assert_not_called()


@patch('utils.history.OutputHistory._render_details_expander')
@patch('streamlit.image')
@patch('streamlit.button')
@patch('streamlit.video')
@patch('streamlit.session_state', new_callable=dict)
@patch('utils.history.extract_thumbnail')
def test_render_project_card_expands_video_on_click(
    mock_extract, mock_state, mock_video, mock_button, mock_image, mock_render_details, tmp_path, mock_metadata
):
    """Test video player appears when play button clicked."""
    # Setup
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    video_path = project_dir / "output.mp4"
    video_path.write_text("video")
    thumbnail_path = project_dir / "thumbnail.jpg"
    thumbnail_path.write_text("thumbnail")

    # Simulate button click - state starts False, button click toggles to True
    mock_state[f"video_expanded_{project_dir.name}"] = False
    mock_button.return_value = True

    history = OutputHistory(tmp_path)

    # Execute
    history._render_project_card(project_dir, mock_metadata)

    # Verify video shown after toggle
    mock_image.assert_called_once()
    mock_video.assert_called_once_with(str(video_path))
