import os
import re
import json
import tempfile
import time
import base64
import datetime
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

    /* Hero Card with Glassmorphic Pink Backdrop */
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
        <div class="feature-desc">Extracts Aadhaar, Bills & Bank data</div>
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
""", unsafe_allow_html=True)

# 1. Structured Data Schema
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
    bank_name: str = Field(description="Bank name from passbook")
    bank_district: str = Field(description="Bank District")
    branch: str = Field(description="Bank branch location name strictly from Bank Passbook (e.g., Khammam, Mudigonda). Never put medical diagnoses or procedures here.")
    ifsc: str = Field(description="IFSC code")
    account_no: str = Field(description="Bank Account number")
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

    return [k for k in found_keys if len(k) > 10]

# 2. Resilient Multimodal Extraction Engine with Active Model Redundancy & Backoff
def extract_data_from_file(file_bytes: bytes, status_box) -> CMRFData:
    keys = get_api_keys()
    if not keys:
        raise RuntimeError("No Gemini API keys configured. Please add your key in Streamlit Secrets.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

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

    4. BANK & NOMINEE DETAILS:
       - Bank Name, District, Branch Name (strictly bank branch location from passbook, NEVER medical procedures), IFSC, Account Number, Account Holder Name.
       - Nominee Name and Nominee Relation to deceased (if applicable).

    5. HOSPITAL & SURGERY DETAILS:
       - Hospital Name, Address with Phone/Fax from letterhead.
       - Date of Surgery/Operation/Admission: extract date or format as DD/MM/YYYY.
       - Treatment / Disease / Purpose for seeking assistance.
       - Estimated / Requested Total Amount as per Essentiality Certificate.
       - Prior CMRF sanction: if mentioned in documents, else 'NIL'.
    """

    # Active endpoints supported for generateContent with structured schemas
    ACTIVE_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

    try:
        last_error = None
        for key_idx, current_key in enumerate(keys):
            client = genai.Client(api_key=current_key)
            status_box.info(f"✨ Connecting to Engine Slot #{key_idx + 1}/{len(keys)}...")
            
            for model_name in ACTIVE_MODELS:
                for retry in range(3):
                    try:
                        uploaded_file = client.files.upload(file=tmp_path)
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[uploaded_file, prompt],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=CMRFData,
                            ),
                        )
                        return CMRFData.model_validate_json(response.text)
                    except BaseException as e:
                        last_error = e
                        err_msg = str(e).lower()

                        # 429 Quota exhausted -> immediately rotate to next API key
                        if any(x in err_msg for x in ["429", "resource_exhausted", "quota"]):
                            if key_idx < len(keys) - 1:
                                status_box.warning(f"Key Slot #{key_idx + 1} reached quota. Switching to Key #{key_idx + 2}...")
                                time.sleep(1)
                            break

                        # 503 Server Demand Spike -> exponential pause and retry
                        elif any(x in err_msg for x in ["503", "unavailable", "high demand", "overloaded"]):
                            pause_sec = (retry + 1) * 2
                            status_box.warning(f"Server demand spike (503). Retrying in {pause_sec}s with {model_name}...")
                            time.sleep(pause_sec)
                            continue
                        else:
                            break

        raise last_error if last_error else RuntimeError("All configured keys exhausted. Please try again.")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# 3. Dynamic Font Configuration (Bookman Old Style / Classic Serif)
SERIF_REGULAR = "Times-Roman"
SERIF_BOLD = "Times-Bold"

for ttf_candidate in ["BOOKOS.TTF", "Bookman.ttf", "bookman.ttf", "BookmanOldStyle.ttf", "BOOKOSB.TTF"]:
    if os.path.exists(ttf_candidate):
        try:
            pdfmetrics.registerFont(TTFont("BookmanOldStyle", ttf_candidate))
            SERIF_REGULAR = "BookmanOldStyle"
            SERIF_BOLD = "BookmanOldStyle"
            break
        except Exception:
            pass

