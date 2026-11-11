import os
import re
import json
import time
import base64
import datetime
import tempfile
import streamlit as st

st.set_page_config(
    page_title="CMRF Portal | Sumanth Muthamala",
    page_icon="🏛️",
    layout="wide"
)

# -------------------------------------------------------------
# 1. POSTER BACKGROUND & CLEAN CONTAINER LAYOUT
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

    if img_b64:
        return f"""
        .stApp, [data-testid="stAppViewContainer"] {{
            background: url("data:image/{ext};base64,{img_b64}") no-repeat center top fixed !important;
            background-size: cover !important;
            background-color: transparent !important;
        }}
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        """
    else:
        return """
        .stApp, [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at 50% 10%, #D8006C 0%, #A10054 45%, #6B0038 100%) !important;
            background-color: transparent !important;
        }}
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        """

bg_css = load_poster_background()

st.markdown(f"""
<style>
    {bg_css}

    /* Pushes Streamlit interaction cards below the poster banner */
    .hero-spacer {{
        height: 520px;
        width: 100%;
    }}

    @media (max-width: 900px) {{
        .hero-spacer {{
            height: 380px;
        }}
    }}

    .block-container {{
        max-width: 960px !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }}

    /* Polished dark glass cards matching the poster aesthetic */
    .portal-box {{
        background: rgba(30, 4, 18, 0.90) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 193, 7, 0.55);
        border-radius: 18px;
        padding: 22px 28px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
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

    /* Form Card Container */
    [data-testid="stForm"] {{
        background: rgba(30, 4, 18, 0.92) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 193, 7, 0.55) !important;
        border-radius: 18px !important;
        padding: 24px !important;
        color: #FFFFFF !important;
    }}

    [data-testid="stForm"] label {{
        color: #F8B4D9 !important;
        font-weight: 600 !important;
    }}

    /* Custom Uploader Card */
    [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 14px;
        padding: 12px;
        border: 1.5px dashed #A60055;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    /* Action buttons matching the poster's gold pill button */
    .stButton > button {{
        background: linear-gradient(135deg, #7A003E 0%, #A60055 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px !important;
        border: 1.5px solid #FFC107 !important;
        border-radius: 30px !important;
        padding: 12px 28px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
        width: 100%;
        margin-top: 10px;
    }}
    .stButton > button:hover {{
        border: 1.5px solid #FFE082 !important;
        box-shadow: 0 10px 28px rgba(255, 193, 7, 0.4) !important;
    }}

    /* Native zero-JS Download Button */
    .native-dl-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: 0.5px;
        text-decoration: none !important;
        border-radius: 30px;
        padding: 14px 28px;
        box-shadow: 0 8px 22px rgba(16, 185, 129, 0.4);
        margin-top: 14px;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }}
</style>

<!-- Top spacer keeps the poster banner, emblem, and photo in clear view -->
<div class="hero-spacer"></div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. SIDEBAR KEY MANAGEMENT
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 API Key Override")
    st.caption("Paste a Gemini API key (AIzaSy...) if your primary secrets hit rate limits.")
    user_custom_key = st.text_input("Temporary Backup Key", type="password", placeholder="AIzaSy...")

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
# 4. LAZY-LOADED PROCESSING & SCHEMAS
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
    return CMRFData

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
    """

    is_large = len(file_bytes) > (15 * 1024 * 1024)
    tmp_path = None
    if is_large:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.6-flash"]

    try:
        last_error = None
        for key in keys:
            client = genai.Client(api_key=key)

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
                status_box.info(f"✨ Analyzing application via [{model_name}]...")
                for attempt in range(3):
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
                        if any(x in err for x in ["401", "unauthenticated"]):
                            break
                        elif any(x in err for x in ["429", "quota"]):
                            break
                        elif any(x in err for x in ["503", "unavailable"]):
                            time.sleep((attempt + 1) * 3)
                            continue
                        else:
                            break
        raise last_error if last_error else RuntimeError("Processing failed. Please verify API key configuration.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# -------------------------------------------------------------
# 5. ROBUST SINGLE-PAGE PROFORMA GENERATOR (NO LAYOUTERROR)
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

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=22,
        rightMargin=22,
        topMargin=10,
        bottomMargin=10
    )
    styles = getSampleStyleSheet()

    hdr_s = ParagraphStyle('Hdr', parent=styles['Normal'], fontName=serif_bld, fontSize=11.5, alignment=1, leading=15)
    box_s = ParagraphStyle('Box', parent=styles['Normal'], fontName=serif_bld, fontSize=9.5, alignment=1, leading=13)
    to_s = ParagraphStyle('To', parent=styles['Normal'], fontName=serif_bld, fontSize=10, leading=13.5)
    lbl_s = ParagraphStyle('Lbl', parent=styles['Normal'], fontName=serif_bld, fontSize=9, leading=12)
    val_s = ParagraphStyle('Val', parent=styles['Normal'], fontName=serif_reg, fontSize=9, leading=12)
    bld_s = ParagraphStyle('Bld', parent=styles['Normal'], fontName=serif_bld, fontSize=9, leading=12)
    dec_s = ParagraphStyle('Dec', parent=styles['Normal'], fontName=serif_reg, fontSize=8.5, leading=11.5)
    enc_s = ParagraphStyle('Enc', parent=styles['Normal'], fontName=serif_reg, fontSize=8, leading=10.5)

    header_table = Table([
        [
            Paragraph("<b>PROFORMA-cum-REQUISITION<br/>FOR SEEKING FINANCIAL ASSISTANCE<br/>FOR MEDICAL TREATMENT/EXGRATIA UNDER<br/>\"CHIEF MINISTER'S RELIEF FUND\"</b>", hdr_s),
            Paragraph("<br/><br/><b>Affix Latest<br/>Passport Size<br/>Photo</b>", box_s)
        ]
    ], colWidths=[452, 99], rowHeights=[115])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (1,0), (1,0), 1.2, colors.black),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))

    to_table = Table([[Paragraph("<b>To<br/>The Hon'ble Chief Minister,<br/>Govt. of Telangana, Hyderabad.</b>", to_s)]], colWidths=[551])
    to_table.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('LEFTPADDING', (0,0), (-1,-1), 0)]))

    deceased_tag = " <font color='#D32F2F'><b>[DECEASED]</b></font>" if data.is_deceased else ""
    full_name = f"{data.name}{deceased_tag}"
    clean_acc = re.sub(r'[^0-9]', '', str(data.account_no)).strip() or str(data.account_no).strip()
    surg_val = data.surgery_date.strip() if (data.surgery_date and data.surgery_date.upper() != "N/A") else "As per Hospital Records / Admission"
    nominee_suf = f" ({data.nominee_relation})" if (data.is_deceased and data.nominee_relation) else ""
    holder_name = f"{data.bank_holder_name}{nominee_suf}" if data.bank_holder_name else data.name

    # 2-column layout to prevent infinite line-wrap overflow
    rows = [
        [Paragraph("01. Name of Patient/Beneficiary (with Surname)", lbl_s), Paragraph(f": <b>{full_name}</b>", bld_s)],
        [Paragraph("02. Father's/Husband's Name", lbl_s), Paragraph(f": {data.relationship}", val_s)],
        [Paragraph("03. Age", lbl_s), Paragraph(f": <b>{data.age}</b>", bld_s)],
        [Paragraph("04. Contact Number", lbl_s), Paragraph(f": {data.mobile_no}", val_s)],
        [Paragraph("05. White Ration Card (FSC) No", lbl_s), Paragraph(f": <b>{data.fsc_no}</b>", bld_s)],
        [Paragraph("06. Aadhar card Number", lbl_s), Paragraph(f": <b>{data.aadhaar_no}</b>", bld_s)],
        [Paragraph("07. Permanent Address", lbl_s), Paragraph(f": {data.address} - {data.pincode}", val_s)],
        [Paragraph("08. Address for Correspondence", lbl_s), Paragraph(f": H.No: {data.village}, {data.mandal} Mandal, {data.district} Dist - {data.pincode}", val_s)],
        [
            Paragraph("09. Bank Details (IFSC, Bank Name, Branch, Name of A/c Holder & A/c No.)", lbl_s),
            Paragraph(
                f": <b>A/c Holder:</b> {holder_name}<br/>"
                f"&nbsp;&nbsp;<b>A/c No:</b> {clean_acc}<br/>"
                f"&nbsp;&nbsp;<b>Bank & Branch:</b> {data.bank_name}, {data.branch}<br/>"
                f"&nbsp;&nbsp;<b>IFSC:</b> {data.ifsc}",
                val_s
            )
        ],
        [Paragraph("10. Name of the Disease / Purpose", lbl_s), Paragraph(f": <b>{data.treatment_diagnosis}</b>", bld_s)],
        [Paragraph("11. Hospital Name & Address", lbl_s), Paragraph(f": {data.hospital_name}", val_s)],
        [Paragraph("12. Date of Surgery/Operation", lbl_s), Paragraph(f": {surg_val}", val_s)],
        [Paragraph("13. Estimated/Requested Amount", lbl_s), Paragraph(f": <b>Rs. {data.amount}/-</b>", bld_s)],
        [Paragraph("14. Prior CMRF Sanction Details", lbl_s), Paragraph(f": {data.prior_cmrf_sanction}", val_s)]
    ]

    items_table = Table(rows, colWidths=[230, 321])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 0.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.8),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    dec_table = Table([[Paragraph("The above information given by me is true and correct as per my knowledge and I request you to sanction financial assistance under CMRF.", dec_s)]], colWidths=[551])
    dec_table.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('LEFTPADDING', (0,0), (-1,-1), 0)]))

    today_str = datetime.date.today().strftime("%d/%m/%Y")
    sign_lbl = "SIGNATURE OF THE NOMINEE / BENEFICIARY" if data.is_deceased else "SIGNATURE OF THE PATIENT/BENEFICIARY"
    sign_table = Table([
        [Paragraph(f"<b>Place:</b> {data.district}", val_s), Paragraph("<b>Yours faithfully</b>", ParagraphStyle('YF', parent=val_s, alignment=2))],
        [Paragraph("", val_s), Paragraph("", val_s)],
        [Paragraph(f"<b>Date:</b> {today_str}", val_s), Paragraph(f"<b>{sign_lbl}</b>", ParagraphStyle('SL', parent=val_s, alignment=2))]
    ], colWidths=[247, 304], rowHeights=[12, 22, 12])
    sign_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('LEFTPADDING', (0,0), (-1,-1), 0)]))

    enc_table = Table([[Paragraph("<b>Enclosures:</b><br/>1. Hospital Estimate in original<br/>2. Copy of White Ration Card/Income certificate issued by the MRO.<br/>3. Copy of Aadhaar Card & Bank Passbook", enc_s)]], colWidths=[551])
    enc_table.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('LEFTPADDING', (0,0), (-1,-1), 0)]))

    doc.build([header_table, Spacer(1, 2), to_table, Spacer(1, 1), items_table, dec_table, Spacer(1, 1), sign_table, Spacer(1, 2), enc_table])

