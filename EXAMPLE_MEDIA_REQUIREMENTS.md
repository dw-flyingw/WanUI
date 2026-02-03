# Example Media Library Requirements

This document describes the requirements and structure for the example media library used in WanUI Studio.

## Overview

The example media library provides pre-loaded media files (images, videos, audio) that users can browse and use directly with the various models without needing to upload their own content. This is useful for:

- Quick testing and experimentation
- Demonstrations and tutorials
- Understanding model capabilities
- Comparing different models with the same input

## Directory Structure

```
assets/examples/
├── metadata.json              # Index of all examples with metadata
├── images/
│   ├── portraits/            # Portrait photos (for S2V, Animate)
│   ├── landscapes/           # Landscape scenes (for T2V, I2V, TI2V)
│   ├── objects/              # Objects and products (for I2V, TI2V)
│   └── characters/           # Character art (for Animate)
├── videos/
│   ├── short_clips/          # 5-10 second clips (for Animate source)
│   ├── motion_references/    # Motion/pose references
│   └── test_videos/          # Various test videos
├── audio/
│   ├── speech_samples/       # Clean speech samples (for S2V)
│   └── music/                # Background music (optional)
└── thumbnails/
    ├── images/               # 320x180 image thumbnails
    ├── videos/               # 320x180 video frame thumbnails
    └── audio/                # 320x180 audio waveform images
```

## Media Requirements by Model

### Images

**For I2V-A14B (Image to Video) and TI2V-5B:**
- **Resolution:** 1280x720 or compatible aspect ratios (16:9, 9:16, 4:3)
- **Minimum:** 480x480 pixels
- **Formats:** JPG, PNG, WebP
- **Categories:**
  - Landscapes: Scenic views, nature, cityscapes
  - Objects: Products, items, abstract compositions
- **Recommendations:**
  - Clear, well-lit images work best
  - Images with depth produce better parallax effects
  - Avoid heavily compressed or noisy images

**For S2V-14B (Speech to Video):**
- **Resolution:** 1024x704 or similar portrait orientations
- **Minimum:** 480x480 pixels
- **Formats:** JPG, PNG, WebP
- **Categories:**
  - Portraits: Front-facing person photos
- **Recommendations:**
  - Portrait orientation preferred
  - Clear face visibility
  - Neutral or simple backgrounds
  - Subject centered in frame

**For Animate-14B:**
- **Resolution:** 1280x720 recommended
- **Minimum:** 720x720 pixels
- **Formats:** JPG, PNG
- **Categories:**
  - Characters: Character art, portraits, full-body images
  - Portraits: Person photos with clear features
- **Recommendations:**
  - Clear, centered subject
  - Simple backgrounds preferred
  - Good contrast between subject and background
  - Full-body or upper-body shots work well

### Videos

**For Animate-14B (source videos):**
- **Duration:** 5-10 seconds (optimal), 3-15 seconds (acceptable)
- **Resolution:** 720P or higher (1280x720+)
- **FPS:** 24-30 fps recommended
- **Formats:** MP4, AVI, MOV
- **Categories:**
  - Short clips: 5-10 second clips with clear motion
  - Motion references: Videos with specific movements or actions
- **Recommendations:**
  - Clear, visible motion
  - Good lighting and stable footage
  - Avoid excessive motion blur
  - Single subject in frame works best
  - Avoid rapid cuts or scene changes

### Audio

**For S2V-14B:**
- **Duration:** 5-15 seconds (for TTS voice cloning references), up to 60 seconds (for direct audio input)
- **Sample Rate:** 16kHz or higher
- **Formats:** MP3, WAV, M4A, AAC
- **Categories:**
  - Speech samples: Clean speech recordings
- **Recommendations:**
  - Clean audio with minimal background noise
  - Clear speech with good articulation
  - For voice cloning: 5-15 seconds is optimal
  - Avoid music or sound effects overlay
  - Mono or stereo both acceptable

## Metadata Schema

