import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Lite", page_icon="⚡", layout="wide")

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

# --- HELPER: ROBUST GENERATOR WITH COUNTDOWN ---
def generate_smart(model, prompt, file_content, status_text):
    """Retries with a visual countdown if the server is busy."""
    try:
        return model.generate_content([prompt, file_content])
    except exceptions.ResourceExhausted:
        # If busy, we wait 30 seconds with a visual timer
        status_text.warning("🚦 Server Busy. Switching to queue...")
        progress_bar = status_text.progress(0)
        for i in range(30):
            time.sleep(1)
            progress_bar.progress((i + 1) / 30)
        
        status_text.info("🔄 Retrying now...")
        try:
            return model.generate_content([prompt, file_content]) # Retry 1
        except:
            status_text.error("❌ Server is too busy right now. Please try again in 5 minutes.")
            return None
    except Exception as e:
        status_text.error(f"Error: {e}")
        return None

# --- MAIN APP ---
st.title("⚡ AI Tender Assistant (Lite Speed)")

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
                st.success("File Ready! Click 'Run Analysis' below.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # 3. The "Run" Button
    if st.session_state.summary is None and st.session_state.myfile:
        if st.button("🚀 Run Analysis (Lite Mode)"):
            # SWITCHING TO THE LITE MODEL
            model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
            
            status_text = st.empty()
            
            # --- STEP A: SUMMARY ---
            status_text.text("1/3 Generating Summary...")
            prompt1 = f"Extract Project Name, EMD, Deadline, Turnover, and Experience. Translate to {language}."
            res1 = generate_smart(model, prompt1, st.session_state.myfile, status_text)
            if res1: st.session_state.summary = res1.text
            
            time.sleep(2) # Short breath

            # --- STEP B: COMPLIANCE ---
            status_text.text("2/3 Checking Compliance...")
            prompt2 = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status."
            res2 = generate_smart(model, prompt2, st.session_state.myfile, status_text)
            if res2: st.session_state.compliance = res2.text

            time.sleep(2) # Short breath

            # --- STEP C: LETTER ---
            status_text.text("3/3 Drafting Letter...")
            prompt3 = f"Write a formal Bid Submission Letter in {language}."
            res3 = generate_smart(model, prompt3, st.session_state.myfile, status_text)
            if res3: st.session_state.letter = res3.text
            
            status_text.success("✅ Analysis Complete!")
            time.sleep(1)
            st.rerun()

# 4. Display Results
if st.session_state.summary:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat"])
    
    with tab1:
        st.subheader(f"Executive Summary ({language})")
        st.markdown(st.session_state.summary)
    
    with tab2:
        st.subheader("Compliance Matrix")
        st.markdown(st.session_state.compliance)
    
    with tab3:
        st.subheader("Bid Submission Letter")
        st.text_area("Copy this:", st.session_state.letter, height=400)
    
    with tab4:
        st.subheader("Ask the Tender")
        user_q = st.text_input("Ask a question:")
        if user_q:
            try:
                # Chat uses the Lite model too for speed
                model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
                res = model.generate_content([f"Answer in {language}: {user_q}", st.session_state.myfile])
                st.write(res.text)
            except:
                st.error("Server Busy. Try again in a moment.")
