# pip install -r requirements.txt
# streamlit run bfsihighlights_app.py

import os
import time
import re
import requests
import pdfplumber
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from io import BytesIO
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import chromedriver_autoinstaller

st.set_page_config(page_title="TCS BFSI Key Highlights", layout="centered")
st.title("📊 TCS Financial Key Highlights Extractor")

# --- User Input Section ---
st.markdown("### Enter Report Details")

fy_input = st.text_input("Enter Financial Year (e.g. 2025-26):")

quarter_map = {
    "Q1 (Apr-Jun)": "quarter1",
    "Q2 (Jul-Sep)": "quarter2",
    "Q3 (Oct-Dec)": "quarter3",
    "Q4 (Jan-Mar)": "quarter4"
}
quarter_label = st.selectbox("Select Quarter:", list(quarter_map.keys()))
quarter_input = quarter_map[quarter_label]

# --- Keyword Setup ---
keywords = [
    "bsfi", "bank", "banking", "insurance", "financial services", "securities",
    "retail", "icici", "hdfc", "sbi", "axis", "kotak", "nbfc",
    "credit", "debit", "investment", "finance"
]

def matches_keywords(line):
    return any(keyword in line.lower() for keyword in keywords)

def highlight_keywords(text):
    for kw in keywords:
        pattern = re.compile(rf"({re.escape(kw)})", re.IGNORECASE)
        text = pattern.sub(r"**\1**", text)
    return text

def create_docx(highlights, fy, quarter):
    doc = Document()
    doc.add_heading(f"TCS BFSI Highlights – FY {fy}, {quarter}", level=1)
    for idx, sentence in enumerate(highlights, 1):
        p = doc.add_paragraph(f"{idx}. ", style="List Number")
        words = re.split(r'(\W+)', sentence)
        for word in words:
            run = p.add_run(word)
            if word.lower() in keywords:
                run.bold = True
    for para in doc.paragraphs:
        para.paragraph_format.space_after = 6
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_pdf(highlights, fy, quarter):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 50, f"TCS BFSI Highlights – FY {fy}, {quarter}")
    c.setFont("Helvetica", 11)
    y = height - 80
    line_height = 16
    for idx, sentence in enumerate(highlights, 1):
        line = f"{idx}. {sentence}"
        wrapped_lines = text_wrap(line, width - 80, c)
        for wrapped in wrapped_lines:
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 11)
            c.drawString(40, y, wrapped)
            y -= line_height
        y -= 5
    c.save()
    buffer.seek(0)
    return buffer

def text_wrap(text, max_width, canvas_obj):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if canvas_obj.stringWidth(test_line, "Helvetica", 11) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

# --- Main Execution ---
if st.button("Get Highlights"):
    if not fy_input or not quarter_input:
        st.warning("⚠️ Please enter both Financial Year and Quarter.")
        st.stop()

    if not re.match(r'^\d{4}-\d{2}$', fy_input):
        st.error("Please enter Financial Year in the format YYYY-YY (e.g. 2025-26).")
        st.stop()

    url = f"https://www.tcs.com/investor-relations/financial-statements#year={fy_input}&quarter={quarter_input}"

    # Auto-install ChromeDriver
    chromedriver_autoinstaller.install()

    options = Options()
    # Set Chrome binary location only on Render
    if "RENDER" in os.environ:
        options.binary_location = "/opt/render/project/src/.chromium-browser-snap/chrome-linux/chrome"

    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
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
            st.error("❌ 'Press Release - USD' PDF not found on the page.")
            st.stop()

        response = requests.get(pdf_url)
        pdf_filename = "press_release_usd.pdf"
        with open(pdf_filename, "wb") as f:
            f.write(response.content)

        highlights = []

        with pdfplumber.open(pdf_filename) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += "\n" + page_text

        full_text_lower = full_text.lower()
        section_match = re.search(
            r'key highlights(.*?)(financial performance|revenue|business highlights|segment performance|analyst assessments|page \d+)',
            full_text_lower,
            re.DOTALL
        )

        if section_match:
            original_match = re.search(
                r'key highlights(.*?)(financial performance|revenue|business highlights|segment performance|analyst assessments|page \d+)',
                full_text,
                re.DOTALL | re.IGNORECASE
            )

            if original_match:
                highlight_block = original_match.group(1)
                collapsed_block = re.sub(r'\n+', ' ', highlight_block.strip())
                collapsed_block = re.sub(r'\s{2,}', ' ', collapsed_block)

                if '•' in collapsed_block:
                    entries = re.split(r'•\s*', collapsed_block)
                else:
                    entries = re.split(r'(?<=[.])\s+', collapsed_block)

                for entry in entries:
                    clean = entry.strip()
                    if not clean:
                        continue
                    if len(clean) > 200 and '.' not in clean:
                        continue
                    if re.match(r'^[A-Z\s\d:,-]+$', clean):
                        continue
                    if matches_keywords(clean):
                        highlights.append(clean)
        else:
            st.warning("⚠️ 'Key Highlights' section not found. PDF structure may have changed.")

        if highlights:
            st.markdown("---")
            st.markdown(f"### ✅ Key Highlights (FY {fy_input}, {quarter_label})")
            for idx, h in enumerate(highlights, 1):
                h_highlighted = highlight_keywords(h)
                st.markdown(f"**{idx}.** {h_highlighted}")

            docx_file = create_docx(highlights, fy_input, quarter_label)
            st.download_button(
                label="📄 Download as Word Document",
                data=docx_file,
                file_name=f"TCS_BFSI_Highlights_{fy_input}_{quarter_input}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            pdf_file = create_pdf(highlights, fy_input, quarter_label)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_file,
                file_name=f"TCS_BFSI_Highlights_{fy_input}_{quarter_input}.pdf",
                mime="application/pdf"
            )
        elif section_match:
            st.warning("✅ Section found, but no BFSI-related keywords matched.")

    except Exception as e:
        st.error(f"🚨 Error: {str(e)}")
