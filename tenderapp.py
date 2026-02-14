import streamlit as st
import google.generativeai as genai
import os

st.title("👨‍⚕️ App Doctor")

# 1. Check Library Version
st.write(f"**Google Library Version:** `{genai.__version__}`")
st.write("(We need version `0.7.0` or higher for Flash)")

# 2. Check API Key
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ No API Key found in Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# 3. List Available Models
st.subheader("📋 Models Available to this Server:")
try:
    models = genai.list_models()
    found_flash = False
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            st.write(f"- `{m.name}`")
            if "flash" in m.name:
                found_flash = True
    
    if found_flash:
        st.success("✅ Flash model found! We just need to copy the exact name above.")
    else:
        st.warning("⚠️ No Flash model found. We might need to use 'gemini-pro'.")

except Exception as e:
    st.error(f"Error listing models: {e}")

# 4. Test Generation
if st.button("Test Connection"):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        st.success(f"✅ It works! Response: {response.text}")
    except Exception as e:
        st.error(f"❌ Test Failed: {e}")
