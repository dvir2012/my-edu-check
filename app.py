import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# 1. הגדרות שפה ומילון
LANG_DICT = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", "select_student": "👤 בחר תלמיד:", "exam_type": "📝 סוג המבחן:", "types": ["מבחן רגיל (פתוח)", "מבחן אמריקאי"], "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון / תשובות", "btn_check": "התחל בדיקה קיצית 🚀"},
    "English": {"dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", "select_student": "👤 Select Student:", "exam_type": "📝 Exam Type:", "types": ["Open Questions", "Multiple Choice"], "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric", "btn_check": "Start Summer Grading 🚀"},
    "العربية": {"dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", "select_student": "👤 اختر الطالب:", "exam_type": "📝 نوع الامتحان:", "types": ["امتحان عادي", "امتحان أمريكي"], "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة", "btn_check": "ابدأ التصحيح الصيفي 🚀"}
}

st.set_page_config(page_title="EduCheck Summer", layout="wide", page_icon="☀️")
selected_lang = st.sidebar.selectbox("🌐 Language", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# 2. עיצוב קיצי ובטוח (CSS)
st.markdown("<style>" + 
    ".stApp { background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%); direction: " + L['dir'] + "; text-align: " + L['align'] + "; }" +
    ".main-header { background: linear-gradient(90deg, #FF8C00 0%, #FAD02E 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; text-align: center; }" +
    "div.stButton > button { background: linear-gradient(45deg, #FF8C00, #FAD02E); border-radius: 20px; color: white; border: none; height: 3.5em; font-weight: bold; width: 100%; }" +
    "div.stButton > button:hover { transform: scale(1.02); box-shadow: 0px 4px 15px rgba(255, 140, 0, 0.3); }" +
    "</style>", unsafe_allow_html=True)

# 3. חיבור ל-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

st.markdown("<h1 class='main-header'>" + L['title'] + "</h1>", unsafe_allow_html=True)

# 4. סיידבר: קוד גישה ורישום
teacher_id = st.sidebar.text_input("🍹 קוד מורה / Teacher Code", type="password")
if not teacher_id:
    st.info("נא להזין קוד גישה בסיידבר כדי להתחיל")
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

with st.sidebar.expander("🏖️ רישום תלמיד חדש"):
    reg_name = st.text_input("שם התלמיד:")
    s1 = st.file_uploader("דגימת כתב 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימה 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימה 3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.button("שמור תלמיד במאגר"):
        if reg_name and s1 and s2 and s3:
            path = os.path.join(base_path, reg_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                Image.open(s).save(os.path.join(path, f"{i}.png"))
            st.success
