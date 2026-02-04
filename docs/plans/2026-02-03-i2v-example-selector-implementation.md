# I2V Example Image Selector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add example image selection with thumbnail grid to I2V page, allowing users to quickly try the model with pre-configured examples.

**Architecture:** Radio button grid UI displaying example thumbnails from `assets/examples/`. Session state tracks loaded example vs uploaded file. When example is loaded, uploader/selector hide; user clicks "Change image" to re-show selectors.

**Tech Stack:** Streamlit, existing ExampleLibrary infrastructure, Python 3.11

---

## Task 1: Add display_radio_grid method to ExampleLibrary

**Files:**
- Modify: `utils/examples.py:201` (append after existing methods)

**Step 1: Write the implementation**

Add this method to the `ExampleLibrary` class:

```python
def display_radio_grid(
    self,
    task: str,
    media_type: Optional[str] = None,
    columns: int = 3,
    show_none_option: bool = False,
    key_suffix: str = ""
) -> Optional[str]:
    """
    Display a radio button grid for selecting examples.

    Args:
        task: Task to filter examples for (e.g., "i2v-A14B")
        media_type: Media type to filter by ('image', 'video', 'audio')
        columns: Number of columns in the grid
        show_none_option: If True, adds "None (Upload My Own)" as first option
        key_suffix: Suffix for widget keys to avoid conflicts

    Returns:
        Selected example ID (str) or None
    """
    # Get filtered examples
    examples = self.get_examples(task=task, media_type=media_type)

    if not examples and not show_none_option:
        st.info("No example images available")
        return None

    # Build options for radio selection
    options = []
    option_ids = []

    if show_none_option:
        options.append("None (Upload My Own)")
        option_ids.append(None)

    for example in examples:
        options.append(example.id)
        option_ids.append(example.id)

    if not options:
        return None

    # Use radio for selection (hidden labels, we'll show visual grid)
    st.write("**Select an example:**")

    # Create visual grid
    cols = st.columns(columns)

    # Initialize selection in session state if not exists
    selection_key = f"example_selection_{task}_{key_suffix}"
    if selection_key not in st.session_state:
        st.session_state[selection_key] = option_ids[0]

    # Render grid
    for idx, example in enumerate(examples):
        col = cols[idx % columns]

        with col:
            # Show thumbnail
            if example.thumbnail.exists():
                st.image(str(example.thumbnail), use_container_width=True)
            else:
                st.warning("No thumbnail")

            # Category badge
            st.caption(f"**{example.category}**")

            # Radio button for this example
            is_selected = st.session_state[selection_key] == example.id
            if st.button(
                "Select" if not is_selected else "✓ Selected",
                key=f"select_{example.id}_{key_suffix}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state[selection_key] = example.id
                st.rerun()

    # If show_none_option, add it as a button below the grid
    if show_none_option:
        st.divider()
        is_none_selected = st.session_state[selection_key] is None
        if st.button(
            "None (Upload My Own)" if not is_none_selected else "✓ None (Upload My Own)",
            key=f"select_none_{key_suffix}",
            use_container_width=True,
            type="primary" if is_none_selected else "secondary"
        ):
            st.session_state[selection_key] = None
            st.rerun()

    return st.session_state[selection_key]
```

**Step 2: Test the method manually**

We'll test this interactively in Task 3 when integrated with I2V page.

**Step 3: Commit**

```bash
git add utils/examples.py
git commit -m "feat: add display_radio_grid method to ExampleLibrary

Adds radio button grid display for example selection with:
- Thumbnail grid layout
- Button-based selection with visual feedback
- Optional 'None' option for returning to upload
- Session state tracking for selection

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Initialize session state for I2V example tracking

**Files:**
- Modify: `pages/i2v_a14b.py:48-49` (add after existing session state init)

**Step 1: Add session state initialization**

After line 49 (`st.session_state[f"{TASK_KEY}_extended_prompt"] = None`), add:

```python
# Initialize example selector session state
if f"{TASK_KEY}_example_loaded" not in st.session_state:
    st.session_state[f"{TASK_KEY}_example_loaded"] = False
