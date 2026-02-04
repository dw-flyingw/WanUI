# S2V Page Example Selector Design

**Date:** 2026-02-04
**Status:** Approved
**Author:** Claude Code

## Overview

Add example selectors for reference images, audio sources, and pose videos on the S2V page. Audio examples serve dual purposes: as main audio source in upload mode, or as TTS reference audio in TTS mode.

## Motivation

The S2V page requires three media inputs (reference image, audio, optional pose video), making it cumbersome for new users to test. Example selectors provide ready-to-use samples that demonstrate both speech and singing capabilities.

## Design

### Inputs Requiring Example Selectors

1. **Reference Image** (required)
   - Available example: `test_portrait_01`
   - Simple selector in left column

2. **Audio Source** (required, mode-aware)
   - Available examples: `talk_sample_01`, `singing_sample_01`
   - **Upload mode:** Used as main audio source
   - **TTS mode:** Used as TTS reference audio for voice cloning
   - Help text adapts based on mode

3. **Pose Video** (optional)
   - Available example: `pose_reference_01`
   - Selector inside "Advanced" expander

### Session State

Three sets of state (9 variables total):

**Reference Image:**
- `{TASK_KEY}_image_example_loaded` - boolean
- `{TASK_KEY}_loaded_image_example_path` - Path
- `{TASK_KEY}_loaded_image_example_id` - string

**Audio Source:**
- `{TASK_KEY}_audio_example_loaded` - boolean
- `{TASK_KEY}_loaded_audio_example_path` - Path
- `{TASK_KEY}_loaded_audio_example_id` - string

**Pose Video:**
- `{TASK_KEY}_pose_example_loaded` - boolean
- `{TASK_KEY}_loaded_pose_example_path` - Path
- `{TASK_KEY}_loaded_pose_example_id` - string

### UI Flow Per Input

**When example loaded:**
1. Show success message with example ID
2. Display the loaded media
3. Show "Clear Example (Upload My Own)" button

**When no example loaded:**
1. Show file uploader
2. Show divider + "OR select an example"
3. Display radio grid of examples
4. Show "Load Selected Example" button

### Audio Mode Handling

Audio mode selection happens first via radio buttons. Example selector appears afterward with mode-specific context:

**Upload Audio File mode:**
- Examples shown as audio source options
- Help text: "Select example audio to use"
- Loaded example replaces need for uploaded audio

**Text-to-Speech mode:**
- Examples shown as TTS reference audio options
- Help text: "Select example for voice cloning reference"
- Loaded example replaces TTS reference audio upload
- Text inputs (reference text + synthesis text) still required

### Validation Updates

Check for either uploaded files OR loaded examples:

```python
# Reference image
if not uploaded_image and not image_example_loaded:
    error("Upload or select reference image")

# Audio - depends on mode
if audio_mode == "Upload audio file":
    if not uploaded_audio and not audio_example_loaded:
        error("Upload or select audio")
elif audio_mode == "TTS":
    if not tts_prompt_audio and not audio_example_loaded:
        error("Provide or select TTS reference audio")
    if not tts_prompt_text or not tts_text:
        error("Provide reference and synthesis text")
```

### File Handling

Copy example files to project input directory when used:

```python
# Reference image
if uploaded_image:
    image_path = save_uploaded_file(uploaded_image, input_dir / "image.jpg")
else:
    shutil.copy(example_image_path, input_dir / "image.jpg")

# Audio (similar pattern for both upload and TTS modes)
# Pose video (if present)
```

### Grid Layout

- Reference image examples: 2 columns (1 example available)
- Audio examples: 2 columns (2 examples available)
- Pose video examples: 1 column (1 example available, inside expander)

## Implementation Notes

- Import `shutil` for copying files
- Import `ExampleLibrary` from `utils.examples`
- Use unique `key_suffix` for each selector: "s2v_image", "s2v_audio", "s2v_pose"
- Audio examples work in both upload and TTS modes with different purposes
- Pose video selector is optional and nested inside expander

## Testing

1. Load image example only → should require audio
2. Load audio example in upload mode → should work as audio source
3. Load audio example in TTS mode → should work as reference audio, still need texts
4. Load pose video example → should be optional, generation works with/without
5. Clear examples and upload files → should use uploaded files
6. Switch audio modes with example loaded → example should work in both modes
