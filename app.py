import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב הממשק (שילוב בהיר-כהה) ---
st.set_page_config(page_title="EduCheck AI PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f1f5f9; direction: rtl; text-align: right; }
    .main-header { 
        text-align: center; font-weight: 900; font-size: 3rem; padding: 1.5rem;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #1e293b !important; color: #f8fafc !important; border-radius: 10px !important;
    }
    .stButton>button {
        width: 100%; background-color: #2563eb; color: white; border-radius: 12px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. פונקציית דף התרגול ---
def show_practice_sheet():
    letters = ['א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ','ך','ל','מ','ם','נ','ן','ס','ע','פ','ף','צ','ץ','ק','ר','ש','ת']
    st.write("### 📝 דף הכנה לאיסוף כתב יד")
    cols = st.columns(4)
    for i, letter in enumerate(letters):
        cols[i % 4].markdown(f"<div style='border: 2px solid #ccc; padding: 10px; text-align: center; margin-bottom: 5px; background: white;'><span style='font-size: 24px; color: black;'>{letter} = </span><br><br></div>", unsafe_allow_html=True)

# --- 4. מבנה האפליקציה ---
st.markdown("<div class='main-header'>EduCheck AI PRO 🧠</div>", unsafe_allow_html=True)

with st.sidebar:
    st.title("תפריט")
    mode = st.radio("בחר מצב:", ["בדיקת מבחן", "הדפסת דף תרגול"])

if mode == "הדפסת דף תרגול":
    show_practice_sheet()
else:
    st.success("✨ המערכת מחוברת ל-Gemini Vision ומזהה כתב יד!")
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        student_name = st.text_input("שם התלמיד:")
        rubric = st.text_area("מחוון תשובות:", height=150)

    with col2:
        source = st.file_uploader("העלה מבחן", type=['png', 'jpg', 'jpeg'])
        camera_img = st.camera_input("או צלם")

    final_img = camera_img if camera_img else source

    if st.button("בדוק מבחן ⚡") and final_img:
        with st.spinner("מנתח..."):
            img = Image.open(final_img)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"נתח את המבחן של {student_name} לפי המחוון: {rubric}. תמלל את התשובות ותן ציון."
            response = model.generate_content([prompt, img])
            st.info(response.text)