Each example must be registered in `assets/examples/metadata.json` with the following structure:

```json
{
  "id": "unique_identifier",
  "path": "relative/path/from/assets/examples/dir",
  "thumbnail": "thumbnails/category/filename.jpg",
  "category": "category_name",
  "tags": ["tag1", "tag2", "tag3"],
  "description": "Human-readable description",
  "compatible_tasks": ["t2v-A14B", "i2v-A14B"],
  "media_type": "image|video|audio",
  "metadata": {
    "resolution": "1280x720",
    "duration": "5.0s",
    "additional_info": "..."
  }
}
```

### Field Descriptions

- **id:** Unique identifier (string), use descriptive names like `landscape_mountain_sunset_01`
- **path:** Relative path from `assets/examples/` directory to the actual media file
- **thumbnail:** Relative path from `assets/examples/` directory to the thumbnail image (320x180)
- **category:** Category name (must match directory structure)
- **tags:** Array of searchable tags for filtering
- **description:** Brief description shown in the UI
- **compatible_tasks:** Array of model task IDs that can use this media:
  - `t2v-A14B`: Text to Video
  - `i2v-A14B`: Image to Video
  - `ti2v-5B`: Fast Text/Image to Video
  - `s2v-14B`: Speech to Video
  - `animate-14B`: Character Animation
- **media_type:** One of: `image`, `video`, `audio`
- **metadata:** (Optional) Additional metadata object with format-specific info

## Adding New Examples

Follow these steps to add a new example to the library:

### 1. Prepare the Media File

Ensure your media meets the requirements for the target model(s).

### 2. Place in Appropriate Directory

```bash
# Example: Adding a portrait image
cp my_portrait.jpg assets/examples/images/portraits/

# Example: Adding a short video clip
cp my_clip.mp4 assets/examples/videos/short_clips/
```

### 3. Generate Thumbnail

Generate a 320x180 thumbnail:

**For Images:**
```bash
convert assets/examples/images/portraits/my_portrait.jpg \
  -resize 320x180^ \
  -gravity center \
  -extent 320x180 \
  assets/examples/thumbnails/images/my_portrait_thumb.jpg
```

Or use ffmpeg:
```bash
ffmpeg -i assets/examples/images/portraits/my_portrait.jpg \
  -vf "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2" \
  assets/examples/thumbnails/images/my_portrait_thumb.jpg
```

**For Videos:**
```bash
# Extract first frame at 320x180
ffmpeg -i assets/examples/videos/short_clips/my_clip.mp4 \
  -vf "select=eq(n\,0),scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2" \
  -frames:v 1 \
  assets/examples/thumbnails/videos/my_clip_thumb.jpg
```

**For Audio:**
```bash
# Generate waveform visualization
ffmpeg -i assets/examples/audio/speech_samples/my_audio.mp3 \
  -filter_complex "showwavespic=s=320x180:colors=4CAF50" \
  -frames:v 1 \
  assets/examples/thumbnails/audio/my_audio_thumb.png
```

### 4. Add Metadata Entry

Edit `assets/examples/metadata.json` and add a new entry to the `examples` array:

```json
{
  "id": "portrait_woman_neutral_01",
  "path": "images/portraits/my_portrait.jpg",
  "thumbnail": "thumbnails/images/my_portrait_thumb.jpg",
  "category": "portraits",
  "tags": ["woman", "neutral-expression", "front-facing", "studio-lighting"],
  "description": "Studio portrait of a woman with neutral expression, ideal for S2V talking head generation",
  "compatible_tasks": ["i2v-A14B", "ti2v-5B", "s2v-14B", "animate-14B"],
  "media_type": "image",
  "metadata": {
    "resolution": "1280x720",
    "aspect_ratio": "16:9",
    "lighting": "studio",
    "background": "neutral"
  }
}
```

### 5. Test

1. Restart the WanUI application
2. Navigate to the **Examples** page
3. Verify your example appears with correct thumbnail and metadata
4. Navigate to a compatible model page
5. Test using the example in generation

