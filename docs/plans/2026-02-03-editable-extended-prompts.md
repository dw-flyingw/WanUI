# Editable Extended Prompts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to edit LLM-generated extended prompts with protection against accidental overwrites.

**Architecture:** Modify Streamlit text areas to be editable, add two-step confirmation for re-extension, update generation logic to use edited prompts, and track edited prompts in metadata.

**Tech Stack:** Streamlit, Python, session state management

---

## Task 1: Update T2V page with editable prompts

**Files:**
- Modify: `pages/t2v_a14b.py:51-56` (session state initialization)
- Modify: `pages/t2v_a14b.py:138-161` (prompt extension UI)
- Modify: `pages/t2v_a14b.py:191` (generation prompt selection)
- Modify: `pages/t2v_a14b.py:255` (metadata tracking)

**Step 1: Add confirmation session state**

In the session state initialization block (after line 56), add:

```python
if f"{TASK_KEY}_confirm_extend" not in st.session_state:
    st.session_state[f"{TASK_KEY}_confirm_extend"] = False
```

**Step 2: Update prompt extension button logic**

Replace lines 138-161 with:

```python
# Prompt extension button with confirmation
col1, col2 = st.columns([1, 4])
with col1:
    has_existing = st.session_state.get(f"{TASK_KEY}_extended_prompt") is not None

    if has_existing and not st.session_state[f"{TASK_KEY}_confirm_extend"]:
        if st.button("Extend Prompt", disabled=not PROMPT_EXTEND_MODEL):
            st.session_state[f"{TASK_KEY}_confirm_extend"] = True
            st.rerun()
    else:
        button_label = "Confirm Extend" if st.session_state[f"{TASK_KEY}_confirm_extend"] else "Extend Prompt"
        extend_clicked = st.button(button_label, disabled=not PROMPT_EXTEND_MODEL)

# Show warning when confirmation needed
if has_existing and st.session_state[f"{TASK_KEY}_confirm_extend"]:
    st.warning("⚠️ This will replace your current extended prompt. Click 'Confirm Extend' to proceed.")

# Handle extension
if extend_clicked:
    with st.spinner("Extending prompt..."):
        result = extend_prompt(prompt, TASK)
        if result.success:
            st.session_state[f"{TASK_KEY}_extended_prompt"] = result.extended_prompt
            st.session_state[f"{TASK_KEY}_confirm_extend"] = False  # Reset confirmation
            st.success("Prompt extended successfully!")
        else:
            st.warning(f"Extension failed: {result.message}")

# Show extended prompt if available (now editable)
if st.session_state.get(f"{TASK_KEY}_extended_prompt"):
    with st.expander("Extended Prompt (editable)", expanded=True):
        st.text_area(
            "Extended",
            value=st.session_state[f"{TASK_KEY}_extended_prompt"],
            height=150,
            key=f"{TASK_KEY}_extended_prompt_edit",
            label_visibility="collapsed",
        )
```

**Step 3: Update generation prompt selection**

Replace line 191 with:

```python
# Use edited extended prompt if available, fall back to original extended, then original prompt
generation_prompt = (
    st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or
    st.session_state.get(f"{TASK_KEY}_extended_prompt") or
    prompt
)
```

**Step 4: Update metadata tracking**

Replace line 255 with:

```python
extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or st.session_state.get(f"{TASK_KEY}_extended_prompt"),
```

**Step 5: Commit T2V changes**

```bash
git add pages/t2v_a14b.py
git commit -m "feat(t2v): add editable extended prompts with confirmation"
```

---

## Task 2: Update I2V page with editable prompts

**Files:**
- Modify: `pages/i2v_a14b.py` (same pattern as T2V)

**Step 1: Read I2V page to find line numbers**

```bash
grep -n "extended_prompt" pages/i2v_a14b.py | head -10
```

Expected: Line numbers for session state init, prompt extension UI, generation logic, metadata

**Step 2: Add confirmation session state**

Find the session state initialization block (similar to T2V line 51-56) and add:

```python
if f"{TASK_KEY}_confirm_extend" not in st.session_state:
    st.session_state[f"{TASK_KEY}_confirm_extend"] = False
```

**Step 3: Update prompt extension button logic**

Replace the prompt extension button and display section (similar to T2V lines 138-161) with the same confirmation logic from Task 1 Step 2.

**Step 4: Update generation prompt selection**

Find the line where `generation_prompt` is set (similar to T2V line 191) and replace with:

```python
generation_prompt = (
    st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or
    st.session_state.get(f"{TASK_KEY}_extended_prompt") or
    prompt
)
```

**Step 5: Update metadata tracking**

Find the metadata creation call (similar to T2V line 255) and update `extended_prompt` parameter to:

```python
extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or st.session_state.get(f"{TASK_KEY}_extended_prompt"),
```

**Step 6: Commit I2V changes**

```bash
git add pages/i2v_a14b.py
git commit -m "feat(i2v): add editable extended prompts with confirmation"
```

---

## Task 3: Update S2V page with editable prompts

**Files:**
- Modify: `pages/s2v_14b.py` (same pattern as T2V)

**Step 1: Read S2V page to find line numbers**

```bash
grep -n "extended_prompt" pages/s2v_14b.py | head -10
```

