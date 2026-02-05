"""Wan2.2 badge for sidebar - professional card design."""

import base64
import mimetypes
from pathlib import Path

import streamlit as st


def render_wan22_badge() -> None:
    """Render a Wan2.2 badge at the top of the sidebar with logo and info."""
    wan22_url = "https://github.com/Wan-Video/Wan2.2"

    # Load Wan2.2 logo
    try:
        logo_path = Path(__file__).parent / "wan22-logo.png"
        logo_b64 = ""
        logo_mime = "image/png"
        if logo_path.exists():
            guessed_mime, _ = mimetypes.guess_type(str(logo_path))
            logo_mime = guessed_mime or "image/png"
            logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    except Exception:
        logo_b64 = ""
        logo_mime = "image/png"

    card_css = f"""
    <style>
      .wan22-card {{
        position: relative;
        display: block;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 16px;
        border: 1px solid rgba(0, 212, 255, 0.35);
        background: radial-gradient(120% 120% at 0% 0%, #1a1a1a 0%, #0f0f0f 45%, #1a1a1a 100%);
        box-shadow: 0 6px 18px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(0, 212, 255, 0.08);
        transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease;
        text-decoration: none;
      }}
      .wan22-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.45), 0 0 20px rgba(0, 212, 255, 0.2), inset 0 0 0 1px rgba(0, 212, 255, 0.12);
        border-color: rgba(0, 212, 255, 0.6);
      }}
      .wan22-card, .wan22-card:hover, .wan22-card * {{ text-decoration: none !important; }}
      .wan22-logo-container {{
        height: 100px;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(0, 212, 255, 0.1) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }}
      .wan22-logo {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        filter: brightness(1.1);
      }}
      .wan22-body {{
        padding: 14px 14px 16px 14px;
        background: linear-gradient(180deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.0));
      }}
      .wan22-title {{
        color: #f0f0f0;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 0.3px;
        margin-bottom: 6px;
      }}
      .wan22-version {{
        color: #00d4ff;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
        opacity: 0.95;
      }}
      .wan22-desc {{
        color: #a0a0a0;
        font-size: 12px;
        line-height: 1.4;
        margin-bottom: 10px;
      }}
      .wan22-tags {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
      }}
      .wan22-tag {{
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.2px;
        padding: 3px 8px;
        border-radius: 999px;
        border: 1px solid rgba(0, 212, 255, 0.35);
        color: #00d4ff;
        background: rgba(0, 212, 255, 0.12);
      }}
      .wan22-cta {{
        margin-top: 10px;
        display: inline-block;
        width: 100%;
        text-align: center;
        color: #0a0a0a;
        background: linear-gradient(135deg, #0099cc 0%, #00d4ff 100%);
        border-radius: 10px;
        padding: 8px 10px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.2px;
        border: none;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
      }}
      .wan22-cta:hover {{
        filter: brightness(1.1);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
      }}
    </style>
    """

    logo_html = ""
    if logo_b64:
        logo_html = f'<img class="wan22-logo" src="data:{logo_mime};base64,{logo_b64}" alt="Wan2.2 Logo" />'

    card_html = f"""
    <a class="wan22-card" href="{wan22_url}" target="_blank" rel="noopener noreferrer">
      <div class="wan22-logo-container">
        {logo_html}
      </div>
      <div class="wan22-body">
        <div class="wan22-version">Version 2.2</div>
        <div class="wan22-title">Wan Video Generation</div>
        <div class="wan22-desc">State-of-the-art multimodal video generation models with MoE architecture.</div>
        <div class="wan22-tags">
          <span class="wan22-tag">14B MoE</span>
          <span class="wan22-tag">720P</span>
          <span class="wan22-tag">Multimodal</span>
        </div>
        <div class="wan22-cta">Learn More ↗</div>
      </div>
    </a>
    """

    with st.sidebar.container():
        st.markdown(card_css + card_html, unsafe_allow_html=True)
