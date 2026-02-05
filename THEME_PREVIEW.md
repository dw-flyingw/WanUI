# Obsidian Precision Theme - Preview Guide

## 🎨 What Changed

Your WanUI Studio has been transformed with the **Obsidian Precision** aesthetic - a modern dark theme inspired by professional creative tools like DaVinci Resolve and Ableton Live.

## 🚀 Quick Preview

Run your Streamlit app to see the new design:

```bash
cd /home/users/wrightda/src/WanUI
streamlit run app.py
```

Then navigate to: `http://localhost:8560`

## ✨ Key Design Features

### 1. **Typography**
- **Outfit** for headings (geometric, modern, technical)
- **Inter** for body text (clean, professional)
- Refined hierarchy with proper font weights

### 2. **Color System**
- **Deep Obsidian Base**: #0a0a0a
- **Surgical Cyan Accent**: #00d4ff
- **Subtle Gradients**: Cyan tints on cards
- **Text Hierarchy**: 4 levels from bright to muted

### 3. **Components**
- **Buttons**: Gradient backgrounds, cyan glow on hover
- **Cards**: Floating appearance with subtle shadows, hover lift
- **Inputs**: Minimal borders, cyan focus glow
- **Metrics**: Dashboard-style with cyan values
- **Sliders**: Glowing cyan accents, precise controls

### 4. **Motion**
- Smooth transitions (0.3s cubic-bezier)
- Hover states: lift + glow + color change
- Fade-in animations on page load
- Staggered card reveals

### 5. **Visual Details**
- Hair-thin borders (1px, 8% opacity)
- Layered depth with shadows
- Frosted glass effects
- Cyan glow on focus/hover

## 📁 Files Modified

### Core Theme Files
- `.streamlit/custom.css` - Complete theme stylesheet (700+ lines)
- `.streamlit/config.toml` - Updated theme colors
- `app.py` - CSS loader integration

### Page Updates
- `pages/home.py` - Enhanced welcome section, refined cards
- `pages/t2v_a14b.py` - New page header styling

### New Utilities
- `utils/theme.py` - Theme loading and helper functions
- `utils/sidebar.py` - Enhanced sidebar header

### Documentation
- `DESIGN.md` - Complete design system documentation
- `THEME_PREVIEW.md` - This guide

## 🎯 What to Notice

### Home Page
1. **Hero Section**: Gradient title with cyan accent
2. **Model Cards**: Floating cards with hover effects
3. **Metrics**: Dashboard-style GPU/model stats
4. **Footer**: Refined with cyan accent

### Model Pages (e.g., T2V)
1. **Page Header**: Large title with icon, clear description
2. **Sidebar**: Styled controls with cyan accents
3. **Buttons**: Primary button has cyan glow
4. **Inputs**: Focus states with glow rings
5. **Sliders**: Cyan accents with hover effects

### Interactive Elements
1. **Hover any card** - Watch the lift + glow effect
2. **Click an input field** - See the cyan focus ring
3. **Drag a slider** - Notice the glowing thumb
4. **Hover a button** - Observe the smooth color transition

## 🔧 Customization

### Change Accent Color
Edit `.streamlit/custom.css` line 17:
```css
--accent-cyan: #00d4ff;  /* Change to your preferred color */
```

### Adjust Animation Speed
Edit `.streamlit/custom.css` lines 39-41:
```css
--transition-fast: 0.15s;    /* Quick interactions */
--transition-smooth: 0.3s;   /* Standard transitions */
--transition-gentle: 0.5s;   /* Gentle animations */
```

### Modify Typography
Edit `.streamlit/custom.css` line 7:
```css
@import url('https://fonts.googleapis.com/css2?family=YourFont...');
```

## 💡 Design Principles Applied

1. **Streamlined, Not Blocky**
   - Rounded corners (8-12px)
   - Subtle borders
   - Generous spacing

2. **Professional Tool Feel**
   - Precision controls
   - Clear hierarchy
   - Technical typography

3. **Modern Dark Aesthetic**
   - Deep blacks
   - Subtle gradients
   - Cyan surgical accents

4. **Refined Motion**
   - Smooth, purposeful transitions
   - No gratuitous animations
   - Micro-interactions that delight

## 🎨 Before vs After

### Before
- Generic Streamlit dark theme
- System fonts (Arial, default sans)
- Flat components
- Minimal styling
- Standard spacing

### After
- Custom Obsidian Precision theme
- Distinctive fonts (Outfit, Inter)
- Layered, floating components
- Cyan accent system
- Refined spacing and depth
- Smooth animations
- Professional tool aesthetic

## 📖 Next Steps

1. **Test the design**: Run the app and explore all pages
2. **Review components**: Check buttons, inputs, cards, metrics
3. **Test interactions**: Hover, click, drag to see animations
4. **Customize if needed**: Adjust colors or spacing in `custom.css`

## 🐛 Troubleshooting

### CSS not loading?
```bash
# Clear Streamlit cache
streamlit cache clear
```

### Fonts not showing?
Check your internet connection - fonts load from Google Fonts CDN.

### Custom styles not applying?
Make sure `load_custom_theme()` is called at the top of each page.

---

**Enjoy your new professional-grade interface!** 🚀
