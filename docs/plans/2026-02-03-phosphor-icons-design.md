# Phosphor Icons Integration Design

**Date:** 2026-02-03
**Status:** Approved
**Theme:** Obsidian Precision

## Overview

Replace emoji icons in the Streamlit navigation with Phosphor Icons Light to create a more refined, professional aesthetic that matches the custom "Obsidian Precision" dark theme.

## Design Decisions

### Icon Library
- **Library:** Phosphor Icons (6,000+ icons)
- **Weight:** Light - Subtle, refined strokes that pair elegantly with Inter body text
- **Rationale:** Geometric, modern aesthetic matches Outfit font's geometric quality

### Color Scheme
- **Approach:** Contextual coloring
- **Behavior:** Icons inherit text color (secondary gray by default, cyan on hover/active state)
- **Rationale:** Better visual hierarchy, active page stands out more clearly

### Implementation Method
- **Approach:** Web font + CSS via CDN
- **Technique:** CSS `::before` pseudo-elements to inject icons
- **Rationale:** Most maintainable, works seamlessly with Streamlit's navigation, no Python code changes

## Icon Mappings

| Page | Current | New Icon | Phosphor Name | Unicode |
|------|---------|----------|---------------|---------|
| Home | 🏠 | ![icon] | house-simple | `\e9c1` |
| Text to Video | 📝 | ![icon] | article | `\e821` |
| Image to Video | 🖼️ | ![icon] | image | `\e9b1` |
| Fast T2V/I2V | ⚡ | ![icon] | lightning | `\ea4f` |
| Speech to Video | 🎤 | ![icon] | waveform | `\eb33` |
| Animate | 🎭 | ![icon] | magic-wand | `\ea7f` |
| Gallery | 🎬 | ![icon] | film-slate | `\e8e3` |
| Examples | 📁 | ![icon] | folder-open | `\e8fc` |

## Technical Implementation

### 1. Integration Approach

Load Phosphor Icons Light via CDN and use CSS `::before` pseudo-elements to inject icons into Streamlit's navigation.

**Benefits:**
- No Python code changes needed
- Icons automatically inherit contextual color scheme
- Scales perfectly with existing typography
- Works seamlessly with `st.navigation()` structure

**Steps:**
1. Add Phosphor Icons stylesheet to `custom.css` via CDN
2. Target Streamlit navigation elements using `[data-testid="stSidebarNav"]`
3. Use `::before` pseudo-elements with Phosphor icon codes
4. Match pages by title using `a[href*="page_name"]` selectors

### 2. CSS Structure

**CDN Import:**
```css
@import url('https://unpkg.com/@phosphor-icons/web@2.0.3/src/light/style.css');
```

**Base Icon Styles:**
```css
[data-testid="stSidebarNav"] a::before {
    font-family: 'Phosphor-Light';
    font-size: 18px;
    margin-right: 8px;
    display: inline-block;
    width: 20px;
    text-align: center;
    transition: var(--transition-fast);
}
```

**Page-Specific Selectors:**
- `a[href*="home"]::before { content: "\e9c1"; }`
- `a[href*="t2v_a14b"]::before { content: "\e821"; }`
- `a[href*="i2v_a14b"]::before { content: "\e9b1"; }`
- `a[href*="ti2v_5b"]::before { content: "\ea4f"; }`
- `a[href*="s2v_14b"]::before { content: "\eb33"; }`
- `a[href*="animate_14b"]::before { content: "\ea7f"; }`
- `a[href*="gallery"]::before { content: "\e8e3"; }`
- `a[href*="examples"]::before { content: "\e8fc"; }`

### 3. Visual Specifications

**Sizing:**
- Icon size: 18px (balanced with sidebar text at 0.9rem)
- Icon spacing: 8px margin-right
- Icon width: 20px (fixed width for alignment)

**Colors:**
- Default: Inherits from parent link (var(--text-secondary))
- Hover/Active: Inherits cyan color (var(--accent-cyan))
- Transitions: Uses existing var(--transition-fast) (0.15s)

**Typography Harmony:**
- Pairs with sidebar text: 0.9rem (line 111, custom.css)
- Complements section headers: 1.1rem (line 101, custom.css)
- Matches button icon-to-text ratios

### 4. Responsive Behavior

**Mobile/Narrow Viewports (<768px):**
- Icons maintain 18px size (touch-friendly)
- Reduce margin-right from 8px to 6px
- Maintain alignment with flex layout

```css
@media (max-width: 768px) {
    [data-testid="stSidebarNav"] a::before {
        margin-right: 6px;
    }
}
```

### 5. Visual Refinements

**Interaction Polish:**
- Color transitions use existing `var(--transition-fast)` for snappy feedback
- Icons maintain alignment even with text wrapping
- Active page indicators (cyan border) extend to include icon

**Hierarchy:**
- Section headers ("Overview", "Models", "Library") remain icon-free
- Separates organizational labels from navigation targets
- Maintains clear visual hierarchy

**Accessibility:**
- Icons are decorative (text labels remain primary)
- `::before` pseudo-elements stay out of accessibility tree
- Screen readers focus on text labels only

## Files Modified

- `.streamlit/custom.css` - Add Phosphor Icons CSS section

## Files Not Modified

- `app.py` - No changes to Python code
- Page files - No changes to page definitions

## Testing Checklist

- [ ] Icons display correctly for all 8 pages
- [ ] Contextual coloring works (gray → cyan on hover/active)
- [ ] Icons align properly with text labels
- [ ] Responsive behavior works on narrow viewports
- [ ] No layout shift or text overlap
- [ ] Screen readers ignore icons, read labels only
- [ ] Active page shows cyan icon + cyan border
- [ ] Section headers remain icon-free

## Future Considerations

- If additional pages are added, follow the pattern: `a[href*="page_file"]::before { content: "\unicode"; }`
- Phosphor Icons library can be updated by changing CDN version in @import
- Alternative weights (Regular, Bold) available if design direction changes
