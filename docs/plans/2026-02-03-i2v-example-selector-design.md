# I2V Example Image Selector Design

**Date**: 2026-02-03
**Status**: Approved
**Target**: Image-to-Video (I2V) page

## Overview

Add example image selection functionality to the I2V page, allowing users to quickly try the model with pre-configured example images instead of uploading their own. Examples are loaded from `assets/examples/` with thumbnails displayed in a radio button grid.

## Design Decisions

### 1. Placement
- Example selector appears **below the file uploader**
- File uploader remains the primary input method
- Examples serve as a convenient secondary option

### 2. Selection Behavior
- **Auto-populate with lock**: When an example is loaded, both the file uploader and example selector are disabled/hidden
- User must explicitly "change" to switch back to upload mode or select a different example
- Prevents confusion about which image source is active

### 3. UI Layout
- **Radio button grid** with clickable thumbnail cards
- 3 columns for desktop viewing
- Single "Load Selected Example" button at bottom
- Each card shows: thumbnail image + category badge (minimal text)
- Clear visual feedback for selected state

### 4. Reset Functionality
- "Change image" button appears when example is loaded
- Re-expands example selector with "None (Upload My Own)" option as first choice
- Allows switching between examples or returning to manual upload

### 5. Display
- Loaded example appears identical to uploaded file
- No special badges or indicators (keeps UI clean)
- Same image preview component used for both sources

## Component Architecture

### State Management

Session state variables (scoped to `{TASK_KEY}`):
- `{TASK_KEY}_selected_example_id`: ID of selected example (None = no selection)
- `{TASK_KEY}_example_loaded`: Boolean indicating if example is active
- `{TASK_KEY}_loaded_example_path`: Path to loaded example file

### Component Flow

```
┌─────────────────────────────────────────────────┐
│ Initial State                                   │
│ ┌─────────────────────────────────────────┐    │
│ │ File Uploader (visible)                  │    │
│ └─────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────┐    │
│ │ Example Selector (visible)               │    │
│ │ - Radio grid with thumbnails             │    │
│ │ - Load Selected button                   │    │
│ └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                    ↓ User loads example
┌─────────────────────────────────────────────────┐
│ Example Loaded State                            │
│ ┌─────────────────────────────────────────┐    │
│ │ Image Preview (visible)                  │    │
│ │ [📝 Change image]                        │    │
│ └─────────────────────────────────────────┘    │
│                                                  │
│ File Uploader (hidden)                          │
│ Example Selector (hidden)                       │
└─────────────────────────────────────────────────┘
                    ↓ User clicks "Change image"
┌─────────────────────────────────────────────────┐
│ Selection State                                 │
│ ┌─────────────────────────────────────────┐    │
│ │ File Uploader (visible)                  │    │
│ └─────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────┐    │
│ │ Example Selector (visible)               │    │
│ │ ○ None (Upload My Own)                   │    │
│ │ ○ Example 1                              │    │
│ │ ○ Example 2                              │    │
│ │ [Load Selected]                          │    │
│ └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Integration Points

1. **Existing code (lines 105-112)**: Wrap file uploader in conditional logic
2. **Generation logic (lines 182, 199-214)**: Check which source is active
3. **ExampleLibrary**: Use existing `utils/examples.py` infrastructure

## Implementation Details

### Files to Modify

#### 1. `pages/i2v_a14b.py`
- Import `ExampleLibrary` from `utils.examples`
- Initialize library pointing to `assets/examples/`
- Add session state initialization for example tracking
- Add `render_example_selector()` helper function
- Update image input section with conditional display logic
- Update generation logic to handle both upload and example sources

#### 2. `utils/examples.py`
- Add new method: `display_radio_grid(task, columns=3, show_none_option=False)`
- Returns selected example ID (deferred loading pattern)
- Renders thumbnail grid using Streamlit columns
- Uses native `st.radio()` for selection state

### Helper Function Structure

```python
def render_example_selector(library, task_key):
    """
    Render radio grid selector for example images.

    Returns:
        selected_example_id (str or None): ID of selected example
    """
    # Get examples filtered for i2v-A14B + media_type=image
    examples = library.get_examples(task="i2v-A14B", media_type="image")

    if not examples:
        st.info("No example images available")
        return None

    # Display radio grid in columns
    # Return selected ID (not auto-loaded)
