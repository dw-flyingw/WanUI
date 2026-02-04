# TI2V Example Image Selector

**Date**: 2026-02-04
**Status**: Approved

## Overview

Add example image selection capability to the fast TI2V page (`ti2v_5b.py`) that matches the pattern used in `i2v_a14b.py`. The selector only appears when the user is in "Image + Text (I2V)" mode.

## Goals

- Provide users with quick access to example images for I2V generation
- Maintain UI consistency with the I2V-A14B page
- Support both uploaded images and example images seamlessly

## Design

### 1. Imports & Initialization

Add `ExampleLibrary` import and initialize at module level:

```python
from utils.examples import ExampleLibrary
import shutil

# Initialize example library
EXAMPLES_ROOT = Path(__file__).parent.parent / "assets" / "examples"
example_library = ExampleLibrary(EXAMPLES_ROOT)
```

### 2. Session State

Add three new session state variables to track example selection:

```python
if f"{TASK_KEY}_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_example_loaded"] = False
if f"{TASK_KEY}_loaded_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
if f"{TASK_KEY}_loaded_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_id"] = None
```

### 3. UI Flow (I2V Mode Only)

When `mode == "Image + Text (I2V)"`:

1. **If example is loaded**: Show the example image with "📝 Change image" button
2. **If no example loaded**: Show both:
   - File uploader for custom images
   - Example selector grid below (with "Load Selected Example" button)

This exactly mirrors the i2v_a14b.py pattern.

### 4. Generation Flow

Handle both image sources:

- **Example images**: Copy from `assets/examples/` to `project_dir/input/`
- **Uploaded images**: Save uploaded file to `project_dir/input/`

Both paths result in `image_path` being set for the generation call.

### 5. Metadata Tracking

Track the image source in metadata:

```python
extra_settings={
    "source_type": "example" | "upload" | "text_only",
    "example_id": "<example_id>" or None,
}
```

## Compatible Examples

From `assets/examples/metadata.json`, two examples are compatible with `ti2v-5B`:

- `i2v_landscape_01` - Landscape/nature image
- `test_portrait_01` - Portrait image

## Implementation Notes

- Pattern replication from `i2v_a14b.py` (lines 46-178, 259-306)
- Only active in I2V mode (no changes to T2V mode)
- Maintains existing file upload functionality
- Uses existing `ExampleLibrary` utility
