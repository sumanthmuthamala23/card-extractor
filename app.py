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
# 3. MODULE 1: INTERACTIVE UPLOAD SECTION
# -------------------------------------------------------------
st.markdown("""
<div class="portal-box">
    <div class="portal-box-title">📂 Module 1: Upload Citizen Application Bundle</div>
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
        for page in comp_writer.pages:
            for img_file_obj in page.images:
                try:
                    pil_img = Image.open(io.BytesIO(img_file_obj.data))
                    if pil_img.mode in ("RGBA", "P"):
                        pil_img = pil_img.convert("RGB")
                    max_dim = 1600
                    if max(pil_img.size) > max_dim:
                        pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    img_out = io.BytesIO()
                    pil_img.save(img_out, format="JPEG", quality=65, optimize=True)
                    img_file_obj.replace(img_out.getvalue(), quality=65)
                except Exception:
                    pass
        comp_buf = io.BytesIO()
        comp_writer.write(comp_buf)
        return comp_buf.getvalue()
    except Exception:
        return raw_bytes

def build_autofill_helper_html(js_snippet: str, applicant_name: str) -> str:
    """Generates a zero-dependency Mac/Windows browser page with a 1-click Copy button."""
    escaped_js = (
        js_snippet.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CMRF Autofill Code - {applicant_name}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #140410; color: #fff; padding: 32px; max-width: 760px; margin: auto; }}
  .card {{ background: #24081d; border: 1.5px solid #FFC107; border-radius: 16px; padding: 24px; box-shadow: 0 12px 30px rgba(0,0,0,0.4); }}
  h2 {{ margin-top: 0; color: #FFC107; }}
  p {{ color: #f8b4d9; font-size: 14px; line-height: 1.5; }}
  button {{ background: linear-gradient(135deg, #059669, #10B981); color: #fff; border: none; padding: 14px 24px; font-size: 16px; font-weight: 700; border-radius: 30px; cursor: pointer; width: 100%; margin: 14px 0; }}
  button:hover {{ opacity: 0.92; }}
  pre {{ background: #0d020a; border: 1px solid #591645; padding: 16px; border-radius: 10px; overflow-x: auto; font-size: 13px; color: #A7F3D0; }}
</style>
</head>
<body>
  <div class="card">
    <h2>⚡ 1-Click CMRF Portal Autofill — {applicant_name}</h2>
    <p>1. Click the green button below to copy the code.<br>
       2. Open <b>cmrf.telangana.gov.in</b>, paste into your Console / Snippet (or run your bookmarklet), and click <b>Fill CMRF Portal</b>.</p>
    <button id="copyBtn" onclick="copyCode()">📋 Copy Autofill Code to Clipboard</button>
    <pre id="codeBlock">{escaped_js}</pre>
  </div>
  <script>
    function copyCode() {{
      const text = document.getElementById('codeBlock').innerText;
      navigator.clipboard.writeText(text).then(() => {{
        const btn = document.getElementById('copyBtn');
        btn.innerText = '✅ Copied! Ready to Paste into CMRF Portal';
        btn.style.background = '#D97706';
      }});
    }}
  </script>
</body>
</html>"""

def create_split_zip(
    bundle_bytes: bytes,
    applicant_slug: str = "CMRF_Bundle",
    proforma_pdf_bytes: bytes = None,
    proforma_filename: str = "00_CMRF_Application_Form.pdf",
    page_classifications: list = None,
    autofill_js_code: str = None,
    applicant_display_name: str = "Applicant"
) -> tuple[bytes, int]:
    """Splits a PDF bundle into individual <1MB pages and packages Proforma + Autofill files into a .zip."""
    from pypdf import PdfReader

    label_map = {}
    if page_classifications:
        for item in page_classifications:
            try:
                p_num = int(getattr(item, "page_number", 0))
                p_lbl = str(getattr(item, "document_type", "")).strip()
                if p_num > 0 and p_lbl:
                    label_map[p_num] = p_lbl
            except Exception:
                pass

    reader = PdfReader(io.BytesIO(bundle_bytes))
    total_pages = len(reader.pages)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if proforma_pdf_bytes:
            zf.writestr(f"00_{proforma_filename}", proforma_pdf_bytes)

        if autofill_js_code:
            zf.writestr(f"00_{applicant_slug}_Autofill_Code.txt", autofill_js_code.encode("utf-8"))
            helper_html = build_autofill_helper_html(autofill_js_code, applicant_display_name)
            zf.writestr(f"00_{applicant_slug}_Click_To_Copy_Autofill.html", helper_html.encode("utf-8"))

        for idx, page in enumerate(reader.pages, start=1):
            page_pdf_bytes = compress_single_page_pdf(page)
            label = ""
            if idx in label_map:
                safe_lbl = re.sub(r'[^a-zA-Z0-9_]', '_', label_map[idx])
                if safe_lbl:
                    label = f"_{safe_lbl}"
            filename = f"Page_{idx:02d}{label}.pdf"
            zf.writestr(filename, page_pdf_bytes)

    return zip_buffer.getvalue(), total_pages

# -------------------------------------------------------------
# 5. LAZY-LOADED AI EXTRACTION & LIVE MODEL AUTO-DISCOVERY
# -------------------------------------------------------------
def get_configured_api_keys(custom_key=""):
    found = []
    if custom_key and len(custom_key.strip()) > 10:
        found.append(custom_key.strip())
    try:
        if "GEMINI_API_KEYS" in st.secrets:
            val = st.secrets["GEMINI_API_KEYS"]
            if isinstance(val, list):
                found.extend([str(x).strip() for x in val if str(x).strip()])
            elif isinstance(val, str):
                cleaned = val.replace('"', '').replace("'", "").replace('[', '').replace(']', '')
                found.extend([p.strip() for p in cleaned.split(",") if p.strip()])
        elif "GEMINI_API_KEY" in st.secrets:
            found.append(str(st.secrets["GEMINI_API_KEY"]).strip())
    except Exception:
        pass
    for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        if k in os.environ and os.environ[k]:
            found.append(os.environ[k].strip())
    seen = set()
    return [k for k in found if len(k) > 15 and not (k in seen or seen.add(k))]

def get_schema():
    from pydantic import BaseModel, Field

    class PageLabel(BaseModel):
        page_number: int = Field(description="1-based page index in the PDF bundle (1, 2, 3...)")
        document_type: str = Field(description="Document type label: 'Aadhaar_Card', 'Ration_Card', 'Bank_Passbook', 'Discharge_Summary', 'Emergency_Certificate', 'IP_First_Bill', 'IP_Last_Bill', 'Essential_Certificate', 'Death_Certificate', or 'Supporting_Doc'")

    class CMRFData(BaseModel):
        is_deceased: bool = Field(description="True if applicant is deceased; False if alive")
        applicant_status: str = Field(description="Strictly 'DECEASED' or 'ALIVE'")
        name: str = Field(description="Patient / Beneficiary name strictly as per Aadhaar (with surname)")
        age: str = Field(description="Derived strictly from Aadhaar DOB/YOB relative to 2026. Format '<number> Yrs'")
        gender: str = Field(description="Strictly 'Male' or 'Female'")
        relationship: str = Field(description="Father or Husband name")
        aadhaar_no: str = Field(description="12-digit Aadhaar number")
        district: str = Field(description="District name")
        mandal: str = Field(description="Mandal name")
        village: str = Field(description="Village name")
        address: str = Field(description="Permanent address from Aadhaar")
        pincode: str = Field(description="Pincode")
        mobile_no: str = Field(description="Contact phone number")
        fsc_no: str = Field(description="White Ration Card / New Food Security Card (FSC) number")
        nominee_name: str = Field(description="Name of Nominee / Legal Heir if deceased")
        nominee_relation: str = Field(description="Nominee relation to deceased")
        bank_name: str = Field(description="Bank name from passbook front page")
        bank_district: str = Field(description="Bank District")
        branch: str = Field(description="Bank branch location name")
        ifsc: str = Field(description="IFSC code strictly from passbook")
        account_no: str = Field(description="Verbatim bank account number digits. Never extract CIF number or phone.")
        bank_holder_name: str = Field(description="Account holder name from passbook")
        hospital_name: str = Field(description="Hospital name and address from letterhead")
        surgery_date: str = Field(description="Surgery or admission date (DD/MM/YYYY or 'N/A')")
        ip_no: str = Field(description="IP Number")
        bill_no: str = Field(description="Bill / ADM Number")
        treatment_diagnosis: str = Field(description="Disease or diagnosis for seeking assistance")
        amount: str = Field(description="Estimated / Requested Total Amount")
        prior_cmrf_sanction: str = Field(default="NIL", description="Prior assistance details or 'NIL'")
        page_classifications: list[PageLabel] = Field(
            default_factory=list,
            description="List mapping each 1-based page_number to its document_type label"
        )
    return CMRFData

def get_live_models_for_client(client) -> list[str]:
    """Queries live stable text/multimodal Gemini models, excluding 0-quota preview/image models."""
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-pro",
    ]
    blocked_keywords = ("embedding", "imagen", "veo", "image", "tts", "audio", "robotics", "computer-use")
    try:
        available = []
        for m in client.models.list():
            m_name = getattr(m, "name", "") or ""
            if m_name.startswith("models/"):
                m_name = m_name.replace("models/", "", 1)
            actions = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            if "gemini" in m_name and not any(b in m_name.lower() for b in blocked_keywords):
                if not actions or "generateContent" in actions:
                    available.append(m_name)

        ordered = [p for p in preferred if p in available]
        extras = [a for a in available if a not in ordered and "preview" not in a.lower() and ("flash" in a or "pro" in a)]
        combined = ordered + extras
        if combined:
            return combined[:6]
    except Exception:
        pass
    return preferred

