import streamlit as st
import google.generativeai as genai
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Ultimate", page_icon="🇮🇳", layout="wide")

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

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Controls")
    language = st.selectbox("Output Language", ["English", "Hindi", "Telugu"])
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing!")
        st.stop()
    genai.configure(api_key=api_key)

# --- MAIN APP ---
st.title("🇮🇳 AI Tender Assistant (Fast Mode)")

if "myfile" not in st.session_state:
    st.session_state.myfile = None

uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    # 1. Upload File Only Once
    if st.session_state.myfile is None:
        with st.spinner("📤 Uploading to AI Brain..."):
            try:
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                myfile = genai.upload_file("temp.pdf")
                time.sleep(2)
                st.session_state.myfile = myfile
                st.success("File Ready! Select a Tab below.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # 2. The Tabs (Click to Activate)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat"])

    # SHARED MODEL
    model = genai.GenerativeModel('gemini-2.5-flash')

    # --- TAB 1: SUMMARY ---
    with tab1:
        st.header("Executive Summary")
        if st.button("Generate Summary"):
            with st.spinner("Analyzing..."):
                try:
                    prompt = f"Extract Project Name, EMD, Deadline, Turnover, and Experience. Translate to {language}."
                    response = model.generate_content([prompt, st.session_state.myfile])
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 2: COMPLIANCE ---
    with tab2:
        st.header("Compliance Matrix")
        if st.button("Generate Matrix"):
            with st.spinner("Scanning 50+ pages..."):
                try:
                    prompt = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status."
                    response = model.generate_content([prompt, st.session_state.myfile])
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 3: LETTER ---
    with tab3:
        st.header("Bid Letter")
        if st.button("Draft Letter"):
            with st.spinner("Writing..."):
                try:
                    prompt = f"Write a formal Bid Submission Letter in {language}. Output ONLY the letter."
                    response = model.generate_content([prompt, st.session_state.myfile])
                    st.text_area("Copy this:", response.text, height=400)
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 4: CHAT ---
    with tab4:
        st.header("Ask the Tender")
        user_q = st.text_input("Example: Is there a penalty for delay?")
        if user_q:
            with st.spinner("Thinking..."):
                try:
                    prompt = f"Answer this based on the file: {user_q}. Language: {language}"
                    res = model.generate_content([prompt, st.session_state.myfile])
                    st.write(res.text)
                except Exception as e:
                    st.error("Session timed out. Reload page.")