Expected: Line numbers for session state init, prompt extension UI, generation logic, metadata

**Step 2: Add confirmation session state**

Add to session state initialization:

```python
if f"{TASK_KEY}_confirm_extend" not in st.session_state:
    st.session_state[f"{TASK_KEY}_confirm_extend"] = False
```

**Step 3: Update prompt extension button logic**

Replace the prompt extension section with confirmation logic from Task 1 Step 2.

**Step 4: Update generation prompt selection**

Replace generation prompt assignment with:

```python
generation_prompt = (
    st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or
    st.session_state.get(f"{TASK_KEY}_extended_prompt") or
    prompt
)
```

**Step 5: Update metadata tracking**

Update metadata `extended_prompt` parameter:

```python
extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or st.session_state.get(f"{TASK_KEY}_extended_prompt"),
```

**Step 6: Commit S2V changes**

```bash
git add pages/s2v_14b.py
git commit -m "feat(s2v): add editable extended prompts with confirmation"
```

---

## Task 4: Update Animate page with editable prompts

**Files:**
- Modify: `pages/animate_14b.py` (same pattern as T2V)

**Step 1: Read Animate page to find line numbers**

```bash
grep -n "extended_prompt" pages/animate_14b.py | head -10
```

Expected: Line numbers for session state init, prompt extension UI, generation logic, metadata

**Step 2: Add confirmation session state**

Add to session state initialization:

```python
if f"{TASK_KEY}_confirm_extend" not in st.session_state:
    st.session_state[f"{TASK_KEY}_confirm_extend"] = False
```

**Step 3: Update prompt extension button logic**

Replace the prompt extension section with confirmation logic from Task 1 Step 2.

**Step 4: Update generation prompt selection**

Replace generation prompt assignment with:

```python
generation_prompt = (
    st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or
    st.session_state.get(f"{TASK_KEY}_extended_prompt") or
    prompt
)
```

**Step 5: Update metadata tracking**

Update metadata `extended_prompt` parameter:

```python
extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or st.session_state.get(f"{TASK_KEY}_extended_prompt"),
```

**Step 6: Commit Animate changes**

```bash
git add pages/animate_14b.py
git commit -m "feat(animate): add editable extended prompts with confirmation"
```

---

## Task 5: Update TI2V page with editable prompts

**Files:**
- Modify: `pages/ti2v_5b.py` (same pattern as T2V)

**Step 1: Read TI2V page to find line numbers**

```bash
grep -n "extended_prompt" pages/ti2v_5b.py | head -10
```

Expected: Line numbers for session state init, prompt extension UI, generation logic, metadata

**Step 2: Add confirmation session state**

Add to session state initialization:

```python
if f"{TASK_KEY}_confirm_extend" not in st.session_state:
    st.session_state[f"{TASK_KEY}_confirm_extend"] = False
```

**Step 3: Update prompt extension button logic**

Replace the prompt extension section with confirmation logic from Task 1 Step 2.

**Step 4: Update generation prompt selection**

Replace generation prompt assignment with:

```python
generation_prompt = (
    st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or
    st.session_state.get(f"{TASK_KEY}_extended_prompt") or
    prompt
)
```

**Step 5: Update metadata tracking**

Update metadata `extended_prompt` parameter:

```python
extended_prompt=st.session_state.get(f"{TASK_KEY}_extended_prompt_edit") or st.session_state.get(f"{TASK_KEY}_extended_prompt"),
```

**Step 6: Commit TI2V changes**

```bash
git add pages/ti2v_5b.py
git commit -m "feat(ti2v): add editable extended prompts with confirmation"
```

---

## Task 6: Manual testing

**Files:**
- Test: All 5 modified page files

**Step 1: Start Streamlit app**

```bash
streamlit run app.py
```

Expected: App starts successfully on port 8560

**Step 2: Test T2V page**

1. Navigate to T2V page
2. Enter a prompt
3. Click "Extend Prompt" (should extend immediately)
4. Verify extended prompt appears in editable text area
5. Edit the extended prompt text
6. Click "Extend Prompt" again
7. Verify warning appears and button changes to "Confirm Extend"
8. Click "Confirm Extend"
9. Verify new extended prompt replaces the old one

**Step 3: Test I2V page**

Repeat Step 2 testing sequence on I2V page.

**Step 4: Test S2V page**

Repeat Step 2 testing sequence on S2V page (upload audio file first).

**Step 5: Test Animate page**

Repeat Step 2 testing sequence on Animate page (upload video file first).

**Step 6: Test TI2V page**

Repeat Step 2 testing sequence on TI2V page.

**Step 7: Document test results**

Create a test summary noting any issues found.

---

## Notes

- All pages follow the same pattern, so changes are mechanical and consistent
- The `key` parameter on text_area automatically syncs edits to session state
- Confirmation logic prevents accidental overwrites without being intrusive
- Generation logic has a clear fallback chain: edited → original extended → user prompt
- Each page has isolated session state via task-specific keys

## Testing Strategy

Manual testing only (no automated tests needed):
1. Verify editable text areas work
2. Verify confirmation flow prevents accidental overwrites
3. Verify edited prompts are used for generation
4. Verify metadata tracks edited prompts
5. Test on all 5 pages