if f"{TASK_KEY}_loaded_example_path" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
if f"{TASK_KEY}_loaded_example_id" not in st.session_state:
    st.session_state[f"{TASK_KEY}_loaded_example_id"] = None
```

**Step 2: Test session state initialization**

Run the I2V page and verify no errors:

```bash
streamlit run app.py
# Navigate to I2V page, confirm it loads without errors
```

Expected: Page loads normally, no new UI changes yet.

**Step 3: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: initialize example selector session state for I2V

Adds session state tracking for:
- example_loaded: boolean flag
- loaded_example_path: Path to loaded example
- loaded_example_id: ID of loaded example

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Add example selector UI to I2V page

**Files:**
- Modify: `pages/i2v_a14b.py:100-108` (replace Input Image section)
- Modify: `pages/i2v_a14b.py:13` (add import)

**Step 1: Add import**

At line 13, after existing imports from `utils.common`, add:

```python
from utils.examples import ExampleLibrary
```

**Step 2: Initialize ExampleLibrary**

After line 41 (`load_custom_theme()`), add:

```python
# Initialize example library
EXAMPLES_ROOT = Path(__file__).parent.parent / "assets" / "examples"
example_library = ExampleLibrary(EXAMPLES_ROOT)
```

**Step 3: Replace Input Image section**

Replace lines 100-108 with:

```python
# Input image
st.subheader("Input Image")

# Check if example is loaded
example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")
loaded_example_id = st.session_state.get(f"{TASK_KEY}_loaded_example_id")

if example_loaded and loaded_example_path:
    # Show loaded example with change button
    st.image(str(loaded_example_path), use_container_width=True)
    st.caption(f"Using example: **{loaded_example_id}**")

    if st.button("📝 Change image", key="change_image_btn"):
        # Clear example state to re-show selectors
        st.session_state[f"{TASK_KEY}_example_loaded"] = False
        st.session_state[f"{TASK_KEY}_loaded_example_path"] = None
        st.session_state[f"{TASK_KEY}_loaded_example_id"] = None
        st.rerun()
else:
    # Show file uploader
    uploaded_image = st.file_uploader(
        "Upload source image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Image to animate. Output aspect ratio will match this image.",
    )
    if uploaded_image:
        st.image(uploaded_image, use_container_width=True)

    # Show example selector
    st.divider()
    st.write("**OR select an example image:**")

    # Display radio grid
    selected_id = example_library.display_radio_grid(
        task=TASK,
        media_type="image",
        columns=3,
        show_none_option=example_loaded,  # Show "None" option if coming from loaded state
        key_suffix="i2v"
    )

    # Load button
    if selected_id is not None:
        if st.button("Load Selected Example", type="primary", use_container_width=True):
            # Get example details
            example = example_library.get_example_by_id(selected_id)
            if example and example.path.exists():
                # Set session state
                st.session_state[f"{TASK_KEY}_example_loaded"] = True
                st.session_state[f"{TASK_KEY}_loaded_example_path"] = example.path
                st.session_state[f"{TASK_KEY}_loaded_example_id"] = example.id
                st.rerun()
            else:
                st.error(f"Example file not found: {selected_id}")
