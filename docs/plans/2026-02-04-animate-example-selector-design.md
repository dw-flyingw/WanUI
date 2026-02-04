# Animate Page Example Selector Design

**Date:** 2026-02-04
**Status:** Approved
**Author:** Claude Code

## Overview

Add example selector UI to the animate page, allowing users to browse and select pre-configured example videos and images instead of uploading their own. Follows the same pattern implemented on the I2V page.

## Motivation

The animate page requires two media inputs (source video + reference image), making it more complex than other pages. Example selectors reduce friction by:
- Providing working examples for new users
- Enabling quick testing of both animation and replacement modes
- Showcasing paired examples (matching video + image combinations)

## Design

### Dual Example Selectors

Unlike I2V (one image input), animate needs two independent selectors:
1. **Source Video Selector** - driving/motion video
2. **Reference Image Selector** - character to animate

Each selector has independent session state and operates separately.

### UI Flow per Input

**When no example loaded:**
1. Show file uploader
2. Show divider + "OR select an example"
3. Display radio grid of examples (2 columns)
4. Show "Load Selected Example" button

**When example loaded:**
1. Show success message with example ID
2. Display the loaded media (video/image)
3. Show "Clear Example (Upload My Own)" button

### Session State

Per input type (video/image):
- `{TASK_KEY}_video_example_loaded` - boolean flag
- `{TASK_KEY}_loaded_video_example_path` - Path to example file
- `{TASK_KEY}_loaded_video_example_id` - Example ID string
- `{TASK_KEY}_image_example_loaded` - boolean flag
- `{TASK_KEY}_loaded_image_example_path` - Path to example file
- `{TASK_KEY}_loaded_image_example_id` - Example ID string

### Generation Logic

Update validation to check for either uploaded files OR loaded examples:
```python
if not uploaded_video and not video_example_loaded:
    st.error("Please upload a source video or select an example")
elif not uploaded_image and not image_example_loaded:
    st.error("Please upload a reference image or select an example")
```

Copy example files to project input directory using `shutil.copy()` when examples are used.

### Existing Examples

Already configured in `metadata.json`:
- `animate_source_video` + `animate_reference_image` (animation mode pair)
- `replace_source_video` + `replace_reference_image` (replacement mode pair)

## Implementation Notes

- Import `ExampleLibrary` from `utils.examples`
- Import `shutil` for copying example files
- Initialize `EXAMPLES_ROOT` after TASK_KEY setup
- Use 2 columns for example grids (narrower than I2V's 3)
- Unique `key_suffix` for each selector: "animate_video" and "animate_image"

## Testing

1. Load video example only → should require image
2. Load image example only → should require video
3. Load both examples → should generate successfully
4. Load example, then clear and upload → should use uploaded file
5. Try both animation and replacement mode pairs
