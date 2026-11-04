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

# 1. Cached Asset Loader
@st.cache_data(show_spinner=False)
def load_assets():
    profile_html = ""
    if os.path.exists("profile.jpg"):
        with open("profile.jpg", "rb") as img_file:
            b64_p = base64.b64encode(img_file.read()).decode()
            profile_html = f'<img class="profile-img" src="data:image/jpeg;base64,{b64_p}" alt="Profile">'

    bg_css_val = ""
    for bg_name in ["background.png", "background.jpg", "bg.png", "bg.jpg"]:
        if os.path.exists(bg_name):
            ext = "png" if bg_name.endswith(".png") else "jpeg"
            with open(bg_name, "rb") as bg_f:
                b64_b = base64.b64encode(bg_f.read()).decode()
                bg_css_val = f"""
                .stApp {{
                    background-image: url("data:image/{ext};base64,{b64_b}") !important;
                    background-size: cover !important;
                    background-position: center top !important;
                    background-repeat: no-repeat !important;
                    background-attachment: fixed !important;
                }}
                """
            break

    if not bg_css_val:
        bg_css_val = """
        .stApp {
            background: radial-gradient(circle at 50% 0%, #FFE6F0 0%, #FFF0F6 45%, #FDE4EF 100%) !important;
        }
        """
    return profile_html, bg_css_val

profile_img_html, bg_css = load_assets()

# Sidebar: Backup API Key Input
with st.sidebar:
    st.markdown("### 🔑 API Key Management")
    st.caption("Paste a Gemini API key to override or test immediately.")
    user_custom_key = st.text_input("Temporary Backup Key", type="password", placeholder="AIzaSy... or AQ....")

# Styling & Card Overlay System
custom_style = f"""
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
        background: radial-gradient(circle, rgba(255,255,255,0.22) 0%, transparent 70%);
        border-radius: 50%;
    }}

    .profile-img {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        object-position: top;
        border: 4.5px solid #FFFFFF;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
        margin-bottom: 12px;
        transition: transform 0.25s ease;
    }}
    .profile-img:hover {{
        transform: scale(1.03);
    }}

    .calligraphy-name {{
        font-family: 'Alex Brush', 'Great Vibes', cursive;
        font-size: 52px;
        font-weight: 400;
        color: #FFFFFF;
        text-shadow: 0 3px 10px rgba(0, 0, 0, 0.28);
        margin: 0;
        line-height: 1.15;
        letter-spacing: 0.5px;
    }}

    .hero-subtitle {{
        font-size: 13.5px;
        font-weight: 700;
        letter-spacing: 2.2px;
        text-transform: uppercase;
        color: #FFF5F9;
        margin-top: 6px;
        opacity: 0.96;
    }}

    .portal-pill {{
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(8px);
        padding: 6px 18px;
        border-radius: 30px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 14px;
        border: 1px solid rgba(255, 255, 255, 0.45);
        letter-spacing: 0.5px;
    }}

    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 22px;
    }}

    .feature-card {{
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 14px 12px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(224, 6, 118, 0.1);
        border: 1px solid rgba(224, 6, 118, 0.16);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .feature-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(224, 6, 118, 0.18);
    }}

    .feature-icon {{
        font-size: 20px;
        margin-bottom: 4px;
    }}

    .feature-title {{
        font-size: 11.5px;
        font-weight: 800;
        color: #B8005A;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .feature-desc {{
        font-size: 11px;
        color: #64748B;
        margin-top: 2px;
        font-weight: 500;
    }}

    .section-header-card {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-radius: 18px;
        padding: 16px 20px;
        border-left: 6px solid #E00676;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        margin-bottom: 18px;
    }}

    .section-title {{
        font-size: 18px;
        font-weight: 800;
        color: #1E293B;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .section-subtitle {{
        font-size: 12.5px;
        color: #64748B;
        margin-top: 4px;
        margin-bottom: 0;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, #D8006C 0%, #FF1493 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16.5px !important;
        letter-spacing: 0.5px !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        border: none !important;
        box-shadow: 0 8px 22px rgba(216, 0, 108, 0.38) !important;
        width: 100%;
        transition: all 0.2s ease !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px rgba(216, 0, 108, 0.48) !important;
    }}

    .stDownloadButton > button {{
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        border: none !important;
        box-shadow: 0 8px 22px rgba(16, 185, 129, 0.35) !important;
        width: 100%;
    }}

    .security-badge {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(8px);
        border: 1px dashed rgba(216, 0, 108, 0.35);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        font-size: 12px;
        font-weight: 600;
        color: #831843;
        margin-top: 14px;
    }}
</style>

<!-- Hero Section -->
<div class="hero-container">
    {profile_img_html}
    <h1 class="calligraphy-name">Sumanth Muthamala</h1>
    <div class="hero-subtitle">Chief Minister's Relief Fund (CMRF)</div>
    <div class="portal-pill">⚡ AI-Powered Automated Processing System</div>
</div>

<!-- Key Highlights -->
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">📑</div>
        <div class="feature-title">Smart OCR</div>
        <div class="feature-desc">Faint Dot-Matrix Passbook Enhanced</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🛡️</div>
        <div class="feature-title">Official Proforma</div>
        <div class="feature-desc">With Bank Account Details Included</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🖨️</div>
        <div class="feature-title">Print Ready</div>
        <div class="feature-desc">100% Scaled Single-Page A4 PDF</div>
    </div>
</div>

<!-- Upload Header -->
<div class="section-header-card">
    <div class="section-title">📂 Upload Citizen Application Bundle</div>
    <p class="section-subtitle">Attach combined PDF documents (Aadhaar, Notary Affidavit / Death Cert, Bank Passbook, Hospital Discharge Summary & Bills)</p>
</div>
"""

