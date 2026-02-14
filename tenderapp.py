import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderAI Pro", page_icon="🔒", layout="centered")

# --- AUTHENTICATION ---
MASTER_PASSWORD = st.secrets.get("APP_PASSWORD", "TenderKing2026") 

def check_password():
    def password_entered():
        if st.session_state["password"] == MASTER_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 TenderAI Login")
    st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("❌ Access Denied")
    return False

if not check_password():
    st.stop()

# --- MAIN APP ---
st.title("🇮🇳 AI Tender Assistant (Pro)")
st.caption("Powered by Gemini 2.5 Flash")

api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ API Key missing. Please add it to Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    with open("temp_tender.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("File Uploaded! ✅")

    if st.button("Analyze Tender"):
        with st.spinner("🧠 Analyzing (If this takes time, we are waiting for quota)..."):
            try:
                # 1. Upload
                myfile = genai.upload_file("temp_tender.pdf")
                time.sleep(2) 

                # 2. SELECT THE UNUSED MODEL
                model = genai.GenerativeModel('gemini-2.5-flash')

                # 3. DEFINE TASKS
                prompt_extract = """
                Extract these details into a Markdown Table:
                - Project Name
                - Estimated Cost
                - EMD Amount
                - Bid Submission Deadline
                - Financial Turnover Required
                - Technical Experience Required
                """
                
                # 4. EXECUTE WITH RETRY LOGIC
                try:
                    response = model.generate_content([prompt_extract, myfile])
                    st.subheader("📊 Executive Summary")
                    st.markdown(response.text)
                    
                    st.divider()
                    st.subheader("📝 Bid Submission Letter")
                    prompt_letter = "Write a formal Bid Submission Cover Letter for this tender. Output ONLY the letter."
                    letter = model.generate_content([prompt_letter, myfile])
                    st.text_area("Copy your letter:", letter.text, height=400)
                    
                except exceptions.ResourceExhausted:
                    st.warning("🚦 Traffic Jam! The free tier is busy. Waiting 60 seconds...")
                    time.sleep(60)
                    st.info("🔄 Retrying now...")
                    # Retry once
                    response = model.generate_content([prompt_extract, myfile])
                    st.subheader("📊 Executive Summary")
                    st.markdown(response.text)

            except Exception as e:
                st.error(f"Error: {e}")