## Best Practices

### Organizing Content

- Use descriptive, consistent naming conventions
- Group similar content in appropriate categories
- Add comprehensive tags for searchability
- Write clear, informative descriptions

### Quality Guidelines

- Use high-quality source media
- Ensure proper licensing (CC0, public domain, or your own content)
- Test examples with target models before adding
- Include diverse content (different subjects, styles, scenarios)

### Thumbnail Guidelines

- Always 320x180 resolution for consistency
- Maintain aspect ratio with padding if needed
- Use representative frames for videos
- Generate clear waveforms for audio

### Metadata Guidelines

- Use clear, specific tags
- List all compatible tasks accurately
- Include relevant technical metadata (resolution, duration, etc.)
- Write descriptions that explain what makes the example useful

## Recommended Initial Content

To populate a useful example library, aim for:

### Images
- **Portraits (S2V):** 5-10 diverse portraits (different ages, genders, ethnicities, expressions)
- **Landscapes (I2V/TI2V):** 5-10 scenic images (mountains, cities, nature, architecture)
- **Characters (Animate):** 5-10 character images (art styles, portraits, full-body)
- **Objects (I2V/TI2V):** 3-5 product or object images

### Videos
- **Short Clips (Animate):** 5-10 clips with clear motion (dancing, talking, gesturing, walking)
- **Motion References:** 3-5 specific movement types (head turns, hand gestures, body movements)

### Audio
- **Speech Samples (S2V):** 5-10 clean speech samples (various voices, languages if applicable)

## Sourcing Example Content

### Free Stock Resources (CC0 License)

**Images:**
- Pexels (https://www.pexels.com/)
- Pixabay (https://pixabay.com/)
- Unsplash (https://unsplash.com/)

**Videos:**
- Pexels Videos (https://www.pexels.com/videos/)
- Pixabay Videos (https://pixabay.com/videos/)
- Coverr (https://coverr.co/)

**Audio:**
- Freesound (https://freesound.org/) - CC0 and CC-BY
- BBC Sound Effects (https://sound-effects.bbcrewind.co.uk/) - Personal/educational use

### Using Your Own Generations

Your own WanUI outputs can make excellent examples! Simply:
1. Copy successful outputs from `output/` directory
2. Generate thumbnails
3. Add metadata entries

### Creating Test Content

For technical testing, you can generate simple test content:

```bash
# Generate solid color test image
ffmpeg -f lavfi -i color=c=blue:s=1280x720:d=1 -frames:v 1 test_image.jpg

# Generate test video with moving text
ffmpeg -f lavfi -i color=c=black:s=1280x720:d=5 \
  -vf "drawtext=text='Test':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  test_video.mp4

# Generate test audio tone
ffmpeg -f lavfi -i "sine=frequency=440:duration=5" test_audio.mp3
```

## Troubleshooting

### Example not appearing in UI

- Check `metadata.json` syntax is valid JSON
- Verify file paths are correct and relative to `assets/examples/` directory
- Ensure thumbnail file exists
- Check file permissions

### Thumbnail not displaying

- Verify thumbnail path in metadata
- Check thumbnail file format (JPG or PNG)
- Ensure 320x180 resolution
- Regenerate thumbnail if corrupted

### Example fails when used in model

- Verify media meets model requirements (resolution, duration, format)
- Check compatible_tasks array includes the correct model
- Test file can be opened with standard tools (ffmpeg, image viewers)
- Check for file corruption

## Maintenance

- Periodically review and update examples
- Remove outdated or poor-quality examples
- Add new examples as models improve
- Keep metadata.json organized and documented
- Monitor file sizes to avoid repository bloat

## Current Library Status

Check the Examples page in WanUI Studio to see:
- Total number of examples
- Distribution by category
- Distribution by media type
- Coverage of each model

Start with a small, high-quality collection and expand based on user needs and model capabilities.
