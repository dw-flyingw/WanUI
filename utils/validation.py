"""
Input validation utilities for uploaded media files.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    message: str
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def get_video_info(video_path: Path) -> Optional[dict]:
    """
    Get video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video info or None if failed
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return None

        import json
        data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            return None

        duration = float(data.get("format", {}).get("duration", 0))

        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": duration,
            "fps": eval(video_stream.get("r_frame_rate", "0/1")),
            "codec": video_stream.get("codec_name", "unknown"),
        }

    except Exception as e:
        return None


def get_audio_info(audio_path: Path) -> Optional[dict]:
    """
    Get audio information using ffprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary with audio info or None if failed
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return None

        import json
        data = json.loads(result.stdout)

        # Find audio stream
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        if not audio_stream:
            return None

        duration = float(data.get("format", {}).get("duration", 0))

        return {
            "duration": duration,
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
            "codec": audio_stream.get("codec_name", "unknown"),
        }

    except Exception as e:
        return None


def validate_image(image_path: Path, task: str) -> ValidationResult:
    """
    Validate an image for a specific task.

    Args:
        image_path: Path to image file
        task: Task name (e.g., "i2v-A14B")

    Returns:
        ValidationResult
    """
    warnings = []

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = width / height

        # Check resolution
        if width < 480 or height < 480:
            return ValidationResult(
                valid=False,
                message=f"Image resolution too low: {width}x{height}. Minimum is 480x480."
            )

        # Warn about non-standard aspect ratios
        standard_ratios = [16/9, 9/16, 4/3, 3/4, 1/1]
        if not any(abs(aspect_ratio - ratio) < 0.1 for ratio in standard_ratios):
            warnings.append(
                f"Unusual aspect ratio {aspect_ratio:.2f}. "
                "Standard ratios (16:9, 9:16, 4:3, etc.) work best."
            )

        # Task-specific checks
        if task == "s2v-14B":
            # S2V works best with portrait-oriented images
            if width > height:
                warnings.append(
                    "S2V (Speech to Video) works best with portrait images. "
                    "Consider using a portrait-oriented image."
                )

        if task == "animate-14B":
            # Animate requires clear subject
            warnings.append(
                "For best results, use images with a clear, centered subject "
                "against a simple background."
            )

        return ValidationResult(
            valid=True,
            message=f"Image valid: {width}x{height}",
            warnings=warnings
        )

    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f"Failed to validate image: {e}"
        )


def validate_video(video_path: Path, task: str) -> ValidationResult:
    """
    Validate a video for a specific task.

    Args:
        video_path: Path to video file
        task: Task name (e.g., "animate-14B")

    Returns:
        ValidationResult
    """
    warnings = []

    info = get_video_info(video_path)
    if not info:
        return ValidationResult(
            valid=False,
            message="Failed to read video information. Ensure the file is a valid video."
        )

    width = info["width"]
    height = info["height"]
    duration = info["duration"]
    fps = info["fps"]

    # Check resolution
    if width < 480 or height < 480:
        return ValidationResult(
            valid=False,
            message=f"Video resolution too low: {width}x{height}. Minimum is 480x480."
        )

    # Task-specific checks
    if task == "animate-14B":
        # Animate works best with 5-10 second clips
        if duration < 3:
            warnings.append(
                f"Video is very short ({duration:.1f}s). "
                "Consider using clips of at least 3-5 seconds."
            )
        elif duration > 15:
            warnings.append(
                f"Video is long ({duration:.1f}s). "
                "Processing may take significant time. Consider trimming to 5-10 seconds."
            )

        # Check FPS
        if fps < 24:
            warnings.append(
                f"Low FPS ({fps:.1f}). Videos with 24-30 FPS produce better results."
            )

    return ValidationResult(
        valid=True,
        message=f"Video valid: {width}x{height}, {duration:.1f}s @ {fps:.1f} FPS",
        warnings=warnings
    )


def validate_audio(audio_path: Path, task: str) -> ValidationResult:
    """
    Validate an audio file for a specific task.

    Args:
        audio_path: Path to audio file
        task: Task name (e.g., "s2v-14B")

    Returns:
        ValidationResult
    """
    warnings = []

    info = get_audio_info(audio_path)
    if not info:
        return ValidationResult(
            valid=False,
            message="Failed to read audio information. Ensure the file is a valid audio file."
        )

    duration = info["duration"]
    sample_rate = info["sample_rate"]

    # Check duration
    if duration < 1:
        return ValidationResult(
            valid=False,
            message=f"Audio too short: {duration:.1f}s. Minimum is 1 second."
        )

    if duration > 60:
        warnings.append(
            f"Audio is long ({duration:.1f}s). "
            "Generation may take significant time."
        )

    # Check sample rate
    if sample_rate < 16000:
        warnings.append(
            f"Low sample rate ({sample_rate} Hz). "
            "For best quality, use audio with 16kHz or higher sample rate."
        )

    return ValidationResult(
        valid=True,
        message=f"Audio valid: {duration:.1f}s @ {sample_rate} Hz",
        warnings=warnings
    )