# 4. Proforma PDF Generator with Bank Details & Standard Passport Photo Dimensions
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

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=12.5,
        alignment=1,
        leading=16
    )
    
    photo_box_style = ParagraphStyle(
        'PhotoBoxStyle',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=10,
        alignment=1,
        leading=14
    )

    to_style = ParagraphStyle(
        'ToStyle',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=10.5,
        leading=14.5
    )

    item_num_lbl = ParagraphStyle(
        'ItemNumLbl',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=10,
        leading=13
    )

    colon_style = ParagraphStyle(
        'ColonStyle',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=10,
        alignment=1,
        leading=13
    )

    val_style = ParagraphStyle(
        'ValStyle',
        parent=styles['Normal'],
        fontName=SERIF_REGULAR,
        fontSize=10,
        leading=13
    )

    val_bold = ParagraphStyle(
        'ValBold',
        parent=styles['Normal'],
        fontName=SERIF_BOLD,
        fontSize=10,
        leading=13
    )

    dec_style = ParagraphStyle(
        'DecStyle',
        parent=styles['Normal'],
        fontName=SERIF_REGULAR,
        fontSize=9.5,
        alignment=0,
        leading=12.5
    )

    encl_style = ParagraphStyle(
        'EnclStyle',
        parent=styles['Normal'],
        fontName=SERIF_REGULAR,
        fontSize=8.5,
        leading=11
    )

    # 1. Header Grid with Standard Passport Photo Box (35mm x 45mm ~ 99pt x 128pt)
    hdr_text = (
        "<b>PROFORMA-cum-REQUISITION<br/>"
        "FOR SEEKING FINANCIAL ASSISTANCE<br/>"
        "FOR MEDICAL TREATMENT/EXGRATIA UNDER<br/>"
        "\"CHIEF MINISTER'S RELIEF FUND\"</b>"
    )
    
    photo_box_text = "<br/><br/><b>Affix Latest<br/>Passport Size<br/>Photo</b>"
    
    header_table_data = [
        [Paragraph(hdr_text, header_style), Paragraph(photo_box_text, photo_box_style)]
    ]
    header_table = Table(header_table_data, colWidths=[452, 99], rowHeights=[120])
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

    # 2. Addressee Block
    to_text = (
        "<b>To<br/>"
        "The Hon'ble Chief Minister,<br/>"
        "Govt. of Telangana,<br/>"
        "Hyderabad.</b>"
    )
    to_table_data = [[Paragraph(to_text, to_style)]]
    to_table = Table(to_table_data, colWidths=[551])
    to_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    # 3. Numbered Items Table (Bank Details Included above Disease)
    deceased_tag = " <font color='#D32F2F'><b>[DECEASED]</b></font>" if (data.is_deceased or "DECEASED" in data.applicant_status.upper()) else ""
    full_name_display = f"{data.name}{deceased_tag}"
    rel_name = re.sub(r'^(S/O|W/O|D/O)\s*[:.\-]?\s*', '', data.relationship, flags=re.IGNORECASE).strip()
    
    clean_branch_data = data.branch.strip()
    if any(term in clean_branch_data.lower() for term in ["surgery", "pciol", "cataract", "hospital", "patient", "fistula"]):
        clean_branch_data = data.district.strip()

    nominee_suffix = f" ({data.nominee_relation})" if (data.is_deceased and data.nominee_relation) else ""
    holder_display = f"{data.bank_holder_name}{nominee_suffix}" if data.bank_holder_name else data.name

    clean_hosp = f"{data.hospital_name}"
    surg_date_val = data.surgery_date.strip() if (data.surgery_date and data.surgery_date.strip().upper() != "N/A") else "As per Hospital Records / Admission"
    prior_sanction = data.prior_cmrf_sanction if data.prior_cmrf_sanction else "Source: NIL        Amount: Rs. NIL"
    if "Source" not in prior_sanction:
        prior_sanction = f"Source: {prior_sanction}        Amount: Rs. NIL"

    items_data = [
        [
            Paragraph("01. Name of the Patient/Beneficiary<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(with Surname)", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>{full_name_display}</b>", val_bold)
        ],
        [
            Paragraph("02. Father's/Husband's Name", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(rel_name if rel_name else data.relationship, val_style)
        ],
        [
            Paragraph("03. Age", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>{data.age}</b>", val_bold)
        ],
        [
            Paragraph("04. Contact Number of Patient/Beneficiary", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(data.mobile_no, val_style)
        ],
        [
            Paragraph("05. White Ration Card Number of Patient/<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Beneficiary", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>{data.fsc_no}</b>", val_bold)
        ],
        [
            Paragraph("06. Aadhar card Number", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>{data.aadhaar_no}</b>", val_bold)
        ],
        [
            Paragraph("07. Permanent Address", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"{data.address} - {data.pincode}", val_style)
        ],
        [
            Paragraph("08. Address for Correspondence", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"H.No: {data.village}, {data.mandal} Mandal, {data.district} Dist - {data.pincode}", val_style)
        ],
        # 09. Bank Details inserted right above Disease
        [
            Paragraph("09. Bank Details<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(IFSC, Bank Name, Branch,<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Name of A/c Holder & A/c No.)", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(
                f"<b>Name of Account Holder:</b> {holder_display}<br/>"
                f"<b>Account Number:</b> {data.account_no}<br/>"
                f"<b>Bank Name & Branch:</b> {data.bank_name}, {clean_branch_data}<br/>"
                f"<b>IFSC Code:</b> {data.ifsc}",
                val_style
            )
        ],
        [
            Paragraph("10. Name of the Disease/Purpose for seeking<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;exgratia/financial assistance", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>{data.treatment_diagnosis}</b>", val_bold)
        ],
        [
            Paragraph("11. Name & Address of Hospital with Phone<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;& Fax Number", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(clean_hosp, val_style)
        ],
        [
            Paragraph("12. Date of Surgery/Operation", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(surg_date_val, val_style)
        ],
        [
            Paragraph("13. Estimated/Requested Amount (Hospital<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;estimation in ORIGINAL to be enclosed)", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(f"<b>Rs. {data.amount}/-</b>", val_bold)
        ],
        [
            Paragraph("14. Whether any amount was sanctioned under<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CMRF or from any other source", item_num_lbl),
            Paragraph(":", colon_style),
            Paragraph(prior_sanction, val_style)
        ]
    ]

    items_table = Table(items_data, colWidths=[220, 12, 319])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    # 4. Declaration Paragraph
    dec_text = (
        "The above information given by me is true and correct as per my knowledge and "
        "I request you to sanction financial assistance under CMRF."
    )
    dec_table_data = [[Paragraph(dec_text, dec_style)]]
    dec_table = Table(dec_table_data, colWidths=[551])
    dec_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    # 5. Sign-off with Dedicated Physical Signature Buffer
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    sign_label = "SIGNATURE OF THE NOMINEE / BENEFICIARY" if data.is_deceased else "SIGNATURE OF THE PATIENT/BENEFICIARY"

    sign_data = [
        [
            Paragraph(f"<b>Place:</b> {data.district}", val_style),
            Paragraph("<b>Yours faithfully</b>", ParagraphStyle('YF', parent=val_style, alignment=2))
        ],
        [
            Paragraph("", val_style),
            Paragraph("", val_style)
        ],
        [
            Paragraph(f"<b>Date:</b> {today_str}", val_style),
            Paragraph(f"<b>{sign_label}</b>", ParagraphStyle('SignLbl', parent=val_style, alignment=2))
        ]
    ]

    sign_table = Table(sign_data, colWidths=[247, 304], rowHeights=[13, 26, 13])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    # 6. Enclosures Block
    encl_data = [
        [Paragraph("<b>Enclosures:</b><br/>1. Hospital Estimate in original<br/>2. Copy of White Ration Card/Income certificate issued by the MRO.<br/>3. Copy of Aadhaar Card & Bank Passbook", encl_style)]
    ]
    encl_table = Table(encl_data, colWidths=[551])
    encl_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    # Build Exact Single-Page A4 Proforma
    doc.build([
        header_table,
        Spacer(1, 2),
        to_table,
        Spacer(1, 1),
        items_table,
        dec_table,
        Spacer(1, 1),
        sign_table,
        Spacer(1, 2),
        encl_table
    ])

# Streamlit User Interface
uploaded_file = st.file_uploader("", type=["pdf"], help="Upload single combined PDF bundle containing all documents.")

st.markdown("""
<div class="security-badge">
    🔒 End-to-End Secure Processing • Confidential Official Extraction
</div>
""", unsafe_allow_html=True)

st.write("")

if uploaded_file is not None:
    if st.button("✨ Generate CMRF Application Form", type="primary"):
        status_box = st.empty()
        try:
            data = extract_data_from_file(uploaded_file.read(), status_box)
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', data.name.strip())
            output_filename = f"{clean_name}_cmrf.pdf"
            
            temp_output_path = os.path.join(tempfile.gettempdir(), output_filename)
            generate_cmrf_pdf(data, temp_output_path)

            status_box.empty()

            if data.is_deceased:
                st.info(f"Detected **DECEASED APPLICANT** Case: Patient **(Late) {data.name}** | Nominee: **{data.bank_holder_name}**")
            else:
                st.success(f"Detected **ALIVE APPLICANT** Case: **{data.name}**")

            with open(temp_output_path, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label=f"⬇️ Download Print-Ready Form ({output_filename})",
                data=pdf_bytes,
                file_name=output_filename,
                mime="application/pdf"
            )

            # Online Portal 1-Click Autofill Payload
            today_str = datetime.date.today().strftime("%d/%m/%Y")
            clean_rel_type = "S/O"
            if "W/O" in data.relationship.upper():
                clean_rel_type = "W/O"
            elif "D/O" in data.relationship.upper():
                clean_rel_type = "D/O"

            clean_rel_name = re.sub(r'^(S/O|W/O|D/O)\s*[:.\-]?\s*', '', data.relationship, flags=re.IGNORECASE).strip()
            
            clean_branch_data = data.branch.strip()
            if any(term in clean_branch_data.lower() for term in ["surgery", "pciol", "cataract", "hospital", "patient", "fistula"]):
                clean_branch_data = data.district.strip()

            portal_payload = {
                "is_deceased": bool(data.is_deceased),
                "aadhaar_no": str(data.aadhaar_no).strip(),
                "age": re.sub(r'[^0-9]', '', str(data.age)),
                "name": data.name.strip(),
                "gender": "Male" if data.gender.lower().startswith("m") else "Female",
                "relationship_type": clean_rel_type,
                "relative_name": clean_rel_name,
                "mobile_no": str(data.mobile_no).strip(),
                "fsc_no": str(data.fsc_no).strip(),
                "district": data.district.strip(),
                "mandal": data.mandal.strip(),
                "village": data.village.strip(),
                "address": data.address.strip(),
                "pincode": str(data.pincode).strip(),
                "ifsc": str(data.ifsc).strip(),
                "bank_name": data.bank_name.strip(),
                "branch": clean_branch_data,
                "account_no": str(data.account_no).strip(),
                "bank_holder_name": data.bank_holder_name.strip(),
                "hospital_name": data.hospital_name.strip(),
                "amount": re.sub(r'[^0-9]', '', str(data.amount)),
                "ip_no": str(data.ip_no).strip(),
                "bill_no": str(data.bill_no).strip(),
                "treatment": data.treatment_diagnosis[:150].strip(),
                "letter_date": today_str
            }

            st.markdown("---")
            st.markdown("#### ⚡ 1-Click Online Portal Autofill Code")
            st.markdown("Copy the code block below, switch to `cmrf.telangana.gov.in`, and click your **⚡ Fill CMRF Portal** bookmark:")
            
            payload_json = json.dumps(portal_payload, indent=2)
            st.code(f"window.cmrfData = {payload_json};", language="javascript")

        except Exception as e:
            status_box.empty()
            st.error(f"Error processing document: {e}")
