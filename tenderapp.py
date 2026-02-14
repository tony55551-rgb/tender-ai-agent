import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
from fpdf import FPDF

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Report", page_icon="📄", layout="wide")

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

# --- PDF GENERATOR FUNCTION ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'TenderAI Analysis Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(summary, compliance, letter, chat_history):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Helper to clean text (FPDF doesn't like some Unicode symbols)
    def clean(text):
        return text.encode('latin-1', 'replace').decode('latin-1').replace("?", "")

    # 1. Executive Summary
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "1. Executive Summary", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, clean(summary))
    pdf.ln(5)

    # 2. Compliance Matrix
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "2. Compliance Matrix", 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, clean(compliance))
    pdf.ln(5)

    # 3. Chat History
    if chat_history:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "3. Q&A Notes", 0, 1)
        pdf.set_font("Arial", size=11)
        for q, a in chat_history:
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(0, 8, f"Q: {clean(q)}")
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, f"A: {clean(a)}")
            pdf.ln(3)

    # 4. Draft Letter
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "4. Draft Bid Letter", 0, 1)
    pdf.set_font("Courier", size=10) # Monospace for letters
    pdf.multi_cell(0, 6, clean(letter))

    return pdf.output(dest='S').encode('latin-1')

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

# --- HELPER: SAFE GENERATOR ---
def generate_safe(prompt, file_content):
    models = ['gemini-1.5-flash', 'gemini-2.0-flash-lite-001', 'gemini-1.5-pro']
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content([prompt, file_content])
        except exceptions.ResourceExhausted:
            st.warning(f"⚠️ {model_name} busy, switching engine...")
            time.sleep(1)
            continue
        except Exception:
            continue
    st.error("❌ All AI models are busy. Wait 1 min.")
    return None

# --- MAIN APP ---
st.title("🇮🇳 AI Tender Assistant (Report Mode)")

# 1. Initialize Memory
if "summary" not in st.session_state: st.session_state.summary = None
if "compliance" not in st.session_state: st.session_state.compliance = None
if "letter" not in st.session_state: st.session_state.letter = None
if "chat_history" not in st.session_state: st.session_state.chat_history = [] # New: List for chat
if "myfile" not in st.session_state: st.session_state.myfile = None

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Tender PDF", type="pdf")

if uploaded_file:
    if st.session_state.myfile is None:
        with st.spinner("📤 Uploading..."):
            try:
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                myfile = genai.upload_file("temp.pdf")
                while myfile.state.name == "PROCESSING":
                    time.sleep(1)
                    myfile = genai.get_file(myfile.name)
                
                st.session_state.myfile = myfile
                st.success("File Ready!")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    # 3. Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat", "📥 Download Report"])
    
    # --- TAB 1: SUMMARY ---
    with tab1:
        st.header(f"Executive Summary ({language})")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            if st.button("Generate Summary"):
                with st.spinner("Analyzing..."):
                    prompt = f"Extract Project Name, EMD (in Rs), Deadline, Turnover, and Experience. Translate to {language}. Replace symbol '₹' with 'Rs.'."
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
                    prompt = f"Create a table of Technical & Qualification Criteria. Columns: Requirement ({language}), Page No, Status. Replace symbol '₹' with 'Rs.'."
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

    # --- TAB 4: CHAT (With History) ---
    with tab4:
        st.header("Ask the Tender")
        
        # Display old chat
        for q, a in st.session_state.chat_history:
            st.info(f"Q: {q}")
            st.write(f"A: {a}")
        
        user_q = st.text_input("Ask a question:")
        if user_q:
            if st.button("Ask"):
                with st.spinner("Thinking..."):
                    res = generate_safe(f"Answer in {language}. Replace '₹' with 'Rs.': {user_q}", st.session_state.myfile)
                    if res:
                        st.write(res.text)
                        # Save to history
                        st.session_state.chat_history.append((user_q, res.text))
                        st.rerun()

    # --- TAB 5: DOWNLOAD PDF (The New Feature) ---
    with tab5:
        st.header("📥 Download Full Report")
        st.write("This generates a PDF containing the Summary, Compliance Matrix, Chat History, and Bid Letter.")
        
        if st.session_state.summary and st.session_state.compliance and st.session_state.letter:
            if st.button("📄 Generate PDF"):
                with st.spinner("Compiling PDF..."):
                    try:
                        pdf_bytes = create_pdf(
                            st.session_state.summary,
                            st.session_state.compliance,
                            st.session_state.letter,
                            st.session_state.chat_history
                        )
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=pdf_bytes,
                            file_name="Tender_Analysis_Report.pdf",
                            mime="application/pdf"
                        )
                        st.success("PDF Ready! Click the button above.")
                    except Exception as e:
                        st.error(f"PDF Error: {e}")
        else:
            st.warning("⚠️ Please generate the Summary, Compliance, and Letter first!")
