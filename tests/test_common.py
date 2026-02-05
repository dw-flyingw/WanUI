"""Tests for common utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from utils.common import extract_thumbnail


def test_extract_thumbnail_success(tmp_path):
    """Test successful thumbnail extraction."""
    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "thumbnail.jpg"

    # Create dummy video file
    video_path.write_text("dummy")

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0)

        # Mock the output file creation
        def create_thumbnail(*args, **kwargs):
            output_path.write_text("thumbnail data")
            return Mock(returncode=0)

        mock_run.side_effect = create_thumbnail

        result = extract_thumbnail(video_path, output_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert str(video_path) in args
        assert str(output_path) in args
        assert "-vf" in args
        assert "scale=640:-1" in args


def test_extract_thumbnail_failure(tmp_path):
    """Test thumbnail extraction failure."""
    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "thumbnail.jpg"

    video_path.write_text("dummy")

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="error")

        result = extract_thumbnail(video_path, output_path)

        assert result is False


def test_extract_thumbnail_nonexistent_video(tmp_path):
    """Test thumbnail extraction with missing video."""
    video_path = tmp_path / "missing.mp4"
    output_path = tmp_path / "thumbnail.jpg"

    result = extract_thumbnail(video_path, output_path)

    assert result is False


def test_extract_thumbnail_custom_width(tmp_path):
    """Test thumbnail extraction with custom width."""
    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "thumbnail.jpg"

    video_path.write_text("dummy")

    with patch('subprocess.run') as mock_run:
        # Mock the output file creation
        def create_thumbnail(*args, **kwargs):
            output_path.write_text("thumbnail data")
            return Mock(returncode=0)

        mock_run.side_effect = create_thumbnail

        extract_thumbnail(video_path, output_path, width=1280)

        args = mock_run.call_args[0][0]
        assert "scale=1280:-1" in args