```

### Generation Logic Updates

```python
# Determine image source
if st.session_state.get(f"{TASK_KEY}_example_loaded"):
    # Use example path
    image_path = st.session_state[f"{TASK_KEY}_loaded_example_path"]
else:
    # Use uploaded file (existing logic)
    image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")
```

## Radio Grid UI Layout

Visual structure:
```
┌─────────────────────────────────────────────┐
│ OR select an example image:                 │
│                                             │
│ ┌───────┐  ┌───────┐  ┌───────┐           │
│ │ ○     │  │ ○     │  │ ○     │           │
│ │[thumb]│  │[thumb]│  │[thumb]│           │
│ │ Label │  │ Label │  │ Label │           │
│ └───────┘  └───────┘  └───────┘           │
│                                             │
│         [Load Selected Example]             │
└─────────────────────────────────────────────┘
```

Implementation:
- 3 columns using `st.columns(3)`
- Each column: thumbnail + category badge
- Selection tracked with `st.radio()` or session state
- Single primary button for loading

## Edge Cases

1. **Example file missing**: Check `example.path.exists()` before loading, show error
2. **No examples available**: Show helpful message directing to add examples
3. **Both uploaded and example selected**: Most recent action takes precedence
4. **Example selector empty state**: Graceful degradation with informative message

## Testing Checklist

- [ ] Initial load: Both uploader and selector visible
- [ ] Upload file: Works normally, selector still visible
- [ ] Select example: Radio selection highlights correctly
- [ ] Load example: Image displays, uploader/selector hidden
- [ ] Change image: Button re-shows selectors with "None" option
- [ ] Select "None": Returns to upload mode
- [ ] Generate with example: Video generates using example image
- [ ] Generate with upload: Works as before
- [ ] No examples scenario: Graceful message displayed
- [ ] Multiple examples: Grid displays correctly with 3 columns

## Extensibility

This pattern can be reused for other pages:
- **S2V page**: Audio example selector
- **Animate page**: Image + video example selectors
- **T2V page**: Optional video reference examples

The `display_radio_grid()` method will be generic enough to work with any media type. Each page needs to:
1. Initialize `ExampleLibrary`
2. Call selector with appropriate task ID and media type filter
3. Handle loaded state with same pattern

## Future Enhancements

Not included in this implementation:
- Search/filter examples by tags
- Preview example output videos
- User-submitted examples
- Drag-to-reorder example priority
- Category-based tabs instead of single filter

## Accessibility

- Radio buttons provide keyboard navigation
- Alt text for thumbnail images
- Clear visual focus indicators
- Screen reader friendly labels
- Color contrast meets WCAG guidelines

## Example Assets Structure

Current structure (already exists):
```
assets/examples/
├── metadata.json              # Example definitions
├── images/
│   ├── landscapes/
│   │   └── i2v_landscape_01.jpg
│   └── portraits/
│       └── test_portrait_01.jpg
└── thumbnails/
    └── images/
        ├── landscapes/
        │   └── i2v_landscape_01_thumb.jpg
        └── portraits/
            └── test_portrait_01_thumb.jpg
```

Adding new examples:
1. Add full-size image to `images/<category>/`
2. Add thumbnail to `thumbnails/images/<category>/`
3. Add metadata entry to `metadata.json` with:
   - Unique ID
   - Paths (relative to `examples/`)
   - Category, tags, description
   - `compatible_tasks: ["i2v-A14B"]`
   - `media_type: "image"`

## Success Criteria

- Users can select and load example images with 2 clicks
- UI remains clean and uncluttered
- No confusion about which image source is active
- Easy to switch between examples and manual upload
- Example system is extensible to other pages
- Performance: Grid loads quickly even with many examples