def extract_bundle(file_bytes: bytes, status_box, custom_key=""):
    from google import genai
    from google.genai import types

    CMRFData = get_schema()
    keys = get_configured_api_keys(custom_key)
    if not keys:
        raise RuntimeError("No Gemini API keys found. Please paste a valid key in the sidebar or in Streamlit Secrets.")

    prompt = """
    Analyze all attached documents for this CMRF application bundle:
    1. STRICT AGE: Derive age strictly from Aadhaar DOB/YOB relative to 2026. Format: '<number> Yrs'.
    2. STATUS: Determine if DECEASED or ALIVE.
    3. DETAILS: Extract patient name (with surname), Aadhaar No, Ration card (FSC) No, mobile number, and address.
    4. BANK PASSBOOK: Extract exact account number digits from passbook. Do NOT confuse with CIF or phone. Extract IFSC, Bank Name, Branch, Holder Name.
    5. MEDICAL: Hospital name/address, admission/surgery date, diagnosis, and total estimation amount.
    6. PAGE CLASSIFICATIONS: For every page (1, 2, 3...), add an entry in `page_classifications` with `page_number` and `document_type` ('Aadhaar_Card', 'Ration_Card', 'Bank_Passbook', 'Discharge_Summary', 'Emergency_Certificate', 'IP_First_Bill', 'IP_Last_Bill', 'Essential_Certificate', 'Death_Certificate', or 'Hospital_Bill').
    """

    is_large = len(file_bytes) > (15 * 1024 * 1024)
    tmp_path = None
    if is_large:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

    try:
        last_error = None
        for round_num in range(2):
            for key_idx, key in enumerate(keys):
                client = genai.Client(api_key=key)
                models = get_live_models_for_client(client)

                if is_large:
                    status_box.info(f"📤 Uploading document ({len(file_bytes)/(1024*1024):.1f} MB)...")
                    up = client.files.upload(file=tmp_path)
                    while up.state.name == "PROCESSING":
                        time.sleep(2)
                        up = client.files.get(name=up.name)
                    payload = [up, prompt]
                else:
                    part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                    payload = [part, prompt]

                for model_name in models:
                    status_box.info(f"✨ Analyzing via Slot #{key_idx + 1} [{model_name}]...")
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=payload,
                            config=types.GenerateContentConfig(
                                temperature=0.0,
                                response_mime_type="application/json",
                                response_schema=CMRFData,
                            ),
                        )
                        return CMRFData.model_validate_json(resp.text)
                    except Exception as e:
                        last_error = e
                        err = str(e).lower()
                        if any(x in err for x in ["401", "unauthenticated", "access_token_type_unsupported"]):
                            break
                        elif any(x in err for x in ["429", "quota", "resource_exhausted", "503", "unavailable", "high demand", "overloaded", "404", "not found"]):
                            status_box.warning(f"{model_name} unavailable/quota-limited. Trying next model...")
                            time.sleep(1)
                            continue
                        else:
                            continue
            if round_num == 0:
                status_box.warning("⏳ High traffic across servers. Retrying rotation pass in 3 seconds...")
                time.sleep(3)

        raise last_error if last_error else RuntimeError("Servers are experiencing heavy demand. Please try again in a moment.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# -------------------------------------------------------------
# 6. HIGH-LEGIBILITY PROPORTIONAL SINGLE-PAGE A4 PROFORMA
# -------------------------------------------------------------
def build_pdf(data, output_path: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    serif_reg, serif_bld = "Times-Roman", "Times-Bold"
    for ttf in ["BOOKOS.TTF", "Bookman.ttf", "bookman.ttf", "BookmanOldStyle.ttf"]:
        if os.path.exists(ttf):
            try:
                pdfmetrics.registerFont(TTFont("BookmanOldStyle", ttf))
                serif_reg = serif_bld = "BookmanOldStyle"
                break
            except Exception:
                pass

    PAGE_W = 543
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=26,
        rightMargin=26,
        topMargin=14,
        bottomMargin=12
    )
    styles = getSampleStyleSheet()

    hdr_s = ParagraphStyle('Hdr', parent=styles['Normal'], fontName=serif_bld, fontSize=13, alignment=1, leading=17)
    box_s = ParagraphStyle('Box', parent=styles['Normal'], fontName=serif_bld, fontSize=10, alignment=1, leading=14)
    to_s = ParagraphStyle('To', parent=styles['Normal'], fontName=serif_bld, fontSize=11, leading=15)
    lbl_s = ParagraphStyle('Lbl', parent=styles['Normal'], fontName=serif_bld, fontSize=10.5, leading=14.5)
    val_s = ParagraphStyle('Val', parent=styles['Normal'], fontName=serif_reg, fontSize=10.5, leading=14.5)
    bld_s = ParagraphStyle('Bld', parent=styles['Normal'], fontName=serif_bld, fontSize=10.5, leading=14.5)
    dec_s = ParagraphStyle('Dec', parent=styles['Normal'], fontName=serif_reg, fontSize=10, leading=13.5)
    enc_s = ParagraphStyle('Enc', parent=styles['Normal'], fontName=serif_reg, fontSize=9, leading=12)

    header_table = Table([
        [
            Paragraph("<b>PROFORMA-cum-REQUISITION<br/>FOR SEEKING FINANCIAL ASSISTANCE<br/>FOR MEDICAL TREATMENT/EXGRATIA UNDER<br/>\"CHIEF MINISTER'S RELIEF FUND\"</b>", hdr_s),
            Paragraph("<br/><br/><b>Affix Latest<br/>Passport Size<br/>Photo</b>", box_s)
        ]
    ], colWidths=[444, 99], rowHeights=[120])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (1,0), (1,0), 1.2, colors.black),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))

    to_table = Table([[Paragraph("<b>To<br/>The Hon'ble Chief Minister,<br/>Govt. of Telangana,<br/>Hyderabad.</b>", to_s)]], colWidths=[PAGE_W])
    to_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    deceased_tag = " <font color='#D32F2F'><b>[DECEASED]</b></font>" if data.is_deceased else ""
    full_name = f"{data.name}{deceased_tag}"
    clean_acc = re.sub(r'[^0-9]', '', str(data.account_no)).strip() or str(data.account_no).strip()
    surg_val = data.surgery_date.strip() if (data.surgery_date and data.surgery_date.upper() != "N/A") else "As per Hospital Records / Admission"
    nominee_suf = f" ({data.nominee_relation})" if (data.is_deceased and data.nominee_relation) else ""
    holder_name = f"{data.bank_holder_name}{nominee_suf}" if data.bank_holder_name else data.name
    rel_clean = re.sub(r'^(S/O|W/O|D/O)\s*[:.\-]?\s*', '', data.relationship, flags=re.IGNORECASE).strip() or data.relationship

    rows = [
        [Paragraph("01. Name of Patient/Beneficiary<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(with Surname)", lbl_s), ":", Paragraph(f"<b>{full_name}</b>", bld_s)],
        [Paragraph("02. Father's/Husband's Name", lbl_s), ":", Paragraph(rel_clean, val_s)],
        [Paragraph("03. Age", lbl_s), ":", Paragraph(f"<b>{data.age}</b>", bld_s)],
        [Paragraph("04. Contact Number", lbl_s), ":", Paragraph(data.mobile_no, val_s)],
        [Paragraph("05. White Ration Card (FSC) No", lbl_s), ":", Paragraph(f"<b>{data.fsc_no}</b>", bld_s)],
        [Paragraph("06. Aadhar card Number", lbl_s), ":", Paragraph(f"<b>{data.aadhaar_no}</b>", bld_s)],
        [Paragraph("07. Permanent Address", lbl_s), ":", Paragraph(f"{data.address} - {data.pincode}", val_s)],
        [Paragraph("08. Address for Correspondence", lbl_s), ":", Paragraph(f"H.No: {data.village}, {data.mandal} Mandal, {data.district} Dist - {data.pincode}", val_s)],
        [
            Paragraph("09. Bank Details<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(IFSC, Bank Name, Branch,<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name of A/c Holder & A/c No.)", lbl_s),
            ":",
            Paragraph(
                f"<b>Name of Account Holder:</b> {holder_name}<br/>"
                f"<b>Account Number:</b> {clean_acc}<br/>"
                f"<b>Bank Name & Branch:</b> {data.bank
