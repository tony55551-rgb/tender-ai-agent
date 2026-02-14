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
    initial_sidebar_state="expanded" # Forces the Left Bar to open by default
)

# --- 2. CSS HACKS: HIDE ADMIN TOOLS ---
# This hides the "Manage App" button, Hamburger Menu, and Footer
# But keeps the Sidebar visible and professional.
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. SECURE ACCESS SYSTEM (No Hardcoded Passwords) ---
def get_valid_keys():
    # 1. Try to get the LIST of codes from Secrets
    try:
        keys = st.secrets.get("access_keys")
        if keys:
            # If it's a single string, wrap it in a list
            if isinstance(keys, str): return [keys]
            return keys
    except:
        pass
    
    # 2. IF NO SECRETS FOUND: Stop the app.
    # This prevents unauthorized access if secrets aren't set up.
    return [] 

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        valid_keys = get_valid_keys()
        
        # Security Check: If no keys are configured in Secrets
        if not valid_keys:
            st.error("⚠️ System Error: Access Keys not configured in Secrets.")
            return

        # Check if the entered password matches ANY key in the list
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
        st.info("Authorized Personnel Only.")
        
        # INPUT FIELD
        st.text_input("Enter your access code", type="password", on_change=password_entered, key="password")
        
        if "password_correct" in st.session_state:
            st.error("❌ Invalid Access Code.")
            
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
        # COPYRIGHT IN PDF
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
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, f"A: {clean(a)}")
            pdf.ln(3)

    # 4. Draft Letter
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "4. Draft Bid Letter", 0, 1)
    pdf.set_font("Courier", size=10)
    pdf.multi_cell(0, 5, clean(letter))

    return pdf.output(dest='S').encode('latin-1')

# --- PROFESSIONAL SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏢 **TenderAI** Enterprise")
    st.success("✅ System Online")
    
    # Display User Info
    user_key = st.session_state.get('used_key', 'Admin')
    st.caption(f"Logged in as: **{user_key}**")
    
    st.markdown("---")
    st.markdown("### ⚙️ **Configuration**")
    language = st.selectbox("Output Language", ["English", "Hindi", "Telugu"])
    
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing!")
        st.stop()
    genai.configure(api_key=api_key)
    
    st.markdown("---")
    if st.button("🔄 Reset / New Project", use_container_width=True):
        for key in list(st.session_state.keys()):
            # Keep login details, clear everything else
            if key not in ['password_correct', 'used_key']: 
                del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.caption("Secured by Google Cloud")
    # COPYRIGHT IN SIDEBAR
    st.markdown("**© 2026 ynotAIagent bundles**") 

# --- HELPER: ROBUST GENERATOR (Traffic Fix) ---
def generate_safe(prompt, file_content):
    # Try 4 different models to find a free lane
    models = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash-lite-001', 'gemini-1.5-pro']
    
    status_placeholder = st.empty()
    
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content([prompt, file_content])
        except exceptions.ResourceExhausted:
            time.sleep(1)
            continue # Try next model
        except Exception:
            continue
            
    # If all fail, wait and retry
    status_placeholder.warning("🚦 High Traffic. Switching lines...")
    time.sleep(10)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content([prompt, file_content])
    except:
        st.error("❌ All AI servers are busy. Please wait 2 minutes.")
        return None

# --- MAIN APP LAYOUT ---
col_hero_1, col_hero_2 = st.columns([3, 1])
with col_hero_1:
    st.title("🇮🇳 Tender Intelligence Suite")
    st.markdown("**Automated Analysis • Compliance Checks • Bid Drafting**")

st.markdown("---")

# 1. Initialize Memory
if "summary" not in st.session_state: st.session_state.summary = None
if "compliance" not in st.session_state: st.session_state.compliance = None
if "letter" not in st.session_state: st.session_state.letter = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "myfile" not in st.session_state: st.session_state.myfile = None

