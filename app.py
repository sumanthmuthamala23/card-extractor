import os
import re
import tempfile
import time
import base64
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="CMRF Auto-Filler | Sumanth Muthamala",
    page_icon="🏛️",
    layout="centered"
)

# Embed profile image dynamically as base64
profile_img_html = ""
if os.path.exists("profile.jpg"):
    with open("profile.jpg", "rb") as img_file:
        b64_data = base64.b64encode(img_file.read()).decode()
        profile_img_html = f'<img class="profile-img" src="data:image/jpeg;base64,{b64_data}">'

# BRS Party Theme & Calligraphy Typography
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
    /* BRS Vibrant Gradient Background */
    .stApp {{
        background: linear-gradient(135deg, #FFF0F6 0%, #FFE3EC 35%, #FDE2EF 70%, #FCE4EC 100%);
        font-family: 'Poppins', sans-serif;
    }}

    /* Main Branding Header Card */
    .hero-card {{
        background: linear-gradient(135deg, #E00676 0%, #FF1493 50%, #FF4081 100%);
        border-radius: 22px;
        padding: 26px 20px;
        text-align: center;
        color: white;
        box-shadow: 0 12px 28px rgba(224, 6, 118, 0.32);
        margin-bottom: 25px;
    }}

    /* Circular Profile Picture */
    .profile-img {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        object-position: top;
        border: 4px solid #FFFFFF;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.22);
        margin-bottom: 10px;
    }}

    /* Cursive Calligraphy Name */
    .calligraphy-name {{
        font-family: 'Great Vibes', cursive;
        font-size: 46px;
        font-weight: 400;
        color: #FFFFFF;
        text-shadow: 2px 3px 6px rgba(0,0,0,0.25);
        margin: 0;
        line-height: 1.1;
    }}

    .hero-subtitle {{
        font-size: 13.5px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #FFF0F6;
        margin-top: 4px;
        opacity: 0.95;
    }}

    .portal-badge {{
        background: rgba(255, 255, 255, 0.25);
        padding: 5px 16px;
        border-radius: 20px;
        font-size: 11.5px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    /* Action Button (BRS Pink) */
    .stButton > button {{
        background: linear-gradient(135deg, #E00676 0%, #FF1493 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 6px 18px rgba(224, 6, 118, 0.35) !important;
        width: 100%;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(224, 6, 118, 0.45) !important;
    }}

    /* Download Button */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.35) !important;
        width: 100%;
    }}
</style>

<div class="hero-card">
    {profile_img_html}
    <h1 class="calligraphy-name">Sumanth Muthamala</h1>
    <div class="hero-subtitle">Chief Minister's Relief Fund (CMRF)</div>
    <div class="portal-badge">⚡ AI-Powered Automated Application System</div>
</div>
""", unsafe_allow_html=True)

# 1. Dual-Status Structured Data Schema
class CMRFData(BaseModel):
    is_deceased: bool = Field(description="True if applicant/patient is deceased; False if alive")
    applicant_status: str = Field(description="Strictly 'DECEASED' if deceased, otherwise 'ALIVE'")
    name: str = Field(description="Name strictly as per Aadhaar card of the patient / deceased applicant")
    age: str = Field(description="Age (e.g., 63 Yrs)")
    relationship: str = Field(description="Father or Husband name of the patient")
    aadhaar_no: str = Field(description="12-digit Aadhaar number of patient / deceased")
    district: str = Field(description="District name")
    mandal: str = Field(description="Mandal name")
    village: str = Field(description="Village name")
    address: str = Field(description="Full address from Aadhaar card")
    pincode: str = Field(description="Pincode")
    mobile_no: str = Field(description="Mobile number from documents / ration card / nominee")
    fsc_no: str = Field(description="New Ration Card / FSC number")
    nominee_name: str = Field(description="Name of Nominee / Legal Heir from Lawyer Notary / Passbook (if deceased)")
    nominee_relation: str = Field(description="Relation of Nominee to Deceased (e.g., Wife, Son, Husband)")
    bank_name: str = Field(description="Bank name from passbook")
    bank_district: str = Field(description="Bank District")
    branch: str = Field(description="Branch name")
    ifsc: str = Field(description="IFSC code")
    account_no: str = Field(description="Bank Account number")
    bank_holder_name: str = Field(description="Account Holder Name as printed on Bank Passbook")
    hospital_name: str = Field(description="Hospital Name from letterhead")
    ip_no: str = Field(description="Patient IP Number")
    bill_no: str = Field(description="Bill / ADM Number")
    treatment_diagnosis: str = Field(description="Chief Diagnosis / Treatment")
    amount: str = Field(description="Total Amount as per Essentiality Certificate")

# Retrieve API keys safely from Streamlit Secrets
def get_api_keys():
    keys = []
    if "GEMINI_API_KEYS" in st.secrets:
        raw = st.secrets["GEMINI_API_KEYS"]
        if isinstance(raw, list):
            keys = [str(k).strip() for k in raw if str(k).strip()]
        elif isinstance(raw, str):
            keys = [k.strip() for k in raw.split(",") if k.strip()]
    elif "GEMINI_API_KEY" in st.secrets:
        keys = [str(st.secrets["GEMINI_API_KEY"]).strip()]
    elif "GEMINI_API_KEY" in os.environ:
        keys = [os.environ["GEMINI_API_KEY"].strip()]
    return [k for k in keys if len(k) > 10 and not k.startswith("AIzaSyKey")]

# 2. Resilient Multimodal Extraction Pipeline
def extract_data_from_file(file_bytes: bytes, status_box) -> CMRFData:
    keys = get_api_keys()
    if not keys:
        raise RuntimeError("No valid Gemini API key found in Secrets. Please configure your key in Streamlit settings.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    prompt = """
    Carefully analyze all attached documents for this CMRF application bundle:
    1. DETERMINE STATUS (ALIVE OR DECEASED):
       - Set is_deceased = True and applicant_status = 'DECEASED' if deceased (affidavit/death cert present), else False and 'ALIVE'.
    2. PATIENT DETAILS: Name, Age, Husband/Father Name, Aadhaar, Full Address, Pincode, Mandal, Village, District, FSC No.
    3. NOMINEE & BANK DETAILS: Bank Name, District, Branch, IFSC, Account No, Account Holder Name (Nominee if deceased).
    4. HOSPITAL & EXPENSES: Hospital Name, IP No, Bill No, Treatment details, Total Amount from Essentiality Certificate.
    """

    try:
        last_error = None
        for key_idx, current_key in enumerate(keys):
            client = genai.Client(api_key=current_key)
            status_box.info(f"Processing application (Engine Slot #{key_idx + 1}/{len(keys)})...")
            try:
                uploaded_file = client.files.upload(file=tmp_path)
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[uploaded_file, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CMRFData,
                    ),
                )
                return CMRFData.model_validate_json(response.text)
            except BaseException as e:
                last_error = e
                err_str = str(e).lower()
                if any(err in err_str for err in ["429", "resource_exhausted", "quota", "503", "unavailable"]):
                    status_box.warning(f"Slot #{key_idx + 1} capacity reached. Switching to next slot...")
                    time.sleep(1)
                    continue
                else:
                    raise e

        raise last_error if last_error else RuntimeError("All configured keys exhausted. Please try again.")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# 3. Direct PDF Layout Generator (Scaled to Single A4 Sheet)
def generate_cmrf_pdf(data: CMRFData, output_pdf_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=18,
        rightMargin=18,
        topMargin=16,
        bottomMargin=16
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, alignment=1, leading=16)
    sec_hdr_style = ParagraphStyle('SecHdrStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=1, leading=14)
    photo_style = ParagraphStyle('PhotoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=1, leading=13)
    
    f_lbl = ParagraphStyle('FLbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13.5)
    f_val = ParagraphStyle('FVal', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=13.5)
    f_val_bold = ParagraphStyle('FValBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, leading=14)
    f_small = ParagraphStyle('FSmall', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11)

    bank_dist = data.bank_district if data.bank_district else data.district

    if data.is_deceased or "DECEASED" in data.applicant_status.upper():
        name_display = f"<b>NAME:</b>  (LATE) {data.name} <font color='#D32F2F'><b>[DECEASED]</b></font>"
        applicant_sec_title = "APPLICANT DETAILS (DECEASED APPLICANT CASE)"
        bank_holder_label = f"<b>Nominee Name (as per Bank Passbook):</b><br/>{data.bank_holder_name}"
        if data.nominee_relation:
            bank_holder_label += f" ({data.nominee_relation})"
        signature_label = "SIGNATURE OF NOMINEE / APPLICANT"
        checklist_notary = "• LAWYER NOTARY AFFIDAVIT & DEATH CERTIFICATE"
    else:
        name_display = f"<b>NAME:</b>  {data.name}"
        applicant_sec_title = "APPLICANT DETAILS"
        bank_holder_label = f"<b>Applicant Name (as per Bank):</b><br/>{data.bank_holder_name}"
        signature_label = "SIGNATURE OF THE APPLICANT"
        checklist_notary = "• HON'BLE MLC ORIGINAL LETTER"

    table_data = [
        # Row 0
        [Paragraph("CMRF / LOC APPLICATION FORM", title_style), "", "", Paragraph("AFFIX PASSPORT<br/>PHOTO", photo_style)],
        # Row 1
        [Paragraph(applicant_sec_title, sec_hdr_style), "", "", ""],
        # Row 2
        [Paragraph("HON'BLE MLC LR NO. & DATE:", f_lbl), "", "", ""],
        # Row 3
        [Paragraph("CMRF TOKEN NUMBER :", f_lbl), "", "", ""],
        # Row 4
        [Paragraph(name_display, f_val_bold), "", "", ""],
        # Row 5
        [Paragraph(f"<b>AGE:</b>  {data.age}", f_val), Paragraph(f"<b>S/O / W/O:</b>  {data.relationship}", f_val), "", ""],
        # Row 6
        [Paragraph(f"<b>AADHAAR NO:</b>  {data.aadhaar_no}", f_val_bold), "", Paragraph(f"<b>MOBILE NO:</b>  {data.mobile_no}", f_val), ""],
        # Row 7
        [Paragraph(f"<b>DISTRICT:</b>  {data.district}", f_val), "", Paragraph(f"<b>MANDAL:</b>  {data.mandal}", f_val), ""],
        # Row 8
        [Paragraph(f"<b>VILLAGE:</b>  {data.village}", f_val), "", Paragraph(f"<b>ADDRESS:</b>  {data.address}", f_val), ""],
        # Row 9
        [Paragraph(f"<b>PINCODE:</b>  {data.pincode}", f_val), "", "", ""],
        # Row 10
        [Paragraph("<b>INCOME CERTIFICATE NO:</b>", f_lbl), "", Paragraph(f"<b>NEW FSC NO:</b>  {data.fsc_no}", f_val_bold), ""],
        # Row 11
        [Paragraph("BANK ACCOUNT DETAILS (NOMINEE / APPLICANT ACCOUNT)", sec_hdr_style), "", "", ""],
        # Row 12
        [Paragraph(f"<b>DISTRICT:</b>  {bank_dist}", f_val), "", Paragraph(f"<b>BANK NAME:</b>  {data.bank_name}", f_val_bold), ""],
        # Row 13
        [Paragraph(f"<b>IFSC:</b>  {data.ifsc}", f_val_bold), "", Paragraph(f"<b>BRANCH:</b>  {data.branch}", f_val), ""],
        # Row 14
        [Paragraph(f"<b>ACCOUNT NUMBER:</b>  {data.account_no}", f_val_bold), "", Paragraph(bank_holder_label, f_val), ""],
        # Row 15
        [Paragraph(f"<b>HOSPITAL:</b><br/>{data.hospital_name}", f_val_bold), "", Paragraph(f"<b>ADM / BILL NO:</b><br/>{data.bill_no}", f_val), Paragraph(f"<b>PATIENT IP NO:</b><br/>{data.ip_no}", f_val_bold)],
        # Row 16
        [Paragraph(f"<b>AMOUNT INCURRED / ESTIMATED :</b>  Rs. {data.amount}/-", f_val_bold), "", "", ""],
        # Row 17
        [Paragraph("<b>DETAILS OF TREATMENT:</b>", f_lbl), Paragraph(f"{data.treatment_diagnosis}", f_val_bold), "", ""],
        # Row 18
        [Paragraph(checklist_notary, f_small), "", Paragraph(signature_label, sec_hdr_style), ""],
        # Row 19
        [Paragraph("• ORIGINAL HOSPITAL BILLS & DISCHARGE SUMMARY", f_small), "", "", ""],
        # Row 20
        [Paragraph("• AADHAAR COPY (DECEASED & NOMINEE)", f_small), "", "", ""],
        # Row 21
        [Paragraph("• NEW RATION CARD / FSC CARD", f_small), "", "", ""],
        # Row 22
        [Paragraph("• BANK PASSBOOK OF NOMINEE (COPY OF FIRST PAGE)", f_small), "", "", ""]
    ]

    col_widths = [168, 122, 150, 119]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.9, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.2),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('SPAN', (0, 0), (2, 0)),
        ('SPAN', (3, 0), (3, 4)),
        ('SPAN', (0, 1), (2, 1)),
        ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#FCE4EC')),
        ('SPAN', (0, 2), (2, 2)),
        ('SPAN', (0, 3), (2, 3)),
        ('SPAN', (0, 4), (2, 4)),
        ('SPAN', (1, 5), (3, 5)),
        ('SPAN', (0, 6), (1, 6)),
        ('SPAN', (2, 6), (3, 6)),
        ('SPAN', (0, 7), (1, 7)),
        ('SPAN', (2, 7), (3, 7)),
        ('SPAN', (0, 8), (1, 8)),
        ('SPAN', (2, 8), (3, 9)),
        ('SPAN', (0, 9), (1, 9)),
        ('SPAN', (0, 10), (1, 10)),
        ('SPAN', (2, 10), (3, 10)),
        ('SPAN', (0, 11), (3, 11)),
        ('BACKGROUND', (0, 11), (3, 11), colors.HexColor('#FCE4EC')),
        ('SPAN', (0, 12), (1, 12)),
        ('SPAN', (2, 12), (3, 12)),
        ('SPAN', (0, 13), (1, 13)),
        ('SPAN', (2, 13), (3, 13)),
        ('SPAN', (0, 14), (1, 14)),
        ('SPAN', (2, 14), (3, 14)),
        ('SPAN', (0, 15), (1, 15)),
        ('SPAN', (0, 16), (3, 16)),
        ('SPAN', (1, 17), (3, 17)),
        ('SPAN', (0, 18), (1, 18)),
        ('SPAN', (2, 18), (3, 22)),
        ('SPAN', (0, 19), (1, 19)),
        ('SPAN', (0, 20), (1, 20)),
        ('SPAN', (0, 21), (1, 21)),
        ('SPAN', (0, 22), (1, 22)),
    ]))
    doc.build([t])

# Streamlit User Interface
st.markdown("### 📄 Upload Citizen Documents")
uploaded_file = st.file_uploader("Upload combined documents (Aadhaar, Notary/Affidavit, Passbook, Bills, Discharge Summary)", type=["pdf"])

if uploaded_file is not None:
    if st.button("✨ Generate CMRF Application", type="primary"):
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
                label=f"⬇️ Download {output_filename}",
                data=pdf_bytes,
                file_name=output_filename,
                mime="application/pdf"
            )
        except Exception as e:
            status_box.empty()
            st.error(f"Error processing document: {e}")
