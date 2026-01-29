import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ותרגומים ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck AI PRO", "sub": "מערכת חכמה לבדיקת מבחנים",
        "teacher_zone": "🔐 מרחב מורה", "id_label": "קוד מורה:", "student_new": "+ תלמיד חדש",
        "student_list": "בחר תלמיד:", "exam_upload": "📸 העלאת מבחן", "rubric_label": "🎯 מחוון בדיקה",
        "btn_check": "התחל ניתוח AI", "style_label": "סגנון בדיקה:", "error_api": "מפתח API חסר!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck AI PRO", "sub": "Smart Exam Analysis System",
        "teacher_zone": "🔐 Teacher Zone", "id_label": "Teacher ID:", "student_new": "+ New Student",
        "student_list": "Select Student:", "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Grading Rubric",
        "btn_check": "Start AI Analysis", "style_label": "Grading Style:", "error_api": "Missing API Key!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك برو", "sub": "نظام ذكي لتقييم الامتحانات",
        "teacher_zone": "🔐 منطقة المعلم", "id_label": "رمز المعلم:", "student_new": "+ طالب جديد",
        "student_list": "اختر طالب:", "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ تحليل الذكاء الاصطناعي", "style_label": "أسلوب التقييم:", "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Pro", layout="wide")

# בחירת שפה - תמיד מוצגת
selected_lang = st.sidebar.selectbox("🌐 Select Language / בחר שפה", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב טכנולוגי מתקדם (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700;800&family=Orbitron:wght@400;700&display=swap');
    
    .stApp {{
        background-color: #0e1117;
        color: #ffffff;
        direction: {L['dir']};
        text-align: {L['align']};
    }}
    
    /* כותרת בסגנון הייטק */
    .main-header {{
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 0px 10px 20px rgba(0,210,255,0.3);
    }}
    
    /* עיצוב כפתורים */
    div.stButton > button {{
        background: linear-gradient(45deg, #00c6ff, #0072ff);
        border: none;
        color: white;
        padding: 20px;
        border-radius: 12px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: 0.4s;
        text-transform: uppercase;
    }}
    
    div.stButton > button:hover {{
        box-shadow: 0px 0px 20px #00c6ff;
        transform: scale(1.02);
    }}

    /* עיצוב קונטיינרים */
    [data-testid="stVerticalBlock"] > div {{
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* התאמת הסיידבר */
    [data-testid="stSidebar"] {{
        background-color: #161b22;
        border-{ 'left' if L['dir'] == 'rtl' else 'right' }: 1px solid #30363d;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. חיבור ל-API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error(L["error_api"])
    st.stop()

# --- 4. תוכן האפליקציה ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #8b949e; font-size: 1.2rem; margin-top: -15px;'>{L['sub']}</p>", unsafe_allow_html=True)

# כניסה בסיידבר
st.sidebar.markdown(f"### {L['teacher_zone']}")
