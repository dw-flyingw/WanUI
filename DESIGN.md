# WanUI Studio - Obsidian Precision Design System

## Design Philosophy

**Concept**: A sleek, professional dark interface inspired by high-end video editing suites and audio workstations. Streamlined, not blocky - precision instruments rather than bold statements.

## Core Aesthetic

### Typography
- **Display Font**: Outfit (geometric, technical, modern)
- **UI Font**: Inter (readable, professional, refined)
- **Code Font**: JetBrains Mono / Fira Code

### Color Palette

#### Base Colors
- `--obsidian-base`: #0a0a0a (Deep background)
- `--obsidian-surface`: #121212 (Elevated surfaces)
- `--obsidian-elevated`: #1a1a1a (Cards, containers)

#### Accent Colors
- `--accent-cyan`: #00d4ff (Primary accent - surgical blue)
- `--accent-cyan-dim`: #0099cc (Hover states)
- `--accent-success`: #00ff88 (Success states)
- `--accent-warning`: #ffaa00 (Warning states)
- `--accent-error`: #ff4466 (Error states)

#### Text Hierarchy
- `--text-primary`: #f0f0f0 (Main content)
- `--text-secondary`: #a0a0a0 (Secondary content)
- `--text-tertiary`: #606060 (Tertiary content)
- `--text-muted`: #404040 (Disabled/muted)

### Visual Language

#### Borders & Edges
- Hair-thin borders (1px, 8% opacity)
- Bright borders on focus (#00d4ff, 30% opacity)
- Rounded corners (8-12px)

#### Shadows & Depth
- **Soft**: 0 2px 8px rgba(0, 0, 0, 0.4)
- **Medium**: 0 4px 16px rgba(0, 0, 0, 0.6)
- **Strong**: 0 8px 32px rgba(0, 0, 0, 0.8)
- **Glow**: 0 0 20px rgba(0, 212, 255, 0.2)

#### Motion
- **Fast**: 0.15s cubic-bezier(0.4, 0, 0.2, 1)
- **Smooth**: 0.3s cubic-bezier(0.4, 0, 0.2, 1)
- **Gentle**: 0.5s cubic-bezier(0.25, 0.1, 0.25, 1)

## Component Guidelines

### Buttons
- Gradient backgrounds for depth
- Cyan accents on hover
- Glow effect on primary actions
- 1-2px hover lift

### Input Fields
- Minimal borders (obsidian-border)
- Cyan focus ring with glow
- Smooth transitions
- Consistent padding (0.6rem 1rem)

### Cards
- Floating appearance with subtle shadows
- Gradient backgrounds (cyan tints)
- Border glow on hover
- 2-4px hover lift

### Metrics
- Dashboard-style presentation
- Cyan value highlighting
- Uppercase labels
- Clean, spacious layout

### Sliders
- Cyan accent tracks
- Glowing thumb on hover
- Precise value display
- Professional control feel

## Layout Principles

1. **Breathing Room**: Generous padding and margins
2. **Visual Hierarchy**: Clear size and weight differences
3. **Subtle Depth**: Layered surfaces with shadows
4. **Floating Panels**: Cards and containers feel elevated
5. **Consistent Spacing**: 1rem base unit, scale by 0.5rem

## Animation Guidelines

### Micro-interactions
- Button hover: Color + glow + lift
- Card hover: Border + glow + lift
- Input focus: Border + glow ring
- Slider drag: Thumb scale + glow

### Page Load
- Fade-in from bottom (fadeInUp)
- Staggered animation for cards (0.1s delay)
- Smooth entrance, not jarring

## Usage

### In Pages
```python
from utils.theme import load_custom_theme, render_page_header

# Load theme at start of page
load_custom_theme()

# Use consistent page header
render_page_header(
    title="Your Page Title",
    description="Brief description of the page",
    icon="📝"  # optional
)
```

### Custom Styles
All styles are defined in `.streamlit/custom.css` and automatically applied to Streamlit components.

## Design Inspiration

- **Video Editing**: DaVinci Resolve, Premiere Pro
- **Audio Tools**: Ableton Live, Logic Pro
- **Code Editors**: VS Code, Sublime Text
- **Design Tools**: Figma (dark mode), Framer

## Key Differentiators

❌ **Avoid**:
- Blocky, chunky components
- Generic system fonts (Roboto, Arial)
- Purple gradients on white
- Overly bright neon colors
- Flat, dimensionless design

✅ **Embrace**:
- Refined, streamlined components
- Distinctive typography (Outfit, Inter)
- Cyan surgical accents
- Subtle depth and shadows
- Professional, tool-like feel

---

**Result**: A distinctive, professional interface that feels like a high-end creative tool, not a generic web app.
