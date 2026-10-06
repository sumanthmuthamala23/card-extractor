import os
import re
import json
import time
import base64
import datetime
import tempfile
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="CMRF Portal | Sumanth Muthamala",
    page_icon="🏛️",
    layout="centered"
)

# Sidebar: Backup API Key Input
with st.sidebar:
    st.markdown("### 🔑 API Key Management")
    st.caption("Paste a Gemini API key to override or test immediately.")
    user_custom_key = st.text_input("Temporary Backup Key", type="password", placeholder="AIzaSy... or AQ....")

# Convert profile image to base64 if present in repo
profile_img_html = ""
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as img_file:
        b64_profile = base64.b64encode(img_file.read()).decode()
        profile_img_html = f'<img class="profile-img" src="data:image/jpeg;base64,{b64_profile}" alt="Profile">'

# Load and encode custom background graphic if present
bg_css = ""
for bg_name in ["background.png", "background.jpg", "bg.png", "bg.jpg"]:
    if os.path.exists(bg_name):
        ext = "png" if bg_name.endswith(".png") else "jpeg"
        with open(bg_name, "rb") as bg_file:
            b64_bg = base64.b64encode(bg_file.read()).decode()
            bg_css = f"""
            .stApp {{
                background-image: url("data:image/{ext};base64,{b64_bg}") !important;
                background-size: cover !important;
                background-position: center top !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            """
        break

if not bg_css:
    bg_css = """
    .stApp {
        background: radial-gradient(circle at 50% 0%, #FFE6F0 0%, #FFF0F6 45%, #FDE4EF 100%) !important;
    }
    """

# Styling & Card Overlay System
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Alex+Brush&family=Great+Vibes&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    {bg_css}

    .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #2D3748;
    }}

    .hero-container {{
        background: linear-gradient(135deg, rgba(216, 0, 108, 0.94) 0%, rgba(230, 0, 118, 0.94) 40%, rgba(255, 20, 147, 0.92) 80%, rgba(255, 64, 129, 0.92) 100%);
        backdrop-filter: blur(10px);
        border-radius: 28px;
        padding: 34px 24px 28px;
        text-align: center;
        color: white;
        box-shadow: 0 16px 36px rgba(216, 0, 108, 0.32), 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }}

    .hero-container::before {{
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 160px;
        height: 160px;
        background: radial-gradient(circle
