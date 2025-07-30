from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920x1080")

    chrome_path = "/usr/bin/google-chrome"
    driver_path = "/usr/bin/chromedriver"

    chrome_options.binary_location = chrome_path

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


# Unified BFSI Highlights Extractor for TCS, Tech Mahindra, Mphasis, Zensar and Infosys 
#pip install requests pdfplumber streamlit selenium reportlab

import os
import re
import time
import requests
import pdfplumber
import streamlit as st
from io import BytesIO
from docx import Document
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- Streamlit Setup ---
st.set_page_config(page_title="BFSI Highlights Extractor", layout="centered")

# Add background and box styling
st.markdown(
    """
    <style>
    .white-box {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 12px;
        margin-top: 1.5rem;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)


background_url = "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDI0LTAyL3Jhd3BpeGVsX29mZmljZV8zNF9jbG9zZXVwX3Bob3RvX2JsYW5rX3Bvc3Rlcl9tb2NrdXB3aGl0ZV93YWxsY181ODljN2QxNi1kM2YwLTQyYTItOTQ4ZS1hYzc2M2UyMjNhNmRfMS5qcGc.jpg"
st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)),url("https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDI0LTAyL3Jhd3BpeGVsX29mZmljZV8zNF9jbG9zZXVwX3Bob3RvX2JsYW5rX3Bvc3Rlcl9tb2NrdXB3aGl0ZV93YWxsY181ODljN2QxNi1kM2YwLTQyYTItOTQ4ZS1hYzc2M2UyMjNhNmRfMS5qcGc.jpg");
        background-image: url("{background_url}");
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
        background-position: center;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("BFSI Highlights Extractor")

# --- Company Selection with Logos ---
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

st.markdown("### Select Company:")

logo_paths = {
    "TCS": r"/Users/khushithakur/Downloads/HCLTECH/tcs.png",
    "Tech Mahindra": r"/Users/khushithakur/Downloads/HCLTECH/techm.png",
    "Mphasis": r"/Users/khushithakur/Downloads/HCLTECH/mphasis.png",
    "Infosys": r"/Users/khushithakur/Downloads/HCLTECH/info.png",
    "Zensar": r"/Users/khushithakur/Downloads/HCLTECH/zensar.png"
}

cols = st.columns(len(logo_paths))
company_names = list(logo_paths.keys())

for i, col in enumerate(cols):
    with col:
        st.image(logo_paths[company_names[i]], width=80)
        if st.button(company_names[i]):
            st.session_state.selected_company = company_names[i]

if not st.session_state.selected_company:
    st.warning("Please select a company above to continue.")
    st.stop()

company = st.session_state.selected_company

# --- Inputs ---
if company == "Infosys":
    fiscal_year = st.text_input("Enter Financial Year (e.g., 2025-2026)")
    quarter_display_map = {
        "Q1 (Apr-Jun)": "q1",
        "Q2 (Jul-Sep)": "q2",
        "Q3 (Oct-Dec)": "q3",
        "Q4 (Jan-Mar)": "q4"
    }
    quarter_label = st.selectbox("Select Quarter:", list(quarter_display_map.keys()))
    quarter_code = quarter_display_map[quarter_label]

elif company == "Zensar":
    fiscal_year = st.text_input("Enter Fiscal Year (e.g., 26 for FY26)")
    quarter_code = st.selectbox("Select Quarter", ["Q1", "Q2", "Q3", "Q4"])
    quarter_label = quarter_code  # Display as-is

else:
    fiscal_year = st.text_input("Enter Financial Year (e.g., 2025-26)")
    quarter_display_map = {
        "Q1 (Apr-Jun)": "q1",
        "Q2 (Jul-Sep)": "q2",
        "Q3 (Oct-Dec)": "q3",
        "Q4 (Jan-Mar)": "q4"
    }
    quarter_code_map_tcs = {
        "Q1 (Apr-Jun)": "quarter1",
        "Q2 (Jul-Sep)": "quarter2",
        "Q3 (Oct-Dec)": "quarter3",
        "Q4 (Jan-Mar)": "quarter4"
    }
    quarter_label = st.selectbox("Select Quarter:", list(quarter_display_map.keys()))
    quarter_code = quarter_display_map[quarter_label]
    quarter_input_tcs = quarter_code_map_tcs[quarter_label]

# --- Keywords ---
keywords = [
    "bfsi", "bank", "banking", "insurance", "financial services", "securities", "retail",
    "investment", "finance", "financial", "asset management", "wealth management", "capital markets",
    "payments", "cards and payments", "brokerage", "trading", "fintech", "treasury", "insurer",
    "reinsurance", "reinsurer", "insurtech", "mortgage", "lender", "lending",
    "custody and fund administration", "custodian"
]
keywords_lower = [k.lower() for k in keywords]

def matches_keywords(line):
    return any(keyword in line.lower() for keyword in keywords)

def highlight_keywords(text):
    for kw in keywords:
        pattern = re.compile(rf"({re.escape(kw)})", re.IGNORECASE)
        text = pattern.sub(r"<b>\1</b>", text)
    return text


def create_docx(highlights, fy, quarter, company):
    doc = Document()
    doc.add_heading(f"{company} BFSI Highlights – FY {fy}, {quarter}", level=1)
    for idx, sentence in enumerate(highlights, 1):
        p = doc.add_paragraph(f"{idx}. ", style="List Number")
        words = re.split(r'(\W+)', sentence)
        for word in words:
            run = p.add_run(word)
            if word.lower() in keywords_lower:
                run.bold = True
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- Extractors ---
def extract_tcs(fy_input, quarter_input_tcs):
    highlights = []
    url = f"https://www.tcs.com/investor-relations/financial-statements#year={fy_input}&quarter={quarter_input_tcs}"

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(7)

    pdf_url = None
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        text = link.text.strip().lower()
        href = link.get_attribute("href")
        if "press release" in text and "usd" in text and href and href.endswith(".pdf"):
            pdf_url = href
            break
    driver.quit()

    if not pdf_url:
        return None, url

    response = requests.get(pdf_url)
    with open("tcs.pdf", "wb") as f:
        f.write(response.content)

    with pdfplumber.open("tcs.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += " ".join([line.strip() for line in page_text.split("\n") if not re.match(r'^\s*Page\s+\d+\s+of\s+\d+\s*$', line)])

    match = re.search(r'(Key Highlights|Key Wins)(.*?)(Customer Speak)', full_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return [], pdf_url

    highlight_block = match.group(2)
    collapsed_block = re.sub(r'\s{2,}', ' ', highlight_block.strip())
    collapsed_block = re.sub(r'\(.*?ranks.*?\)', '', collapsed_block, flags=re.IGNORECASE)
    sentences = re.split(r'(?<=[.])\s+', collapsed_block)
    for sentence in sentences:
        if matches_keywords(sentence):
            highlights.append(sentence.strip())

    return highlights, pdf_url

def extract_techm(fy_input, quarter_code):
    fy_match = re.match(r'^20(\d{2})-?(\d{2})$', fy_input)
    if not fy_match:
        return None, ""
    fy_short = fy_match.group(2)
    pdf_url = f"https://insights.techmahindra.com/investors/tml-{quarter_code}-fy-{fy_short}-press-release.pdf"
    try:
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return None, pdf_url
        with open("techm_press_release.pdf", "wb") as f:
            f.write(response.content)

        highlights = []
        with pdfplumber.open("techm_press_release.pdf") as pdf:
            full_text = " ".join(
                " ".join(re.sub(r'^\s*•\s*', '', line).strip() for line in page.extract_text().split("\n"))
                for page in pdf.pages if page.extract_text()
            )

        match = re.search(r'(Key Deal Wins|Key Wins)(.*?)(Business Highlights)', full_text, re.DOTALL | re.IGNORECASE)
        if not match:
            return [], pdf_url

        win_block = match.group(2)
        cleaned_block = re.sub(r'\s{2,}', ' ', win_block.strip())
        sentences = re.split(r'(?<=[.])\s+', cleaned_block)
        return [s.strip() for s in sentences if matches_keywords(s)], pdf_url
    except Exception as e:
        return None, str(e)

def extract_mphasis(fy_input, quarter_code):
    end_year = "20" + fy_input.split("-")[1]
    url = f"https://www.mphasis.com/content/dam/mphasis-com/global/en/investors/financial-results/{end_year}/{quarter_code}-earnings-press-release.pdf"
    response = requests.get(url)
    if response.status_code != 200:
        return None, url
    with open("mphasis.pdf", "wb") as f:
        f.write(response.content)
    with pdfplumber.open("mphasis.pdf") as pdf:
        full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    match = re.search(r"(deal wins\s*:?.*?)(awards and recognitions|recognitions and analyst positioning)", full_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return [], url
    section = re.sub(r'[\u2022\u2023\u25AA\u25CF\u2013\u2014\-]', '\n', match.group(1))
    fragments = re.split(r'(?<=[.!?])\s+(?=[A-Z])', re.sub(r'\s+', ' ', section))
    return [line.strip() for line in fragments if matches_keywords(line)], url

def extract_infosys(fiscal_year, quarter):
    base_url = "https://www.infosys.com/investors/reports-filings/quarterly-results"
    pdf_url = f"{base_url}/{fiscal_year}/{quarter}/documents/ifrs-usd-press-release.pdf"
    try:
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return None, pdf_url

        with pdfplumber.open(BytesIO(response.content)) as pdf:
            full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        full_text = re.sub(r"Page \d+ of \d+", "", full_text).replace("•", "")
        full_text = re.sub(r"\s+", " ", full_text)

        match = re.search(r"Client wins\s*&\s*Testimonials(.*?)(Recognitions\s*&\s*Awards|Recognitions|Awards)", full_text, re.IGNORECASE | re.DOTALL)
        if not match:
            return [], pdf_url

        section = match.group(1).strip()
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", section)
        return [highlight_keywords(s.strip()) for s in sentences if matches_keywords(s)], pdf_url
    except Exception as e:
        return None, str(e)

def extract_zensar(fy_input, quarter_code):
    base = "https://www.zensar.com/sites/default/files/investor/analyst-meet/"
    suffixes = [
        f"Zensar-{quarter_code}FY{fy_input}-Press-release.pdf",
        f"Zensar-{quarter_code}FY{fy_input}-Press-Release.pdf",
        f"Zensar-{quarter_code}FY{fy_input}Press-Release.pdf",
        f"Zensar-{quarter_code}FY{fy_input}Press-release.pdf",
    ]
    pdf_url = None
    for suffix in suffixes:
        url = base + suffix
        if requests.head(url).status_code == 200:
            pdf_url = url
            break
    if not pdf_url:
        return None, None

    response = requests.get(pdf_url)
    if response.status_code != 200:
        return None, pdf_url

    def combine_multiline_points(lines):
        points, current = [], ""
        for line in lines:
            if re.match(r"^[•\-\d\.]{0,3}\s*[A-Z]", line):
                if current:
                    points.append(current.strip())
                current = line
            else:
                current += " " + line
        if current:
            points.append(current.strip())
        return points

    with pdfplumber.open(BytesIO(response.content)) as pdf:
        full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    start_match = re.search(r"Significant Wins", full_text, re.IGNORECASE)
    end_matches = [re.search(r"Awards and Recognitions", full_text, re.IGNORECASE),
                   re.search(r"Corporate Excellence Snapshot", full_text, re.IGNORECASE)]
    end_pos = min([m.start() for m in end_matches if m], default=None)

    if not start_match or not end_pos:
        return [], pdf_url

    segment = full_text[start_match.end():end_pos]
    lines = [line.strip() for line in segment.split("\n") if line.strip()]
    points = combine_multiline_points(lines)

    matches = []
    for point in points:
        cleaned = re.sub(r"^[•\-\d\.\s]+", "", point)
        if matches_keywords(cleaned):
            matches.append(cleaned.strip())

    return matches, pdf_url

# --- Run Button ---
if st.button("Get Highlights"):
    if not fiscal_year or \
   (company == "Infosys" and not re.match(r'^\d{4}-\d{4}$', fiscal_year)) or \
   (company not in ["Infosys", "Zensar"] and not re.match(r'^\d{4}-\d{2}$', fiscal_year)) or \
   (company == "Zensar" and not re.match(r'^\d{2}$', fiscal_year)):
        st.error("❌ Invalid fiscal year format.")
        st.stop()

    highlights, source_url = [], ""
    if company == "TCS":
        highlights, source_url = extract_tcs(fiscal_year, quarter_input_tcs)
    elif company == "Tech Mahindra":
        highlights, source_url = extract_techm(fiscal_year, quarter_code)
    elif company == "Mphasis":
        highlights, source_url = extract_mphasis(fiscal_year, quarter_code)
    elif company == "Infosys":
        highlights, source_url = extract_infosys(fiscal_year, quarter_code)
    elif company == "Zensar":
        highlights, source_url = extract_zensar(fiscal_year, quarter_code)



    if highlights is None:
        st.error(f"❌ PDF not found or error: {source_url}")
    elif highlights:
        with st.container():
            html = f"""
            <div class="white-box">
                <h3>BFSI Highlights from {company} (FY {fiscal_year}, {quarter_label})</h3>
            """
            for idx, line in enumerate(highlights, 1):
                highlighted = highlight_keywords(line)
                html += f"<p><b>{idx}.</b> {highlighted}</p>"

            html += "</div>"  # Close white-box
            st.markdown(html, unsafe_allow_html=True)

            # Show download button inside Streamlit block
            docx_file = create_docx(highlights, fiscal_year, quarter_label, company)
            st.download_button(
                label="📥 Download Highlights as Word Document",
                data=docx_file,
                file_name=f"{company}_BFSI_Highlights_{fiscal_year}_{quarter_code}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    else:
        st.warning("No BFSI-related highlights found.")
