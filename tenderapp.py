import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Manual", page_icon="🎛️", layout="wide")

# --- AUTHENTICATION ---
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

    st.title("🔒 TenderAI Login")
    st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("❌ Access Denied")
    return False

if not check_password():
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Controls")
    language = st.selectbox("Output Language", ["English", "Hindi", "Telugu"])
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing!")
        st.stop()
    genai.configure(api_key=api_key)
    
    if st.button("🔄 Start New Tender"):
        for key in list(st.session_state.keys()):
            if key != 'password_correct': 
                del st.session_state[key]
        st.rerun()

# --- HELPER: GENERATOR WITH FALLBACK ---
def generate_safe(prompt, file_content):
    """Tries to generate content using the best available model."""
    # List of models to try (Best to Lite)
    models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite-001', 'gemini-1.5-pro']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content([prompt, file_content])
        except exceptions.ResourceExhausted:
            st.warning(f"⚠️ {model_name} is busy. Trying next model...")
            time.sleep(2)
            continue # Try next model
        except Exception:
            continue # If model not found, try next
            
    st.error("❌ All models are busy right now. Please wait 1 minute.")
    return None

# --- MAIN APP ---
st.title("🇮🇳 AI Tender Assistant (Manual Mode)")

# 1. Initialize Memory
if "summary" not in st.session_state: st.session_state.summary = None
if "compliance" not in st.session_state: st.session_state.compliance = None
if "letter" not in st.session_state: st.session_state.letter = None
if "myfile" not in st.session_state: st.session_state.myfile = None

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    # Upload to Gemini (Only once)
    if st.session_state.myfile is None:
        with st.spinner("📤 Uploading to AI Brain..."):
            try:
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                myfile = genai.upload_file("temp.pdf")
                while myfile.state.name == "PROCESSING":
                    time.sleep(1)
                    myfile = genai.get_file(myfile.name)
                
                st.session_state.myfile = myfile
                st.success("File Ready! Select a Tab below.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # 3. The Manual Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat"])
    
    # --- TAB 1: SUMMARY ---
    with tab1:
        st.header(f"Executive Summary ({language})")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            if st.button("Generate Summary"):
                with st.spinner("Analyzing..."):
                    prompt = f"Extract Project Name, EMD, Deadline, Turnover, and Experience. Translate to {language}."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.summary = res.text
                        st.rerun()

    # --- TAB 2: COMPLIANCE ---
    with tab2:
        st.header("Compliance Matrix")
        if st.session_state.compliance:
            st.markdown(st.session_state.compliance)
        else:
            if st.button("Generate Matrix"):
                with st.spinner("Scanning..."):
                    prompt = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.compliance = res.text
                        st.rerun()

    # --- TAB 3: LETTER ---
    with tab3:
        st.header("Bid Submission Letter")
        if st.session_state.letter:
            st.text_area("Copy this:", st.session_state.letter, height=400)
        else:
            if st.button("Draft Letter"):
                with st.spinner("Drafting..."):
                    prompt = f"Write a formal Bid Submission Letter in {language}."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.letter = res.text
                        st.rerun()

    # --- TAB 4: CHAT ---
    with tab4:
        st.header("Ask the Tender")
        user_q = st.text_input("Ask a question:")
        if user_q:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([f"Answer in {language}: {user_q}", st.session_state.myfile])
                st.write(res.text)
            except:
                st.warning("Server busy. Wait 10s.")
