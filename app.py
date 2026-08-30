import os
import re
import tempfile
import time
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field

st.set_page_config(page_title="CMRF Application Auto-Filler", page_icon="📄", layout="centered")

# 1. Data Schema
class CMRFData(BaseModel):
    name: str = Field(description="Name strictly as per Aadhaar card")
    age: str = Field(description="Age (e.g., 63 Yrs)")
    relationship: str = Field(description="Father or Husband name")
    aadhaar_no: str = Field(description="12-digit Aadhaar number")
    district: str = Field(description="District name")
    mandal: str = Field(description="Mandal name")
    village: str = Field(description="Village name")
    address: str = Field(description="Full address from Aadhaar card")
    pincode: str = Field(description="Pincode")
    mobile_no: str = Field(description="Mobile number")
    fsc_no: str = Field(description="New Ration Card / FSC number")
    bank_name: str = Field(description="Bank name")
    bank_district: str = Field(description="Bank District")
    branch: str = Field(description="Branch name")
    ifsc: str = Field(description="IFSC code")
    account_no: str = Field(description="Bank Account number")
    bank_holder_name: str = Field(description="Applicant Name as printed on Bank Passbook")
    hospital_name: str = Field(description="Hospital Name from letterhead")
    ip_no: str = Field(description="Patient IP Number")
    bill_no: str = Field(description="Bill / ADM Number")
    treatment_diagnosis: str = Field(description="Chief Diagnosis / Treatment")
    amount: str = Field(description="Total Amount as per Essentiality Certificate")

