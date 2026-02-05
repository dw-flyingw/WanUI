# Gallery Thumbnail Optimization Design

**Date:** 2026-02-04
**Status:** Approved

## Problem

The gallery currently loads full video files for every project card, causing:
- High bandwidth usage (10-100MB per video)
- Slow page load times
- Poor user experience with many videos
- Unnecessary loading of videos the user may not want to watch

## Solution

Implement thumbnail-based gallery with on-demand video loading:
- Extract first frame as static thumbnail image
- Display thumbnails in gallery grid
- Load full video only when user clicks "Play Video"

## Architecture

### Thumbnail Generation

**Implementation Location:** `utils/common.py`

Add new function:
```python
def extract_thumbnail(video_path: Path, output_path: Path, width: int = 640) -> bool:
    """Extract first frame from video as thumbnail using ffmpeg"""
```

**Specifications:**
- Extract frame at 0.1s (avoids black frames at 0s)
- Save as `thumbnail.jpg` in project directory
- Target width: 640px (maintains aspect ratio)
- Quality: 85% JPEG
- Returns True on success, False on failure

**Caching Strategy:**
- Check for existing `thumbnail.jpg` in project directory
- Generate on-demand if missing (~0.5s one-time cost)
- No expiration - persists until manually deleted
- Subsequent loads are instant

### Gallery Display

**Implementation Location:** `utils/history.py` - `_render_project_card()` method

**Modified Card Layout:**
```
[Thumbnail Image]
[▶ Play Video] button
[Model, Project, Duration info]
[View Details] expander (existing)
```

**Rendering Flow:**
1. Calculate thumbnail path: `project_dir / "thumbnail.jpg"`
2. Check if thumbnail exists
3. Generate if missing using `extract_thumbnail()`
4. Display thumbnail with `st.image()`
5. Add "▶ Play Video" button
6. When clicked, expand section with `st.video()`

**Click Behavior:**
- Use Streamlit button to trigger video expansion
- Video player appears between button and metadata
- Session state tracks expanded videos: `f"video_expanded_{project_dir.name}"`
- Each card manages state independently

### Error Handling

**Graceful Degradation:**
- Thumbnail generation fails → fallback to video or placeholder
- Video file missing → show "video not found" message
- Silent failures with user-friendly messages

## Performance Impact

**First Gallery Load (per video):**
- +0.5s thumbnail generation (one-time cost)
- Only affects videos without cached thumbnails

**Subsequent Loads:**
- Instant (uses cached thumbnails)
- ~99% bandwidth reduction (100KB vs 10-100MB)
- 10-50x faster page load time

**Storage:**
- ~100KB per thumbnail
- Stored in project directory alongside video
- Minimal overhead for significant performance gain

## File Changes

### New Code
- `utils/common.py`: Add `extract_thumbnail()` function

### Modified Code
- `utils/history.py`: Update `_render_project_card()` method
  - Add thumbnail path calculation
  - Add thumbnail generation check
  - Replace `st.video()` with `st.image()` + expandable player
  - Add session state management

## Future Enhancements

Potential future improvements (out of scope for this design):
- Background batch thumbnail generation
- Thumbnail regeneration on video change
- Custom thumbnail selection
- Animated GIF previews
- Thumbnail size configuration

## Implementation Notes

- Uses existing ffmpeg utilities pattern from `utils/common.py`
- Maintains backward compatibility (generates thumbnails for existing videos)
- No changes to metadata structure
- No changes to video generation pipeline
