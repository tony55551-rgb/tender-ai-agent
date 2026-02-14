import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
from fpdf import FPDF

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TenderAI Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS HACKS: HIDE ADMIN TOOLS ONLY ---
# I removed the code that broke the sidebar. 
# Now it only hides the "Manage App" button and the Header/Footer.
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. VOUCHER SYSTEM ---
def get_valid_keys():
    try:
        keys = st.secrets.get("access_keys")
        if keys:
            if isinstance(keys, str): return [keys]
            return keys
    except:
        pass
    return [st.secrets.get("APP_PASSWORD", "TenderKing2026")]

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        valid_keys = get_valid_keys()
        if st.session_state["password"] in valid_keys:
            st.session_state["password_correct"] = True
            st.session_state["used_key"] = st.session_state["password"] 
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🔒 TenderAI Secure Access</h1>", unsafe_allow_html=True)
        st.info("Enter your Access Voucher to begin.")
        st.text_input("Voucher Code", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("❌ Invalid Voucher.")
    return False

if not check_password():
    st.stop()

# --- PDF GENERATOR ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'TenderAI Professional Analysis Report', 0, 1, 'C')
        self.line(10, 20, 200, 20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'© 2026 ynotAIagent bundles | Page {self.page_no()}', 0, 0, 'C')

def create_pdf(summary, compliance, letter, chat_history):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    def clean(text):
        return text.encode('latin-1', 'replace').decode('latin-1').replace("?", "")

    # 1. Executive Summary
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "1. Executive Summary", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, clean(summary))
    pdf.ln(5)

    # 2. Compliance Matrix
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "2. Compliance Matrix", 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, clean(compliance))
    pdf.ln(5)

    # 3. Chat History
    if chat_history:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "3. Q&A Notes", 0, 1)
        pdf.set_font("Arial", size=11)
        for
