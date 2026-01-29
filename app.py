import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות ועיצוב קיצי ---
st.set_page_config(page_title="EduCheck Summer PRO", layout="wide", page_icon="☀️")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%); }
    .main-header { color: #E67E22; text-align: center; font-family: 'Fredoka', sans-serif; font-size: 3rem; }
    div.stButton > button { background: linear-gradient(45deg, #FF8C00, #FAD02E); border-radius: 20px; color: white; border: none; padding: 10px 20px; }
    .stTextArea textarea { border-radius: 15px; border: 2px solid #FAD02E; }
    </style>
    """, unsafe_allow_html=True)

# חיבור ל-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")
    st.stop()

st.markdown("<h1 class='main-header'>EduCheck Summer ☀️</h1>", unsafe_allow_html=True)

# --- 2. סרגל צדי: ניהול מורה ומאגר תלמידים ---
st.sidebar.title("🍹 הגדרות מערכת")
teacher_id = st.sidebar.text_input("קוד מורה (לאבטחה):", type="password")

if not teacher_id:
    st.info("אנא הזן קוד מורה בסרגל הצדי כדי להתחיל.")
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# אזור רישום תלמיד חדש (העלאת מאגר אותיות)
with st.sidebar.expander("📝 רישום תלמיד חדש (מאגר אותיות)"):
    reg_name = st.text_input("שם התלמיד לרישום:")
    reg_samples = st.file_uploader("העלה דגימות כתב יד (2-3 תמונות):", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if st.button("שמור מאגר אותיות"):
        if reg_name and reg_samples:
            student_path = os.path.join(base_path, reg_name)
            if not os.path.exists(student_path): os.makedirs(student_path)
            for i, s in enumerate(reg_samples):
                with open(os.path.join(student_path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.success(f"המאגר עבור {reg_name} נוצר!")
            st.rerun()

# --- 3. אזור העבודה הראשי ---
st.markdown("### 🔍 שלב הבדיקה")
col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

with col1:
    st.subheader("👤 פרטי התלמיד")
    # רשימה נפתחת של תלמידים שקיימים במאגר
    existing_students = os.listdir(base_path)
    student_name = st.selectbox("בחר תלמיד מהמאגר:", [""] + existing_students)
    
with col2:
    st.subheader("📸 העלאת המבחן")
    exam_file = st.file_uploader("העלה את דף המבחן לבדיקה:", type=['png', 'jpg', 'jpeg'])

with col3:
    st.subheader("🎯 מחוון")
    rubric = st.text_area("הכנס את התשובות הנכונות:", height=100)

st.divider()

# --- 4. לוגיקה של ה-AI ---