```

**Step 4: Test the UI**

```bash
streamlit run app.py
# Navigate to I2V page
# Test:
# 1. Example selector appears below uploader
# 2. Click example thumbnail -> "Select" button highlights
# 3. Click "Load Selected Example" -> image displays, uploader/selector hide
# 4. Click "Change image" -> selectors re-appear
```

Expected: Full example selection workflow works.

**Step 5: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: add example selector UI to I2V page

Adds radio button grid example selector:
- Shows below file uploader
- Displays example thumbnails in 3-column grid
- Load button loads selected example
- Change button re-shows selectors
- Hides uploader/selector when example loaded

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Update generation logic to handle example source

**Files:**
- Modify: `pages/i2v_a14b.py:170-182` (generation button logic)

**Step 1: Update validation and image source logic**

Replace lines 170-182 (from `if st.button("Generate Video"` through `input_dir.mkdir`):

```python
if st.button("Generate Video", type="primary", use_container_width=True):
    # Determine image source
    example_loaded = st.session_state.get(f"{TASK_KEY}_example_loaded", False)
    loaded_example_path = st.session_state.get(f"{TASK_KEY}_loaded_example_path")

    # Validate input
    if not example_loaded and not uploaded_image:
        st.error("Please upload a source image or select an example")
    elif example_loaded and not loaded_example_path:
        st.error("Example path not found. Please select an example again.")
    else:
        generation_start = datetime.now()

        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        input_dir = project_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
```

**Step 2: Update image save logic**

Find the line `image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")` (around line 182) and replace with:

```python
        # Determine and save image source
        if example_loaded:
            # Copy example to input directory
            import shutil
            image_path = input_dir / "image.jpg"
            shutil.copy2(loaded_example_path, image_path)
        else:
            # Save uploaded image
            image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")
```

**Step 3: Test generation with example**

```bash
streamlit run app.py
# Navigate to I2V page
# Test:
# 1. Load example, click "Generate Video"
# 2. Verify generation starts
# 3. Check output/<project>/input/image.jpg is the example
# 4. Verify generation completes successfully
```

Expected: Generation works with example images.

**Step 4: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: support example images in I2V generation

Updates generation logic to:
- Validate either uploaded or example image
- Copy example to input directory for generation
- Handle both upload and example sources

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Update metadata to track example source

**Files:**
- Modify: `pages/i2v_a14b.py:229-251` (metadata creation)

**Step 1: Add example tracking to metadata**

In the `create_metadata()` call (around line 229), add to the `extra_settings` dict:

Before:
```python
        extra_settings={
            "frame_num": frame_num,
        },
```

After:
```python
        extra_settings={
            "frame_num": frame_num,
            "source_type": "example" if example_loaded else "upload",
            "example_id": st.session_state.get(f"{TASK_KEY}_loaded_example_id") if example_loaded else None,
        },
```

**Step 2: Test metadata**

```bash
streamlit run app.py
# Generate with example
# Check output/<project>/metadata.json
# Verify extra_settings contains source_type and example_id
```

Expected: metadata.json includes example tracking.

**Step 3: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "feat: track example source in generation metadata

Adds to metadata.json:
- source_type: 'example' or 'upload'
- example_id: ID of example if used

Enables tracking which examples were used for generation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Handle edge cases and improve UX

**Files:**
- Modify: `pages/i2v_a14b.py:100-150` (example selector section)

**Step 1: Add no-examples handling**

In the example selector section (after line showing divider and "OR select"), add check:

```python
    # Show example selector
    st.divider()

    # Check if examples exist
    available_examples = example_library.get_examples(task=TASK, media_type="image")
    if not available_examples:
        st.info("No example images available for I2V. You can add examples to `assets/examples/`.")
    else:
        st.write("**OR select an example image:**")

        # Display radio grid
        selected_id = example_library.display_radio_grid(
            task=TASK,
            media_type="image",
            columns=3,
            show_none_option=example_loaded,
            key_suffix="i2v"
        )

        # Load button
        if selected_id is not None:
            if st.button("Load Selected Example", type="primary", use_container_width=True):
                # Get example details
                example = example_library.get_example_by_id(selected_id)
                if example and example.path.exists():
                    # Set session state
                    st.session_state[f"{TASK_KEY}_example_loaded"] = True
                    st.session_state[f"{TASK_KEY}_loaded_example_path"] = example.path
                    st.session_state[f"{TASK_KEY}_loaded_example_id"] = example.id
                    st.rerun()
                else:
                    st.error(f"Example file not found: {selected_id}")
```

**Step 2: Add uploaded_image variable initialization**

At the start of the else block (line ~120), ensure `uploaded_image` is accessible:

Add before the file uploader:
```python
    # Initialize uploaded_image for scope
    uploaded_image = None
```

Actually, this is already defined in the file uploader. Adjust the conditional to define it in scope for the generation button. Move the `uploaded_image` variable to module scope by initializing it before the conditional:

Before line 100 section, after imports initialization, add:
```python
# Initialize image source variables
uploaded_image = None
```

Then in the else block around line 121, just assign to it:
```python
    # Show file uploader
    uploaded_image = st.file_uploader(
```

**Step 3: Test edge cases**

```bash
# Test 1: No examples scenario
# Temporarily rename assets/examples to assets/examples_backup
# Run app, navigate to I2V
# Expected: Info message about no examples

# Test 2: Missing example file
# In metadata.json, add fake entry with non-existent path
# Try to load it
# Expected: Error message

# Test 3: Switch between upload and example
# Upload image, then load example, then click Change and upload again
# Expected: All transitions work smoothly

# Restore examples directory
mv assets/examples_backup assets/examples
```

Expected: All edge cases handled gracefully.

**Step 4: Commit**

```bash
git add pages/i2v_a14b.py
git commit -m "fix: handle edge cases in example selector

- Show info message when no examples available
- Validate example file exists before loading
- Fix variable scoping for uploaded_image
- Improve error messages

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Manual integration testing

**Files:**
- None (testing only)

**Step 1: Complete test checklist**

Run through all test scenarios from design doc:

```bash
streamlit run app.py
```

Test checklist:
- [ ] Initial load: Both uploader and selector visible
- [ ] Upload file: Works normally, selector still visible
- [ ] Select example: Selection highlights correctly
- [ ] Load example: Image displays, uploader/selector hidden
- [ ] Change image: Button re-shows selectors
- [ ] Select different example: Loads correctly
- [ ] Generate with example: Video generates using example image
- [ ] Generate with upload: Works as before
- [ ] No examples scenario: Graceful message displayed
- [ ] Multiple examples: Grid displays correctly with 3 columns
- [ ] Project folder creates correctly with example source

**Step 2: Check output files**

Verify generation output structure:
```bash
# After generating with example
ls -la output/<project_name>/
# Expected:
# - input/image.jpg (copy of example)
# - output_<timestamp>.mp4
# - metadata.json (with source_type: "example")
# - prompt.txt

cat output/<project_name>/metadata.json | grep example_id
# Expected: Shows example ID if example was used
```

**Step 3: Document results**

No commit for this step; results inform if fixes are needed.

---

## Task 8: Update documentation

**Files:**
- Modify: `pages/i2v_a14b.py:291-302` (Tips section at bottom)

**Step 1: Update tips section**

Replace the tips section at the end:

```python
# Footer
st.divider()
st.markdown(
    """
**Tips:**
- Upload an image and describe how you want it to animate
- **Or click an example image below the uploader to try pre-configured samples**
- Leave the prompt empty to let the model automatically determine motion
- Output video aspect ratio will match your input image
- Click "Extend Prompt" to enhance your description with cinematic elements
- Use 2+ GPUs for faster generation with FSDP parallelism
- Click "Change image" to switch between uploaded and example images
"""
)
```

**Step 2: Commit documentation**

```bash
git add pages/i2v_a14b.py
git commit -m "docs: update I2V tips to mention example selector

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Final Testing

**Run full end-to-end test:**

1. Start fresh:
```bash
streamlit run app.py
```

2. Navigate to I2V page

3. Test example workflow:
   - Select landscape example
   - Load it
   - Add prompt: "Gentle camera pan across the scene"
   - Generate video
   - Verify output

4. Test upload workflow:
   - Click "Change image"
   - Upload own image
   - Generate video
   - Verify output

5. Check both outputs have correct metadata

**Success criteria:**
- All manual tests pass
- No console errors
- UI is responsive and intuitive
- Generated videos work correctly
- Metadata tracks source correctly

---

## Extensibility Notes

This implementation provides a pattern for other pages:

**For S2V audio examples:**
```python
# In pages/s2v_14b.py
audio_library = ExampleLibrary(EXAMPLES_ROOT)
selected_id = audio_library.display_radio_grid(
    task="s2v-14B",
    media_type="audio",
    columns=2,
    key_suffix="s2v_audio"
)
```

**For Animate image/video examples:**
```python
# In pages/animate_14b.py
# Two separate selectors for reference image and source video
ref_id = example_library.display_radio_grid(
    task="animate-14B",
    media_type="image",
    columns=3,
    key_suffix="animate_ref"
)

src_id = example_library.display_radio_grid(
    task="animate-14B",
    media_type="video",
    columns=3,
    key_suffix="animate_src"
)
```

The `display_radio_grid` method is designed to be reusable across all pages with consistent UX.
