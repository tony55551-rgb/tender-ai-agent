import streamlit as st
import google.generativeai as genai
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Pro", page_icon="🇮🇳", layout="wide")

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
    
    # Reset Button to clear memory
    if st.button("🔄 Start New Tender"):
        for key in list(st.session_state.keys()):
            if key != 'password_correct': # Keep logged in
                del st.session_state[key]
        st.rerun()

# --- MAIN APP ---
st.title("🇮🇳 AI Tender Assistant (Persistent)")

# 1. Initialize Memory (Session State)
# This ensures variables exist even if we haven't generated them yet
if "summary" not in st.session_state:
    st.session_state.summary = None
if "compliance" not in st.session_state:
    st.session_state.compliance = None
if "letter" not in st.session_state:
    st.session_state.letter = None
if "myfile" not in st.session_state:
    st.session_state.myfile = None

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    # Upload to Gemini (Only once per file)
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
    # Only show button if we haven't generated results yet
    if st.session_state.summary is None and st.session_state.myfile:
        if st.button("🚀 Run Full Analysis"):
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # --- STEP A: SUMMARY ---
            with st.spinner("Generating Summary..."):
                prompt1 = f"Extract Project Name, EMD, Deadline, Turnover, and Experience. Translate to {language}."
                response1 = model.generate_content([prompt1, st.session_state.myfile])
                st.session_state.summary = response1.text # SAVE TO MEMORY

            # --- STEP B: COMPLIANCE ---
            with st.spinner("Checking Compliance..."):
                prompt2 = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status."
                response2 = model.generate_content([prompt2, st.session_state.myfile])
                st.session_state.compliance = response2.text # SAVE TO MEMORY

            # --- STEP C: LETTER ---
            with st.spinner("Drafting Letter..."):
                prompt3 = f"Write a formal Bid Submission Letter in {language}."
                response3 = model.generate_content([prompt3, st.session_state.myfile])
                st.session_state.letter = response3.text # SAVE TO MEMORY
            
            st.rerun() # Refresh page to show results

# 4. Display Results (Reads from Memory)
if st.session_state.summary:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat"])
    
    with tab1:
        st.subheader(f"Executive Summary ({language})")
        st.markdown(st.session_state.summary) # Read from memory
    
    with tab2:
        st.subheader("Compliance Matrix")
        st.markdown(st.session_state.compliance) # Read from memory
    
    with tab3:
        st.subheader("Bid Submission Letter")
        st.text_area("Copy this:", st.session_state.letter, height=400) # Read from memory
    
    with tab4:
        st.subheader("Ask the Tender")
        user_q = st.text_input("Ask a question:")
        if user_q:
            model = genai.GenerativeModel('gemini-2.5-flash')
            res = model.generate_content([f"Answer in {language}: {user_q}", st.session_state.myfile])
            st.write(res.text)
