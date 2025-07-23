
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


import os
import time
import re
import requests
import pdfplumber
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

st.set_page_config(page_title="TCS BFSI Key Highlights", layout="centered")

st.title("TCS Financial Key Highlights Extractor")

# Input fields
fy_input = st.text_input("Enter Financial Year (e.g. 2025-26):")
quarter_input = st.selectbox("Select Quarter:", ["quarter1", "quarter2", "quarter3", "quarter4"])

if st.button("Get Highlights"):
    if not fy_input or not quarter_input:
        st.warning("Please enter both Financial Year and Quarter.")
        st.stop()

    # Keywords to search
    keywords = [
        "bsfi", "bank", "banking", "insurance", "financial services", "securities",
        "retail", "icici", "hdfc", "sbi", "axis", "kotak", "nbfc",
        "credit", "debit", "investment", "finance"
    ]

    def matches_keywords(line):
        return any(keyword in line.lower() for keyword in keywords)

    # Construct URL
    url = f"https://www.tcs.com/investor-relations/financial-statements#year={fy_input}&quarter={quarter_input}"

    # Set up Selenium headless browser
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')  # For some environments like Streamlit Cloud

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(7)

        # Locate PDF link
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
            st.error("'Press Release - USD' PDF not found on the page.")
            st.stop()

        pdf_filename = "press_release_usd.pdf"
        response = requests.get(pdf_url)
        with open(pdf_filename, "wb") as f:
            f.write(response.content)

        highlights = []
        capture = False

        with pdfplumber.open(pdf_filename) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split("\n")

                for line in lines:
                    lower_line = line.lower()

                    if "key highlights" in lower_line:
                        capture = True
                    elif capture and (
                        "financial performance" in lower_line or
                        "revenue" in lower_line or
                        re.match(r"^\d+\.", lower_line)
                    ):
                        capture = False
                    elif capture and matches_keywords(line):
                        highlights.append(line.strip())

        if highlights:
            st.subheader(f" Key Highlights related to BFSI (FY {fy_input}, {quarter_input}):")
            for h in highlights:
                st.markdown(f"• {h}")
        else:
            st.warning(" No relevant highlights found in the 'Key Highlights' section.")
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")