st.markdown(custom_style, unsafe_allow_html=True)

# 2. Structured Data Schema
class CMRFData(BaseModel):
    is_deceased: bool = Field(description="True if applicant/patient is deceased; False if alive")
    applicant_status: str = Field(description="Strictly 'DECEASED' if deceased, otherwise 'ALIVE'")
    name: str = Field(description="Name strictly as per Aadhaar card of the patient / deceased applicant (with Surname)")
    age: str = Field(description="Patient age strictly calculated from the Aadhaar card Date of Birth (DOB) or Year of Birth (YOB) relative to current year 2026. Format strictly as '<number> Yrs' (e.g., '52 Yrs'). Do NOT use hospital document age.")
    gender: str = Field(description="Patient gender strictly 'Male' or 'Female'")
    relationship: str = Field(description="Father or Husband name of the patient")
    aadhaar_no: str = Field(description="12-digit Aadhaar number of patient / deceased")
    district: str = Field(description="District name")
    mandal: str = Field(description="Mandal name")
    village: str = Field(description="Village name")
    address: str = Field(description="Full permanent address from Aadhaar card")
    pincode: str = Field(description="Pincode")
    mobile_no: str = Field(description="Contact / Mobile number of patient / beneficiary / nominee")
    fsc_no: str = Field(description="White Ration Card / New Food Security Card (FSC) number")
    nominee_name: str = Field(description="Name of Nominee / Legal Heir from Lawyer Notary / Passbook (if deceased)")
    nominee_relation: str = Field(description="Relation of Nominee to Deceased (e.g., Wife, Son, Husband)")
    bank_name: str = Field(description="Bank name strictly from the Bank Passbook front page")
    bank_district: str = Field(description="Bank District")
    branch: str = Field(description="Bank branch location name strictly from Bank Passbook (e.g., Khammam, Sattupalli). Never put medical diagnoses or procedures here.")
    ifsc: str = Field(description="IFSC code strictly from the Bank Passbook")
    account_no: str = Field(
        description="Bank Account Number strictly as printed next to 'Account No' or 'A/c No' on the Bank Passbook. Must be the exact verbatim digits. Do NOT confuse with CIF Number or Customer ID."
    )
    bank_holder_name: str = Field(description="Account Holder Name as printed on Bank Passbook")
    hospital_name: str = Field(description="Name & Address of Hospital with Phone/Fax Number from letterhead")
    surgery_date: str = Field(description="Date of Surgery / Operation / Admission Date (DD/MM/YYYY or 'N/A')")
    ip_no: str = Field(description="Patient IP Number")
    bill_no: str = Field(description="Bill / ADM Number")
    treatment_diagnosis: str = Field(description="Name of Disease / Purpose for seeking exgratia / financial assistance")
    amount: str = Field(description="Estimated / Requested Total Amount as per Essentiality Certificate")
    prior_cmrf_sanction: str = Field(default="NIL", description="Details if any amount was previously sanctioned under CMRF or other source, else 'NIL'")

