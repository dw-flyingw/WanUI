# Cancellable Video Generation Design

**Date:** 2026-02-03
**Status:** Implemented

## Problem

Users could accidentally click the "Generate Video" button multiple times during video generation, which takes a long time. There was no way to cancel an in-progress generation.

## Solution

Modified the UI to dynamically change the "Generate Video" button to "⏹️ Cancel Generation" while video generation is in progress, allowing users to terminate long-running generation processes.

## Architecture

### Core Changes

**1. Modified `utils/generation.py`:**
- Changed `run_generation()` to use `subprocess.Popen()` instead of `subprocess.run()` for non-blocking execution
- Added `cancellation_check` callback parameter that accepts a callable returning True when cancellation is requested
- Implemented polling loop that checks for cancellation every 500ms
- Added graceful termination with `process.terminate()` followed by forced `process.kill()` if needed (10s timeout)
- Updated function signature and docstring to document the new parameter

**2. Modified all page files:**
- `pages/t2v_a14b.py`
- `pages/i2v_a14b.py`
- `pages/s2v_14b.py`
- `pages/animate_14b.py`
- `pages/ti2v_5b.py`

### Session State Management

Each page now tracks three session state variables:
- `{TASK_KEY}_generating` - Boolean flag indicating if generation is active
- `{TASK_KEY}_cancel_requested` - Boolean flag to signal cancellation
- `{TASK_KEY}_extended_prompt` - (existing) Stores extended prompt

### UI Flow

```
┌─────────────────────────────────────────┐
│ User clicks "Generate Video"            │
│ - Set _generating = True                │
│ - Set _cancel_requested = False         │
│ - Start generation process              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Button changes to "⏹️ Cancel Generation" │
│ (type="secondary")                      │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌────────────────┐  ┌─────────────────┐
│ User waits     │  │ User clicks     │
│ Generation     │  │ Cancel button   │
│ completes      │  │ - Set cancel_   │
│                │  │   requested=True│
│                │  │ - st.rerun()    │
└────────┬───────┘  └────────┬────────┘
         │                   │
         │                   ▼
         │         ┌──────────────────┐
         │         │ Polling loop     │
         │         │ detects cancel   │
         │         │ - terminate()    │
         │         │ - wait(10s)      │
         │         │ - kill() if hung │
         │         └────────┬─────────┘
         │                  │
         ▼                  ▼
┌─────────────────────────────────────────┐
│ Set _generating = False                 │
│ Show appropriate status message         │
│ Button returns to "Generate Video"      │
└─────────────────────────────────────────┘
```

### Generation Function Changes

```python
def run_generation(
    # ... existing parameters ...
    cancellation_check: Optional[callable] = None,
) -> tuple[bool, str, float]:
    # Start process with Popen
    process = subprocess.Popen(...)

    # Poll until complete or cancelled
    while process.poll() is None:
        if cancellation_check and cancellation_check():
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            return False, "Generation cancelled by user", elapsed
        time.sleep(0.5)  # Poll every 500ms

    # Handle completion
    stdout, stderr = process.communicate()
    # ... return results
```

### Page Implementation Pattern

```python
# Session state initialization
if f"{TASK_KEY}_generating" not in st.session_state:
    st.session_state[f"{TASK_KEY}_generating"] = False
if f"{TASK_KEY}_cancel_requested" not in st.session_state:
    st.session_state[f"{TASK_KEY}_cancel_requested"] = False

# Dynamic button rendering
if st.session_state.get(f"{TASK_KEY}_generating", False):
    if st.button("⏹️ Cancel Generation", type="secondary", use_container_width=True):
        st.session_state[f"{TASK_KEY}_cancel_requested"] = True
        st.rerun()
else:
    if st.button("Generate Video", type="primary", use_container_width=True):
        st.session_state[f"{TASK_KEY}_generating"] = True
        st.session_state[f"{TASK_KEY}_cancel_requested"] = False

        # Cancellation check callback
        def check_cancellation():
            return st.session_state.get(f"{TASK_KEY}_cancel_requested", False)

        # Run generation with cancellation support
        success, output, generation_time = run_generation(
            # ... parameters ...
            cancellation_check=check_cancellation,
        )

        # Reset flag after completion/cancellation
        st.session_state[f"{TASK_KEY}_generating"] = False

        # Handle cancellation
        if not success:
            if "cancelled by user" in output.lower():
                status.update(label="Generation cancelled", state="error")
                st.warning("Generation was cancelled.")
            else:
                status.update(label="Generation failed", state="error")
                st.error(output)
            st.stop()
```

## Edge Cases Handled

1. **Graceful vs Forced Termination:** Process is first sent SIGTERM via `terminate()`, with a 10-second grace period. If it doesn't exit cleanly, `kill()` is used to force termination.

2. **Process Polling:** Uses 500ms polling interval to balance responsiveness vs CPU usage.

3. **Timeout Handling:** The existing timeout mechanism still works - if the process runs longer than the timeout, it's terminated even without user cancellation.

4. **Status Messages:** Distinguishes between cancelled, failed, and successful generation with appropriate UI feedback.

## Files Modified

1. **utils/generation.py** - ~50 lines modified
   - Added `cancellation_check` parameter
   - Changed `subprocess.run()` to `subprocess.Popen()` with polling
   - Added graceful/forced termination logic

2. **pages/t2v_a14b.py** - ~30 lines modified
3. **pages/i2v_a14b.py** - ~30 lines modified
4. **pages/s2v_14b.py** - ~30 lines modified
5. **pages/animate_14b.py** - ~30 lines modified
6. **pages/ti2v_5b.py** - ~30 lines modified

**Total:** ~200 lines of changes across 6 files

## Testing Considerations

- Verify button state changes correctly when generation starts
- Test cancellation during different stages of generation
- Verify process termination (check with `ps aux | grep generate.py`)
- Test that subsequent generations work after cancellation
- Verify timeout still works as expected

## Future Enhancements

1. **Preprocessing Cancellation:** The `run_preprocessing()` function in `animate_14b.py` could be updated with the same cancellation pattern for long preprocessing operations.

2. **Progress Feedback:** Could show partial progress updates during generation by reading stdout from the process in real-time.

3. **Partial File Cleanup:** Currently leaves partial output files after cancellation. Could add optional cleanup logic.
