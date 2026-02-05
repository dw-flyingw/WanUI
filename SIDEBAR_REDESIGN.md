# Sidebar Redesign - Wan2.2 & HPE PCAI Cards

## Overview

The sidebar has been redesigned to match the Medgemma style with professional card components at the top and bottom.

## Changes Made

### 1. Assets Added

Copied from Medgemma and Wan2.2 repos:
- `assets/wan22-logo.png` - Wan2.2 logo
- `assets/hpe-ai.png` - HPE AI hero image
- `assets/HPE.png` - HPE logo

### 2. New Badge Components

Created two professional badge modules:

#### `assets/wan22_badge.py`
- **Position**: Top of sidebar
- **Style**: Cyan accent (#00d4ff) matching Obsidian Precision theme
- **Features**:
  - Wan2.2 logo display
  - Version badge (2.2)
  - Model description
  - Tags: 14B MoE, 720P, Multimodal
  - Clickable link to GitHub repo
  - Hover effects with glow

#### `assets/hpe_badge.py`
- **Position**: Bottom of sidebar
- **Style**: Green accent (#00b388) from HPE branding
- **Features**:
  - HPE AI hero image
  - HPE branding
  - Description of AI solutions
  - Tags: AI infrastructure, edge to cloud, GreenLake
  - Clickable link to hpe.com/ai
  - Hover effects

### 3. Updated Sidebar Utilities

`utils/sidebar.py` now includes:

#### `render_sidebar_header()`
- Renders Wan2.2 badge at the top
- Replaces old logo + title approach
- Call this at the start of each page

#### `render_sidebar_footer()`
- Renders HPE PCAI badge at the bottom
- Adds separator divider
- Call this at the end of each page

### 4. Updated All Pages

All page files now include:
- `from utils.sidebar import render_sidebar_header, render_sidebar_footer`
- `render_sidebar_header()` call at the start
- `render_sidebar_footer()` call at the end

Pages updated:
- ✅ `pages/home.py`
- ✅ `pages/t2v_a14b.py`
- ✅ `pages/i2v_a14b.py`
- ✅ `pages/ti2v_5b.py`
- ✅ `pages/s2v_14b.py`
- ✅ `pages/animate_14b.py`
- ✅ `pages/gallery.py`
- ✅ `pages/examples.py`

## Visual Design

### Wan2.2 Card (Top)
```
┌─────────────────────────────────┐
│   [Wan2.2 Logo - centered]      │  ← Logo area with cyan gradient
├─────────────────────────────────┤
│ VERSION 2.2                      │  ← Cyan badge
│ Wan Video Generation             │  ← Title
│ State-of-the-art multimodal...   │  ← Description
│                                  │
│ [14B MoE] [720P] [Multimodal]   │  ← Tags with cyan accent
│                                  │
│     [Learn More ↗]               │  ← Cyan gradient button
└─────────────────────────────────┘
```

### HPE PCAI Card (Bottom)
```
┌─────────────────────────────────┐
│   [Hero Image - HPE AI]          │  ← Hero image
├─────────────────────────────────┤
│ AI SOLUTIONS                     │  ← Green kicker
│ HPE Artificial Intelligence      │  ← Title with HPE wordmark
│ Accelerate AI from edge to...    │  ← Description
│                                  │
│ [AI infrastructure] [edge...]    │  ← Tags with green accent
│                                  │
│     [Explore HPE AI ↗]           │  ← Green button
└─────────────────────────────────┘
```

## Design Features

### Shared Styling
- **Border**: 1px solid with brand color (cyan/green)
- **Border Radius**: 14px for smooth corners
- **Shadow**: Multi-layer with inset highlights
- **Hover Effects**:
  - 2px lift (translateY)
  - Enhanced shadow
  - Brighter border
  - Smooth transitions (0.15s - 0.2s)

### Color Schemes

**Wan2.2 Card**:
- Primary: #00d4ff (cyan)
- Background: Dark gradient (#1a1a1a → #0f0f0f)
- Border: rgba(0, 212, 255, 0.35)

**HPE Card**:
- Primary: #00b388 (green)
- Background: Dark gradient (#0f1311 → #131614)
- Border: rgba(0, 179, 136, 0.35)

## Integration with Obsidian Precision Theme

Both cards:
- Use the same design language as the main theme
- Match the professional, streamlined aesthetic
- Include smooth animations
- Feature floating/elevated appearance
- Integrate seamlessly with sidebar styling

## Testing

Run the app and check:
```bash
streamlit run app.py
```

1. **Wan2.2 card** appears at top of sidebar
2. **HPE card** appears at bottom of sidebar
3. Both cards have hover effects
4. Links open in new tabs
5. Styling matches Obsidian Precision theme

## Customization

### Change Links
Edit the badge files:
- `assets/wan22_badge.py` - Line 14: `wan22_url`
- `assets/hpe_badge.py` - Line 9: `hpe_url`

### Update Images
Replace files in `assets/`:
- `wan22-logo.png` - Wan2.2 logo
- `hpe-ai.png` - HPE hero image

### Modify Styling
Edit CSS in the badge files:
- Colors in `card_css` variable
- Layout in card structure
- Hover effects in `:hover` rules

---

**Result**: Professional sidebar branding that matches high-end creative tools, with clear model identity (Wan2.2) and infrastructure partner (HPE) visibility.