# 2. Resilient Data Extraction
def extract_data_from_file(file_bytes: bytes) -> CMRFData:
    client = genai.Client()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        uploaded_file = client.files.upload(file=tmp_path)
        prompt = """
        Extract all details required for the CMRF Application from the attached documents:
        - Name, Age, Relationship (Husband/Father Name), District, Mandal, Village, Full Address, Pincode: from Aadhaar.
        - Mobile No: from documents or ration card.
        - FSC/Ration Card No: from Food Security Card.
        - Bank Name, Bank District, Branch, IFSC, Account Number, Applicant Name (as per Bank): from Bank Passbook.
        - Hospital Name: top letterhead of Hospital documents.
        - IP No and Bill No: from In-Patient Bill or Discharge Summary.
        - Details of Treatment: from Chief Diagnosis / Diagnosis.
        - Amount: total amount from the Essentiality Certificate.
        """

        # Stable production models only
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None

        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[uploaded_file, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=CMRFData,
                        ),
                    )
                    return CMRFData.model_validate_json(response.text)
                except APIError as e:
                    last_error = e
                    # If 404 model not found, immediately switch model
                    if getattr(e, 'code', None) == 404:
                        break
                    # If 503 capacity spike or 429 rate limit, back off and retry
                    time.sleep(2 * (attempt + 1))
                    continue
                except Exception as e:
                    last_error = e
                    time.sleep(1)
                    continue

        raise last_error if last_error else RuntimeError("Failed to extract document data.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# 3. Direct PDF Form Generator
def generate_cmrf_pdf(data: CMRFData, output_pdf_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=1, leading=14)
    sec_hdr_style = ParagraphStyle('SecHdrStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, alignment=1, leading=12)
    photo_style = ParagraphStyle('PhotoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, alignment=1, leading=12)
    
    f_lbl = ParagraphStyle('FLbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12)
    f_val = ParagraphStyle('FVal', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=12)
    f_val_bold = ParagraphStyle('FValBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12)
    f_small = ParagraphStyle('FSmall', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10)

    bank_dist = data.bank_district if data.bank_district else data.district

    table_data = [
        [Paragraph("CMRF / LOC APPLICATION FORM", title_style), "", "", Paragraph("AFFIX PASSPORT<br/>PHOTO", photo_style)],
        [Paragraph("APPLICANT DETAILS", sec_hdr_style), "", "", ""],
        [Paragraph("HON'BLE MLC LR NO. & DATE:", f_lbl), "", "", ""],
        [Paragraph("CMRF TOKEN NUMBER :", f_lbl), "", "", ""],
        [Paragraph(f"<b>NAME:</b>  {data.name}", f_val_bold), "", "", ""],
        [Paragraph(f"<b>AGE:</b>  {data.age}", f_val), Paragraph(f"<b>S/O / W/O:</b>  {data.relationship}", f_val), "", ""],
        [Paragraph(f"<b>AADHAAR NO:</b>  {data.aadhaar_no}", f_val_bold), "", Paragraph(f"<b>MOBILE NO:</b>  {data.mobile_no}", f_val), ""],
        [Paragraph(f"<b>DISTRICT:</b>  {data.district}", f_val), "", Paragraph(f"<b>MANDAL:</b>  {data.mandal}", f_val), ""],
        [Paragraph(f"<b>VILLAGE:</b>  {data.village}", f_val), "", Paragraph(f"<b>ADDRESS:</b>  {data.address}", f_val), ""],
        [Paragraph(f"<b>PINCODE:</b>  {data.pincode}", f_val), "", "", ""],
        [Paragraph("<b>INCOME CERTIFICATE NO:</b>", f_lbl), "", Paragraph(f"<b>NEW FSC NO:</b>  {data.fsc_no}", f_val_bold), ""],
        [Paragraph("BANK ACCOUNT DETAILS", sec_hdr_style), "", "", ""],
        [Paragraph(f"<b>DISTRICT:</b>  {bank_dist}", f_val), "", Paragraph(f"<b>BANK NAME:</b>  {data.bank_name}", f_val_bold), ""],
        [Paragraph(f"<b>IFSC:</b>  {data.ifsc}", f_val_bold), "", Paragraph(f"<b>BRANCH:</b>  {data.branch}", f_val), ""],
        [Paragraph(f"<b>ACCOUNT NUMBER:</b>  {data.account_no}", f_val_bold), "", Paragraph(f"<b>Applicant Name (as per Bank):</b><br/>{data.bank_holder_name}", f_val), ""],
        [Paragraph(f"<b>HOSPITAL:</b><br/>{data.hospital_name}", f_val_bold), "", Paragraph(f"<b>ADM / BILL NO:</b><br/>{data.bill_no}", f_val), Paragraph(f"<b>PATIENT IP NO:</b><br/>{data.ip_no}", f_val_bold)],
        [Paragraph(f"<b>AMOUNT INCURRED / ESTIMATED :</b>  Rs. {data.amount}/-", f_val_bold), "", "", ""],
        [Paragraph("<b>DETAILS OF TREATMENT:</b>", f_lbl), Paragraph(f"{data.treatment_diagnosis}", f_val_bold), "", ""],
        [Paragraph("• HON'BLE MLC ORIGINAL LETTER", f_small), "", Paragraph("SIGNATURE OF THE APPLICANT", sec_hdr_style), ""],
        [Paragraph("• ORIGINAL HOSPITAL BILLS", f_small), "", "", ""],
        [Paragraph("• AADHAAR COPY", f_small), "", "", ""],
        [Paragraph("• NEW RATION CARD / INCOME CERTIFICATE", f_small), "", "", ""],
        [Paragraph("• BANK PASSBOOK (COPY OF FIRST PAGE)", f_small), "", "", ""]
    ]

    col_widths = [165, 120, 150, 120]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('SPAN', (0, 0), (2, 0)),
        ('SPAN', (3, 0), (3, 4)),
        ('SPAN', (0, 1), (2, 1)),
        ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#EEEEEE')),
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
        ('BACKGROUND', (0, 11), (3, 11), colors.HexColor('#EEEEEE')),
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
st.title("CMRF Application Auto-Filler")
st.write("Upload any citizen's combined PDF attachments to generate the filled CMRF form.")

uploaded_file = st.file_uploader("Upload Citizen Documents PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Generate CMRF Application", type="primary"):
        with st.spinner("Analyzing documents & generating print-ready form..."):
            try:
                data = extract_data_from_file(uploaded_file.read())
                clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', data.name.strip())
                output_filename = f"{clean_name}_cmrf.pdf"
                
                temp_output_path = os.path.join(tempfile.gettempdir(), output_filename)
                generate_cmrf_pdf(data, temp_output_path)

                st.success(f"Form generated successfully for **{data.name}**")
                
                with open(temp_output_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label=f"⬇️ Download {output_filename}",
                    data=pdf_bytes,
                    file_name=output_filename,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error processing document: {e}")