def get_api_keys():
    found_keys = []
    if user_custom_key and len(user_custom_key.strip()) > 10:
        found_keys.append(user_custom_key.strip())
        
    try:
        if "GEMINI_API_KEYS" in st.secrets:
            val = st.secrets["GEMINI_API_KEYS"]
            if isinstance(val, list):
                found_keys.extend([str(x).strip() for x in val if str(x).strip()])
            elif isinstance(val, str):
                cleaned = val.replace('"', '').replace("'", "").replace('[', '').replace(']', '')
                for piece in cleaned.split(","):
                    if piece.strip():
                        found_keys.append(piece.strip())
        elif "GEMINI_API_KEY" in st.secrets:
            found_keys.append(str(st.secrets["GEMINI_API_KEY"]).strip())
    except Exception:
        pass

    for env_k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        if env_k in os.environ and os.environ[env_k]:
            found_keys.append(os.environ[env_k].strip())

    valid_keys = []
    seen = set()
    for k in found_keys:
        k_clean = k.strip()
        if len(k_clean) > 15 and k_clean not in seen:
            seen.add(k_clean)
            valid_keys.append(k_clean)

    return valid_keys

# 3. Resilient Multi-Model Extraction Engine (Supports both small & large files with state polling)
def extract_data_from_file(file_bytes: bytes, status_box) -> CMRFData:
    keys = get_api_keys()
    if not keys:
        raise RuntimeError("No Gemini API keys found. Please paste a valid key in the sidebar or in Streamlit Secrets.")

    prompt = """
    Carefully analyze all attached documents for this CMRF application bundle:
    
    1. STRICT AGE CALCULATION RULE:
       - Locate the Aadhaar Card of the applicant/patient.
       - Look for Date of Birth (DOB) or Year of Birth (YOB) printed on Aadhaar.
       - Calculate exact age relative to current year (2026).
         * Example: If DOB is 15/08/1974 -> 2026 - 1974 = 52 Yrs.
         * Example: If 'Year of Birth: 1968' -> 2026 - 1968 = 58 Yrs.
       - CRITICAL: Never take the age written on Hospital bills or discharge summaries. Derive age exclusively from Aadhaar.

    2. DETERMINE STATUS & GENDER:
       - Set is_deceased = True and applicant_status = 'DECEASED' if deceased (affidavit/death cert present), else False and 'ALIVE'.
       - Identify patient gender ('Male' or 'Female').

    3. PATIENT DETAILS:
       - Name: strictly as per Aadhaar card (with Surname).
       - Relationship: Father or Husband name from Aadhaar card.
       - Aadhaar No: 12-digit number of patient/deceased.
       - District, Mandal, Village, Full Permanent Address, Pincode: strictly from Aadhaar card.
       - Mobile Number: from documents / ration card / nominee.
       - New FSC No: White Ration Card Number / Food Security Card number.

    4. HIGH-PRECISION BANK PASSBOOK & ACCOUNT NUMBER EXTRACTION:
       - Find the Bank Passbook page (first page / front cover).
       - PASSBOOK CHARACTERISTICS: Indian bank passbooks (especially State Bank of India - SBI, Telangana Grameena Bank, Union Bank) use faint, low-contrast dot-matrix pin printing.
       - DO NOT CONFUSE 'CIF Number' WITH 'Account No'. The line labeled 'CIF Number' contains a customer identifier. Look strictly for the label: 'Account No.', 'A/c No.', or 'SB Account No.'.
       - CRITICAL DOT-MATRIX CLARITY: In faint dot-matrix printing:
         * Do NOT confuse the digit '1' with '2'.
         * Do NOT confuse '8' with '0' or '2'.
         * Look closely at the dot pattern: read each single digit of the Account Number with maximum optical fidelity.
       - Extract Bank Name, Branch location (e.g. Sattupalli, Khammam), IFSC code, and printed Account Holder Name.

    5. HOSPITAL & SURGERY DETAILS:
       - Hospital Name, Address with Phone/Fax from letterhead.
       - Date of Surgery/Operation/Admission: extract date or format as DD/MM/YYYY.
       - Treatment / Disease / Purpose for seeking assistance.
       - Estimated / Requested Total Amount as per Essentiality Certificate.
       - Prior CMRF sanction: if mentioned in documents, else 'NIL'.
    """

    # If file is over 15MB, write to temporary file to prevent memory crash
    is_large = len(file_bytes) > (15 * 1024 * 1024)
    tmp_path = None
    if is_large:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

    MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.6-flash"]

    try:
        last_error = None
        for key_idx, current_key in enumerate(keys):
            client = genai.Client(api_key=current_key)
            
            # Prepare file payload
            content_payload = None
            if is_large:
                status_box.info(f"📤 Uploading large bundle ({len(file_bytes)/(1024*1024):.1f} MB) to Google AI Engine...")
                uploaded_file = client.files.upload(file=tmp_path)
                
                # Poll until file is ACTIVE
                status_box.info("⏳ Processing large document pages...")
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                
                if uploaded_file.state.name == "FAILED":
                    raise RuntimeError("Google File API failed to process the large PDF. Please try a compressed copy.")
                content_payload = [uploaded_file, prompt]
            else:
                pdf_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                content_payload = [pdf_part, prompt]

            for model_name in MODELS_TO_TRY:
                status_box.info(f"✨ Analyzing application via Slot #{key_idx + 1}/{len(keys)} [{model_name}]...")
                
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=content_payload,
                            config=types.GenerateContentConfig(
                                temperature=0.0,
                                response_mime_type="application/json",
                                response_schema=CMRFData,
                            ),
                        )
                        return CMRFData.model_validate_json(response.text)
                    except BaseException as e:
                        last_error = e
                        err_msg = str(e).lower()

                        if any(x in err_msg for x in ["401", "unauthenticated", "invalid authentication", "access_token_type_unsupported"]):
                            status_box.warning(f"Key Slot #{key_idx + 1} rejected. Switching to next key...")
                            break

                        elif any(x in err_msg for x in ["429", "resource_exhausted", "quota"]):
                            status_box.warning(f"Key Slot #{key_idx + 1} reached quota on {model_name}. Trying next key...")
                            time.sleep(1)
                            break

                        elif any(x in err_msg for x in ["503", "unavailable", "high demand", "overloaded"]):
                            pause_sec = (attempt + 1) * 3
                            status_box.warning(f"{model_name} busy (503). Retrying in {pause_sec}s (Attempt {attempt + 1}/3)...")
                            time.sleep(pause_sec)
                            continue
                        else:
                            break

        raise last_error if last_error else RuntimeError("All configured keys and fallback models exhausted. Please try again.")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# 4. Cached Font Configuration
