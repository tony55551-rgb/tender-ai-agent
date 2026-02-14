import streamlit as st
import google.generativeai as genai
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="TenderAI Pro", page_icon="🔒", layout="centered")

# --- AUTHENTICATION (The Lock) ---
# We look for the password in the cloud secrets, or default to a simple one
MASTER_PASSWORD = st.secrets.get("APP_PASSWORD", "TenderKing2026") 

def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == MASTER_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
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
    st.stop()  # Stop here if not logged in

# --- MAIN APP (Only runs after login) ---
st.title("🇮🇳 AI Tender Assistant (Pro)")
st.caption("Secure Enterprise Edition")

# --- API KEY HANDLING ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API Key missing. Please add it to Streamlit Secrets.")
    st.stop()

# Configure Gemini
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Key Error: {e}")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    # Save temp file
    with open("temp_tender.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("File Uploaded! ✅")

    if st.button("Analyze Tender"):
        with st.spinner("🧠 Analyzing Document..."):
            try:
                # Upload to Gemini
                myfile = genai.upload_file("temp_tender.pdf")
                time.sleep(3) # Wait for processing

                # --- THE FIX: USING THE LITE MODEL FROM YOUR LIST ---
                model = genai.GenerativeModel('gemini-2.0-flash-lite-001')

                # 1. Extract Data
                prompt_extract = """
                Extract these details into a Markdown Table:
                - Project Name
                - Estimated Cost
                - EMD Amount
                - Bid Submission Deadline
                - Financial Turnover Required
                - Technical Experience Required
                """
                response = model.generate_content([prompt_extract, myfile])
                st.subheader("📊 Executive Summary")
                st.markdown(response.text)
                
                # 2. Draft Letter
                st.divider()
                st.subheader("📝 Bid Submission Letter")
                prompt_letter = """
                You are a Bid Manager. Write a formal Bid Submission Cover Letter for this tender. 
                Use professional Indian Business English.
                Mention we accept all terms and conditions.
                Output ONLY the letter.
                """
                letter = model.generate_content([prompt_letter, myfile])
                st.text_area("Copy your letter:", letter.text, height=400)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
