import io
import os
import re
import json
import time
import base64
import zipfile
import datetime
import tempfile
import streamlit as st

st.set_page_config(
    page_title="CMRF Portal | Sumanth Muthamala",
    page_icon="🏛️",
    layout="wide"
)

# -------------------------------------------------------------
# 1. SIDEBAR: THEME MODES & API KEY OVERRIDE
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ✨ Visual Theme & Glaze Mode")
    ui_theme = st.selectbox(
        "Select Portal Aesthetic",
        [
            "Royal Magenta & Gold (Poster Match)",
            "Telangana Official Navy & Emerald",
            "Midnight Obsidian Glass"
        ],
        index=0
    )
    enable_animations = st.toggle("Enable Shimmer & Float Animations", value=True)
    st.markdown("---")
    st.markdown("### 🔑 API Key Override")
    st.caption("Paste a Gemini API key (AIzaSy...) if primary secrets hit quota.")
    user_custom_key = st.text_input("Temporary Backup Key", type="password", placeholder="AIzaSy...")

# -------------------------------------------------------------
# 2. DYNAMIC BACKGROUND & GLAZING ANIMATION CSS
# -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_poster_background():
    img_b64 = ""
    ext = "png"
    candidates = [
        "background.png",
        "background.jpg",
        "bg.png",
        "bg.jpg",
        "a_polished_poster_style_app_landing_background_in.png"
    ]
    for name in candidates:
        if os.path.exists(name):
            try:
                with open(name, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                    ext = "png" if name.endswith(".png") else "jpeg"
                    break
            except Exception:
                pass
    return img_b64, ext

img_b64, ext = load_poster_background()

if ui_theme == "Telangana Official Navy & Emerald":
    card_bg = "rgba(10, 25, 47, 0.90)"
    accent_primary = "#10B981"
    accent_secondary = "#34D399"
    btn_grad = "linear-gradient(135deg, #065F46 0%, #059669 100%)"
    fallback_bg = "radial-gradient(circle at 50% 10%, #0F294A 0%, #09192F 60%, #040D1A 100%)"
elif ui_theme == "Midnight Obsidian Glass":
    card_bg = "rgba(15, 15, 20, 0.92)"
    accent_primary = "#F59E0B"
    accent_secondary = "#FCD34D"
    btn_grad = "linear-gradient(135deg, #B45309 0%, #D97706 100%)"
    fallback_bg = "radial-gradient(circle at 50% 10%, #1F2937 0%, #111827 60%, #030712 100%)"
else:
    card_bg = "rgba(30, 4, 18, 0.90)"
    accent_primary = "#FFC107"
    accent_secondary = "#FFE082"
    btn_grad = "linear-gradient(135deg, #7A003E 0%, #A60055 100%)"
    fallback_bg = "radial-gradient(circle at 50% 10%, #D8006C 0%, #A10054 45%, #6B0038 100%)"

if img_b64 and ui_theme == "Royal Magenta & Gold (Poster Match)":
    bg_rule = f"""
    .stApp, [data-testid="stAppViewContainer"] {{
        background: url("data:image/{ext};base64,{img_b64}") no-repeat center top fixed !important;
        background-size: cover !important;
        background-color: transparent !important;
    }}
    """
    spacer_height = "520px"
else:
    bg_rule = f"""
    .stApp, [data-testid="stAppViewContainer"] {{
        background: {fallback_bg} !important;
        background-color: transparent !important;
    }}
    """
    spacer_height = "30px"

anim_css = """
@keyframes goldGlaze {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), 0 0 12px rgba(255, 193, 7, 0.25); }
    50% { box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 24px rgba(255, 193, 7, 0.55); }
}
.portal-box {
    animation: pulseGlow 4s ease-in-out infinite;
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.portal-box:hover {
    transform: translateY(-3px);
}
.native-dl-btn, .zip-dl-btn {
    background-size: 200% 200% !important;
    animation: goldGlaze 4s ease infinite !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
.native-dl-btn:hover, .zip-dl-btn:hover {
    transform: translateY(-2px) scale(1.01) !important;
}
""" if enable_animations else ""

st.markdown(f"""
<style>
    {bg_rule}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    {anim_css}

    .hero-spacer {{
        height: {spacer_height};
        width: 100%;
    }}

    @media (max-width: 900px) {{
        .hero-spacer {{
            height: {"380px" if spacer_height == "520px" else "20px"};
        }}
    }}

    .block-container {{
        max-width: 980px !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }}

    .portal-box {{
        background: {card_bg} !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid {accent_primary};
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 18px;
        color: #FFFFFF;
    }}

    .portal-box-title {{
        color: #FFFFFF;
        font-size: 19px;
        font-weight: 800;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }}

    .portal-box-subtitle {{
        color: #F8B4D9;
        font-size: 13px;
        margin-bottom: 0px;
    }}

    [data-testid="stForm"] {{
        background: {card_bg} !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid {accent_primary} !important;
        border-radius: 18px !important;
        padding: 24px !important;
        color: #FFFFFF !important;
    }}

    [data-testid="stForm"] label {{
        color: {accent_secondary} !important;
        font-weight: 600 !important;
    }}

    [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.96);
        border-radius: 14px;
        padding: 12px;
        border: 2px dashed {accent_primary};
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    .stButton > button {{
        background: {btn_grad} !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 15.5px !important;
        letter-spacing: 0.5px !important;
        border: 1.5px solid {accent_primary} !important;
        border-radius: 30px !important;
        padding: 12px 24px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
        width: 100%;
    }}
    .stButton > button:hover {{
        border: 1.5px solid {accent_secondary} !important;
        box-shadow: 0 10px 28px rgba(255, 193, 7, 0.4) !important;
    }}

    .native-dl-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(135deg, #059669, #10B981, #047857);
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 15.5px;
        letter-spacing: 0.5px;
        text-decoration: none !important;
        border-radius: 30px;
        padding: 14px 24px;
        box-shadow: 0 8px 22px rgba(16, 185, 129, 0.4);
        margin-top: 10px;
        border: 1.5px solid rgba(255, 255, 255, 0.5);
    }}

    .zip-dl-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(135deg, #D97706, #F59E0B, #B45309);
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 15.5px;
        letter-spacing: 0.5px;
        text-decoration: none !important;
        border-radius: 30px;
        padding: 14px 24px;
        box-shadow: 0 8px 22px rgba(245, 158, 11, 0.4);
        margin-top: 10px;
        border: 1.5px solid rgba(255, 255, 255, 0.6);
    }}
</style>

<div class="hero-spacer"></div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. INTERACTIVE UPLOAD SECTION
# -------------------------------------------------------------
st.markdown("""
<div class="portal-box">
    <div class="portal-box-title">📂 Upload Citizen Application Bundle</div>
    <div class="portal-box-subtitle">Attach combined PDF documents (Aadhaar, Notary Affidavit / Death Cert, Bank Passbook, Hospital Discharge Summary & Bills)</div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose PDF Application Bundle",
    type=["pdf"],
    label_visibility="collapsed",
    help="Upload single combined PDF bundle containing all documents."
)

# -------------------------------------------------------------
# 4. PDF PAGE SPLITTER, <1MB COMPRESSOR & AUTOFILL PACKAGER
# -------------------------------------------------------------
def compress_single_page_pdf(writer_page) -> bytes:
    """Writes a single pypdf page to bytes and ensures size is strictly under 1MB for CMRF portal."""
    from pypdf import PdfWriter

    temp_writer = PdfWriter()
    temp_writer.add_page(writer_page)
    buf = io.BytesIO()
    temp_writer.write(buf)
    raw_bytes = buf.getvalue()

    if len(raw_bytes) <= 950 * 1024:
        return raw_bytes

    try:
        from PIL import Image
        comp_writer = PdfWriter()
        comp_writer.add_page(writer_page)
        for page in comp_writer
