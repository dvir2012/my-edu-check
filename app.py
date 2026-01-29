import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ומילון ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", 
        "sub": "בדיקת מבחנים בכיף ובקלות", "teacher_zone": "🍹 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד (מאגר אותיות)",
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה דגימות כתב יד:",
        "save_btn": "שמור מאגר אותיות", "select_student": "בחר תלמיד מהמאגר:",
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון",
        "btn_check": "התחל בדיקה חכמה 🚀", "scan_msg": "מנתח את המבחן...",
        "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", 
        "sub": "Easy & Breezy Grading", "teacher_zone": "🍹 Teacher Zone",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry (Handwriting)",
        "student_name_label": "Student Name:", "upload_samples": "Upload Handwriting Samples:",
        "save_btn": "Save Handwriting Data", "select_student": "Select Student:",
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start AI Analysis 🚀", "scan_msg": "Analyzing Exam...",
        "error_api": "Missing API Key!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide")

# בחירת שפה בסיידבר
selected_lang = st.sidebar.selectbox("🌐 שפה / Language", ["עברית", "English"])
L = LANG_DICT[selected_lang]

# --- 2. תיקון עיצוב - הצמדה לימין (RTL) ---
# הקוד הזה הופך את כל האתר לימין אם בחרת עברית
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Fredoka:wght@400;600&display=swap');
    
    .stApp {{
        background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%);
        direction: {L['dir']};
        text-align: {L['align']};
        font-family: 'Assistant', sans-serif;
    }}
    
    /* הפיכת הסיידבר */
    [data-testid="stSidebar"] {{
        direction: {L['dir']};
        text-align: {L['align']};
    }}

    /* תיקון יישור לתיבות טקסט ותפריטים */
    .stTextArea textarea
    