@st.cache_resource(show_spinner=False)
def register_fonts():
    reg = "Times-Roman"
    bld = "Times-Bold"
    for ttf_candidate in ["BOOKOS.TTF", "Bookman.ttf", "bookman.ttf", "BookmanOldStyle.ttf", "BOOKOSB.TTF"]:
        if os.path.exists(ttf_candidate):
            try:
                pdfmetrics.registerFont(TTFont("BookmanOldStyle", ttf_candidate))
                reg = "BookmanOldStyle"
                bld = "BookmanOldStyle"
                break
            except Exception:
                pass
    return reg, bld

SERIF_REGULAR, SERIF_BOLD = register_fonts()

# 5. Proforma PDF Generator
def generate_cmrf_pdf(data: CMRFData, output_pdf_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=22,
        rightMargin=22,
        topMargin=12,
        bottomMargin=12
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=12.5, alignment=1, leading=16)
    photo_box_style = ParagraphStyle('PhotoBoxStyle', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=10, alignment=1, leading=14)
    to_style = ParagraphStyle('ToStyle', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=10.5, leading=14.5)
    item_num_lbl = ParagraphStyle('ItemNumLbl', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=10, leading=13)
    colon_style = ParagraphStyle('ColonStyle', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=10, alignment=1, leading=13)
    val_style = ParagraphStyle('ValStyle', parent=styles['Normal'], fontName=SERIF_REGULAR, fontSize=10, leading=13)
    val_bold = ParagraphStyle('ValBold', parent=styles['Normal'], fontName=SERIF_BOLD, fontSize=10, leading=13)
    dec_style = ParagraphStyle('DecStyle', parent=styles['Normal'], fontName=SERIF_REGULAR, fontSize=9.5, alignment=0, leading=12.5)
    encl_style = ParagraphStyle('EnclStyle', parent=styles['Normal'], fontName=SERIF_REGULAR, fontSize=8.5, leading=11)

    hdr_text = (
        "<b>PROFORMA-cum-REQUISITION<br/>"
        "FOR SEEKING FINANCIAL ASSISTANCE<br/>"
        "FOR MEDICAL TREATMENT/EXGRATIA UNDER<br/>"
        "\"CHIEF MINISTER'S RELIEF FUND\"</b>"
    )
    photo_box_text = "<br/><br/><b>Affix Latest<br/>Passport Size<br/>Photo</b>"
    
    header_table = Table([[Paragraph(hdr_text, header_style), Paragraph(photo_box_text, photo_box_style)]], colWidths=[452, 99], rowHeights=[120])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('BOX', (1, 0), (1, 0), 1.2, colors.black),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (1, 0), (1, 0), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))

    to_text = "<b>To<br/>The Hon'ble Chief Minister,<br/>Govt. of Telangana,<br/>Hyderabad.</b>"
    to_table = Table([[Paragraph(to_text, to_style)]], colWidths=[551])
    to_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    deceased_tag = " <font color='#D32F2F'><b>[DECEASED]</b></font>" if (data.is_deceased or "DECEASED" in data.applicant_status.upper()) else ""
