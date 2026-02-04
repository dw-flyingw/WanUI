# Remove Library Section from Sidebar

**Date:** 2026-02-04

## Overview

Simplified the sidebar navigation by removing the "Library" section containing the Examples page.

## Changes

**Before:**
- "Overview": Home, Gallery
- "Models": T2V, I2V, TI2V, S2V, Animate
- "Library": Examples

**After:**
- "Overview": Home, Gallery
- "Models": T2V, I2V, TI2V, S2V, Animate

## Implementation

Modified `app.py`:
- Removed `examples_page` definition
- Removed "Library" section from `st.navigation()` configuration

## Rationale

Streamlines the UI to focus on core functionality: overview pages and model pages. The examples page was not needed in the primary navigation.
