import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TenderAI Ultimate", page_icon="🇮🇳", layout="wide")

# --- AUTHENTICATION (The Gatekeeper) ---
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

    st.title("🔒 TenderAI Secure Login")
    st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("❌ Access Denied")
    return False

if not check_password():
    st.stop()

# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Feature 1: Multi-Language Support
    language = st.selectbox("Output Language", ["English", "Hindi", "Telugu"])
    
    st.divider()
    st.info(f"Logged in as: Admin\nModel: Gemini 2.5 Flash")

# API Key Check
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ API Key missing. Please add GOOGLE_API_KEY to Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- MAIN APP UI ---
st.title("🇮🇳 AI Tender Assistant (Ultimate)")
st.caption("Extract • Analyze • Draft • Chat")

uploaded_file = st.file_uploader("Upload Tender Document (PDF)", type="pdf")

if uploaded_file:
    # Save temp file
    with open("temp_tender.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("File Uploaded! ✅")
    
    # Create Tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "✅ Compliance", "📝 Draft Letter", "💬 Chat with Tender"])

    # SHARED PROCESSING (We analyze once, use everywhere)
    if st.button("🚀 Run Full Analysis"):
        with st.spinner("Processing Document... (This may take 15 seconds)"):
            try:
                myfile = genai.upload_file("temp_tender.pdf")
                time.sleep(2) # Buffer for upload
                
                # Use the powerful 2.5 model
                model = genai.GenerativeModel('gemini-2.5-flash')

                # --- TAB 1: SUMMARY ---
                prompt_summary = f"""
                Analyze this tender document.
                Extract the following details into a Markdown Table:
                - Project Name
                - Estimated Cost
                - EMD Amount
                - Bid Submission Deadline
                - Financial Turnover Required
                - Technical Experience Required
                
                IMPORTANT: Translate the entire summary into {language}.
                """
                response_summary = model.generate_content([prompt_summary, myfile])
                
                # --- TAB 2: COMPLIANCE MATRIX ---
                prompt_compliance = f"""
                Scan the document for "Technical Specifications" and "Qualification Criteria".
                Create a Markdown Table with 3 columns:
                1. Requirement Description (Translate to {language})
                2. Page Number Reference
                3. Compliance Status (Leave blank for user)
                """
                response_compliance = model.generate_content([prompt_compliance, myfile])

                # --- TAB 3: BID LETTER ---
                prompt_letter = f"""
                Write a formal Bid Submission Cover Letter for this tender.
                Use professional {language} (or English if English is selected).
                Ensure it is formatted as a formal business letter.
                """
                response_letter = model.generate_content([prompt_letter, myfile])

                # Store results in session state so they don't disappear
                st.session_state['summary'] = response_summary.text
                st.session_state['compliance'] = response_compliance.text
                st.session_state['letter'] = response_letter.text
                st.session_state['file_ready'] = True
                st.session_state['myfile'] = myfile # Keep file reference for chat

            except Exception as e:
                st.error(f"Error during analysis: {e}")

    # --- DISPLAY RESULTS (If analysis is done) ---
    if st.session_state.get('file_ready'):
        
        with tab1:
            st.subheader(f"📊 Executive Summary ({language})")
            st.markdown(st.session_state['summary'])
        
        with tab2:
            st.subheader("✅ Compliance Matrix")
            st.markdown(st.session_state['compliance'])
            st.download_button("Download Compliance Matrix", st.session_state['compliance'], file_name="compliance.md")
        
        with tab3:
            st.subheader("📝 Bid Submission Letter")
            st.text_area("Copy your letter:", st.session_state['letter'], height=400)
        
        with tab4:
            st.subheader("💬 Ask the Tender")
            user_question = st.text_input("Ask anything (e.g., 'Is Joint Venture allowed?'):")
            if user_question:
                with st.spinner("Thinking..."):
                    try:
                        # Re-use the file reference from session state
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        q_prompt = f"Answer this question based ONLY on the provided tender document: {user_question}. Answer in {language}."
                        answer = model.generate_content([q_prompt, st.session_state['myfile']])
                        st.write(answer.text)
                    except Exception as e:
                        st.error("Session expired. Please re-upload to chat.")