# -------------------------------------------------------------
# 6. EXECUTION & VERIFICATION FORM
# -------------------------------------------------------------
if uploaded_file is not None:
    if st.button("✨ Extract Citizen Application Data", type="primary"):
        status_box = st.empty()
        try:
            raw_data = extract_bundle(uploaded_file.read(), status_box, user_custom_key)
            st.session_state["cmrf_data"] = raw_data
            status_box.empty()
            st.success("✅ Application extracted successfully. Review and confirm below.")
        except Exception as e:
            status_box.empty()
            st.error(f"Error: {e}")

if "cmrf_data" in st.session_state:
    data = st.session_state["cmrf_data"]
    
    st.markdown("""
    <div class="portal-box" style="margin-top: 20px;">
        <div class="portal-box-title">📝 Administrative Verification & Edit</div>
        <div class="portal-box-subtitle">Confirm bank account and identity details before printing the official proforma.</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("verify_form"):
        c1, c2 = st.columns(2)
        with c1:
            edit_acc = st.text_input("Bank Account Number (Exact Digits)", value=re.sub(r'[^0-9]', '', str(data.account_no)))
            edit_ifsc = st.text_input("Bank IFSC Code", value=data.ifsc)
            edit_bank = st.text_input("Bank Name", value=data.bank_name)
            edit_branch = st.text_input("Bank Branch", value=data.branch)
            edit_holder = st.text_input("Account Holder Name", value=data.bank_holder_name)
        with c2:
            edit_name = st.text_input("Patient / Applicant Name", value=data.name)
            edit_aadhaar = st.text_input("Aadhaar Number", value=data.aadhaar_no)
            edit_age = st.text_input("Patient Age", value=data.age)
            edit_phone = st.text_input("Contact Number", value=data.mobile_no)
            edit_fsc = st.text_input("White Ration / FSC Card No", value=data.fsc_no)
            edit_amt = st.text_input("Estimation / Bill Amount", value=data.amount)
            
        submitted = st.form_submit_button("🖨️ Generate Official Proforma PDF & Autofill")

    if submitted:
        data.account_no = edit_acc.strip()
        data.ifsc = edit_ifsc.strip().upper()
        data.bank_name = edit_bank.strip()
        data.branch = edit_branch.strip()
        data.bank_holder_name = edit_holder.strip()
        data.name = edit_name.strip()
        data.aadhaar_no = edit_aadhaar.strip()
        data.age = edit_age.strip()
        data.mobile_no = edit_phone.strip()
        data.fsc_no = edit_fsc.strip()
        data.amount = edit_amt.strip()

        clean_slug = re.sub(r'[^a-zA-Z0-9_]', '_', data.name.strip())
        out_filename = f"{clean_slug}_cmrf.pdf"
        out_path = os.path.join(tempfile.gettempdir(), out_filename)
        build_pdf(data, out_path)

        with open(out_path, "rb") as f:
            pdf_bytes = f.read()

        b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{out_filename}" class="native-dl-btn">⬇️ Download Official Proforma ({out_filename})</a>', unsafe_allow_html=True)

        clean_rel_type = "W/O" if "W/O" in data.relationship.upper() else ("D/O" if "D/O" in data.relationship.upper() else "S/O")
        clean_rel_name = re.sub(r'^(S/O|W/O|D/O)\s*[:.\-]?\s*', '', data.relationship, flags=re.IGNORECASE).strip()
        
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
            "branch": data.branch.strip(),
            "account_no": re.sub(r'[^0-9]', '', str(data.account_no)).strip(),
            "bank_holder_name": data.bank_holder_name.strip(),
            "hospital_name": data.hospital_name.strip(),
            "amount": re.sub(r'[^0-9]', '', str(data.amount)),
            "ip_no": str(data.ip_no).strip(),
            "bill_no": str(data.bill_no).strip(),
            "treatment": data.treatment_diagnosis[:150].strip(),
            "letter_date": datetime.date.today().strftime("%d/%m/%Y")
        }

        st.markdown("---")
        st.markdown("#### ⚡ 1-Click Online Portal Autofill Code")
        st.code(f"window.cmrfData = {json.dumps(portal_payload, indent=2)};", language="javascript")
