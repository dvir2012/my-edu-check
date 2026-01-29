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
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה דגימות כתב יד:",
        "save_btn": "שמור מאגר אותיות", "select_student": "בחר תלמיד:",
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון",
        "btn_check": "התחל בדיקה חכמה 🚀", "scan_msg": "מנתח את המבחן...",
        "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", 
        "sub": "Easy & Breezy Grading", "teacher_zone": "🍹 Teacher Zone",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "upload_samples": "Upload Samples:",
        "save_btn": "Save Handwriting", "select_student": "Select Student:",
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start AI Analysis 🚀", "scan_msg": "Analyzing Exam...",
        "error_api": "Missing API Key!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide")

# בחירת שפה בסיידבר
selected_lang = st.sidebar.selectbox("🌐 שפה / Language", ["עברית", "English"])
L = LANG_DICT[selected_lang]

# --- 2. תיקון עיצוב ויישור לימין (RTL) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%);
        direction: {L['dir']};
        text-align: {L['align']};
    }}
    
    /* יישור כללי של אלמנטים */
    [data-testid="stSidebar"], .stTextArea, .stTextInput, .stSelectbox {{
        direction: {L['dir']} !important;
        text-align: {L['align']} !important;
    }}

    .main-header {{
        background: linear-gradient(90deg, #FF8C00 0%, #FAD02E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
    }}

    div.stButton > button {{
        background: linear-gradient(45deg, #FF8C00, #FAD02E);
        border-radius: 20px;
        color: white;
        border: none;
        width: 100%;
        height: 3em;
        font-size: 1.2rem;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. חיבור ל-API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error(L["error_api"])
    st.stop()

st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #E67E22; font-size: 1.2rem;'>{L['sub']}</p>", unsafe_allow_html=True)

# סיידבר
st.sidebar.title(L["teacher_zone"])
teacher_id = st.sidebar.text_input(L["id_label"], type="password")

if not teacher_id:
    st.info("אנא הכנס קוד מורה כדי להתחיל")
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# רישום תלמיד
with st.sidebar.expander(L["student_reg"]):
    reg_name = st.text_input(L["student_name_label"], key="reg_name")
    reg_samples = st.file_uploader(L["upload_samples"], type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if st.button(L["save_btn"]):
        if reg_name and reg_samples:
            student_path = os.path.join(base_path, reg_name)
            if not os.path.exists(student_path): os.makedirs(student_path)
            for i, s in enumerate(reg_samples):
                with open(os.path.join(student_path, f"sample_{i}.png"), "wb") as f:
                    f.write
