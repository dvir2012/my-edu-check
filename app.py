import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API ---
# שים לב: אם ה-Key הזה לא עובד, תצטרך להוציא חדש ב-Google AI Studio
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב הממשק (שילוב כהה-בהיר) ---
st.set_page_config(page_title="EduCheck AI PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; direction: rtl; text-align: right; }
    .main-header { 
        background: #1e293b; color: white; padding: 2rem; 
        border-radius: 20px; text-align: center; margin-bottom: 2rem;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #f1f5f9 !important; color: #1e293b !important;
        border: 2px solid #cbd5e1 !important; border-radius: 10px !important;
    }
    .stButton>button {
        background: #2563eb; color: white; border-radius: 12px;
        font-weight: bold; width: 100%; height: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. מבנה התפריט והאפליקציה ---
st.markdown("<div class='main-header'><h1>EduCheck AI PRO 🧠</h1><p>בדיקת מבחנים חכמה בעברית</p></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📝 דף תרגול א-ת"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 פרטים")
        student_name = st.text_input("שם התלמיד:")
        rubric = st.text_area("מחוון תשובות (מה נכון?):", height=150)

    with col2:
        st.subheader("📸 העלאה")
        img_file = st.file_uploader("העלה צילום מבחן", type=['png', 'jpg', 'jpeg'])
        camera_img = st.camera_input("או צלם")

    final_img = camera_img if camera_img else img_file

    if st.button("בדוק עכשיו ⚡"):
        if final_img and student_name:
            with st.spinner("מנתח..."):
                try:
                    img = Image.open(final_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח את המבחן של {student_name} לפי המחוון: {rubric}. תמלל את התשובות, תן ציון ומשוב בעברית."
                    response = model.generate_content([prompt, img])
                    
                    st.success("הבדיקה הושלמה!")
                    st.markdown("### תוצאות:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"שגיאה בחיבור ל-AI: {e}")
        else:
            st.warning("נא למלא שם ולהעלות תמונה.")

with tab2:
    st.subheader("דף איסוף כתב יד להדפסה")
    letters = ['א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ','ך','ל','מ','ם','נ','ן','ס','ע','פ','ף','צ','ץ','ק','ר','ש','ת']
    cols = st.columns(4)
    for i, l in enumerate(letters):
        cols[i % 4].markdown(f"<div style='border:1px solid #ccc; padding:10px; text-align:center; background:white; color:black;'>{l} = <br><br></div>", unsafe_allow_html=True)
