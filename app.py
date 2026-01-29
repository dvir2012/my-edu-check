import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ומילון ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", 
        "sub": "בדיקת מבחנים בכיף ובקלות", "teacher_zone": "🍹 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד",
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה 3 דגימות כתב יד:",
        "save_btn": "שמור מאגר אותיות", "select_student": "בחר תלמיד:",
        "exam_type": "סוג המבחן:", "types": ["מבחן רגיל (פתוח)", "מבחן אמריקאי"],
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון / תשובות נכונות",
        "btn_check": "התחל בדיקה חכמה 🚀", "scan_msg": "מבצע סריקה עמוקה וחידוד ראייה...",
        "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", 
        "sub": "Easy & Breezy Grading", "teacher_zone": "🍹 Teacher Lounge",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "upload_samples": "Upload 3 Samples:",
        "save_btn": "Save Handwriting", "select_student": "Select Student:",
        "exam_type": "Exam Type:", "types": ["Open Questions", "Multiple Choice"],
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start Smart Analysis 🚀", "scan_msg": "Deep scanning...",
        "error_api": "Missing API Key!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", 
        "sub": "تصحيح الامتحانات بكل سهولة ومتعة", "teacher_zone": "🍹 منطقة المعلم",
        "id_label": "رمز الدخول:", "student_reg": "📝 تسجيل طالب جديد",
        "student_name_label": "اسم الطالب:", "upload_samples": "تحميل 3 نماذج للخط:",
        "save_btn": "حفظ القاعدة", "select_student": "اختر الطالب:",
        "exam_type": "نوع الامتحان:", "types": ["امتحان عادي", "امتحان أمريكي"],
        "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح 🚀", "scan_msg": "جاري التحليل...",
        "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide")
selected_lang = st.sidebar.selectbox("🌐 שפה / Language / اللغة", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב ויישור לימין (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%); direction: {L['dir']}; text-align: {L['align']}; }}
    [data-testid="stSidebar"], .stTextArea, .stTextInput, .stSelect
