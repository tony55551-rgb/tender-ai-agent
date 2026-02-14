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

# --- 2. HIDE STREAMLIT BRANDING & ADD CUSTOM FOOTER ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
MASTER_PASSWORD = st.secrets.get("APP_PASSWORD", "TenderKing2026") 

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        if st.session_state["password"] == MASTER_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Professional Login Screen
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔒 TenderAI Secure Access</h1>", unsafe_allow_html=True)
        st.info("This is a restricted enterprise portal. Please authorize yourself.")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("❌ Access Denied. Contact Administrator.")
    return False

if not check_password():
    st.stop()

# --- PDF GENERATOR WITH BRANDING ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'TenderAI Professional Analysis Report', 0, 1, 'C')
        self.line(10, 20, 200, 20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        # BRANDING IN PDF
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
        for q, a in chat_history:
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(0, 6, f"Q: {clean(q)}")
            pdf.set_font("Arial", size=