# 2. File Uploader
if st.session_state.myfile is None:
    st.info("👋 Welcome. Please upload a Tender Document (PDF) to begin analysis.")
    uploaded_file = st.file_uploader("Select Tender PDF", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        with st.spinner("🔄 Encrypting & Uploading to AI Core..."):
            try:
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                myfile = genai.upload_file("temp.pdf")
                while myfile.state.name == "PROCESSING":
                    time.sleep(1)
                    myfile = genai.get_file(myfile.name)
                
                st.session_state.myfile = myfile
                st.success("✅ Document Loaded Successfully")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")

else:
    # 3. Dashboard
    st.success(f"📂 Active Document: **{st.session_state.myfile.display_name}**")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executive Summary", 
        "✅ Compliance Matrix", 
        "📝 Draft Bid Letter", 
        "💬 AI Consultant", 
        "📥 Export Report"
    ])
    
    # --- TAB 1: SUMMARY ---
    with tab1:
        st.markdown("### 📋 Project Overview")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            if st.button("🚀 Generate Summary", type="primary"):
                with st.spinner("Analyzing..."):
                    prompt = f"Extract Project Name, EMD (in Rs), Deadline, Turnover, and Experience. Translate to {language}. Replace symbol '₹' with 'Rs.'."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.summary = res.text
                        st.rerun()

    # --- TAB 2: COMPLIANCE ---
    with tab2:
        st.markdown("### ✅ Qualification Check")
        if st.session_state.compliance:
            st.markdown(st.session_state.compliance)
        else:
            if st.button("🔍 Scan for Compliance", type="primary"):
                with st.spinner("Scanning..."):
                    prompt = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status. Replace symbol '₹' with 'Rs.'."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.compliance = res.text
                        st.rerun()

    # --- TAB 3: LETTER ---
    with tab3:
        st.markdown("### ✍️ Bid Submission Letter")
        if st.session_state.letter:
            st.text_area("Final Draft", st.session_state.letter, height=450)
        else:
            if st.button("📝 Write Letter", type="primary"):
                with st.spinner("Drafting..."):
                    prompt = f"Write a formal Bid Submission Letter in {language}."
                    res = generate_safe(prompt, st.session_state.myfile)
                    if res:
                        st.session_state.letter = res.text
                        st.rerun()

    # --- TAB 4: CHAT ---
    with tab4:
        st.markdown("### 💬 Ask the Consultant")
        for q, a in st.session_state.chat_history:
            st.markdown(f"**You:** {q}")
            st.info(f"**AI:** {a}")
        
        st.markdown("---")
        col_q, col_btn = st.columns([4,1])
        with col_q:
            user_q = st.text_input("Ask a question:", placeholder="e.g., Is Joint Venture allowed?")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ask", type="primary", use_container_width=True):
                if user_q:
                    with st.spinner("Thinking..."):
                        res = generate_safe(f"Answer in {language}. Replace '₹' with 'Rs.': {user_q}", st.session_state.myfile)
                        if res:
                            st.session_state.chat_history.append((user_q, res.text))
                            st.rerun()

    # --- TAB 5: DOWNLOAD ---
    with tab5:
        st.markdown("### 📥 Final Report")
        if st.session_state.summary and st.session_state.compliance and st.session_state.letter:
            if st.button("📄 Compile PDF Report", type="primary"):
                with st.spinner("Building PDF..."):
                    try:
                        pdf_bytes = create_pdf(
                            st.session_state.summary,
                            st.session_state.compliance,
                            st.session_state.letter,
                            st.session_state.chat_history
                        )
                        st.download_button(
                            label="⬇️ Download PDF Now",
                            data=pdf_bytes,
                            file_name="Tender_Analysis_Report.pdf",
                            mime="application/pdf"
                        )
                        st.success("Ready for download!")
                    except Exception as e:
                        st.error(f"PDF Error: {e}")
        else:
            st.warning("⚠️ Complete Analysis first.")
