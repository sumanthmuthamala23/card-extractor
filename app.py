import io
import json
import re
from datetime import date
import fitz  # PyMuPDF
import pandas as pd
import streamlit as st
from PIL import Image
import google.generativeai as genai

# Page setup
st.set_page_config(page_title="Card Data Extractor", layout="centered")
st.title("Card Data Extractor")
st.write("Upload up to 6 identity documents (PDF, JPEG, JPG) to extract Name, ID Number, and calculate exact Age as of today.")

# Fetch API key directly from Secrets or user fallback
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    api_key = st.text_input("Enter Google Gemini API Key:", type="password")

# Calculate exact age from DOB or Birth Year
def calculate_exact_age(dob_str, year_only=None):
    today = date.today()
    
    if dob_str and isinstance(dob_str, str):
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', dob_str)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                birth_date = date(year, month, day)
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return int(age)
            except ValueError:
                pass
        
        match_iso = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', dob_str)
        if match_iso:
            year, month, day = int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))
            try:
                birth_date = date(year, month, day)
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return int(age)
            except ValueError:
                pass

    if year_only:
        try:
            y = int(year_only)
            return int(today.year - y)
        except (ValueError, TypeError):
            pass
            
    if dob_str and isinstance(dob_str, str):
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', dob_str)
        if year_match:
            return int(today.year - int(year_match.group(1)))

    return "N/A"

if api_key:
    genai.configure(api_key=api_key)

    model_name = "gemini-3.6-flash"
    try:
        model = genai.GenerativeModel(model_name)
    except Exception:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

    uploaded_files = st.file_uploader(
        "Choose PDF or Image files", 
        type=["pdf", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        if len(uploaded_files) > 6:
            st.warning("Please upload a maximum of 6 files at once.")
        else:
            if st.button("Process Documents"):
                results = []
                progress_bar = st.progress(0)
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    image = None
                    try:
                        if uploaded_file.type == "application/pdf":
                            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                            page = doc.load_page(0)
                            pix = page.get_pixmap(dpi=200)
                            image = Image.open(io.BytesIO(pix.tobytes("png")))
                        else:
                            image = Image.open(uploaded_file)

                        if image:
                            prompt = """
                            Analyze this identity card image and extract:
                            {
                              "name": "Full Name of Person",
                              "card_number": "Card or ID Number",
                              "dob": "DD/MM/YYYY or YYYY if only year is printed",
                              "year_of_birth": 1990
                            }
                            Output strictly valid JSON only without markdown code blocks.
                            """
                            
                            response = model.generate_content([prompt, image])
                            clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                            data = json.loads(clean_text)
                            
                            raw_dob = data.get("dob", "")
                            raw_yob = data.get("year_of_birth", None)
                            exact_age = calculate_exact_age(raw_dob, raw_yob)

                            results.append({
                                "File Name": uploaded_file.name,
                                "Name of Person": data.get("name", "N/A"),
                                "Card / ID Number": data.get("card_number", "N/A"),
                                "Age (in Years)": exact_age,
                                "DOB": raw_dob
                            })
                            
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        results.append({
                            "File Name": uploaded_file.name,
                            "Name of Person": "Extraction Failed",
                            "Card / ID Number": "N/A",
                            "Age (in Years)": "N/A",
                            "DOB": "N/A"
                        })
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                if results:
                    df = pd.DataFrame(results)
                    st.success("Extraction & Age Calculation Complete!")
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", data=csv, file_name="calculated_card_data.csv", mime="text/csv")